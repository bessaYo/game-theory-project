import numpy as np

class Participant:
    def __init__(self, id, load_profile, pv=False, pv_profile=None):
        self.id = id
        self.pv = pv
        self.energy_demand = np.round(load_profile.copy(), 3)
        self.energy_supply = np.round(pv_profile.copy(), 3) if pv_profile is not None else np.zeros_like(load_profile)
        self.cost = 0
        self.revenue = 0

class CDAMarket:
    def __init__(self, participants, otc_contracts, min_price, max_price):
        self.participants = participants
        self.otc_contracts = otc_contracts
        self.min_price = min_price
        self.max_price = max_price
        self.order_book = []
        self.trade_history = []

    # Apply OTC contracts to adjust energy demand and supply before the order matching starts
    def apply_otc_contracts(self, time_slot):
        for contract in self.otc_contracts:
            buyer_id, seller_id, quantity, price = contract
            for participant in self.participants:
                if participant.id == seller_id:
                    seller = participant
                if participant.id == buyer_id:
                    buyer = participant
    
            # Check if the seller has enough supply and buyer has enough demand
            if seller.energy_supply[time_slot] >= quantity and buyer.energy_demand[time_slot] >= quantity:
                # Adjust supply and demand
                seller.energy_supply[time_slot] -= quantity
                buyer.energy_demand[time_slot] -= quantity

                # Adjust financial transactions
                seller.revenue += quantity * price
                buyer.cost += quantity * price
                print(f"OTC Contract executed: {seller_id} sells {quantity} kWh to {buyer_id} at {price}€ per unit.")

    # Prosumers consume their energy first and then supply the excess energy    
    def deduce_prosumer_supply(self, time_slot):
        for participant in self.participants:
            if participant.pv:
                # Calculate net energy
                net_energy = participant.energy_supply[time_slot] - participant.energy_demand[time_slot]
                
                # Adjust demand and supply based on net energy
                if net_energy > 0:
                    participant.energy_supply[time_slot] = net_energy
                    participant.energy_demand[time_slot] = 0
                else:
                    participant.energy_demand[time_slot] = -net_energy
                    participant.energy_supply[time_slot] = 0

    # Collect orders from participants based on their strategy
    def collect_orders(self, strategy, time_slot):
        for participant in self.participants:
            bid_price, bid_quantity, ask_price, ask_quantity = strategy(participant, self.min_price, self.max_price, time_slot)
            if bid_quantity > 0:
                self.order_book.append((participant.id, 'bid', bid_price, bid_quantity, time_slot))
                print(f"Collected bid order from {participant.id}: {bid_quantity} kWh at {bid_price}€/kWh for time slot {time_slot}")
            if ask_quantity > 0:
                self.order_book.append((participant.id, 'ask', ask_price, ask_quantity, time_slot))
                print(f"Collected ask order from {participant.id}: {ask_quantity} kWh at {ask_price}€/kWh for time slot {time_slot}")


    # Create order book where bids are sorted in descending order and asks are sorted in ascending order
    def match_orders(self, time_slot):
        # Bids are sorted in descending order
        bids = sorted([order for order in self.order_book if order[1] == 'bid'], key=lambda x: -x[2])
        # Asks are sorted in ascending order
        asks = sorted([order for order in self.order_book if order[1] == 'ask'], key=lambda x: x[2])

        matches = []
        iterations = min(len(bids), len(asks))
        for i in range(iterations):
            bid = bids[i]
            ask = asks[i]
            if bid[2] >= ask[2]:
                quantity = min(bid[3], ask[3])
                match_price = (bid[2] + ask[2]) / 2
                matches.append((ask[0], bid[0], quantity, match_price))
                self.trade_history.append(match_price) # Add trade to trade history
                
                # Find participant and update demand/supply for current time slot
                for participant in self.participants:
                    if participant.id == bid[0]:
                        participant.energy_demand[time_slot] -= quantity
                        participant.cost += quantity * match_price
                    if participant.id == ask[0]:
                        participant.energy_supply[time_slot] -= quantity
                        participant.revenue += quantity * match_price
                
                # Update order book
                self.order_book.remove(bid)
                self.order_book.remove(ask)
                updated_bid_quantity = bid[3] - quantity
                updated_ask_quantity = ask[3] - quantity
                if updated_bid_quantity > 0:
                    self.order_book.append((bid[0], 'bid', bid[2], updated_bid_quantity, bid[4]))
                if updated_ask_quantity > 0:
                    self.order_book.append((ask[0], 'ask', ask[2], updated_ask_quantity, ask[4]))
        if len(matches) > 0:
            for match in matches:
                print(f"Matched order: {match[0]} sells {match[2]} kWh to {match[1]} at {match[3]}€/kWh")
        return matches
    

    # Clear unmatched orders with provider prices
    def clear_market(self):
        for order in self.order_book:
            participant = next(p for p in self.participants if p.id == order[0])
            if order[1] == 'bid':
                participant.cost += order[3] * self.max_price
                print(f"Unmatched bid for {participant.id} cleared with provider: {order[3]} kWh from {order[0]} at {self.max_price}€/kWh")
            else:
                participant.revenue += order[3] * self.min_price
                print(f"Unmatched ask for {participant.id} cleared with provider: {order[3]} kWh from {order[0]} at {self.min_price}€/kWh")
        self.order_book = []



# Zero-Intelligence Strategy where agents randomly choose a price and quantity
def zi_strategy(participant, min_price, max_price, time_slot):
    bid_price = ask_price = bid_quantity = ask_quantity = 0

    # Prosumers can only sell energy if they have excess energy
    if participant.pv and participant.energy_supply[time_slot] > 0:
        ask_price = np.random.uniform(min_price, max_price)
        ask_quantity = participant.energy_supply[time_slot]
    
    # All participants can buy energy
    if participant.energy_demand[time_slot] > 0:
        bid_price = np.random.uniform(min_price, max_price)
        bid_quantity = participant.energy_demand[time_slot]
    
    return bid_price, bid_quantity, ask_price, ask_quantity

# Eyes on the Best Strategy where agents set their prices based on the best bid and ask prices
# def eob_strategy(participant, best_bid_price, best_ask_price, min_price, max_price, time_remaining):
#     # Delta berechnen, abhängig von der verbleibenden Zeit
#     delta = (1 - (time_remaining ** 2)) * ((max_price - min_price) / 2)
#     if best_bid_price >= best_ask_price:
#         bid_price = best_bid_price - delta
#         ask_price = best_ask_price + delta
#     else:
#         bid_price = best_bid_price + delta
#         ask_price = best_ask_price - delta
#     bid_quantity = np.maximum(participant.energy_supply - participant.energy_demand, 0).sum()
#     ask_quantity = np.maximum(participant.energy_demand - participant.energy_supply, 0).sum()
#     return (bid_price, bid_quantity, ask_price, ask_quantity)
