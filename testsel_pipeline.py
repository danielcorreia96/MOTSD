# coding=utf-8
import json
import random

import click
import numpy as np
from jmetal.core.algorithm import Algorithm

import backend.selection.objectives as metrics
from backend.evaluation.execution_item import RevisionResults
from backend.evaluation.summary import ResultsSummary
from backend.integrations.svn_utils import get_log, get_log_for_revision
from backend.selection.problem_data import ProblemData
from backend.selection.test_selection import TestSelection, my_binary_mopso

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


@cli.command("user")
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
def run_optimization(objectives, masked, activity_matrix, demo_config, swarm_size):
    """
        User input-based execution of the pipeline
    """
    with open(demo_config, mode="r") as demo_file:
        config = json.load(demo_file)
    # Build problem data
    data = ProblemData(
        activity_matrix,
        config["branch"],
        config["fails_start_dt"],
        config["from_dt"],
        config["to_dt"],
        ignore_tests=config["ignore_tests"],
    )

    data.swarm_size = swarm_size

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
        run_pipeline(data, metrics, revision_results, config["ignore_changes"])
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
@click.argument("output_file", type=click.Path())
def run_optimization_for_demo(
    activity_matrix, demo_config, objectives, masked, swarm_size, output_file
):
    def run_tool_for_revision(revision, data, previous_rev, ignore_changes):
        print(f"Running pipeline demo with the following objectives: {objectives}")
        metrics = [OBJECTIVES_MAP[key] for key in objectives]
        # Reset problem data to original matrices
        data.reset()

        # Run pipeline for revision
        revision_results = RevisionResults(
            revision, data.branch, data.ignore_tests, previous_rev, masked
        )
        run_pipeline(data, metrics, revision_results, ignore_changes)
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
        config["fails_start_dt"],
        config["from_dt"],
        config["to_dt"],
        ignore_tests=config["ignore_tests"],
    )

    data.swarm_size = swarm_size

    # Run tool for each revision
    results = []
    previous = None
    # for log_e in log[:100]:
    for log_e in log:
        if not is_ignored_project(log_e.changelist, config["ignore_changes"]):
            res = run_tool_for_revision(log_e, data, previous, config["ignore_changes"])
            results.append(res)
            previous = res

    # Build results summary report
    summary = ResultsSummary(results, data)

    # - print summary to terminal
    summary.export_to_text()

    # save data to pickle
    with open(output_file, mode="wb") as output:
        summary.export_to_pickle(output)


@cli.command("random")
@click.option("--fixed", is_flag=True, help="Use a fixed test sample for evaluation")
@click.option(
    "--filtered",
    is_flag=True,
    help="Filter matrix using changelist for evaluation fairness with MOTSD",
)
@click.argument("random_p", type=click.FLOAT)
@click.argument("all_tests", type=click.Path(exists=True, readable=True))
@click.argument("activity_matrix", type=click.Path(exists=True, readable=True))
@click.argument("demo_config", type=click.Path(exists=True, readable=True))
@click.argument("output_file", type=click.Path())
def run_random_demo(
    activity_matrix, demo_config, output_file, random_p, all_tests, fixed, filtered
):
    def run_tool_for_revision(revision, data, previous_rev, ignore_changes, t_sample):
        revision_results = RevisionResults(
            revision, data.branch, data.ignore_tests, previous_rev
        )
        if filtered:
            # Running in filtered mode for evaluation fairness with MOTSD, i.e. filter matrix with changelist
            # Get indexes for methods changed by a commit
            changed_idxs = data.get_changed_indexes_for_changelist(
                revision.changelist, ignore_changes
            )

            # Stop pipeline if no changed indexes were extracted
            if type(changed_idxs) == str:
                revision_results.error_no_changed_items = changed_idxs
                return revision_results

        if not fixed:
            # Running in not fixed sample mode, i.e. get a new test sample for each commit
            t_sample = random.sample(tests, int(random_p * (len(tests))))

        revision_results.solutions_found = t_sample
        revision_results.print_results(data, fixed_demo=True)

        return revision_results

    # Get log based on demo config
    with open(demo_config, mode="r") as demo_file:
        config = json.load(demo_file)

    log = get_log(config["branch_path"], config["from_dt"], config["to_dt"])

    # Read all tests file
    with open(all_tests, mode="r") as tests_file:
        tests = [test.strip() for test in tests_file.readlines()]

    tests_sample = random.sample(tests, int(random_p * (len(tests))))

    # Build problem data
    data = ProblemData(
        activity_matrix,
        config["branch"],
        config["fails_start_dt"],
        config["from_dt"],
        config["to_dt"],
        ignore_tests=config["ignore_tests"],
    )

    # Run tool for each revision
    results = []
    previous = None
    # for log_e in log[:100]:
    for log_e in log:
        if not is_ignored_project(log_e.changelist, config["ignore_changes"]):
            res = run_tool_for_revision(
                log_e, data, previous, config["ignore_changes"], tests_sample
            )
            results.append(res)
            previous = res

    # Build results summary report
    summary = ResultsSummary(results, data)

    # - print summary to terminal
    summary.export_to_text()

    # save data to pickle
    with open(output_file, mode="wb") as output:
        summary.export_to_pickle(output)


def run_pipeline(data, objectives, revision: RevisionResults, ignore_changes):
    # Get indexes for methods changed by a commit
    changed_idxs = data.get_changed_indexes_for_changelist(
        revision.changelist, ignore_changes
    )

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


def is_ignored_project(changelist, ignore_changes):
    return all(
        any(
            ignore in change[1]
            for ignore in ignore_changes
        )
        for change in changelist
    )


if __name__ == "__main__":
    cli()
