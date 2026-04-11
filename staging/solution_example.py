"""
This is a template solution. It buys or sells product X according to a
fair price of `CONFIG["fair_price"]` (buy low, sell high). It also
makes sure that the position limits are respected.

Here are things you MUST know before implementing a solution:

  - The data structures and helper functions from `core/` are all
    already imported for you (see `__init__.py`). However, you should
    import 3rd party libraries yourself. These include:

        numpy, pandas, statistics, math, typing, jsonpickle

  - All the core functions are designed not to raise exceptions.
    Whether they succeed or fail will be known by checking the return
    value (check their docstring for details). You MUST make sure
    your code CANNOT raise exceptions in any way.

  - If you need to print logs, use the `logger.print`. This will allow
    the backtester tool (credit to @jmerle) to capture your logs.

  - The last two lines of `Trader.run` MUST be:

        logger.flush(state, result, conversions, traderData)
        return result, conversions, traderData

    where `state` is the state given as argument for `Trader.run`,
    `result` is the `dict[Product, list[Order]]` of orders you want to
    place, `conversions` is the number of conversions (ignore this for
    now), and `traderData` is the data you want to pass to the next
    timestamp. Note that `traderData` must be encoded with
    `jsonpickle.dumps` first.
"""


##### LOGGER #####
# This will be replaced by the logger class from `core/logger.py`.
from core.logger import logger
##### LOGGER #####
##### CONFIG #####
"""
If you specify a config file, the submission tool will replace this
with the actual configs specified in `staging/config.py`. Otherwise,
this part will be removed.

TODO: Add basic testing for silly mistakes
If you want to test your solution and you have multiple configs, you
need to specify the config you want to test. Other than for testing,
do NOT write anything in this part.
"""
CONFIG = {}
##### CONFIG #####


# Easier to always import these
from datamodel import Time, Product, Symbol, Position, UserId, \
    ObservationValue, Listing, Observation, Order, OrderDepth, \
    Trade, TradingState, ProsperityEncoder
