# coding=utf-8
import os
import pickle
import re
from typing import Optional, Any

import click

from backend.evaluation.summary import ResultsSummary


@click.group()
def cli():
    pass


@cli.command("per_batch")
@click.argument("data_dir", type=click.Path(exists=True))
@click.option(
    "--innocent", is_flag=True, help="Recompute each sample using innocent filter"
)
def start(data_dir, innocent):
    for batch in ["demo1", "demo2", "demo3", "demo4"]:
        for prob in [str(int(x * 100)) for x in [0.10, 0.15, 0.20, 0.25]]:
            pattern = re.compile(prob + r"_\d+_" + batch + r".pickle")
            results = [
                os.path.abspath(os.path.join(data_dir, x))
                for x in os.listdir(data_dir)
                if re.search(pattern, x) is not None
            ]
            aggregated: ResultsSummary = pickle.load(open(results[0], mode="rb"))
            if innocent:
                aggregated.recompute_innocent()
            for file in results[1:]:
                summary = pickle.load(open(file, mode="rb"))
                if innocent:
                    summary.recompute_innocent()
                aggregated.merge_same(summary)

            for k in aggregated.red_stats:
                aggregated.red_stats[k] = aggregated.red_stats[k] / 10
            for k in aggregated.new_feedback_time:
                aggregated.new_feedback_time[k] = aggregated.new_feedback_time[k] / 10
            print(f"{aggregated.export_to_csv_line()}")


@cli.command("per_prob")
@click.argument("data_dir", type=click.Path(exists=True))
@click.option(
    "--innocent", is_flag=True, help="Recompute each sample using innocent filter"
)
def start(data_dir, innocent):
    for prob in [str(int(x * 100)) for x in [0.10, 0.15, 0.20, 0.25]]:
        prob_results = []
        for batch in ["demo1", "demo2", "demo3", "demo4"]:
            pattern = re.compile(prob + r"_\d+_" + batch + r".pickle")
            results = [
                os.path.abspath(os.path.join(data_dir, x))
                for x in os.listdir(data_dir)
                if re.search(pattern, x) is not None
            ]
            aggregated: ResultsSummary = pickle.load(open(results[0], mode="rb"))
            if innocent:
                aggregated.recompute_innocent()
            for file in results[1:]:
                summary = pickle.load(open(file, mode="rb"))
                if innocent:
                    summary.recompute_innocent()
                aggregated.merge_same(summary)

            for k in aggregated.red_stats:
                aggregated.red_stats[k] = aggregated.red_stats[k] / 10
            for k in aggregated.new_feedback_time:
                aggregated.new_feedback_time[k] = aggregated.new_feedback_time[k] / 10

            prob_results.append(aggregated)

        while len(prob_results) > 1:
            prob_results[0].merge_diff(prob_results.pop())
        prob_final = prob_results.pop()
        prob_final.normalize_diff(4)
        print(f"{prob_final.export_to_csv_line()}")


if __name__ == "__main__":
    cli()
