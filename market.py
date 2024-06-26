import numpy as np

class Participant:
    def __init__(self, id, load_profile, pv=False, pv_profile=None, battery_capacity=0):
        self.id = id
        self.pv = pv
        self.energy_demand = np.round(load_profile.copy(), 3)
        self.energy_supply = np.round(pv_profile.copy(), 3) if pv else np.zeros_like(load_profile)
        self.cost = 0
        self.revenue = 0
        self.__energy_storage = 0
        self.battery_capacity = battery_capacity

    def load_battery(self, load):
        new_storage = self.__energy_storage + load
        remaining = max(new_storage - self.battery_capacity, 0)
        self.__energy_storage = min(new_storage, self.battery_capacity)       # load battery and
        return remaining                                                    # ... output remaining energy (that couldn't be stored)
    
    def withdraw_battery(self, demand):
        withdraw = min(demand, self.__energy_storage)                         
        self.__energy_storage -= withdraw                                     # withdraw stored energy from battery and
        return withdraw
    
    def get_storage(self):          # Method to get private attribute energy_storage
        return self.__energy_storage

class CDAMarket:
    def __init__(self, participants, otc_contracts, min_price, max_price):
        self.participants = participants
        self.otc_contracts = otc_contracts
        self.min_price = min_price
        self.max_price = max_price
        self.order_book = []
        self.previous_order_book = []
        self.trade_history = []
        self.provider_sell = 0
        self.provider_buy = 0
        self.traditional_buyers = 0
        self.traditional_sellers = 0

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

    # Prosumers consume their energy first
    def balance_prosumer_energy(self, time_slot):
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
   
    def manage_battery_storage(self, time_slot, bat_strategy, printer):
            for participant in self.participants:
                if participant.pv:
                    net_energy = participant.energy_supply[time_slot] - participant.energy_demand[time_slot]

                    if bat_strategy == 'bat_CDA' and net_energy > 0:
                        excess_energy = participant.load_battery(net_energy)
                        participant.energy_supply[time_slot] = excess_energy
                        if printer: print(f"Participant {participant.id} - Excess energy after loading battery: {excess_energy} kWh")
                    elif net_energy < 0:
                        needed_energy = - net_energy
                        withdrawn_energy = participant.withdraw_battery(needed_energy)
                        participant.energy_demand[time_slot] -= withdrawn_energy
                        if printer: print(f"Participant {participant.id} - Additional energy needed after battery withdrawal: {needed_energy} kWh")

    # Collect orders from participants based on their strategy
    def collect_orders(self, strategy, time_slot, current_round, total_rounds, printer):
        self.previous_order_book = self.order_book.copy()
        self.order_book = []
        for participant in self.participants:
            current_bids = [order for order in self.previous_order_book if order[1] == 'bid']
            current_asks = [order for order in self.previous_order_book if order[1] == 'ask']
            bid_price, bid_quantity, ask_price, ask_quantity = strategy(
                participant, self.min_price, self.max_price, time_slot, current_bids, current_asks, current_round, total_rounds)
            if bid_quantity > 0:
                self.order_book.append((participant.id, 'bid', bid_price, bid_quantity, time_slot))
                if printer: print(f"{participant.id} places bid for {bid_quantity} kWh at {bid_price}€/kWh")
            if ask_quantity > 0:
                self.order_book.append((participant.id, 'ask', ask_price, ask_quantity, time_slot))
                if printer: print(f"{participant.id} places ask for {ask_quantity} kWh at {ask_price}€/kWh")


    # Match orders based on the current order book
    def match_orders(self, time_slot, printer):
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
        if printer:
            if len(matches) > 0:
                for match in matches:
                    print(f"Matched order: {match[0]} sells {match[2]} kWh to {match[1]} at {match[3]}€/ with total cost {match[2] * match[3]}€")
            else:
                print("No matches found for this round.")
        return matches
    

    # Clear unmatched orders with provider prices
    def clear_market(self, bat_strategy, printer):
        for order in self.order_book:
            participant = next(p for p in self.participants if p.id == order[0])
            if order[1] == 'bid':
                cost =  order[3] * self.max_price
                participant.cost += cost
                self.provider_buy += cost
                if printer: print(f"Unmatched bid for {participant.id} cleared with provider: {order[3]} kWh for {order[0]} at {self.max_price}€/kWh with total cost {cost}€")
            else:
                remaining_quantity = order[3]
                if bat_strategy == 'CDA_bat':
                    remaining_quantity = participant.load_battery(order[3])
                #remaining_quantity = participant.load_battery(order[3])
                if remaining_quantity > 0:
                    revenue = remaining_quantity * self.min_price
                    participant.revenue += revenue
                    self.provider_sell += revenue
                    if printer: print(f"Unmatched ask for {participant.id} cleared with provider: {remaining_quantity} kWh from {order[0]} at {self.min_price}€/kWh with total revenue {revenue}€")
        self.order_book = []
    
    def traditional_prices(self, time_slot):
        for participant in self.participants:
            net_energy = participant.energy_supply[time_slot] - participant.energy_demand[time_slot]

            if net_energy > 0:
                self.traditional_sellers += net_energy * self.min_price
            else:
                self.traditional_buyers += abs(net_energy) * self.max_price



