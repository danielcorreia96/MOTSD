# coding=utf-8
import pickle
import backend
import os
import click

from backend.evaluation.summary import ResultsSummary


@click.group()
def cli():
    pass


@cli.command("start")
@click.argument("data_dir", type=click.Path(exists=True))
def start(data_dir):
	for batch in ["demo1","demo2","demo3","demo4"]:
	    results = [
	    	os.path.abspath(os.path.join(data_dir, x)) 
	    	for x in os.listdir(data_dir) 
	    	if f"{batch}.pickle" in x #and len(x) == 24
	    ]
	    for file in results:
	        summary: ResultsSummary = pickle.load(open(file, mode="rb"))
	        #print(f"{file[-16:-13]}")
	        print(f"==Results for {file}\n{summary.export_to_csv_line()}")



if __name__ == '__main__':
    cli()
