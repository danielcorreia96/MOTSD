# coding=utf-8
import json
import time
import subprocess
import re
import click


@click.group()
def cli():
    pass


@cli.command("run")
@click.argument("config_file", type=click.Path(exists=True, readable=True))
def run_profiler_for_config(config_file):
    """
    Run OpenCover profiler for a given configuration file

    :param config_file: path to the configuration file
    """
    # Load config file
    with open(config_file, mode="r") as demo_file:
        config = json.load(demo_file)
        test_lists = config["runlists"]

    with open(f"{config['branch']}_log_profiler.txt", mode="a") as log_file:
        for testlist in test_lists:
            run_coverage_profiler(config, testlist, log_file)


def run_coverage_profiler(config, testlist, log_file):
    """
    Run OpenCover profiler for a given list of tests and configuration file

    :param config: path to configuration file
    :param testlist: path to file with list of tests to run
    :param log_file: path to logging file
    """
    def write_log(message):
        print(message)
        log_file.write(message + "\n")
        log_file.flush()

    write_log(testlist)
    command, testlist_id = get_opencover_args(config, testlist)
    write_log(f"Command: {command} --> Output: {testlist_id}")

    # Run and profile tests with OpenCover
    start = time.perf_counter()
    subprocess.call(command)
    end = time.perf_counter()

    write_log(f"Run for {testlist_id}: {(end - start) / 60} minutes")


def get_opencover_args(config, testlist):
    """
    Builds an OpenCover command according to the configuration file and list of tests provided.

    :param config: path to configuration file
    :param testlist: path to file with list of tests to run
    :return: an OpenCover command and the id of the list of tests
    """
    # Load relevant data from config
    args = [
        f" -target: {config['runner']}",
        f" -targetargs:{' '.join(config['runner_args'])} {testlist}",
        f" -threshold:{config['threshold']} ",
        " -hideskipped:All ",
        " -mergebyhash ",
        #        " -skipautoprops ",
        f" -filter:{' '.join(config['filters'])} ",
        f" -coverbytest:{';'.join(config['cover_by_test'])} ",
        f" -searchdirs: {config['searchdirs_path']} ",
        " -register:user ",
    ]
    testlist_id = re.search(re.escape(config["runlists_path"]) + r"(.*).in", testlist).group(1)

    # Build OpenCover command with arguments
    command = [config["opencover_exec"]]
    command.extend(args)
    command.append(f"-output:{config['reports_path']}refactor_{testlist_id}.xml")
    return command, testlist_id


if __name__ == "__main__":
    cli()
