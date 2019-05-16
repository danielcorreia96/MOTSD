# coding=utf-8
import numpy as np


def ddu(particle, base):
    # consider only selected subset of matrix
    particle = np.array(particle)
    sub_matrix = base[particle == 1]
    if sub_matrix.size == 0:
        return 0

    p_res = norm_density(sub_matrix)
    g_res = diversity(sub_matrix)
    u_res = uniqueness(sub_matrix)
    return p_res * g_res * u_res


def norm_density(matrix):
    return 1 - abs(1 - 2 * (np.count_nonzero(matrix) / matrix.size))


def diversity(matrix):
    # using numpy magic from https://stackoverflow.com/a/27007787
    dt = np.dtype((np.void, matrix.dtype.itemsize * matrix.shape[1]))
    b = np.ascontiguousarray(matrix).view(dt)
    _, cnt = np.unique(b, return_counts=True)

    numerator = sum(map(lambda x: x * (x - 1), cnt))
    denominator = matrix.shape[0] * (matrix.shape[0] - 1)
    if denominator == 0:
        return 0
    return 1 - numerator / denominator


def uniqueness(matrix):
    # using numpy magic from https://stackoverflow.com/a/27007787
    dt = np.dtype((np.void, matrix.T.dtype.itemsize * matrix.T.shape[1]))
    b = np.ascontiguousarray(matrix.T).view(dt)
    _, cnt = np.unique(b, return_counts=True)

    numerator = len(cnt)
    denominator = matrix.T.shape[0]
    if denominator == 0:
        return 0
    return numerator / denominator
