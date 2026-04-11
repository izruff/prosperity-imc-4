# Instructions

## Writing your implementation

Put the implementation for class `Trader` in `staging/solution.py`. This file is ignored by Git; this is so we can push changes and avoid conflicts.

See `solution_example.py` for a basic template. Note that you are meant to fill in the `_run` method instead of `run` (the implementation in `trader.py` already handles all logic other than the trading strategy itself). See `trader.py` for how to use the trader class.

## Using `core/` functions

All the helper functions are in the `core/` directory. The easiest way to use them for now is to simply copy-paste what you want to use (this also makes it easy to collaborate with AI agents). Note that we cannot import them since the submission must be one single file.

## Using the logger

The backtest visualizer (credit to @jmerle) requires a specific logging format to be able to show backtesting data properly. To log a message, write

```
logger.print("your message here")
```

You don't need to import `logger` (it is already handled by the `submit.py` script). Do NOT log anything other than strings (this will likely cause an error when uploading the log to the visualizer).

Also, the `run` method should call `logger.flush` at the end of every iteration, but again this is already implemented for you.

## Multiple configs

Sometimes, you may want to tweak your algorithm and test multiple configurations (e.g. to do grid search). In this case, you can put your configs in `staging/config.py`. This file is also ignored by Git.

The submission tool will create multiple scripts, one for each item in the config list. See `config_example.py` for a basic template and details about the structure. Note that it is optional; if there is no `config.py` file, only one script is generated.

## Submission

To generate the ready-to-submit script(s), run

```
uv run submit.py [round_num] [name] [use_config]
```

where:
- `round_num` is the current round number (1 to 5, 0 for tutorial),
- `name` is what you want to name the script, and
- `use_config` is 1 if you want to use `config.py`, else 0.

This will generate the script(s) in `build/` and also copy them to a new directory under `versions/`. The names will be prefixed with a `%d%H%M%S` timestamp to guarantee uniqueness and automatic ordering. After testing, please upload relevant testing results (graphs, logs, your own notes, etc.) to this version directory.
