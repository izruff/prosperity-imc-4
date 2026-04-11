"""
An extension of the `Trader` class with helper functions to make
life easier.
"""

from datamodel import Product, Order, TradingState
import jsonpickle

# You should not copy this import over to `solution.py`.
from core.logger import logger


class BaseTrader:
    def load_state(self, state: TradingState):
        raise NotImplementedError

    def bid(self):
        raise NotImplementedError

    def run(self, state):
        raise NotImplementedError


class TutorialTrader(BaseTrader):
    pos_limits: dict[Product, int] = {
        "EMERALDS": 80,
        "TOMATOES": 80,
    }

    def load_state(self, state: TradingState):
        self.state = state

        # User-defined data from previous time step
        self.data = None if state.traderData == "" else \
            jsonpickle.loads(state.traderData)

        # Divide by 100 so each step is 1 increment of time
        self.ts = state.timestamp / 100

        # Mapping from product to its denomination
        # TODO: This is not yet used; update later once enough info.
        self.denomination_map = {
            symbol: listing.denomination
            for symbol, listing in state.listings.items()
        }

        # Mapping from product to its symbol
        # TODO: It could be the case that the datamodel is outdated and
        # some dicts are actually using Product as key but is typed as
        # Symbol (and vice versa). For now, we can assume product ==
        # symbol, so we actually don't use this yet. Update later once
        # we have more info.
        self.symbol_map = {
            listing.product: symbol
            for symbol, listing in state.listings.items()
        }

        # Buy orders (price, qty) sorted in descending order of price
        # (first = best bid, last = worst bid)
        self.buy_orders = {
            symbol: list(map(lambda t: (int(t[0]), int(t[1])),
                             sorted(order_depth.buy_orders.items(),
                                    reverse=True)))
            for symbol, order_depth in state.order_depths.items()
        }

        # Sell orders (price, qty) sorted in ascending order of price
        # (first = best ask, last = worst ask)
        self.sell_orders = {
            symbol: list(map(lambda t: (int(t[0]), -int(t[1])),
                             sorted(order_depth.sell_orders.items())))
            for symbol, order_depth in state.order_depths.items()
        }

        # Remaining buy orders if matching were to take place
        # In other words, if we were to submit self.orders_to_send,
        # the matching engine will first attempt to match our buy
        # orders with the sell orders in self.sell_orders. The result
        # of that will be self.buy_orders_am (am = after matching).
        # This is useful if we want to market make (for example);
        # simply look at the first element of self.buy_orders_am for
        # the best bid.
        # (has same sorting as self.buy_orders)
        self.buy_orders_am = self.buy_orders.copy()

        # Remaining sell orders if matching were to take place
        # (has same sorting as self.sell_orders)
        self.sell_orders_am = self.sell_orders.copy()

        # The list of trades we made on the last time step we had any
        # trades; this is the only way to know our exact trades.
        self.own_trades = state.own_trades.copy()

        # Market trades made on the previous time step
        self.market_trades = state.market_trades.copy()

        # Our current position
        self.position = {
            listing.product: state.position.get(listing.product, 0)
            for listing in state.listings.values()
        }

        # Ignore for now
        self.observations = state.observations

        # There is a cap on the number of buy/sell orders you can make
        # in a given time step. The resulting position must not exceed
        # the position limit if all buy orders are filled, or if all
        # sell orders are filled.
        # TODO: We currently don't enforce this! It is up to the user.
        self.max_buy_orders = {
            product: self.pos_limits[product] - self.position[product]
            for product in self.pos_limits
        }
        self.max_sell_orders = {
            product: self.pos_limits[product] + self.position[product]
            for product in self.pos_limits
        }

        # To be filled in by self._run using self.send_[buy|sell]_order
        self.orders_to_send = {listing.product: []
                               for listing in state.listings.values()}

    # This is AFTER MATCHING
    def best_bid(self, product: Product):
        if self.buy_orders_am[product]:
            return self.buy_orders_am[product][0][0]
        return None

    # This is AFTER MATCHING
    def best_ask(self, product: Product):
        if self.sell_orders_am[product]:
            return self.sell_orders_am[product][0][0]
        return None

    # This is AFTER MATCHING
    def best_bid_qty(self, product: Product):
        if self.buy_orders_am[product]:
            return self.buy_orders_am[product][0][1]
        return None

    # This is AFTER MATCHING
    def best_ask_qty(self, product: Product):
        if self.sell_orders_am[product]:
            return self.sell_orders_am[product][0][1]
        return None

    # Call this to write data for the next timestamp. Make sure the old
    # data is no longer used.
    def write_data(self, data = None):
        self.data = "" if data is None else jsonpickle.dumps(data)

    def send_buy_order(self, product: Product, price: int,
                       quantity: int, msg: str = None):
        self.orders_to_send[product].append(
            Order(product, price, quantity)
        )
        unmatched_qty = quantity
        while unmatched_qty > 0:
            best_ask = self.best_ask(product)
            if best_ask is None or best_ask > price:
                break
            best_ask_qty = self.best_ask_qty(product)
            match_qty = min(unmatched_qty, best_ask_qty)
            unmatched_qty -= match_qty
            if best_ask_qty == match_qty:
                self.sell_orders_am[product].pop(0)
            else:
                self.sell_orders_am[product][0] = \
                    (best_ask, best_ask_qty - match_qty)
        if msg:
            logger.print(f"BUY {quantity} {product} @ {price} ({msg})")

    def send_sell_order(self, product: Product, price: int,
                        quantity: int, msg: str = None):
        self.orders_to_send[product].append(Order(product, price, -quantity))
        unmatched_qty = quantity
        while unmatched_qty > 0:
            best_bid = self.best_bid(product)
            if best_bid is None or best_bid < price:
                break
            best_bid_qty = self.best_bid_qty(product)
            match_qty = min(unmatched_qty, best_bid_qty)
            unmatched_qty -= match_qty
            if best_bid_qty == match_qty:
                self.buy_orders_am[product].pop(0)
            else:
                self.buy_orders_am[product][0] = \
                    (best_bid, best_bid_qty - match_qty)
        if msg:
            logger.print(f"SELL {quantity} {product} @ {price} ({msg})")

    def _run(self):
        raise NotImplementedError

    def run(self, state: TradingState):
        self.load_state(state)
        self._run()
        if self.data is None:
            self.data = ""
        logger.flush(state, self.orders_to_send, 0, self.data)  # no conversions this round
        return self.orders_to_send, 0, self.data
