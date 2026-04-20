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


def get_submission_code(fname):
    try:
        with open(fname, "r") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Submission file (`{fname}`) not found")


def check_script_validity(script):
    # TODO: Raise exception if the script is invalid
    pass


def generate_final_script(fname):
    submission_code = get_submission_code(fname)
    logger_pattern = re.compile(
        r"##### LOGGER REPLACE FOR FINAL SUBMISSION #####\n(.*?)\n##### LOGGER REPLACE FOR FINAL SUBMISSION #####", re.DOTALL)
    trader_raise_pattern = re.compile(
        r"raise e\s*?##### RAISE REPLACE FOR FINAL SUBMISSION #####", re.DOTALL)

    logger_match = logger_pattern.search(submission_code)
    trader_raise_match = trader_raise_pattern.search(submission_code)

    dummy_logger_code = """
class Logger:
    def print(self, *args, **kwargs):
        print(*args, **kwargs)
    def flush(self, *args, **kwargs):
        pass  #TODO
        
"""

    if logger_match:
        submission_code = re.sub(logger_pattern, dummy_logger_code,
                                 submission_code)
    if trader_raise_match:
        submission_code = re.sub(trader_raise_pattern, 'return {}, 0, ""',
                                 submission_code)

    return submission_code


def get_time_now():
    return datetime.now().strftime("%d%H%M%S")


def save_script(code):
    with open(f"build/FINAL.py", "w") as f:
        f.write(code)


def main():
    fname = sys.argv[1]
    code = generate_final_script(fname)
    save_script(code)
    print("Done!")


if __name__ == "__main__":
    main()