# Zero-Intelligence Strategy where agents randomly choose a price and quantity
def zi_strategy(participant, min_price, max_price, time_slot, current_bids, current_asks, current_round, total_rounds):
    bid_price = ask_price = bid_quantity = ask_quantity = 0

    # Prosumers can only sell energy if they have excess energy
    #if participant.pv:
    #    total_supply = participant.energy_supply[time_slot] + participant.withdraw_battery(participant.energy_storage)
    #    if total_supply > 0:
    #        ask_price = np.random.uniform(min_price, max_price)
    #        ask_quantity = total_supply

    if participant.pv and participant.energy_supply[time_slot] > 0:
        ask_price = np.random.uniform(min_price, max_price)
        ask_quantity = participant.energy_supply[time_slot]
    
    # All participants can buy energy
    if participant.energy_demand[time_slot] > 0:
        bid_price = np.random.uniform(min_price, max_price)
        bid_quantity = participant.energy_demand[time_slot]
    
    return bid_price, bid_quantity, ask_price, ask_quantity

# EOB Strategy where agents choose a price based on the current market state
def eob_strategy(participant, min_price, max_price, time_slot, current_bids, current_asks, current_round, total_rounds):
    bid_price = ask_price = bid_quantity = ask_quantity = 0
    
    remaining_time_factor = (total_rounds - current_round) / total_rounds
    delta = remaining_time_factor * (max_price - min_price) / 100 
    if current_bids and current_asks:
        max_bid = max(bid[2] for bid in current_bids)
        min_ask = min(ask[2] for ask in current_asks)

        if max_bid >= min_ask:
            bid_price = max(min_price, max_bid - delta)
            ask_price = min(max_price, min_ask + delta)
        else:
            bid_price = min(max_price, max_bid + delta)
            ask_price = max(min_price, min_ask - delta)
    else:
        bid_price = np.random.uniform(min_price, max_price - delta)
        ask_price = np.random.uniform(min_price + delta, max_price)

    if participant.energy_demand[time_slot] > 0:
        bid_quantity = participant.energy_demand[time_slot]
    else:
        bid_price = 0

    # Prosumers can only sell energy if they have excess energy
    #if participant.pv:
    #    total_supply = participant.energy_supply[time_slot] + participant.withdraw_battery(participant.energy_storage)
    #    if total_supply > 0: ask_quantity = total_supply
    #    else: ask_price = 0
    #else: ask_price = 0

    if participant.pv and participant.energy_supply[time_slot] > 0:
        ask_quantity = participant.energy_supply[time_slot]
    else:
        ask_price = 0

    return bid_price, bid_quantity, ask_price, ask_quantity