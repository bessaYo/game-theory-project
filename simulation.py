from market import CDAMarket, Participant, zi_strategy
from loadProfiles import load_profiles, G1
import matplotlib.pyplot as plt
import random

# time slots per day a 15-minute intervals
time_slots = 96

# feed-in tariff in €/kWh
min_price = 0.37

# retail tariff in €/kWh
max_price = 0.5

# number of prosumers and consumers
num_prosumers = 8
num_consumers = 8

participants = []

# otc contracts
otc_contracts = [('C1', 'P1', 30, 0.45), ('C2', 'P2', 20, 0.4), ('C3', 'P3', 10, 0.35)]

# add particpants with load and pv profiles
for i in range(num_consumers):
    load_profile = random.choice(load_profiles)
    participants.append(Participant(id=f'C{i+1}', load_profile=load_profile, pv=False))

for i in range(num_prosumers):
    load_profile = random.choice(load_profiles)
    pv_profile = G1 
    participants.append(Participant(id=f'P{i+1}', load_profile=load_profile, pv=True, pv_profile=pv_profile))

# initialize market
market = CDAMarket(participants, otc_contracts, min_price, max_price)

# simulation
for time_slot in range(time_slots):
    if time_slot in range(40,50):
        print("--------------------------------------------------")
        print(f"Time Slot {time_slot + 1}/{time_slots}")
        # apply otc contracts and adjust prosumer supply once at the beginning of each time slot
        market.deduce_prosumer_supply(time_slot)
        market.apply_otc_contracts(time_slot)

        # try to match orders multiple times within the time slot
        for round in range(15): # in a 15-minute interval, one round per minute
            print(f"Round {round + 1} in Time Slot {time_slot + 1}")
            market.collect_orders(zi_strategy, time_slot)
            market.match_orders(time_slot)
            market.order_book = []
        
        # clear the market after all rounds are completed
        market.clear_market()


trade_history = market.trade_history 

x_values = [i * 5 for i in range(len(trade_history))]

plt.figure(figsize=(10, 5))
plt.plot(x_values, trade_history, '-o', label='Trade Prices', color='blue') 
plt.title('Trade Prices for Specific Time Slots')
plt.xlabel('Trade Number')
plt.ylabel('Price (€/kWh)')
plt.yticks([min_price, max_price], [f'Min Price: {min_price}€/kWh', f'Max Price: {max_price}€/kWh'])
plt.legend()
plt.grid(True)
plt.show()