##### LOGGER #####
from core.logger import logger
##### LOGGER #####
##### CONFIG #####
CONFIG = {}
##### CONFIG #####


import functools  # check if I can use cache decorator


class Trader:
    def bid(self):
        pass    
    def run(self, state):
        logger.print(state.toJSON())
        logger.flush(state, {}, 0, "")
        return {}, 0, ""
