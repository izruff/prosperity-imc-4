"""
Special logger class to allow the backtester tool (credit to @jmerle)
to capture logs.
"""


from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState
from typing import List, Any
import json


class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi = 0, min(len(value), max_length)
        out = ""

        while lo <= hi:
            mid = (lo + hi) // 2

            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."

            encoded_candidate = json.dumps(candidate)

            if len(encoded_candidate) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        return out


logger = Logger()



"""
Check the calculation of PnL and the behavior of the matching engine.
It is known that unfilled orders are cancelled at the end of the
timestamp; I didn't bother checking this, assumed it is true.
"""


from datamodel import Time, Product, Symbol, Position, UserId, \
    ObservationValue, Listing, Observation, Order, OrderDepth, \
    Trade, TradingState, ProsperityEncoder
import jsonpickle


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

        # Our own trades on the previous (??) time step (could also be
        # the last time step we had any trades; don't care about this
        # for now)
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


class Trader(TutorialTrader):
    def _run(self):
        if self.ts == 0:
            # Buy order is way better than best bid; should always be
            # filled by matching engine
            self.send_buy_order("TOMATOES", 5025, 10, "test")
            # Then check how PnL is calculated for this timestamp
        elif self.ts == 1:
            # Same as before but with much higher quantity; bots might
            # fill part of it
            self.send_buy_order("TOMATOES", 5025, 70, "test")
            # Then check how PnL is calculated for this timestamp
        
        # Check if matching logic is correct.
        logger.print("sell_orders:", str(self.sell_orders))
        logger.print("sell_orders_am:", str(self.sell_orders_am))
        # Wait until the end of day and see how PnL is calculated
        # across all timestamps.
