# coding=utf-8
import random
import re
from dataclasses import dataclass
from typing import List

import numpy as np
from faker import Factory

from backend.integrations.database import get_testfails_for_revision
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


@dataclass
class RevisionResults:
    branch: str
    rev_id: str
    rev_date: str
    changelist: list
    error_no_changed_items: str
    solutions_found: list
    score: tuple  # (score %, # matched, # expected, # tests)
    solution_metrics: list
    new_feedback_time: float
    computing_time: float
    orig_rev_history: set
    real_rev_history: set
    innocent: bool

    def __init__(
        self, svn_log_entry, branch, ignored_tests, previous_rev, masked=False
    ):
        self.branch = branch
        self.rev_id = svn_log_entry.revision
        self.rev_date = str(svn_log_entry.date)
        self.changelist = svn_log_entry.changelist
        self.masked = masked

        self.error_no_changed_items = None
        self.innocent = None

        self.set_revision_history(previous_rev, ignored_tests)

        if masked:
            self.fake = Factory.create()

        self.solutions_found = []
        self.score = (-1, -1, -1, -1)
        self.new_feedback_time = 0
        self.computing_time = 0
        self.solution_metrics = []

    def set_revision_history(self, previous: "RevisionResults", ignored: List[str]):
        """
        Set revision history values (i.e. lists of failing tests names) for this revision.

        :param previous: execution results from the previous revision
        :param ignored: list of tests to ignore
        """
        # Set original revision history
        rev_results = get_testfails_for_revision(revision=self.rev_id)
        self.orig_rev_history = set(rev_results.FULLNAME.values)

        # If no failing tests returned from the database, use failing tests of previous revision
        if len(self.orig_rev_history) == 0:
            if previous is not None:
                self.orig_rev_history = previous.orig_rev_history
            else:
                self.orig_rev_history = set()

        # Set real revision history to be used
        # 1. remove ignored tests based on configuration file
        self.real_rev_history = set(
            filter(
                lambda test: all(x not in test for x in ignored), self.orig_rev_history
            )
        )

        # 2. keep only failing tests not in previous revision
        if previous is not None:
            self.real_rev_history = set(
                filter(
                    lambda x: x not in previous.orig_rev_history, self.real_rev_history
                )
            )

    def print_results(self, data: ProblemData, fixed_demo=False):
        """
        Print execution results to stdout.

        :param data: data associated with this execution
        :param fixed_demo: flag indicating whether this a random selection or not
        """

        def get_fake_filename(file: str) -> str:
            """
            Get a fake filename to mask the given file path.

            :param file: file path for which a fake name should be generated
            :return: a generated fake file path
            """
            result = re.search(r"/.*\.(.*)", file)
            if result is None:
                # this is a directory -> get a random file path with some random file extension
                return self.fake.file_path(
                    depth=random.randint(3, 5),
                    extension=random.choice(
                        ["cs", "tsx", "json", "oml", "csproj", "xml"]
                    ),
                )
            else:
                # this a file -> get a random filename and keep the file extension
                extension = result.group(1)
                filename = self.fake.file_path(
                    depth=random.randint(3, 5), extension=" "
                )
                filename = "/".join([x.capitalize() for x in filename[:-1].split("/")])
                return filename + extension

        # Revision Id + Changelist
        if self.masked:
            fake_changelist = [(x[0], get_fake_filename(x[1])) for x in self.changelist]
            changes = "\n\t".join(map(lambda x: str(x), fake_changelist))
        else:
            changes = "\n\t".join(map(lambda x: str(x), self.changelist))

        revision_id = f"rev_id: {self.rev_id} ({self.rev_date})"
        print(f"{revision_id}\nchangelist:\n\t{changes}")

        # Execution results
        if type(self.error_no_changed_items) == str:
            # If no changed indexes were extracted, then print the error message
            print(f"Revision {self.rev_id} failed due to {self.error_no_changed_items}")
            self.print_revision_status()
        else:
            if fixed_demo:
                # For random selections, the solution is stored in self.solutions_found
                self.print_revision_status()
                self.print_solution_score(0, self.solutions_found)
                self.computing_time = 0.1
                print(f"Solution Size: {len(self.solutions_found)} tests")
                self.new_feedback_time = sum(
                    [
                        data.history_test_execution_times[test]
                        for test in self.solutions_found
                    ]
                )
                print(
                    f"Solution Feedback Loop Time: {self.new_feedback_time:.0f} seconds"
                )
            else:
                self.print_revision_status()
                self.print_execution_results(data)
                self.print_solution_list(data)
                self.print_execution_inspection(data)

        # separator
        print("==========================" * 4)

    def print_revision_status(self):
        """
        Print status of this revision: pass/fail, number and list of failing tests.

        """
        if len(self.orig_rev_history) == 0:
            print(f"Revision {self.rev_id} had no failing tests")
        else:
            failed_tests = f"{len(self.orig_rev_history)} failed tests"
            if self.masked:
                print(f"Revision {self.rev_id} - {failed_tests}")
            else:
                joined = "\n\t".join(self.orig_rev_history)
                print(f"Revision {self.rev_id} - {failed_tests}:\n\t{joined}")

    def print_execution_results(self, data: ProblemData):
        """
        Print results of this execution to stdout

        - Computing Time
        - Objectives values of each solution
        - Score of each solution
        :param data: data related to this execution
        """
        # Computing Time
        print("Computing time: " + str(self.computing_time))

        # Objectives values of each solution
        print_function_values_to_screen(self.solutions_found, data)

        # Score of each solution
        for i, solution in enumerate(self.solutions_found):
            pos = np.array(solution.variables[0])
            rev_solution = list(data.tests_index[pos == 1])
            self.print_solution_score(i, rev_solution)

    def print_execution_inspection(self, data: ProblemData):
        """
        Print inspection conclusions over this execution.

        Inspection checks if it was possible to select a test given the available data (before/after filters)

        :param data: data related to this execution
        """

        def inspection_checker(tests_data: np.ndarray):
            """
            Check if the provided array of tests contains the failing tests for this revision.

            The counts of possible/impossible to find tests are printed.

            :param tests_data: array of test names
            """
            available, impossible = 0, 0
            for test in self.real_rev_history:
                if any(x in test for x in tests_data):
                    # print(f"{test} = Available")
                    available += 1
                else:
                    print(f"\t{test} = Impossible")
                    impossible += 1
            print(f"Available={available} || Impossible={impossible}")

        print(f"Check test availability vs original data - {data.original_tests.shape}")
        inspection_checker(data.original_tests)

        print(f"Check test availability vs filtered data - {data.tests_index.shape}")
        inspection_checker(data.tests_index)

    def print_solution_list(self, data: ProblemData):
        """
        Print solution results for this execution: solution size, feedback time and list of selected tests

        :param data: data related to this execution
        """

        def get_fake_test_name() -> str:
            """
            Get a generated fake test name
            :return: a random test name
            """
            test_name = self.fake.file_path(depth=random.randint(3, 5), extension=" ")
            test_name = test_name[1:-2].replace("/", ".")
            test_name = "Test." + ".".join(
                [x.capitalize() for x in test_name.split(".")]
            )
            return test_name

        # Store objectives values of this solution
        solution = self.solutions_found[0]
        self.solution_metrics = solution.objectives

        pos = np.array(solution.variables[0])
        rev_solution = list(data.tests_index[pos == 1])
        # Solution Size + Feedback Time
        print(f"Solution Size: {len(rev_solution)} tests")
        self.new_feedback_time = sum(
            [data.history_test_execution_times[test] for test in rev_solution]
        )
        print(f"Solution Feedback Loop Time: {self.new_feedback_time:.0f} seconds")

        # Selected Tests
        if self.masked:
            rev_solution = [get_fake_test_name() for _ in rev_solution]
        solution_tests = "\n\t".join(rev_solution)
        print(f"\t{solution_tests}")

    def print_solution_score(self, i: int, rev_solution: List[str]):
        """
        Print score (i.e. number of failing tests found) of this solution.

        :param i: number id of this solution
        :param rev_solution: list of tests selected by this solution
        """

        def get_matching_tests() -> List[str]:
            """
            Get list of selected tests matching with the set of failing tests.

            :return: a list of test names
            """
            return [
                test
                for test in self.real_rev_history
                if any(x in test for x in rev_solution)
            ]

        sol_size = len(rev_solution)
        sol_id = f"Solution {i} ({sol_size})"

        if len(self.real_rev_history) == 0:
            print(f"{sol_id} = only ignored tests")
            self.score = (-1, 0, 0, sol_size)
        else:
            matching = get_matching_tests()
            score = (len(matching) / len(self.real_rev_history)) * 100
            match_vs_rev = f"{len(matching)}/{len(self.real_rev_history)}"
            if self.masked:
                print(f"{sol_id} = {match_vs_rev} ({score:.0f}%)")
            else:
                # Also print matching test names, if not using masked mode
                print(f"{sol_id} = {match_vs_rev} ({score:.0f}%) -> {matching}")

            self.score = (score, len(matching), len(self.real_rev_history), sol_size)
