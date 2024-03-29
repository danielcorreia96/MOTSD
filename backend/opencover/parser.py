# coding=utf-8
import xml.etree.ElementTree as ET
import json
import itertools
import re
import numpy as np

import backend.opencover.utils as utils


def get_modules_from_report(report):
    """
    Extracts maps for tests and code modules names to its XML elements.

    :param report: path to XML coverage report
    :return: 2 maps (tests and code) mapping a module name to its XML element
    """
    _, root_modules = ET.parse(report).getroot()
    test_modules, code_modules = {}, {}

    for child in root_modules:
        name = utils.get_module_name(child)
        code_modules[name] = child
        if "Tests" in name:
            test_modules[name] = child

    return test_modules, code_modules


def get_files_map_from_report(report, branch):
    """
    Get map between file uids and their file path name.

    :param report: path to the XML coverage report
    :param branch: branch name to locate the start of the file path
    :return: map between file uids and file path names
    """
    test_modules, code_modules = get_modules_from_report(report)
    files_map = {}

    for module in code_modules.values():
        for file in utils.get_module_files(module):
            uid, path = file.attrib["uid"], file.attrib["fullPath"]
            re_search = re.search(branch + r"\\(.*)\.cs", path)
            if re_search:
                name = re_search.group(1).replace("\\", ".")
                files_map[uid] = name

    return files_map


def build_tests_map(test_modules_map):
    tests_uids_map = {}

    for module in test_modules_map.values():
        for method in utils.get_module_tracked_methods(module):
            uid, name = method.attrib["uid"], method.attrib["name"]
            tests_uids_map[uid] = name

    return tests_uids_map


def build_methods_map(code_modules):
    methods_uids_map = {}
    counter = itertools.count(1)

    for module in code_modules.values():
        for clazz in utils.get_module_classes(module):
            for method in utils.get_class_methods(clazz):
                method_name = utils.get_method_name(method)
                methods_uids_map["m" + str(next(counter))] = method_name

    return methods_uids_map


def build_id_activity_matrix(code_modules, methods_uids_map, files_map):
    # id-activity matrix
    #    key   - method id
    #    value - test id
    def get_method_id(method_name):
        for (key, value) in methods_uids_map.items():
            if value == method_name:
                return key

    activity_matrix = dict.fromkeys(methods_uids_map.keys(), [])

    for module in code_modules.values():
        for clazz in utils.get_module_classes(module):
            for method in utils.get_class_methods(clazz):
                method_name, tests = utils.get_method_coverage(method)
                if method_name is not None:
                    method_id = get_method_id(method_name)
                    activity_matrix[method_id] = tests
                    # Update methods map with namespace fix
                    fix_methods_map_namespace(
                        files_map, method, method_id, method_name, methods_uids_map
                    )

    return activity_matrix


def fix_methods_map_namespace(
    files_map, method, method_id, method_name, methods_uids_map
):
    """
    Replace method namespace with containing file path.

    :param files_map: map of uids to file paths
    :param method: method XML element
    :param method_id: method uid
    :param method_name: method name
    :param methods_uids_map: map of uids to method names
    """
    file_ref = utils.get_method_file_ref(method)
    if file_ref is not None:
        file_ref = file_ref.attrib["uid"]
        if files_map.get(file_ref) is not None:
            return_type, name = re.search(r"(.* ).*(::.*)", method_name).groups()
            new_namespace = files_map[file_ref]
            new_method_name = "".join([return_type, new_namespace, name])
            methods_uids_map[method_id] = new_method_name


def build_binary_activity_matrix(id_act_matrix, method_uid_map, test_uid_map):
    binary_activity_matrix = []
    tests_index = list(test_uid_map.keys())
    methods_index = list(method_uid_map.keys())

    # Fill with empty cells
    for _ in range(len(test_uid_map.keys())):
        row = [0 for _ in range(len(method_uid_map.keys()))]
        binary_activity_matrix.append(row)

    # Fill with activity results
    for method, tests in id_act_matrix.items():
        if method is not None and tests is not None:
            method_pos = methods_index.index(method)
            for test in tests:
                try:
                    test_pos = tests_index.index(test)
                    binary_activity_matrix[test_pos][method_pos] = 1
                except ValueError:
                    pass

    return binary_activity_matrix


def filter_activity_matrix(activity_matrix, method_uid_map, test_uid_map):
    # Load data before filters
    array_act_matrix = np.array(activity_matrix, dtype=bool)
    tests_index = np.array(list(test_uid_map.keys()))
    methods_index = np.array(list(method_uid_map.keys()))
    print(f"-- Before filters: {array_act_matrix.shape}")

    # Filter methods without activity
    active_methods = ~np.all(array_act_matrix == 0, axis=0)
    array_act_matrix = array_act_matrix[:, active_methods]
    methods_index = methods_index[active_methods]
    filtered_method_uid_map = {k: method_uid_map[k] for k in methods_index}
    print(f"-- After methods filter: {array_act_matrix.shape}")

    # Filter tests without activity
    active_tests = ~np.all(array_act_matrix == 0, axis=1)
    tests_index = tests_index[active_tests]
    filtered_test_uid_map = {k: test_uid_map[k] for k in tests_index}
    array_act_matrix = array_act_matrix[active_tests]
    print(f"-- After tests filter: {array_act_matrix.shape}")

    return array_act_matrix, filtered_method_uid_map, filtered_test_uid_map


def export_data_to_json(output_name, activity_matrix, methods_map, tests_map):
    """
        Exports processed data to json files

        :param output_name: name identifier for the JSON output files
        :param tests_map: map of ids to tests
        :param methods_map: map of ids to methods
        :param activity_matrix: binary activity matrix (test x method)
    """
    with open(f"data/jsons/testids_{output_name}.json", "w") as outfile:
        json.dump(tests_map, outfile, indent=4)

    with open(f"data/jsons/methodids_{output_name}.json", "w") as outfile:
        json.dump(methods_map, outfile, indent=4)

    with open(f"data/jsons/actmatrix_{output_name}.json", "w") as outfile:
        json.dump(activity_matrix.astype("int").tolist(), outfile)
