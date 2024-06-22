# simulate.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from market import CDAMarket, Participant, zi_strategy, eob_strategy


np.random.seed(0)

# time arrays and scalars
day_slots = 96
day_time = np.linspace(0, 24, day_slots*5)
days = 14

# Estimated Values for L1 and L2 (acc. to source-paper)
time_points = np.arange(25)
L1_values = np.array([500, 425, 375, 350, 350, 350, 375, 500, 600, 575, 525, 500, 515, 515, 515, 550, 600, 700, 915, 1010, 975, 915, 850, 675, 475])
L2_values = np.array([400, 350, 350, 325, 300, 300, 325, 400, 475, 550, 625, 675, 725, 760, 740, 685, 650, 700, 825, 850, 850, 800, 740, 575, 400])

# Smoothed Values
cs_L1 = CubicSpline(time_points, L1_values)
cs_L2 = CubicSpline(time_points, L2_values)
L1 = cs_L1(day_time)
L2 = cs_L2(day_time)

load_profiles = {
    # Load Profiles L1
    'L1_1' : L1,
    'L1_2' : L1 * 1.25,
    'L1_3' : L1 * 1.5,

    # Load Profiles L2
    'L2_1' : L2,
    'L2_2' : L2 * 1.25,
    'L2_3' : L2 * 1.5
}

# PV Generation Curve (adapted from Paper Source)
pv_profile = (1440 * np.exp(-((day_time - 12) ** 2) / 8)  + 5 * np.random.normal(size=day_time.size)) * (day_time > 6) * (day_time < 18) + 20 * np.random.normal(size=day_time.size) * (day_time > 9) * (day_time < 16)

# feed-in tariff in CNY/kWh
min_price = 0.1327

# retail tariff in CNY/kWh
max_price = 0.4175

# 18 participants with pv and 18 participants without pv
num_prosumers = 18
num_consumers = 18

participants = []

# add participants to the market with load profiles and pv profiles
for i in range(num_consumers):
    m = i & 6
    match m:
        case 0:
            profile = load_profiles['L1-1']
        case 1:
            profile = load_profiles['L1-2']
        case 2:
            profile = load_profiles['L1-3']
        case 3:
            profile = load_profiles['L2-1']
        case 4:
            profile = load_profiles['L2-2']
        case 5:
            profile = load_profiles['L2-3']

    participants.append(Participant(id=f'C{i+1}', profile=profile))

for i in range(num_prosumers):
    m = i & 6
    match m:
        case 0:
            profile = load_profiles['L1-1']
        case 1:
            profile = load_profiles['L1-2']
        case 2:
            profile = load_profiles['L1-3']
        case 3:
            profile = load_profiles['L2-1']
        case 4:
            profile = load_profiles['L2-2']
        case 5:
            profile = load_profiles['L2-3']
            
    participants.append(Participant(id=f'P{i+1}', profile=profile, pv=True, pv_profile=pv_profile))

def simulate_cda_market(participants, strategy_func, min_price, max_price, days, day_slots):
    market = CDAMarket(participants, min_price, max_price)
    results = []
    for t in range(day_slots):
        time_remaining = (day_slots - t) / day_slots
        market.collect_orders(strategy_func, t, time_remaining)
        matches = market.match_orders()
        results.extend(matches)
        market.clear_market()
    return results

# simulation with Zero-Intelligence Strategy
zi_matches = simulate_cda_market(participants, zi_strategy, min_price, max_price, day_slots)

# simulation with Eyes on the Best Strategy
eob_matches = simulate_cda_market(participants, eob_strategy, min_price, max_price, day_slots)

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
