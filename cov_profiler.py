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
    # Load config file
    with open(config_file, mode="r") as demo_file:
        config = json.load(demo_file)
        test_lists = config["runlists"]

    with open(f"{config['branch']}_log_profiler.txt", mode="a") as log_file:
        for testlist in test_lists:
            run_coverage_profiler(config, testlist, log_file)


def run_coverage_profiler(config, testlist, log_file):
    print(testlist)
    log_file.write(testlist + "\n")
    log_file.flush()

    command, output = get_opencover_args(config, testlist)

    print(f"Command: {command} --> Output: {output}")
    log_file.write(f"Command: {command} --> Output: {output}\n")
    log_file.flush()

    # Run and profile tests with OC
    start = time.perf_counter()
    subprocess.call(command)
    end = time.perf_counter()

    print(f"Run for {output}: {(end - start) / 60} minutes")
    log_file.write(f"Run for {output}: {(end - start) / 60} minutes\n")
    log_file.flush()


def get_opencover_args(config, testlist):
    # Load relevant data from config
    runner = config["runner"]
    runner_args = config["runner_args"]
    threshold = config["threshold"]
    filters = config["filters"]
    cover_by_test = config["cover_by_test"]
    search_dirs = config["searchdirs_path"]

    # Build OpenCover command
    args = [
        f" -target: {runner}",
        f" -targetargs:{' '.join(runner_args)} {testlist}",
        f" -threshold:{threshold} ",
        " -hideskipped:All ",
        " -mergebyhash ",
        #        " -skipautoprops ",
        f" -filter:{' '.join(filters)} ",
        f" -coverbytest:{';'.join(cover_by_test)} ",
        f" -searchdirs: {search_dirs} ",
        " -register:user ",
    ]
    command = [config["opencover_exec"]]
    command.extend(args)

    runlists_path = config["runlists_path"]
    pattern = re.escape(runlists_path) + r"(.*).in"
    output = re.search(pattern, testlist).group(1)

    reports_path = config["reports_path"]
    command.append(f"-output:{reports_path}refactor_{output}.xml")
    return command, output


if __name__ == "__main__":
    cli()
