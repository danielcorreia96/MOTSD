# coding=utf-8
import random
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List

import numpy as np
from faker import Factory

from backend.integrations.database import get_testfails_for_revision, has_missing_builds_for_revision
from backend.selection.problem_data import ProblemData


def print_function_values_to_screen(solutions, data):
    # Adapted from JMetalPy
    if type(solutions) is not list:
        solutions = [solutions]

    for solution in solutions:
        print(str(solutions.index(solution)) + ": ", sep="  ", end="", flush=True)
        print(solution.objectives, sep="  ", end="", flush=True)
        pos = np.array(solution.variables[0])
        rev_solution = list(data.tests_index[pos == 1])
        print(f" (sol_size: {len(rev_solution)})")


def print_results_summary(results):
    """

    :type results: List[RevisionResults]
    """

    def print_error_stats(message, pattern, executions):
        error_cases = [
            res for res in executions if pattern in res.error_no_changed_items
        ]
        red_error_cases = [res for res in error_cases if len(res.orig_rev_history) > 0]
        print(f"# {message}: {len(error_cases)} (red: {len(red_error_cases)})")

    def get_tool_executions(executions):
        return [res for res in executions if type(res.error_no_changed_items) != str]

    def get_tool_no_executions(executions):
        return [res for res in executions if type(res.error_no_changed_items) == str]

    def get_total_innocent_reds(executions):
        """

        :type executions: List[RevisionResults]
        """
        count = 0
        previous_fails = set()
        for res in executions:
            # If it is a tool execution over a red commit with no found tests
            if (
                type(res.error_no_changed_items) != str
                and len(res.orig_rev_history) > 0
                # and res.solution_score[0] == 0
            ):
                # If previous revision test fails is a superset, then the current commit is innocent
                if previous_fails.issuperset(res.orig_rev_history):
                    count += 1
                    res.innocent = True
            previous_fails = res.orig_rev_history
        return count

    def get_f1_score(solution_score):
        # 2 * precision * recall / (precision + recall)
        numerator = (
            2
            * (solution_score[1] / solution_score[3])
            * (solution_score[1] / solution_score[2])
        )
        denominator = (solution_score[1] / solution_score[3]) + (
            solution_score[1] / solution_score[2]
        )
        return numerator / denominator if denominator != 0 else 0

    tool_executions = get_tool_executions(results)
    tool_no_exec = get_tool_no_executions(results)
    total_innocent_reds = get_total_innocent_reds(results)

    red_commits = [res for res in results if len(res.orig_rev_history) > 0]
    commits_ = (len(red_commits) / len(results)) * 100
    print(f"# Commits - {len(results)} (red: {len(red_commits)} -> {commits_:.0f}%)")

    red_executions = [res for res in tool_executions if len(res.orig_rev_history) > 0]
    executions_ = (len(tool_executions) / len(results)) * 100
    print(
        f"Tool Executions: {len(tool_executions)} -> {executions_:.0f}% (red: {len(red_executions)})"
    )

    # Print error stats for no tool executions
    print_error_stats(
        message="No .cs files error",
        pattern="no covered .cs files",
        executions=tool_no_exec,
    )
    print_error_stats(
        message="No coverage data error",
        pattern="no coverage data",
        executions=tool_no_exec,
    )
    print_error_stats(
        message="New file error",
        pattern="new files or modified",
        executions=tool_no_exec,
    )

    # Print results regarding the tool's ability to find the red tests
    not_innocent_red_executions = [res for res in red_executions]
    not_found_red_tests = [
        res for res in not_innocent_red_executions if res.solution_score[0] == 0
    ]
    red_ignored_tests = [
        res for res in not_innocent_red_executions if res.solution_score[0] == -1
    ]
    found_red_tests_at_least_one = [
        res for res in not_innocent_red_executions if res.solution_score[0] > 0
    ]
    found_red_tests_at_least_half = [
        res for res in not_innocent_red_executions if res.solution_score[0] >= 50
    ]
    found_red_tests_all = [
        res for res in not_innocent_red_executions if res.solution_score[0] == 100
    ]

    valid_red_tests_scores = [
        res.solution_score[0]
        for res in not_innocent_red_executions
        if res.solution_score[0] >= 0 and res.solution_score[2] > 0
    ]

    valid_red_tests_precision = [
        res.solution_score[1] / res.solution_score[3]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_micro_precision_n = [
        res.solution_score[1]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_micro_precision_d = [
        res.solution_score[3]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_recall = [
        res.solution_score[1] / res.solution_score[2]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_micro_recall_n = [
        res.solution_score[1]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_micro_recall_d = [
        res.solution_score[2]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    valid_red_tests_f1 = [
        get_f1_score(res.solution_score) 
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    print("Tool Found Red Test(s) ?")
    print(f"Innocent Reds: {total_innocent_reds}")
    print(f"Only Ignored Tests: {len(red_ignored_tests)}")
    print(f"Score Stats (for actual reds)")
    print(f"No: {len(not_found_red_tests)}")
    print(f"Yes, At least one: {len(found_red_tests_at_least_one)}")
    print(f"Yes, +50%: {len(found_red_tests_at_least_half)}")
    print(f"Yes, 100%: {len(found_red_tests_all)}")
    print(f"Average Score: {sum(valid_red_tests_scores)/len(valid_red_tests_scores)}")

    print(
        f"Macro-Precision: {(sum(valid_red_tests_precision)/len(valid_red_tests_precision)) * 100}%"
    )
    print(
        f"Micro-Precision: {(sum(valid_red_tests_micro_precision_n)/sum(valid_red_tests_micro_precision_d)) * 100}%"
    )

    print(f"Macro-Recall: {(sum(valid_red_tests_recall)/len(valid_red_tests_recall)) * 100}%")
    print(f"Micro-Recall: {(sum(valid_red_tests_micro_recall_n)/sum(valid_red_tests_micro_recall_d)) * 100}%")
    print(f"F1 Score: {(sum(valid_red_tests_f1)/len(valid_red_tests_f1)) * 100}%")

    sizes = np.array([res.solution_score[3] for res in tool_executions])
    print(
        f"Sol Size (avg, min, max, std): ({np.average(sizes)}, {np.min(sizes)}, {np.max(sizes)}, {np.std(sizes)})"
    )
    pass


@dataclass
class RevisionResults:
    branch: str
    rev_id: str
    rev_date: datetime
    changelist: list
    error_no_changed_items: str
    solutions_found: list
    solution_score: tuple  # (score %, # matched, # expected, # tests)
    computing_time: float
    orig_rev_history: set
    real_rev_history: set
    innocent: bool

    def __init__(self, svn_log_entry, branch, ignored_tests, masked=False):
        self.branch = branch
        self.rev_id = svn_log_entry.revision
        self.rev_date = svn_log_entry.date
        self.changelist = svn_log_entry.changelist
        self.masked = masked

        self.error_no_changed_items = None
        self.innocent = None

        # get revision results from database
        rev_results = get_testfails_for_revision(revision=self.rev_id)
        self.orig_rev_history = set(rev_results.FULLNAME.values)

        self.missing_builds = False
        if len(self.orig_rev_history) == 0:
            self.missing_builds = has_missing_builds_for_revision(revision=self.rev_id)

        # Filter ignored tests from config
        self.real_rev_history = set(
            filter(
                lambda test: all(x not in test for x in ignored_tests),
                self.orig_rev_history,
            )
        )

        self.fake = Factory.create()

    def print_results(self, data: ProblemData):
        def get_fake_filename(file_changed):
            result = re.search(r"/.*\.(.*)", file_changed)
            if result is None:  # directory
                return self.fake.file_path(
                    depth=random.randint(3, 5),
                    extension=random.choice(
                        ["cs", "tsx", "json", "oml", "csproj", "xml"]
                    ),
                )
            else:
                extension = result.group(1)
                filename = self.fake.file_path(
                    depth=random.randint(3, 5), extension=" "
                )
                filename = "/".join([x.capitalize() for x in filename[:-1].split("/")])
                return filename + extension

        # basic info
        if self.masked:
            fake_changelist = [(x[0], get_fake_filename(x[1])) for x in self.changelist]
            changes = "\n\t".join(map(lambda x: str(x), fake_changelist))
        else:
            changes = "\n\t".join(map(lambda x: str(x), self.changelist))

        revision_id = f"rev_id: {self.rev_id} ({self.rev_date})"
        print(f"{revision_id}\nchangelist:\n\t{changes}")

        # execution results
        if type(self.error_no_changed_items) == str:
            # If no changed indexes were extracted, then print the error message
            print(f"Revision {self.rev_id} failed due to {self.error_no_changed_items}")
            self.print_revision_status()
        else:
            self.print_revision_status()
            self.print_execution_results(data)
            self.print_solution_list(data)
            self.print_execution_inspection(data)

        # separator
        print("==========================" * 4)

    def print_execution_results(self, data):
        print("Computing time: " + str(self.computing_time))
        print_function_values_to_screen(self.solutions_found, data)

        for i, solution in enumerate(self.solutions_found):
            pos = np.array(solution.variables[0])
            rev_solution = list(data.tests_index[pos == 1])
            if len(self.orig_rev_history) > 0:
                self.print_solution_score(i, rev_solution)
                # solution_tests = "\n\t".join(rev_solution)
                # print(f"\t{solution_tests}")
            else:
                self.solution_score = (0, 0, 0, len(rev_solution))

    def print_execution_inspection(self, data):
        def aux_loop(tests_data):
            available, impossible = 0, 0
            for test in self.real_rev_history:
                if any(x in test for x in tests_data):
                    # print(f"{test} = Available")
                    available += 1
                else:
                    print(f"\t{test} = Impossible")
                    impossible += 1
            print(f"Available={available} || Impossible={impossible}")

        print(f"Checking test availability against original data - {data.original_tests.shape}")
        aux_loop(data.original_tests)

        print(f"Checking test availability against filtered data - {data.tests_index.shape}")
        aux_loop(data.tests_index)

    def print_solution_list(self, data):
        def get_fake_test_name():
            test_name = self.fake.file_path(depth=random.randint(3, 5), extension=" ")
            test_name = test_name[1:-2].replace("/", ".")
            test_name = "Test." + ".".join(
                [x.capitalize() for x in test_name.split(".")]
            )
            return test_name

        solution = self.solutions_found[0]
        pos = np.array(solution.variables[0])
        if self.masked:
            rev_solution = list(data.tests_index[pos == 1])
            rev_solution = [get_fake_test_name() for _ in rev_solution]
        else:
            rev_solution = list(data.tests_index[pos == 1])

        print(f"Solution Size: {len(rev_solution)} tests")
        # solution_tests = "\n\t".join(rev_solution)
        # print(f"\t{solution_tests}")

    def print_solution_score(self, i, rev_solution):
        def get_matching_tests(rev_solution):
            return [
                test
                for test in self.real_rev_history
                if any(x in test for x in rev_solution)
            ]

        sol_size = len(rev_solution)
        sol_id = f"Solution {i} ({sol_size})"

        if len(self.real_rev_history) == 0:
            print(f"{sol_id} = only ignored tests")
            self.solution_score = (-1, 0, 0, sol_size)
        else:
            matching = get_matching_tests(rev_solution)
            score = (len(matching) / len(self.real_rev_history)) * 100
            match_vs_rev = f"{len(matching)}/{len(self.real_rev_history)}"
            if self.masked:
                print(f"{sol_id} = {match_vs_rev} ({score:.0f}%)")
            else:
                print(f"{sol_id} = {match_vs_rev} ({score:.0f}%) -> {matching}")

            self.solution_score = (
                score,
                len(matching),
                len(self.real_rev_history),
                sol_size,
            )

    def print_revision_status(self):
        if len(self.orig_rev_history) == 0:
            if self.missing_builds:
                print(f"Revision {self.rev_id} has missing builds")
            else:
                print(f"Revision {self.rev_id} had no failing tests")
        else:
            failed_tests = f"{len(self.orig_rev_history)} failed tests"
            if self.masked:
                print(f"Revision {self.rev_id} - {failed_tests}")
            else:
                joined = "\n\t".join(self.orig_rev_history)
                print(f"Revision {self.rev_id} - {failed_tests}:\n\t{joined}")
