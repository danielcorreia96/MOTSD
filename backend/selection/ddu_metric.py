# coding=utf-8
import numpy as np


def ddu(matrix: np.ndarray):
    """
    Calculate DDU metric value for given activity matrix.

    Reference: Perez, Alexandre, Rui Abreu, and Arie van Deursen. "A test-suite diagnosability metric for
    spectrum-based fault localization approaches." Proceedings of the 39th International Conference on
    Software Engineering. IEEE Press, 2017.

    :param matrix: activity matrix
    :return: DDU value
    """
    return norm_density(matrix) * diversity(matrix) * uniqueness(matrix)


def norm_density(matrix: np.ndarray):
    """
    Calculate normalized density for a given activity matrix.

    :param matrix: activity matrix
    :return: normalized density value
    """
    return 1 - abs(1 - 2 * (np.count_nonzero(matrix) / matrix.size))


def diversity(matrix: np.ndarray):
    """
    Calculate test diversity for a given activity matrix.

    :param matrix: activity matrix
    :return: test diversity value
    """
    # using numpy magic from https://stackoverflow.com/a/27007787 to count identical rows
    dt = np.dtype((np.void, matrix.dtype.itemsize * matrix.shape[1]))
    b = np.ascontiguousarray(matrix).view(dt)
    _, cnt = np.unique(b, return_counts=True)

    numerator = sum(map(lambda x: x * (x - 1), cnt))
    denominator = matrix.shape[0] * (matrix.shape[0] - 1)
    if denominator == 0:
        return 0
    return 1 - numerator / denominator


def uniqueness(matrix: np.ndarray):
    """
    Calculate uniqueness for a given activity matrix.

    :param matrix: activity matrix
    :return: uniqueness value
    """
    # using numpy magic from https://stackoverflow.com/a/27007787 to count identical columns
    dt = np.dtype((np.void, matrix.T.dtype.itemsize * matrix.T.shape[1]))
    b = np.ascontiguousarray(matrix.T).view(dt)
    _, cnt = np.unique(b, return_counts=True)

    numerator = len(cnt)
    denominator = matrix.T.shape[0]
    if denominator == 0:
        return 0
    return numerator / denominator
