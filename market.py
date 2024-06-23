import numpy as np

# time arrays and scalars
day_slots = 96
day_time = np.linspace(0, 24, day_slots*5)
days = 14

# Definition of Participant
# A participant has an id, a load profile, a flag indicating whether it is a prosumer, and a PV profile
class Participant:
    def __init__(self, id, profile, pv=False, pv_profile=None, battery_capacity=0):
        self.id = id
        self.profile = profile
        self.pv = pv
        self.pv_profile = pv_profile
        self.energy_demand = np.array(profile)
        self.energy_supply = np.zeros_like(profile) if not pv else np.array(pv_profile)
        self.bids = []
        self.asks = []
        self.energy_storage = np.zeros(days + 1)


# Definition of the Continuous Double Auction Market
# The market has a list of participants, a minimum price, and a maximum price
# The market collects orders from participants based on a given strategy
# The market matches orders and clears the market
class CDAMarket:
    def __init__(self, participants, min_price, max_price):
        self.participants = participants
        self.min_price = min_price
        self.max_price = max_price
        self.order_book = []

    def collect_orders(self, strategy, time_slot, time_remaining):
        best_bid_price = self.min_price
        best_ask_price = self.max_price
        for participant in self.participants:
            bid_price, bid_quantity, ask_price, ask_quantity = strategy(participant, best_bid_price, best_ask_price, self.min_price, self.max_price, time_remaining)
            if bid_quantity > 0:
                self.order_book.append((participant.id, 'bid', bid_price, bid_quantity, time_slot))
                best_bid_price = max(best_bid_price, bid_price)
            if ask_quantity > 0:
                self.order_book.append((participant.id, 'ask', ask_price, ask_quantity, time_slot))
                best_ask_price = min(best_ask_price, ask_price)

    # create order book where bids are sorted in descending order and asks are sorted in ascending order
    def match_orders(self):
        # bids are sorted in descending order
        bids = sorted([order for order in self.order_book if order[1] == 'bid'], key=lambda x: -x[2])
        # asks are sorted in ascending order
        asks = sorted([order for order in self.order_book if order[1] == 'ask'], key=lambda x: x[2])
        matches = []
        while bids and asks and bids[0][2] >= asks[0][2]:
            bid = bids.pop(0)
            ask = asks.pop(0)
            quantity = min(bid[3], ask[3])
            match_price = (bid[2] + ask[2]) / 2
            matches.append((bid[0], ask[0], quantity, match_price))
            if bid[3] > quantity:
                bids.insert(0, (bid[0], 'bid', bid[2], bid[3] - quantity, bid[4]))
            if ask[3] > quantity:
                asks.insert(0, (ask[0], 'ask', ask[2], ask[3] - quantity, ask[4]))
        self.order_book = bids + asks
        return matches

    def clear_market(self):
        self.order_book = []

# Strategies for agents

# Zero-Intelligence Strategy where agents randomly choose a price and quantity
def zi_strategy(participant, best_bid_price, best_ask_price, min_price, max_price, time_remaining):
    bid_price = np.random.uniform(min_price, max_price) if participant.pv else 0     # set bid orders to 0 for consumers
    bid_quantity = np.maximum(participant.energy_supply - participant.energy_demand, 0).sum() if participant.pv else 0     # set bid orders to 0 for consumers
    ask_price = np.random.uniform(min_price, max_price)
    ask_quantity = np.maximum(participant.energy_demand - participant.energy_supply, 0).sum()
    return (bid_price, bid_quantity, ask_price, ask_quantity)

# Eyes on the Best Strategy where agents set their prices based on the best bid and ask prices
def eob_strategy(participant, best_bid_price, best_ask_price, min_price, max_price, time_remaining):
    # Delta berechnen, abhängig von der verbleibenden Zeit
    delta = (1 - (time_remaining ** 2)) * ((max_price - min_price) / 2)
    if best_bid_price >= best_ask_price:
        bid_price = best_bid_price - delta if participant.pv else 0     # set bid orders to 0 for consumers
        ask_price = best_ask_price + delta
    else:
        bid_price = best_bid_price + delta if participant.pv else 0     # set bid orders to 0 for consumers
        ask_price = best_ask_price - delta
    bid_quantity = np.maximum(participant.energy_supply - participant.energy_demand, 0).sum() if participant.pv else 0     # set bid orders to 0 for consumers
    ask_quantity = np.maximum(participant.energy_demand - participant.energy_supply, 0).sum()
    return (bid_price, bid_quantity, ask_price, ask_quantity)
