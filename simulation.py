# simulate.py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
from market import *


np.random.seed(0)

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

# function to determine weather each day
def weather(alpha_prev_day):
    alpha = abs(1 - abs(np.random.normal(loc = alpha_prev_day)))     # better for seed(0)
    #alpha = abs(np.random.normal(loc = old_alpha))     # better w/o seed
    return 1 if alpha > 1 else alpha

alpha = np.ones(days + 1)

# PV Generation Curve (adapted from Paper Source)
pv_profile = (1440 * np.exp(-((day_time - 12) ** 2) / 8)  + 5 * np.random.normal(size=day_time.size)) * (day_time > 6) * (day_time < 18) + 20 * np.random.normal(size=day_time.size) * (day_time > 9) * (day_time < 16)

# feed-in tariff in €/kWh in Germany 2024
min_price = 0.1327

# retail tariff in €/kWh in Germany 2024
max_price = 0.4175

# 18 participants with pv and 18 participants without pv
num_prosumers = 18
num_consumers = 18

participants = []
matches = [[],[]]
df = [[],[]]
strategies = np.array[[zi_strategy, eob_strategy], ['bat_CDA', 'CDA_bat']]

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
            
    participants.append(Participant(id=f'P{i+1}', profile=profile, pv=True, pv_profile=pv_profile, battery_capacity=5000))

def simulate_p2p_market(participants, strategy_func, min_price, max_price, day_slots):
    market = CDAMarket(participants, min_price, max_price)
    results = []
    for t in range(day_slots):
        time_remaining = (day_slots - t) / day_slots
        for p in participants:
            p.energy_demand[t] =- p.withdraw_battery(p.energy_demand[t])        # Ufuk: energy-array-elems sollten noch so verrechnet werden, dass aus W -> kWh wird
            if strategy_func[1] == 'bat_CDA':
                p.energy_storage =+ p.load_battery(p.pv_profile[t] - p.energy_demand[t])
        market.collect_orders(strategy_func[0], t, time_remaining)
        matches = market.match_orders()
        results.extend(matches)
        for p in participants:
            if strategy_func[1] == 'CDA_bat': p.energy_storage =+ p.load_battery(p.energy_supply[t] - p.energy_demand[t])               
        market.clear_market()
        return results

for trade_s in range(len(strategies[0])):
    for bat_s in range(len(strategies[1])):
        for d in range(1, days + 1):
            # determine weather for the day
            alpha[d] = weather(alpha[d-1])

            # pv-profile of prosumers depending on weather
            for p in participants:
                p.pv_profile = p.pv_profile * alpha[d]


            # simulation of all Strategy-Combinations
            matches[trade_s][bat_s] = simulate_p2p_market(participants, strategies[trade_s][bat_s], min_price, max_price)
            df[trade_s][bat_s] = pd.DataFrame(matches[trade_s][bat_s], columns=['Buyer', 'Seller', 'Quantity', 'Price'])      # create dataframes for visualization


# visualization         # Ufuk: verschieben in For-Loops oben
plt.figure(figsize=(14, 7))

plt.subplot(2, 2, 1)
plt.plot(zi_df.index, zi_df['Price'], label='ZI Trade Prices', alpha=0.6)
plt.xlabel('Trade Number')
plt.ylabel('Price')
plt.legend()
plt.title('Zero-Intelligence Strategy - Trade Prices')

plt.subplot(2, 2, 2)
plt.plot(eob_df.index, eob_df['Price'], label='EOB Trade Prices', alpha=0.6)
plt.xlabel('Trade Number')
plt.ylabel('Price')
plt.legend()
plt.title('Eyes on the Best Strategy - Trade Prices')

plt.tight_layout()
plt.show()
