# coding=utf-8
import json
import re
from typing import List

import pandas as pd
from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from backend.integrations import database


def normalize_test_name(tests: np.ndarray):
    """
    Normalize test names to match database.

    - Replace / with + to support dashboard tests
    - Discard return type
    - Only keep namespace and method name

    :param tests: list of test names
    :return: array with test names normalized
    """
    return map(
        lambda test: ".".join(
            re.search(r"(.*)::(.*)\(", test.replace("/", "+").split(" ")[1]).groups()
        ),
        tests,
    )


def normalize_iterative_test_name(test: str):
    """
    Normalize iterative test name, if necessary

    :param test: test name
    :return: normalized test name
    """
    if re.match(r"(.*\..+)\+.+", test):
        return re.match(r"(.*\..+)\+.+", test).group(1)
    return test


def get_historical_metric_map(query_results: pd.DataFrame) -> dict:
    """
    Convert 2-columns query results to a dictionary mapping the test name to the historical metric value

    :param query_results: 2-columns pandas dataframe with the query results
    :return: dictionary mapping the test names to the historical metric values
    """
    history_metric_map = defaultdict(int)
    for test, time in query_results.values:
        key = normalize_iterative_test_name(test)
        history_metric_map[key] += time
    return history_metric_map


@dataclass
class ProblemData:
    original_matrix: np.ndarray
    original_tests: np.ndarray
    original_methods: np.ndarray
    activity_matrix: np.ndarray
    tests_index: np.ndarray
    methods_index: np.ndarray
    methods_map: dict
    history_test_fails: dict
    history_test_execution_times: dict
    new_files: dict
    branch: str
    ignore_tests: list

    swarm_size: int

    def __init__(
        self,
        activity_matrix_path,
        branch,
        fails_start_date,
        from_date,
        to_date,
        ignore_tests=None,
    ):
        """
        ProblemData initialization.

        - Load JSON data for an activity matrix file
        - Filter tests with no activity (zero rows)
        :param activity_matrix_path: path of the activity matrix JSON file
        """
        if ignore_tests is None:
            ignore_tests = []
        self.branch = branch
        self.ignore_tests = ignore_tests

        self.load_json_data(activity_matrix_path)
        self.filter_tests_with_no_activity()

        # Load historical data
        self.history_test_fails = get_historical_metric_map(
            database.get_test_name_fails(fails_start_date, from_date)
        )
        self.history_test_execution_times = get_historical_metric_map(
            database.get_test_execution_times(from_date, to_date)
        )

        self.new_files = {}

    def load_json_data(self, activity_matrix):
        """
        Loads JSON data for an activity matrix.

        The loaded JSON data includes:
            - The binary activity matrix itself
            - The tests considered
            - The methods considered

        :param activity_matrix: path of the activity matrix JSON file
        """
        print(f"Loading json data from {activity_matrix}")
        # Find relative path and timestamp to load tests/methods maps
        actm_pattern = r"(.*)\\actmatrix_(.*)\.json"
        path, timestamp = re.search(actm_pattern, activity_matrix).groups()

        # activity matrix
        with open(activity_matrix) as actm_file:
            self.activity_matrix = np.array(json.load(actm_file), dtype=bool)
            self.original_matrix = self.activity_matrix

        # tests
        with open(f"{path}\\testids_{timestamp}.json") as tests_file:
            tests = np.array(list(json.load(tests_file).values()))
            self.tests_index = np.array(list(normalize_test_name(tests)))
            self.original_tests = self.tests_index

        # methods
        with open(f"{path}\\methodids_{timestamp}.json") as methods_file:
            self.methods_map = json.load(methods_file)
            # print(f"methods map: {len(self.methods_map.keys())}")
            self.methods_index = np.array(list(self.methods_map.values()))
            self.original_methods = self.methods_index

    def reset(self):
        """
        Reset current activity matrix, tests and methods data to the originally loaded data.

        """
        self.activity_matrix = self.original_matrix
        self.tests_index = self.original_tests
        self.methods_index = self.original_methods

    def filter_tests_with_no_activity(self):
        """
            Filter tests with no activity (zero rows).
        """
        active_tests = ~np.all(self.activity_matrix == 0, axis=1)
        self.tests_index = self.tests_index[active_tests]
        self.activity_matrix = self.activity_matrix[active_tests]

    def filter_methods_with_no_activity(self):
        """
            Filter methods with no activity (zero columns)
        """
        active_methods = ~np.all(self.activity_matrix == 0, axis=0)
        self.methods_index = self.methods_index[active_methods]
        self.activity_matrix = self.activity_matrix[:, active_methods]

    def filter_data_for_commit(self, changed_methods):
        """
        Filter matrix and indexes based on commit.
        Also, the changed data is filtered for tests/methods with no activity

        :param changed_methods: indexes of methods changed by the commit
        """
        self.activity_matrix = self.activity_matrix[:, changed_methods]
        self.methods_index = self.methods_index[changed_methods]

        # Filter no activity tests/methods
        self.filter_tests_with_no_activity()
        self.filter_methods_with_no_activity()

    def get_changed_indexes_for_changelist(
        self, changelist: List[List], ignore_changes: List
    ) -> object:
        """
        Get the changed method indexes in the activity matrix based on the changelist

        :param changelist: list of changed files (each element is pair with the type of change and the filename)
        :param ignore_changes: list of file paths to be ignored
        :return: on success, returns a list of changed indexes in the activity matrix.
                 on failure, returns a string describing the error case
        """
        # Filter changelist before processing
        changelist = [
            change
            for change in changelist
            if not any(
                (ignore in change[1]) or (change[1] == "/platform/trunk")
                for ignore in ignore_changes
            )
        ]

        # Process changelist
        new_files = []
        changed_files = []
        cs_pattern = self.branch + r"/(.*)\.cs$"
        xaml_cs_pattern = self.branch + r"/(.*)xaml\.cs"
        for x in changelist:
            if re.search(cs_pattern, x[1]):
                # Check if it's not a *.xaml.cs file
                if not re.search(xaml_cs_pattern, x[1]):
                    filename = re.search(cs_pattern, x[1]).group(1)
                    dot_filename = filename.replace("/", ".")
                    changed_files.append(dot_filename)
                    # Check if new file and store in hash table
                    if x[0] == "A":
                        self.new_files[dot_filename] = 123
                        new_files.append(dot_filename)
                    # Check if modified an already known new file
                    elif self.new_files.get(dot_filename) is not None:
                        new_files.append(dot_filename)

        # Check if no .cs files were changed
        if not changed_files:
            return "[Error] Changelist contains no covered .cs files"

        # Check if only changed new files
        if len(changed_files) == len(new_files):
            return "[Error] Changelist contains only new files or modified new files"

        # Map files to method indexes
        changed_indexes = []
        for method in self.methods_map.values():
            if any(changed in method for changed in changed_files):
                matched_methods = np.where(self.methods_index == method)
                changed_indexes.append(matched_methods[0][0])

        # Check if there are no method indexes to return
        if not changed_indexes:
            return "[Error] The provided activity matrix has no coverage data for the changed files"

        return changed_indexes
