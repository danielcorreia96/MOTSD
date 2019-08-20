# coding=utf-8
import pickle
from dataclasses import dataclass
from typing import List

import numpy as np

import backend.evaluation.utils
from backend.evaluation.execution_item import RevisionResults
from backend.selection.problem_data import ProblemData


@dataclass
class ResultsSummary:
    data: List[RevisionResults]
    commits: dict
    executions: dict
    errors: dict
    red_stats: dict
    solution_size: dict
    computing_time: dict
    orig_feedback_time: float
    new_feedback_time: dict

    def __init__(self, results: List[RevisionResults], data: ProblemData):
        tool_executions = backend.evaluation.utils.get_tool_executions(results)
        tool_no_exec = backend.evaluation.utils.get_tool_no_executions(results)
        total_innocent_reds = backend.evaluation.utils.get_total_innocent_reds(results)

        # Commits
        red_commits = [res for res in results if len(res.real_rev_history) > 0]
        self.commits = {
            "total": len(results),
            "red": len(red_commits),
            "red_p": len(red_commits) / len(results),
        }

        # Executions
        red_executions = [
            res for res in tool_executions if len(res.real_rev_history) > 0
        ]
        self.executions = {
            "total": len(tool_executions),
            "total_p": len(tool_executions) / len(results),
            "red": len(red_executions),
            "red_p": len(red_executions) / len(tool_executions),
        }

        # Errors
        error_cases = {
            "No .cs Files": "no covered .cs files",
            "No Coverage Data": "no coverage data",
            "New Files": "new files or modified",
        }
        self.errors = {}
        for error, pattern in error_cases.items():
            total, red = backend.evaluation.utils.get_error_stats(pattern, tool_no_exec)
            self.errors[error] = {"total": len(total), "red": len(red)}

        # Red Stats
        # Print results regarding the tool's ability to find the red tests
        not_innocent_red_executions = [
            res for res in red_executions if res.innocent is not True
        ]
        # not_innocent_red_executions = [res for res in red_executions]
        not_found_red_tests = [
            res for res in not_innocent_red_executions if res.solution_score[0] == 0
        ]
        red_ignored_tests = [
            res for res in not_innocent_red_executions if res.solution_score[0] == -1
        ]
        found_red_tests_at_least_one = [
            res for res in not_innocent_red_executions if res.solution_score[0] > 0
        ]

        self.red_stats = {
            "Innocent Reds": total_innocent_reds,
            "Only Ignored Tests": len(red_ignored_tests),
            "Valid Reds": len(not_innocent_red_executions),
            "No": len(not_found_red_tests) / len(not_innocent_red_executions),
            "At Least One": len(found_red_tests_at_least_one)
            / len(not_innocent_red_executions),
            "Macro-Precision": backend.evaluation.utils.get_macro_precision(
                not_innocent_red_executions
            ),
            "Micro-Precision": backend.evaluation.utils.get_micro_precision(
                not_innocent_red_executions
            ),
            "Macro-Recall": backend.evaluation.utils.get_macro_recall(
                not_innocent_red_executions
            ),
            "Micro-Recall": backend.evaluation.utils.get_micro_recall(
                not_innocent_red_executions
            ),
        }

        # Solution Size
        metric_keys = ["avg", "min", "max", "std", "P10", "P25", "P50", "P75", "P90"]
        sizes = np.array([res.solution_score[3] for res in tool_executions])
        self.solution_size = dict(
            zip(metric_keys, backend.evaluation.utils.get_metric_stats(sizes))
        )

        # Computing Time
        times = np.array(
            [res.computing_time for res in tool_executions if res.computing_time > 0]
        )
        self.computing_time = dict(
            zip(metric_keys, backend.evaluation.utils.get_metric_stats(times))
        )

        # Original Feedback Time
        self.orig_feedback_time = sum(data.history_test_execution_times.values())

        # New Feedback Time
        feedback_times = np.array(
            [
                res.new_feedback_time
                for res in tool_executions
                if res.new_feedback_time > 0
            ]
        )
        self.new_feedback_time = dict(
            zip(metric_keys, backend.evaluation.utils.get_metric_stats(feedback_times))
        )

        # Store data
        self.data = results
        for res in self.data:
            res.solutions_found = []

    def export_to_text(self):
        commits = list(self.commits.values())
        print(f"# Commits - {commits[0]} (red: {commits[1]} -> {commits[2]*100:.0f}%)")

        execs = list(self.executions.values())
        print(
            f"Tool Executions: {execs[0]} -> {execs[1]*100:.0f}% "
            f" (red: {execs[2]} - {execs[3]*100:.0f}%)"
        )

        for error, [total, red] in self.errors.items():
            print(
                f"# {error}: {self.errors[error][total]} (red: {self.errors[error][red]})"
            )

        print("Tool Found Red Test(s) ?")
        red_stats = list(self.red_stats.values())
        print(f"Innocent Reds: {red_stats[0]}")
        print(f"Only Ignored Tests: {red_stats[1]}")
        print(f"Score Stats (for actual reds)")
        print(f"Valid Reds: {red_stats[2]}")
        print(f"No: {red_stats[3] * 100:.0f}%")
        print(f"Yes, At least one: {red_stats[4] * 100:.0f}%")
        print(f"Macro-Precision: {red_stats[5] * 100:.0f}%")
        print(f"Micro-Precision: {red_stats[6] * 100:.0f}%")
        print(f"Macro-Recall: {red_stats[7] * 100:.0f}%")
        print(f"Micro-Recall: {red_stats[8] * 100:.0f}%")

        solution_size = list(self.solution_size.values())
        self.print_metric_stats("Solution Size", solution_size)

        computing_time = list(self.computing_time.values())
        self.print_metric_stats("Computing Time", computing_time)

        print(f"Original Feedback Time: {self.orig_feedback_time:.0f}")
        feedback_time = list(self.new_feedback_time.values())
        self.print_metric_stats("New Feedback Time", feedback_time)

    def export_to_pickle(self, file):
        import gc

        gc.collect()
        pickle.dump(self, file, protocol=pickle.HIGHEST_PROTOCOL)

    def export_to_csv_line(self, only_stats=False):
        line = []
        if not only_stats:
            line.extend(list(self.commits.values()))
            line.extend(list(self.executions.values()))

            for error, [total, red] in self.errors.items():
                line.extend([self.errors[error][total], self.errors[error][red]])

        line.extend(list(self.red_stats.values()))
        line.extend(list(self.solution_size.values()))
        line.extend(list(self.computing_time.values()))
        line.extend([int(self.orig_feedback_time)])
        line.extend(list(self.new_feedback_time.values()))

        # stringify items
        line = [str(x) for x in line]
        return "|".join(line)

    @staticmethod
    def print_metric_stats(name, data):
        """
            Print avg, min, max, stdev + percentiles (10, 25, 50, 75, 90)
        """

        def unpack(values):
            return ",".join(str(x) for x in values)

        stats, percentiles = data[0:4], data[4:]

        print(f"{name} (avg, min, max, std): ({unpack(stats)})")
        print(f"{name} Percentiles (10, 25, 50, 75, 90): ({unpack(percentiles)})")
