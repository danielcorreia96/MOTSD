# coding=utf-8
from typing import List

import numpy as np

from backend.selection.demo_stats import RevisionResults
from backend.selection.problem_data import ProblemData


def print_results_summary(results: List[RevisionResults], data: ProblemData):
    csv_line = []
    tool_executions = get_tool_executions(results)
    tool_no_exec = get_tool_no_executions(results)
    total_innocent_reds = get_total_innocent_reds(results)

    red_commits = [res for res in results if len(res.orig_rev_history) > 0]
    commits_ = (len(red_commits) / len(results)) * 100
    print(f"# Commits - {len(results)} (red: {len(red_commits)} -> {commits_:.0f}%)")
    csv_line.extend([len(results)])

    red_executions = [res for res in tool_executions if len(res.orig_rev_history) > 0]
    executions_ = (len(tool_executions) / len(results)) * 100
    print(
        f"Tool Executions: {len(tool_executions)} "
        f"-> {executions_:.0f}% (red: {len(red_executions)})"
    )
    csv_line.extend([len(tool_executions), executions_, len(red_executions)])

    # Print error stats for no tool executions
    csv_line.extend(
        print_error_stats(
            message="No .cs files error",
            pattern="no covered .cs files",
            executions=tool_no_exec,
        )
    )

    csv_line.extend(
        print_error_stats(
            message="No coverage data error",
            pattern="no coverage data",
            executions=tool_no_exec,
        )
    )

    csv_line.extend(
        print_error_stats(
            message="New file error",
            pattern="new files or modified",
            executions=tool_no_exec,
        )
    )

    # Print results regarding the tool's ability to find the red tests
    # not_innocent_red_executions = [res for res in red_executions if res.innocent is not True]
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

    print("Tool Found Red Test(s) ?")
    print(f"Innocent Reds: {total_innocent_reds}")
    print(f"Only Ignored Tests: {len(red_ignored_tests)}")
    print(f"Score Stats (for actual reds)")
    print(f"No: {len(not_found_red_tests)}")
    print(f"Yes, At least one: {len(found_red_tests_at_least_one)}")
    print(f"Yes, +50%: {len(found_red_tests_at_least_half)}")
    print(f"Yes, 100%: {len(found_red_tests_all)}")
    csv_line.extend([len(not_found_red_tests), len(found_red_tests_at_least_one)])

    red_tests_precision = [
        res.solution_score[1] / res.solution_score[3]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0 and res.solution_score[3] > 0
    ]

    red_tests_micro_precision_n = [
        res.solution_score[1]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    red_tests_micro_precision_d = [
        res.solution_score[3]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    red_tests_recall = [
        res.solution_score[1] / res.solution_score[2]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    red_tests_micro_recall_n = [
        res.solution_score[1]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    red_tests_micro_recall_d = [
        res.solution_score[2]
        for res in not_innocent_red_executions
        if res.solution_score[2] > 0
    ]

    macro_precision = sum(red_tests_precision) / len(red_tests_precision)
    micro_precision = sum(red_tests_micro_precision_n) / sum(
        red_tests_micro_precision_d
    )
    macro_recall = sum(red_tests_recall) / len(red_tests_recall)
    micro_recall = sum(red_tests_micro_recall_n) / sum(red_tests_micro_recall_d)

    print(f"Macro-Precision: {macro_precision * 100:.0f}%")
    print(f"Micro-Precision: {micro_precision * 100:.0f}%")
    print(f"Macro-Recall: {macro_recall * 100:.0f}%")
    print(f"Micro-Recall: {micro_recall * 100:.0f}%")
    csv_line.extend([macro_precision, micro_precision, macro_recall, micro_recall])

    sizes = np.array([res.solution_score[3] for res in tool_executions])
    csv_line.extend(print_metric_stats(name="Solution Size ", data=sizes))

    times = np.array([res.computing_time for res in tool_executions])
    print(f"Average Computing Time: {np.average(times):.0f}")
    csv_line.extend([np.average(times)])

    original_feedback_time = sum(data.history_test_execution_times.values())
    feedback_times = np.array([res.new_feedback_time for res in tool_executions])
    print(f"Original Feedback Time: {original_feedback_time:.0f}")
    csv_line.extend(print_metric_stats(name="New Feedback Time", data=feedback_times))

    print("|".join(str(x) for x in csv_line))

    pass


def print_error_stats(message, pattern, executions):
    error_cases = [res for res in executions if pattern in res.error_no_changed_items]
    red_error_cases = [res for res in error_cases if len(res.orig_rev_history) > 0]
    print(f"# {message}: {len(error_cases)} (red: {len(red_error_cases)})")
    return [len(error_cases)]


def print_metric_stats(name, data):
    """
        Print avg, min, max, stdev + percentiles (10, 25, 50, 75, 90)
    """

    def unpack(values):
        return ",".join(str(x) for x in values)

    stats = [np.average(data), np.min(data), np.max(data), np.std(data)]
    percentiles = [np.percentile(data, p) for p in [10, 25, 50, 75, 90]]

    print(f"{name} (avg, min, max, std): ({unpack(stats)})")
    print(f"{name} Percentiles (10, 25, 50, 75, 90): ({unpack(percentiles)})")
    return [*stats, *percentiles]


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
