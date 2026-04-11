"""
This script reads your `solution.py` and creates a single script in
`build/` that is ready for submission. See `staging/README.md` for
more details.
"""


import json
import re
from datetime import datetime
import sys
import os
import shutil


def get_solution_code():
    try:
        with open("staging/solution.py", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            "Solution file (`staging/solution.py`) not found")


def get_logger_code():
    try:
        with open("core/logger.py", "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            "Logger file (`core/logger.py`) not found")


def get_configs():
    try:
        from staging.config import CONFIG  # type: ignore
        assert isinstance(CONFIG, list), \
            "CONFIG must be a list of dicts"
        assert all(isinstance(conf, dict) for conf in CONFIG), \
            "Each config must be a dict with values of type int, " \
            "float, str, bool, or a list of it."
        return CONFIG  # just assume the values are valid
    except ImportError:
        return None


def check_script_validity(script):
    # TODO: Raise exception if the script is invalid
    pass


def generate_scripts(use_config):
    solution_code = get_solution_code()
    logger_code = get_logger_code()
    config_pattern = re.compile(
        r"##### CONFIG #####\n(.*?)\n##### CONFIG #####", re.DOTALL)
    logger_pattern = re.compile(
        r"##### LOGGER #####\n(.*?)\n##### LOGGER #####", re.DOTALL)

    config_match = config_pattern.search(solution_code)
    logger_match = logger_pattern.search(solution_code)
    if not config_match or not logger_match:
        raise ValueError(
            "Config or logger section not found in solution.py")

    # need to use repr since special characters are escaped by re.sub
    solution_code = re.sub(logger_pattern, repr(logger_code)[1:-1],
                           solution_code)

    configs = get_configs() if use_config else None

    if configs is None:
        script = re.sub(config_pattern, "", solution_code)
        check_script_validity(script)
        return [(None, script)]

    else:
        scripts = []
        for conf in configs:
            conf_label = "_".join(
                f"{k}_{'_'.join(str(i) for i in v) if isinstance(v, list) else str(v)}"
                for k, v in conf.items()
            )
            conf_str = str(conf)
            script = re.sub(config_pattern,
                            repr("CONFIG = " + conf_str)[1:-1],
                            solution_code)
            check_script_validity(script)
            scripts.append((conf_label, script))

        return scripts


def get_time_now():
    return datetime.now().strftime("%d%H%M%S")


def save_script(round_num, name, scripts, use_config):
    unique_name = f"{get_time_now()}_{name}"
    round_name = f"round_{round_num}" if round_num > 0 else "tutorial"
    version_dir = f"versions/{round_name}/{unique_name}"

    for conf_label, script in scripts:
        full_fname = unique_name + \
            ("" if conf_label is None else f"_{conf_label}")
        full_version_dir = version_dir + \
            ("" if conf_label is None else f"/{conf_label}")

        os.makedirs("build", exist_ok=True)
        os.makedirs(f"{full_version_dir}",
                    exist_ok=False)  # it should not already exist
        with open(f"build/{full_fname}.py", "w") as f:
            f.write(script)
        with open(f"{full_version_dir}/submission.py", "w") as f:
            f.write(script)

    shutil.copy("staging/solution.py", f"{version_dir}/solution.py")
    if use_config:
        shutil.copy("staging/config.py", f"{version_dir}/config.py")


def main():
    round_num, name, use_config = int(sys.argv[1]), sys.argv[2], \
        bool(int(sys.argv[3]))
    scripts = generate_scripts(use_config)
    save_script(round_num, name, scripts, use_config)
    print("Done!")


if __name__ == "__main__":
    main()
