# coding=utf-8
import numpy as np

from jmetal.core.solution import BinarySolution

from backend.selection.ddu_metric import ddu
from backend.selection.test_selection import TestSelection


def calculate_ddu(problem: TestSelection, solution: BinarySolution):
    """
    Objective - DDU

    :param problem:
    :param solution:
    :return:
    """
    ddu_value = ddu(solution.variables[0], problem.activity_matrix)
    return round(-1 * ddu_value, 2)


def calculate_norm_coverage(problem: TestSelection, solution: BinarySolution):
    """
    Objective - Coverage

    :param problem:
    :param solution:
    :return:
    """
    # consider only selected subset of matrix
    particle = np.array(solution.variables[0])
    sub_matrix = problem.activity_matrix[particle == 1]
    if sub_matrix.size == 0:
        return 0

    sum_tests = np.sum(sub_matrix, axis=0)
    sum_tests[sum_tests > 0] = 1  # normalize to 1/0
    return -1 * (np.sum(sum_tests) / sub_matrix.shape[1])


def calculate_coverage(problem: TestSelection, solution: BinarySolution):
    """
    Objective - Coverage

    :param problem:
    :param solution:
    :return:
    """
    # consider only selected subset of matrix
    particle = np.array(solution.variables[0])
    sub_matrix = problem.activity_matrix[particle == 1]
    if sub_matrix.size == 0:
        return 0

    sum_tests = np.sum(sub_matrix, axis=0)
    return -1 * (np.sum(sum_tests) / sub_matrix.shape[1])


def calculate_number_of_tests(problem: TestSelection, solution: BinarySolution):
    """
    Objective - Total Tests Selected

    :param problem:
    :param solution:
    :return:
    """
    total_tests = len(problem.tests_index[solution.variables[0]])
    if total_tests == 0:
        total_tests = 123456
    return total_tests


def calculate_history_test_fails(problem: TestSelection, solution: BinarySolution):
    """
    Objective - Total Previous Test Failures

    :param problem:
    :param solution:
    :return:
    """
    testfails_history = _parse_history_to_list(
        problem.history_test_fails, problem.tests_index[solution.variables[0]]
    )
    return -1 * sum(testfails_history)


def calculate_history_test_exec_times(problem: TestSelection, solution: BinarySolution):
    """
    Objective - Total Execution Times

    :param problem:
    :param solution:
    :return:
    """
    test_exec_time_history = _parse_history_to_list(
        problem.history_test_exec_times, problem.tests_index[solution.variables[0]]
    )
    return sum(test_exec_time_history)


def _parse_history_to_list(history_results: dict, selected_tests: np.ndarray):
    return [history_results.get(test, 0) for test in selected_tests]
