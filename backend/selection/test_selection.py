# coding=utf-8
import random
from typing import List

from jmetal.core.problem import BinaryProblem
from jmetal.core.solution import BinarySolution
from jmetal.operator import BitFlipMutation
from jmetal.util.archive import CrowdingDistanceArchive
from jmetal.util.termination_criterion import StoppingByEvaluations

from backend.selection.binary_mopso import BMOPSO
from backend.selection.problem_data import ProblemData


class TestSelection(BinaryProblem):
    def __init__(self, problem_data: ProblemData, objectives: List):
        super(TestSelection, self).__init__()
        self.objectives = objectives
        self.activity_matrix = problem_data.activity_matrix
        self.tests_index = problem_data.tests_index
        self.methods_index = problem_data.methods_index
        self.history_test_fails = problem_data.history_test_fails
        self.history_test_exec_times = problem_data.history_test_execution_times

        self.number_of_tests = self.activity_matrix.shape[0]
        # self.number_of_objectives = 2
        self.number_of_objectives = len(objectives)
        self.number_of_variables = 1
        self.number_of_constraints = 0

        # self.obj_directions = [self.MAXIMIZE, self.MAXIMIZE]
        # self.obj_labels = ["DDU", "Total Previous Test Failures"]
        # self.obj_directions = [self.MAXIMIZE, self.MAXIMIZE, self.MINIMIZE]
        # self.obj_labels = ['DDU', '# Test Failures', '# Tests Selected']

    def get_name(self) -> str:
        return "Test Selection Problem"

    def create_solution(self) -> BinarySolution:
        random.seed(123)
        new_solution = BinarySolution(
            number_of_variables=self.number_of_variables,
            number_of_objectives=self.number_of_objectives,
        )

        new_solution.variables[0] = [
            True if random.randint(0, 1) == 0 else False
            for _ in range(self.number_of_tests)
        ]

        return new_solution

    def evaluate(self, solution: BinarySolution) -> BinarySolution:
        solution.objectives = [func(self, solution) for func in self.objectives]
        return solution


def my_binary_mopso(problem: TestSelection):
    return BMOPSO(
        problem=problem,
        swarm_size=200,
        epsilon=0.075,
        mutation=BitFlipMutation(probability=0.5),
        leaders=CrowdingDistanceArchive(100),
        termination_criterion=StoppingByEvaluations(max=1000),
    )
