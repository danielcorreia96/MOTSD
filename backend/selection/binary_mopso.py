# coding=utf-8
import random
from copy import copy
from typing import List, Optional

import numpy
from jmetal.config import store
from jmetal.core.algorithm import ParticleSwarmOptimization
from jmetal.core.problem import BinaryProblem
from jmetal.core.solution import BinarySolution
from jmetal.operator.mutation import BitFlipMutation
from jmetal.util.archive import BoundedArchive, NonDominatedSolutionListArchive
from jmetal.util.comparator import DominanceComparator, EpsilonDominanceComparator
from jmetal.util.solution_list import Evaluator, Generator
from jmetal.util.termination_criterion import TerminationCriterion


class BMOPSO(ParticleSwarmOptimization):
    def __init__(
        self,
        problem: BinaryProblem,
        swarm_size: int,
        mutation: BitFlipMutation,
        leaders: Optional[BoundedArchive],
        epsilon: float,
        termination_criterion: TerminationCriterion,
        swarm_generator: Generator = store.default_generator,
        swarm_evaluator: Evaluator = store.default_evaluator,
    ):

        super(BMOPSO, self).__init__(problem=problem, swarm_size=swarm_size)
        self.swarm_generator = swarm_generator
        self.swarm_evaluator = swarm_evaluator

        self.termination_criterion = termination_criterion
        self.observable.register(termination_criterion)

        self.mutation_operator = mutation

        self.leaders = leaders

        self.epsilon = epsilon
        self.epsilon_archive = NonDominatedSolutionListArchive(
            # EpsilonDominanceComparator(epsilon)
            DominanceComparator()
        )

        self.c1_min = 1.5
        self.c1_max = 2.0
        self.c2_min = 1.5
        self.c2_max = 2.0
        self.r1_min = 0.0
        self.r1_max = 1.0
        self.r2_min = 0.0
        self.r2_max = 1.0
        self.weight_min = 0.1
        self.weight_max = 0.5
        self.change_velocity1 = -1
        self.change_velocity2 = -1

        self.dominance_comparator = DominanceComparator()

        self.speed = numpy.zeros(
            (
                self.swarm_size,
                self.problem.number_of_variables,
                self.problem.number_of_tests,
            ),
            dtype=float,
        )

    def create_initial_solutions(self) -> List[BinarySolution]:
        return [self.swarm_generator.new(self.problem) for _ in range(self.swarm_size)]

    def evaluate(self, solution_list: List[BinarySolution]):
        return self.swarm_evaluator.evaluate(solution_list, self.problem)

    def stopping_condition_is_met(self) -> bool:
        return self.termination_criterion.is_met

    def initialize_global_best(self, swarm: List[BinarySolution]) -> None:
        for particle in swarm:
            if self.leaders.add(particle):
                self.epsilon_archive.add(copy(particle))

    def initialize_particle_best(self, swarm: List[BinarySolution]) -> None:
        for particle in swarm:
            particle.attributes["local_best"] = copy(particle)

    def initialize_velocity(self, swarm: List[BinarySolution]) -> None:
        for i in range(self.swarm_size):
            for j in range(self.problem.number_of_variables):
                self.speed[i][j] = 0.0

    def update_velocity(self, swarm: List[BinarySolution]) -> None:
        for i in range(self.swarm_size):
            best_particle = copy(swarm[i].attributes["local_best"])
            best_global = self.select_global_best()

            r1 = round(random.uniform(self.r1_min, self.r1_max), 1)
            r2 = round(random.uniform(self.r2_min, self.r2_max), 1)
            c1 = round(random.uniform(self.c1_min, self.c1_max), 1)
            c2 = round(random.uniform(self.c2_min, self.c2_max), 1)
            w = round(random.uniform(self.weight_min, self.weight_max), 1)

            for var in range(swarm[i].number_of_variables):
                best_particle_diff = numpy.subtract(
                    numpy.array(best_particle.variables[var]),
                    numpy.array(swarm[i].variables[var]),
                    dtype=numpy.float32,
                )
                best_global_diff = numpy.subtract(
                    numpy.array(best_global.variables[var]),
                    numpy.array(swarm[i].variables[var]),
                    dtype=numpy.float32,
                )

                self.speed[i][var] = (
                    w * numpy.array(self.speed[i][var])
                    + (c1 * r1 * best_particle_diff)
                    + (c2 * r2 * best_global_diff)
                )

    def update_position(self, swarm: List[BinarySolution]) -> None:
        for i in range(self.swarm_size):
            particle = swarm[i]

            for j in range(particle.number_of_variables):
                particle.variables[j] = self.compute_position(self.speed[i][j])

    def compute_position(self, speed):
        updated_positions = (
            numpy.random.random_sample(speed.shape) < self._sigmoid(speed)
        ) * 1
        return list(numpy.array(updated_positions, dtype=bool))

    def _sigmoid(self, x):
        return 1 / (1 + numpy.exp(-x))

    def update_global_best(self, swarm: List[BinarySolution]) -> None:
        for particle in swarm:
            if self.leaders.add(copy(particle)):
                self.epsilon_archive.add(copy(particle))

    def update_particle_best(self, swarm: List[BinarySolution]) -> None:
        for i in range(self.swarm_size):
            flag = self.dominance_comparator.compare(
                swarm[i], swarm[i].attributes["local_best"]
            )
            if flag != 1:
                swarm[i].attributes["local_best"] = copy(swarm[i])

    def perturbation(self, swarm: List[BinarySolution]) -> None:
        for i in range(self.swarm_size):
            if (i % 6) == 0:
                self.mutation_operator.execute(swarm[i])

    def select_global_best(self) -> BinarySolution:
        leaders = self.leaders.solution_list

        if len(leaders) > 2:
            particles = random.sample(leaders, 2)

            if self.leaders.comparator.compare(particles[0], particles[1]) < 1:
                best_global = copy(particles[0])
            else:
                best_global = copy(particles[1])
        else:
            best_global = copy(self.leaders.solution_list[0])

        return best_global

    def init_progress(self) -> None:
        self.evaluations = self.swarm_size
        self.leaders.compute_density_estimator()

        self.initialize_velocity(self.solutions)
        self.initialize_particle_best(self.solutions)
        self.initialize_global_best(self.solutions)

    def update_progress(self) -> None:
        self.evaluations += self.swarm_size
        self.leaders.compute_density_estimator()

        observable_data = self.get_observable_data()
        observable_data["SOLUTIONS"] = self.epsilon_archive.solution_list
        self.observable.notify_all(**observable_data)

    def get_result(self) -> List[BinarySolution]:
        return self.epsilon_archive.solution_list

    def get_name(self) -> str:
        return "my-BMOPSO"
