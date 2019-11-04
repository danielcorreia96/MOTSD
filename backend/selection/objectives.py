# coding=utf-8
import numpy as np

from jmetal.core.solution import BinarySolution

from backend.selection.ddu_metric import ddu
from backend.selection.test_selection import TestSelection

def get_selected_matrix(particle: list, activity_matrix: np.ndarray) -> np.ndarray:
    """
    Get subset of the activity matrix selected by the particle.

    :param particle: a particle representing a candidate selection
    :param activity_matrix: full activity matrix
    :return: selected subset of the activity matrix
    """
    particle = np.array(particle)
    sub_matrix = activity_matrix[particle == 1]
    return sub_matrix

def calculate_ddu(problem: TestSelection, solution: BinarySolution) -> float:
    """
    Calculate DDU metric for a candidate solution.

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: DDU value
    """
    sub_matrix = get_selected_matrix(solution.variables[0], problem.activity_matrix)
    if sub_matrix.size == 0:
        return 0

    ddu_value = ddu(sub_matrix)
    return round(-1 * ddu_value, 2)


def calculate_norm_coverage(problem: TestSelection, solution: BinarySolution) -> float:
    """
    Calculate normalized coverage for a candidate solution.

    Note: the return value is negated to support objective maximization

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: normalized coverage value
    """
    sub_matrix = get_selected_matrix(solution.variables[0], problem.activity_matrix)
    if sub_matrix.size == 0:
        return 0

    sum_tests = np.sum(sub_matrix, axis=0)
    sum_tests[sum_tests > 0] = 1  # normalize to 1/0
    return -1 * (np.sum(sum_tests) / sub_matrix.shape[1])


def calculate_coverage(problem: TestSelection, solution: BinarySolution) -> float:
    """
    Calculate coverage without normalization for a candidate solution.

    Note: the return value is negated to support objective maximization

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: coverage value without normalization
    """
    # consider only selected subset of matrix
    sub_matrix = get_selected_matrix(solution.variables[0], problem.activity_matrix)
    if sub_matrix.size == 0:
        return 0

    sum_tests = np.sum(sub_matrix, axis=0)
    return -1 * (np.sum(sum_tests) / sub_matrix.shape[1])


def calculate_number_of_tests(problem: TestSelection, solution: BinarySolution) -> int:
    """
    Calculate total number of tests selected for a candidate solution.

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: total number of tests selected
    """
    total_tests = len(problem.tests_index[solution.variables[0]])
    if total_tests == 0:
        total_tests = 123456
    return total_tests


def calculate_history_test_fails(problem: TestSelection, solution: BinarySolution) -> int:
    """
    Calculate total previous test failures for a candidate solution.

    Note: the return value is negated to support objective maximization

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: total previous test failures
    """
    testfails_history = _parse_history_to_list(
        problem.history_test_fails, problem.tests_index[solution.variables[0]]
    )
    return -1 * sum(testfails_history)


def calculate_history_test_exec_times(problem: TestSelection, solution: BinarySolution) -> float:
    """
    Calculate total execution time for a candidate solution.

    :param problem: the test selection problem instance
    :param solution: a candidate solution
    :return: total execution time
    """
    test_exec_time_history = _parse_history_to_list(
        problem.history_test_exec_times, problem.tests_index[solution.variables[0]]
    )
    return sum(test_exec_time_history)


def _parse_history_to_list(history_results: dict, selected_tests: np.ndarray) -> list:
    """
    Helper method to parse an historical metrics map into a list of values based on the selected tests.

    :param history_results: map of historical metrics
    :param selected_tests: list of selected tests names
    :return: list of historical metric values
    """
    return [history_results.get(test, 0) for test in selected_tests]
