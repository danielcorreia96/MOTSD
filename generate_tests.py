# coding=utf-8
COVERAGE_MAP = {"ddu": "d", "coverage": "c", "norm_coverage": "n"}

HISTORY_MAP = {"exec_times": "e", "fails": "f", "n_tests": "t"}

DATA = [
    (
        "demo1",
        "data\\jsons\\actmatrix_v2_trunk_demo1.json",
        "data\\poc_demos\\trunk_demo1.config",
    ),
    (
        "demo2",
        "data\\jsons\\actmatrix_v2_trunk_demo2.json",
        "data\\poc_demos\\trunk_demo2.config",
    ),
    (
        "demo3",
        "data\\jsons\\actmatrix_v2_trunk_demo3.json",
        "data\\poc_demos\\trunk_demo3.config",
    ),
    (
        "demo4",
        "data\\jsons\\actmatrix_v2_trunk_demo4.json",
        "data\\poc_demos\\trunk_demo4.config",
    ),
]

COMMAND = "python testsel_pipeline.py demo"

OUTPUT_PATH = "data\\results\\thesis"


def print_command(metrics, size, data, config, output):
    print(f"{COMMAND} {metrics} {size} {data} {config} {output}.pickle > {output}.out")


def baseline_tests():
    base = f"{OUTPUT_PATH}\\baseline\\base_"
    metrics, size = "-o ddu -o fails", 100
    for (batch, json_data, config) in DATA:
        name = f"{base}{batch}"
        print_command(metrics, size, json_data, config, name)
    print()


def metrics_combos_tests():
    from itertools import permutations, product

    base = f"{OUTPUT_PATH}\\metrics_combos\\mcombos_"
    for (batch, json_data, config) in DATA:
        for (cov, hist) in product(COVERAGE_MAP.items(), HISTORY_MAP.items()):
            combos = permutations([cov, hist], 2)
            for ((m1_key, m1_name), (m2_key, m2_name)) in combos:
                name = f"{base}{m1_name}{m2_name}_{batch}"
                metrics, size = f"-o {m1_key} -o {m2_key}", 100
                print_command(metrics, size, json_data, config, name)
        print()
    print()


def swarm_size_tests():
    base = f"{OUTPUT_PATH}\\swarm_size\\swsize_"
    metrics = "-o ddu -o fails"
    for (batch, json_data, config) in DATA:
        sizes = [5, 10, 25, 50, 100, 200, 400]
        for size in sizes:
            name = f"{base}{size}_{batch}"
            print_command(metrics, size, json_data, config, name)

    print()


if __name__ == "__main__":
    # baseline
    baseline_tests()

    # swarm size
    swarm_size_tests()

    # metrics combos
    metrics_combos_tests()
