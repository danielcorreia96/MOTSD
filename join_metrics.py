# coding=utf-8
import os
import pickle
import re
from itertools import permutations
from itertools import product

import click

from backend.evaluation.summary import ResultsSummary
from generate_tests import COVERAGE_MAP
from generate_tests import HISTORY_MAP


@click.group()
def cli():
    pass


@cli.command("per_size")
@click.argument("data_dir", type=click.Path(exists=True))
def start(data_dir):
    sizes = [5, 10, 25, 50, 100, 200, 400]
    for size in [str(x) for x in sizes]:
        print_merged_results(size, data_dir)


@cli.command("per_2combos")
@click.argument("data_dir", type=click.Path(exists=True))
def start(data_dir):
    all_combos = []
    for (cov, hist) in product(COVERAGE_MAP.items(), HISTORY_MAP.items()):
        combos = [f"{m1}{m2}" for ((_, m1), (_, m2)) in permutations([cov, hist], 2)]
        all_combos.extend(combos)
    all_combos.sort()

    for name in all_combos:
        print_merged_results(name, data_dir)


@cli.command("per_3combos")
@click.argument("data_dir", type=click.Path(exists=True))
def start(data_dir):
    all_combos = []
    for (cov, hist1, hist2) in product(
        COVERAGE_MAP.items(), HISTORY_MAP.items(), HISTORY_MAP.items()
    ):
        if hist1 == hist2:
            continue
        combos = permutations([cov, hist1, hist2], 3)
        for ((_, m1_name), (_, m2_name), (_, m3_name)) in combos:
            metrics_name = f"{m1_name}{m2_name}{m3_name}"
            if metrics_name in all_combos:
                continue
            all_combos.append(metrics_name)
    all_combos.sort()

    for name in all_combos:
        print_merged_results(name, data_dir)


def print_merged_results(key, data_dir):
    key_results = []
    for batch in ["demo1", "demo2", "demo3", "demo4"]:
        pattern = re.compile(r"_" + key + r"_" + batch + r".pickle")
        results = [
            os.path.abspath(os.path.join(data_dir, x))
            for x in os.listdir(data_dir)
            if re.search(pattern, x) is not None
        ]
        aggregated: ResultsSummary = pickle.load(open(results[0], mode="rb"))
        for file in results[1:]:
            aggregated.merge_same(pickle.load(open(file, mode="rb")))

        key_results.append(aggregated)

    while len(key_results) > 1:
        key_results[0].merge_diff(key_results.pop())
    key_final = key_results.pop()
    key_final.normalize_diff(4)
    # print(f"{key}")
    print(f"{key_final.export_to_csv_line(prefix=key.upper())}")


if __name__ == "__main__":
    cli()
