"""
This is a template config. The file `staging/config.py` is optional;
if you don't need to test multiple configs, then don't create it.

Your `CONFIG` variable MUST be a `list[dict[str, Value]]`, where

    Value = int | float | str | bool | list[int | float | str | bool]

Please try to keep the key names short; 1-2 characters is recommended.
The keys will be used to label the scripts, and it is easier if the
labels are short.
"""

def get_data():
    # example of getting data from somewhere else
    return {"mid_price": 1000}

mid_price = get_data()["mid_price"]
fair_prices = [mid_price + i for i in range(-20, 21, 10)]

# Make sure a `CONFIG` variable is defined, otherwise it will be empty.
CONFIG = [
    {
        "fp": fair_price,
    }
    for fair_price in fair_prices
]
