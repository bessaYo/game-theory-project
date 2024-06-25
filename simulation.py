import matplotlib.pyplot as plt
from market import CDAMarket, Participant, zi_strategy, eob_strategy
from loadProfiles import load_profiles, G1
from indexes import calculate_average_price, calculate_price_dispersion, calculate_payment_reduction, calculate_income_increase, calculate_community_welfare
import random

# configuration
time_slots = 96
min_price = 0.37
max_price = 0.5
num_prosumers = 18
num_consumers = 18
otc_contracts = [('C1', 'P1', 30, 0.45), ('C2', 'P2', 20, 0.4), ('C3', 'P3', 10, 0.35)]


def initialize_participants():
    participants = []
    for i in range(num_consumers):
        load_profile = random.choice(load_profiles)
        participants.append(Participant(id=f'C{i+1}', load_profile=load_profile, pv=False))
    for i in range(num_prosumers):
        load_profile = random.choice(load_profiles)
        pv_profile = G1 
        participants.append(Participant(id=f'P{i+1}', load_profile=load_profile, pv=True, pv_profile=pv_profile))
    return participants

def run_simulation(strategy):
    market = CDAMarket(initialize_participants(), otc_contracts, min_price, max_price)
    trade_history = []
    provider_buy, provider_sell = 0, 0
    traditional_buyers, traditional_sellers = 0, 0
 
    for time_slot in range(time_slots):
        if time_slot in [38]:  # Simulating only for one time slot
            
            print("-" * 50)
            print(f"Processing time slot {time_slot}...")
            market.deduce_prosumer_supply(time_slot)
            x, y = market.traditional_prices(time_slot)
            traditional_buyers += x
            traditional_sellers += y
            market.apply_otc_contracts(time_slot)
            
            for round in range(15):  # 15 rounds per 15-minute time slot
                print(f"Processing round {round}...")
                market.collect_orders(strategy, time_slot, round, 15)
                trades = market.match_orders(time_slot)
                # for participant in market.participants:
                #     print(f"Participant {participant.id}: Demand={participant.energy_demand[time_slot]}, Supply={participant.energy_supply[time_slot]}, Revenue={participant.revenue}, Cost={participant.cost}")
                trade_history.extend(trades)

            market.clear_market()
            provider_buy += market.provider_buy
            provider_sell += market.provider_sell

    return trade_history, provider_buy, provider_sell, traditional_buyers, traditional_sellers

# run simulation with ZI and EOB strategies
zi_c_trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers = run_simulation(zi_strategy)
eob_c_trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers = run_simulation(eob_strategy)

# # average price
average_price_zi = calculate_average_price(zi_c_trades)
average_price_eob = calculate_average_price(eob_c_trades)
print(f"Average price for ZI strategy: {average_price_zi}")
print(f"Average price for EOB strategy: {average_price_eob}")


# # price dispersion
price_dispersion_zi = calculate_price_dispersion(zi_c_trades, average_price_zi)
price_dispersion_eob = calculate_price_dispersion(eob_c_trades, average_price_eob)
print(f"Price dispersion for ZI strategy: {price_dispersion_zi}")
print(f"Price dispersion for EOB strategy: {price_dispersion_eob}")

# # payment reduction
payment_reduction_zi = calculate_payment_reduction(zi_c_trades, traditional_buyers, provider_buy)
payment_reduction_eob = calculate_payment_reduction(eob_c_trades, traditional_buyers, provider_buy)
print(f"Payment reduction for ZI strategy: {payment_reduction_zi}")
print(f"Payment reduction for EOB strategy: {payment_reduction_eob}")

# # income increase
income_increase_zi = calculate_income_increase(zi_c_trades, traditional_sellers, provider_sell)
income_increase_eob = calculate_income_increase(eob_c_trades, traditional_sellers, provider_sell)
print(f"Income increase for ZI strategy: {income_increase_zi}")
print(f"Income increase for EOB strategy: {income_increase_eob}")

# # community welfare
welfare_zi = calculate_community_welfare(zi_c_trades, traditional_sellers, traditional_buyers, provider_buy, provider_sell)
welfare_eob = calculate_community_welfare(eob_c_trades, traditional_sellers, traditional_buyers, provider_buy, provider_sell)
print(f"Community welfare for ZI strategy: {welfare_zi}")
print(f"Community welfare for EOB strategy: {welfare_eob}")