# coding=utf-8
import os
from multiprocessing import Pool
import click

@click.group()
def cli():
    pass

@cli.command("start")
@click.argument("input_list", type=click.Path(exists=True, readable=True))
def start(input_list):
    with open(input_list, mode="r") as infile:
        combos = infile.readlines()

    with Pool(processes=3) as pool:
        pool.map(run_command, combos)


def run_command(command):
    print(f"Running command: {command}")
    os.system(command)


if __name__ == "__main__":
    cli()
