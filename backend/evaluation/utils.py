# coding=utf-8
from typing import List, Tuple

import numpy as np

from backend.evaluation.execution_item import RevisionResults


def get_metric_stats(data: np.ndarray) -> List[int]:
    """
    Calculate basic stats and percentiles for the given metric data points.

    - Stats: average, min, max, standard deviation
    - Percentiles: 10, 25, 50, 75, 90

    :param data: array of metric values
    :return: list of  stats and percentiles values
    """
    stats = [np.average(data), np.min(data), np.max(data), np.std(data)]
    percentiles = [np.percentile(data, p) for p in [10, 25, 50, 75, 90]]
    return list(map(int, [*stats, *percentiles]))


def get_micro_recall(executions: List[RevisionResults]) -> float:
    """
    Calculate micro-averaged recall for a list of tool executions.

    :param executions: list of RevisionResults objects
    :return: micro-recall value
    """
    micro_recall_n = [res.score[1] for res in executions if res.score[2] > 0]
    micro_recall_d = [res.score[2] for res in executions if res.score[2] > 0]
    return sum(micro_recall_n) / sum(micro_recall_d)


def get_macro_recall(executions: List[RevisionResults]) -> float:
    """
    Calculate macro-averaged recall for a list of tool executions.

    :param executions: list of RevisionResults objects
    :return: macro-recall value
    """
    red_tests_recall = [
        res.score[1] / res.score[2] for res in executions if res.score[2] > 0
    ]
    return sum(red_tests_recall) / len(red_tests_recall)


def get_micro_precision(executions: List[RevisionResults]) -> float:
    """
    Calculate micro-averaged precision for a list of tool executions.

    :param executions: list of RevisionResults objects
    :return: micro-precision value
    """
    micro_precision_n = [res.score[1] for res in executions if res.score[2] > 0]
    micro_precision_d = [res.score[3] for res in executions if res.score[2] > 0]
    return sum(micro_precision_n) / sum(micro_precision_d)


def get_macro_precision(executions: List[RevisionResults]) -> float:
    """
    Calculate macro-averaged precision for a list of tool executions.

    :param executions: list of RevisionResults objects
    :return: macro-precision value
    """
    red_tests_precision = [
        res.score[1] / res.score[3]
        for res in executions
        if res.score[2] > 0 and res.score[3] > 0
    ]
    return sum(red_tests_precision) / len(red_tests_precision)


def get_error_stats(
    pattern: str, executions: List[RevisionResults]
) -> Tuple[List, List]:
    """
    Get lists of execution results with a given error message for all commits and for only red commits.

    :param pattern: error message pattern to search for
    :param executions: list of execution results
    :return: two lists of execution results: one for all commits, another only for red commits
    """
    error_cases = [res for res in executions if pattern in res.error_no_changed_items]
    red_error_cases = [res for res in error_cases if len(res.real_rev_history) > 0]
    return error_cases, red_error_cases


def get_tool_executions(executions: List[RevisionResults]) -> List[RevisionResults]:
    """
    Get only the tool executions from a list of execution results.

    :param executions: list of execution results
    :return: list of tool executions
    """
    return [res for res in executions if type(res.error_no_changed_items) != str]


def get_tool_no_executions(executions: List[RevisionResults]) -> List[RevisionResults]:
    """
    Get only the failed tool executions from a list of execution results.

    :param executions: list of execution results
    :return: list of failed tool executions
    """
    return [res for res in executions if type(res.error_no_changed_items) == str]


def get_total_innocent_reds(executions: List[RevisionResults]) -> int:
    """
    Get number of innocent red commits from a given list of execution results.

    :param executions: list of execution results
    :return: number of innocent red commits
    """
    count = 0
    previous_fails = set()
    for res in executions:
        copy_res = res.real_rev_history.copy()
        # If it is a tool execution over a red commit
        if type(res.error_no_changed_items) != str and len(res.real_rev_history) > 0:
            # If previous revision test fails is a superset, then the current commit is innocent
            if previous_fails.issuperset(res.real_rev_history):
                count += 1
                res.innocent = True

            # Filter tests present in previous revision test fails
            # res.real_rev_history = set(filter(lambda x: x not in previous_fails, res.real_rev_history))
            # # If the new set of test fails is empty, then the current commit is innocent
            # if len(res.real_rev_history) == 0:
            #     count += 1
            #     res.innocent = True
        previous_fails = copy_res
    return count
