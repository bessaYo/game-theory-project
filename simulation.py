# simulate.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from market import CDAMarket, Participant, zi_strategy, eob_strategy


np.random.seed(0)

# example for load profiles and pv profiles
time_slots = 96  
load_profiles = {
    'L1-1': np.random.uniform(0.2, 1.0, time_slots),
    'L2-1': np.random.uniform(0.1, 0.9, time_slots)
}
pv_profile = np.random.uniform(0.5, 1.5, time_slots)



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
    profile = load_profiles['L1-1'] if i < num_consumers // 2 else load_profiles['L2-1']
    participants.append(Participant(id=f'C{i+1}', profile=profile))

for i in range(num_prosumers):
    profile = load_profiles['L1-1'] if i < num_prosumers // 2 else load_profiles['L2-1']
    participants.append(Participant(id=f'P{i+1}', profile=profile, pv=True, pv_profile=pv_profile))

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

# visualization
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
