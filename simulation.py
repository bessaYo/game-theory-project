# simulate.py
import numpy as np
import random
import pandas as pd
import matplotlib.pyplot as plt
from market import CDAMarket, Participant, zi_strategy, eob_strategy
from loadProfiles import load_profiles, pv_profile

print(f"Load profiles {load_profiles}")

print(f"PV profiles {pv_profile}")

np.random.seed(0)

# time slots per day
time_slots = 96  

# labels of load profiles
profiles = ['L1-1', 'L1-2', 'L1-3', 'L2-1', 'L2-2', 'L2-3']

# feed-in tariff in CNY/kWh
min_price = 0.37

# retail tariff in CNY/kWh
max_price = 0.5


# 18 participants with pv and 18 participants without pv
num_prosumers = 18
num_consumers = 18

participants = []

# add participants to the market with load profiles and pv profiles
for i in range(num_consumers):
    profile = random.choice(profiles)
    load_profile = load_profiles[profile]
    participants.append(Participant(id=f'C{i+1}', profile=load_profile))

for i in range(num_prosumers):
    profile = random.choice(profiles)
    load_profile = load_profiles[profile]
    participants.append(Participant(id=f'P{i+1}', profile=load_profile, pv=True, pv_profile=pv_profile))

for participant in participants:
    print(f'{participant.id} - Load: {participant.energy_demand}, Supply: {participant.energy_supply}')

def simulate_cda_market(participants, strategy_func, min_price, max_price, time_slots):
    market = CDAMarket(participants, min_price, max_price)
    results = []
    for t in range(time_slots):
        time_remaining = (time_slots - t) / time_slots
        market.collect_orders(strategy_func, t, time_remaining)
        matches = market.match_orders()
        results.extend(matches)
        market.clear_market()
    return results

# simulation with Zero-Intelligence Strategy
zi_matches = simulate_cda_market(participants, zi_strategy, min_price, max_price, time_slots)

# simulation with Eyes on the Best Strategy
eob_matches = simulate_cda_market(participants, eob_strategy, min_price, max_price, time_slots)

# create dataframes for visualization
zi_df = pd.DataFrame(zi_matches, columns=['Buyer', 'Seller', 'Quantity', 'Price'])
eob_df = pd.DataFrame(eob_matches, columns=['Buyer', 'Seller', 'Quantity', 'Price'])

#visualization
plt.figure(figsize=(14, 7))

plt.subplot(2, 1, 1)
plt.plot(zi_df.index, zi_df['Price'], label='ZI Trade Prices', alpha=0.6)
plt.xlabel('Trade Number')
plt.ylabel('Price')
plt.legend()
plt.title('Zero-Intelligence Strategy - Trade Prices')

plt.subplot(2, 1, 2)
plt.plot(eob_df.index, eob_df['Price'], label='EOB Trade Prices', alpha=0.6)
plt.xlabel('Trade Number')
plt.ylabel('Price')
plt.legend()
plt.title('Eyes on the Best Strategy - Trade Prices')

plt.tight_layout()
plt.show()
