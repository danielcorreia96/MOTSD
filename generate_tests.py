# coding=utf-8
COVERAGE_MAP = {"ddu": "d", "norm_coverage": "n"}

HISTORY_MAP = {"exec_times": "e", "fails": "f", "n_tests": "t"}

DATA = [
    (
        "demo1",
        "all_trunk_demo1_tests.in",
        "data\\jsons\\actmatrix_v2_trunk_demo1.json",
        "data\\poc_demos\\trunk_demo1.config",
    ),
    (
        "demo2",
        "all_trunk_demo2_tests.in",
        "data\\jsons\\actmatrix_v2_trunk_demo2.json",
        "data\\poc_demos\\trunk_demo2.config",
    ),
    (
        "demo3",
        "all_trunk_demo3_tests.in",
        "data\\jsons\\actmatrix_v2_trunk_demo3.json",
        "data\\poc_demos\\trunk_demo3.config",
    ),
    (
        "demo4",
        "all_trunk_demo4_tests.in",
        "data\\jsons\\actmatrix_v2_trunk_demo4.json",
        "data\\poc_demos\\trunk_demo4.config",
    ),
]

COMMAND = "python testsel_pipeline.py demo"
RANDOM_COMMAND = "python testsel_pipeline.py random"

OUTPUT_PATH = "data\\results\\thesis"


def print_command(metrics, size, data, config, output):
    print(f"{COMMAND} {metrics} {size} {data} {config} {output}.pickle > {output}.out")


def print_random_command(
    tests, data, config, output, random_prob, fixed=False, filtered=False
):
    options = ""
    if fixed:
        options += "--fixed "
    if filtered:
        options += "--filtered "
    print(
        f"{RANDOM_COMMAND} {options} {random_prob} {tests} {data} {config} {output}.pickle > {output}.out"
    )


def baseline_tests():
    base = f"{OUTPUT_PATH}\\baseline\\base_"
    metrics, size = "-o ddu -o fails", 100
    for (batch, json_data, config) in DATA:
        name = f"{base}{batch}"
        print_command(metrics, size, json_data, config, name)
    print()


def metrics_2combos_tests():
    from itertools import permutations, product

    base = f"{OUTPUT_PATH}\\metrics_combos\\mcombos_"
    for (batch, _, json_data, config) in DATA:
        for (cov, hist) in product(COVERAGE_MAP.items(), HISTORY_MAP.items()):
            combos = permutations([cov, hist], 2)
            for ((m1_key, m1_name), (m2_key, m2_name)) in combos:
                name = f"{base}{m1_name}{m2_name}_{batch}"
                metrics, size = f"-o {m1_key} -o {m2_key}", 100
                print_command(metrics, size, json_data, config, name)
        print()
    print()


def metrics_3combos_tests():
    from itertools import permutations, product

    base = f"{OUTPUT_PATH}\\metrics_combos\\mcombos_"
    for (batch, _, json_data, config) in DATA:
        combos_done = []
        for (cov, hist1, hist2) in product(
            COVERAGE_MAP.items(), HISTORY_MAP.items(), HISTORY_MAP.items()
        ):
            if hist1 == hist2:
                continue
            combos = permutations([cov, hist1, hist2], 3)
            for ((m1_key, m1_name), (m2_key, m2_name), (m3_key, m3_name)) in combos:
                metrics_name = f"{m1_name}{m2_name}{m3_name}"
                if metrics_name in combos_done:
                    continue
                name = f"{base}{metrics_name}_{batch}"
                metrics, size = f"-o {m1_key} -o {m2_key} -o {m3_key}", 100
                print_command(metrics, size, json_data, config, name)
                combos_done.append(metrics_name)
        print()
    print()


def metrics_4combos_tests():
    from itertools import permutations, product

    base = f"{OUTPUT_PATH}\\metrics_combos\\mcombos_"
    for (batch, _, json_data, config) in DATA:
        combos_done = []
        for (cov, hist1, hist2, hist3) in product(
            COVERAGE_MAP.items(),
            HISTORY_MAP.items(),
            HISTORY_MAP.items(),
            HISTORY_MAP.items(),
        ):
            if hist1 == hist2 or hist1 == hist3 or hist2 == hist3:
                continue
            combos = permutations([cov, hist1, hist2, hist3], 4)
            for (
                (m1_key, m1_name),
                (m2_key, m2_name),
                (m3_key, m3_name),
                (m4_key, m4_name),
            ) in combos:
                metrics_name = f"{m1_name}{m2_name}{m3_name}{m4_name}"
                if metrics_name in combos_done:
                    continue
                name = f"{base}{metrics_name}_{batch}"
                metrics, size = f"-o {m1_key} -o {m2_key} -o {m3_key} -o {m4_key}", 100
                print_command(metrics, size, json_data, config, name)
                combos_done.append(metrics_name)
        print()
    print()


def swarm_size_tests():
    base = f"{OUTPUT_PATH}\\swarm_size\\swsize_"
    metrics = "-o ddu -o fails"
    for (batch, _, json_data, config) in DATA:
        sizes = [5, 10, 25, 50, 100, 200, 400]
        for size in sizes:
            name = f"{base}{size}_{batch}"
            print_command(metrics, size, json_data, config, name)
    print()


def random_fixed_tests():
    base = f"{OUTPUT_PATH}\\random_fixed\\ranfixed_"
    for (batch, tests, json_data, config) in DATA:
        random_p = [0.10, 0.15, 0.20, 0.25]
        for prob in random_p:
            for i in range(1, 11):
                name = f"{base}{str(int(prob*100))}_{i}_{batch}"
                print_random_command(
                    tests, json_data, config, name, prob, fixed=True, filtered=False
                )
        print()
    print()


def random_dynamic_tests():
    base = f"{OUTPUT_PATH}\\random_dynamic\\randynam_"
    for (batch, tests, json_data, config) in DATA:
        random_p = [0.10, 0.15, 0.20, 0.25]
        for prob in random_p:
            for i in range(1, 11):
                name = f"{base}{str(int(prob*100))}_{i}_{batch}"
                print_random_command(
                    tests, json_data, config, name, prob, fixed=False, filtered=False
                )
        print()
    print()


def random_dynamic_filtered_tests():
    base = f"{OUTPUT_PATH}\\random_dynamic_filter\\randynamfilter_"
    for (batch, tests, json_data, config) in DATA:
        random_p = [0.10, 0.15, 0.20, 0.25]
        for prob in random_p:
            for i in range(1, 11):
                name = f"{base}{str(int(prob*100))}_{i}_{batch}"
                print_random_command(
                    tests, json_data, config, name, prob, fixed=False, filtered=True
                )
        print()
    print()


def random_fixed_filtered_tests():
    base = f"{OUTPUT_PATH}\\random_fixed_filter\\ranfixedfilter_"
    for (batch, tests, json_data, config) in DATA:
        random_p = [0.10, 0.15, 0.20, 0.25]
        for prob in random_p:
            for i in range(1, 11):
                name = f"{base}{str(int(prob*100))}_{i}_{batch}"
                print_random_command(
                    tests, json_data, config, name, prob, fixed=True, filtered=True
                )
        print()
    print()


if __name__ == "__main__":
    random_fixed_tests()
    random_fixed_filtered_tests()
    random_dynamic_tests()
    random_dynamic_filtered_tests()
    # baseline
    # baseline_tests()

    # swarm size
    # swarm_size_tests()

    # metrics 2-combos
    # metrics_2combos_tests()

    # metrics 3-combos
    # metrics_3combos_tests()

    # metrics 4-combos
    # metrics_4combos_tests()
