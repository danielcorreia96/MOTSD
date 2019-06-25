# coding=utf-8
import json

import click
import numpy as np
from jmetal.core.algorithm import Algorithm

import backend.selection.objectives as metrics
from backend.selection.demo_stats import RevisionResults, print_results_summary
from backend.selection.problem_data import ProblemData
from backend.selection.test_selection import TestSelection, my_binary_mopso
from backend.integrations.svn_utils import get_log, get_log_for_revision

np.random.seed(1234)
np.set_printoptions(threshold=np.inf)

OBJECTIVES_MAP = {
    "ddu": metrics.calculate_ddu,
    "n_tests": metrics.calculate_number_of_tests,
    "fails": metrics.calculate_history_test_fails,
    "exec_times": metrics.calculate_history_test_exec_times,
    "norm_coverage": metrics.calculate_norm_coverage,
    "coverage": metrics.calculate_coverage,
}


@click.group()
def cli():
    pass


@cli.command("single")
@click.option(
    "--objectives",
    "-o",
    required=True,
    type=click.Choice(list(OBJECTIVES_MAP.keys())),
    multiple=True,
)
@click.option("--masked", is_flag=True)
@click.argument("activity_matrix", type=click.Path(exists=True, readable=True))
@click.argument("demo_config", type=click.Path(exists=True, readable=True))
def run_optimization(objectives, masked, activity_matrix, demo_config):
    """
        Runs optimization pipeline for a given ACTIVITY_MATRIX (json file)
    """
    with open(demo_config, mode="r") as demo_file:
        config = json.load(demo_file)
    # Build problem data
    data = ProblemData(
        activity_matrix,
        config["branch"],
        config["from_dt"],
        ignore_tests=config["ignore_tests"],
    )

    while True:
        revision = input("Target Revision Id: ")
        log = [log_e for log_e in get_log_for_revision(config["branch_path"], revision)]
        if not log:
            continue
        log_entry = log[0]

        print(f"Running pipeline demo with the following objectives: {objectives}")
        metrics = [OBJECTIVES_MAP[key] for key in objectives]
        # Reset problem data to original matrices
        data.reset()

        # Run pipeline for revision
        revision_results = RevisionResults(
            log_entry, data.branch, data.ignore_tests, masked
        )
        run_pipeline(data, metrics, revision_results)
        revision_results.print_results(data)


@cli.command("demo")
@click.option(
    "--objectives",
    "-o",
    required=True,
    type=click.Choice(list(OBJECTIVES_MAP.keys())),
    multiple=True,
)
@click.option("--masked", is_flag=True)
@click.argument("swarm_size", type=click.INT)
@click.argument("activity_matrix", type=click.Path(exists=True, readable=True))
@click.argument("demo_config", type=click.Path(exists=True, readable=True))
def run_optimization_for_demo(activity_matrix, demo_config, objectives, masked, swarm_size):
    def is_ignored_project(changelist, ignore_changes):
        return all(
            any(ignore in change[1] for ignore in ignore_changes)
            for change in changelist
        )

    def run_tool_for_revision(revision, data):
        print(f"Running pipeline demo with the following objectives: {objectives}")
        metrics = [OBJECTIVES_MAP[key] for key in objectives]
        # Reset problem data to original matrices
        data.reset()

        # Run pipeline for revision
        revision_results = RevisionResults(
            revision, data.branch, data.ignore_tests, masked
        )
        run_pipeline(data, metrics, revision_results)
        revision_results.print_results(data)

        return revision_results

    # Get log based on demo config
    with open(demo_config, mode="r") as demo_file:
        config = json.load(demo_file)

    log = get_log(config["branch_path"], config["from_dt"], config["to_dt"])

    # Build problem data
    data = ProblemData(
        activity_matrix,
        config["branch"],
        config["from_dt"],
        ignore_tests=config["ignore_tests"],
    )

    data.swarm_size = swarm_size

    # Run tool for each revision
    results = [
        run_tool_for_revision(log_e, data)
        for log_e in log
        if not is_ignored_project(log_e.changelist, config["ignore_changes"])
    ]

    # Print results summary report
    print_results_summary(results)


def run_pipeline(data, objectives, revision: RevisionResults):
    # Get indexes for methods changed by a commit
    changed_idxs = data.get_changed_indexes_for_changelist(revision.changelist)

    # Stop pipeline if no changed indexes were extracted
    if type(changed_idxs) == str:
        revision.error_no_changed_items = changed_idxs
        return

    # Filter matrix and indexes based on commit
    data.filter_data_for_commit(changed_idxs)

    # Run optimizer for the reduced matrix
    problem = TestSelection(data, objectives)
    solution_front = run_optimizer(my_binary_mopso(problem, data.swarm_size), revision)
    revision.solutions_found = solution_front


def run_optimizer(algorithm: Algorithm, revision: RevisionResults):
    # Run optimizer algorithm
    algorithm.run()
    front = algorithm.get_result()
    revision.computing_time = algorithm.total_computing_time

    # return sorted(front, key=lambda x: (x.objectives[0]))
    return sorted(front, key=lambda x: (x.objectives[0], x.objectives[1]))


if __name__ == "__main__":
    cli()
