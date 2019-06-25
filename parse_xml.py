# coding=utf-8
import itertools
import os
from functools import partial
from multiprocessing import Pool

import click
import numpy as np

from backend.opencover import parser


@click.command("multiple")
@click.argument("reports_path")
@click.argument("output_name")
@click.argument("branch_name")
def process_multiple_xml_reports(reports_path, output_name, branch_name):
    report_files = list(
        map(
            lambda report: os.path.abspath(os.path.join(reports_path, report)),
            os.listdir(reports_path),
        )
    )

    # Collect id-activity matrices for each report
    with Pool(processes=2) as pool:
        result = pool.map(
            partial(get_id_activity_matrix, branch=branch_name), report_files
        )

    array_result = np.array(result)
    id_act_matrices = array_result[:, 0]
    methods_map, tests_map = array_result[0, 1], array_result[0, 2]

    # Merge id-activity matrices
    x = {
        k: [d.get(k, []) for d in id_act_matrices]
        for k in {k for d in id_act_matrices for k in d}
    }
    merged_id_act_matrices = {k: list(itertools.chain(*x[k])) for k in x}

    export_activity_matrix(merged_id_act_matrices, methods_map, output_name, tests_map)


def export_activity_matrix(activity_matrix, methods_map, output_name, tests_map):
    # Convert id-activity matrix to binary activity matrix
    print(f"Converting to the binary activity matrix")
    binary_act_matrix = parser.build_binary_activity_matrix(
        activity_matrix, methods_map, tests_map
    )
    # Filter activity matrix to reduce json file output size
    print(f"Filtering methods/tests with no activty from the matrix")
    filter_act_matrix, methods_map, tests_map = parser.filter_activity_matrix(
        binary_act_matrix, methods_map, tests_map
    )
    # Export results to json
    print(f"Exporting processed data to json files")
    parser.export_data_to_json(output_name, filter_act_matrix, methods_map, tests_map)

    print("Report processing done")


def get_id_activity_matrix(xml_report, branch):
    # Get files map
    print(f"Getting file map to handle c# namespace issues")
    files_map = parser.get_files_map_from_report(xml_report, branch)
    # Split xml report based on module type (test vs code)
    print(f"Loading xml report {xml_report}")
    test_modules, code_modules = parser.get_modules_from_report(xml_report)
    # Fill uid maps with tests names and methods names
    print(f"Mapping tests and methods uids")
    tests_map = parser.build_tests_map(test_modules)
    methods_map = parser.build_methods_map(code_modules)
    # Build activity matrix based on ids
    print(f"Building the id-activity matrix")
    id_act_matrix = parser.build_id_activity_matrix(
        code_modules, methods_map, files_map
    )
    print(f" {xml_report} -- {len(id_act_matrix)}")
    return id_act_matrix, methods_map, tests_map


if __name__ == "__main__":
    process_multiple_xml_reports()
