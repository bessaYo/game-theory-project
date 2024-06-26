import matplotlib.pyplot as plt
from market import CDAMarket, Participant, zi_strategy, eob_strategy
from loadProfiles import *
from indexes import calculate_average_price, calculate_price_dispersion, calculate_payment_reduction, calculate_income_increase, calculate_community_welfare

# configuration
min_price = 0.1327      # feed-in tariff in €/kWh in Germany 2024
max_price = 0.4175      # retail tariff in €/kWh in Germany 2024
num_prosumers = 18
num_consumers = 18
otc_contracts = [('C1', 'P1', 30, 0.1), ('C2', 'P2', 20, 0.2), ('C3', 'P3', 10, 0.3)]
strategies = [[zi_strategy, eob_strategy], ['bat_CDA', 'CDA_bat']]
#trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(10))
trades, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(6))

# add participants to the market with load profiles and prosumers additionally with pv profiles
def initialize_participants(weather=1):      
    participants = []
    for i in range(num_consumers):
        m = i % 6
        profile = load_profiles[m]
        participants.append(Participant(id=f'C{i+1}', load_profile=profile))

    for i in range(num_prosumers):
        m = i % 6
        profile = load_profiles[m]      
        participants.append(Participant(id=f'P{i+1}', load_profile=profile, pv=True, pv_profile=G1 * weather, battery_capacity=5))
    return participants

def run_simulation(strategy):
    trade_history = []
    provider_buy, provider_sell = 0, 0
    traditional_buyers, traditional_sellers = 0, 0
 
    for d in range(1, days + 1):
        alpha[d] = weather(alpha[d-1])
        market = CDAMarket(initialize_participants(alpha[d]), otc_contracts, min_price, max_price)

        for time_slot in range(time_slots):
            print("-" * 50)
            print(f"Processing time slot {time_slot}...")
            market.deduce_prosumer_supply(time_slot, strategy[1])
            x, y = market.traditional_prices(time_slot)
            traditional_buyers += x
            traditional_sellers += y
            market.apply_otc_contracts(time_slot)
            
            for round in range(15):  # 15 rounds per 15-minute time slot
                print(f"Processing round {round}...")
                market.collect_orders(strategy[0], time_slot, round, 15)
                trades = market.match_orders(time_slot)
                # for participant in market.participants:
                #     print(f"Participant {participant.id}: Demand={participant.energy_demand[time_slot]}, Supply={participant.energy_supply[time_slot]}, Revenue={participant.revenue}, Cost={participant.cost}")
                trade_history.extend(trades)

            market.clear_market(strategy[1])
            provider_buy += market.provider_buy
            provider_sell += market.provider_sell

    return trade_history, provider_buy, provider_sell, traditional_buyers, traditional_sellers

# run simulation with ZI and EOB strategies and battery strategies
for trade_s in range(len(strategies[0])):
    for bat_s in range(len(strategies[1])):
        strategy = (strategies[0][trade_s], strategies[1][bat_s])  # trading and battery storage strategies for this round
        #trades[2*trade_s + bat_s], provider_buy[2*trade_s + bat_s], provider_sell[2*trade_s + bat_s], traditional_buyers[2*trade_s + bat_s], traditional_sellers[2*trade_s + bat_s] = run_simulation(strategy)
        trades[2*trade_s + bat_s], provider_buy, provider_sell, traditional_buyers, traditional_sellers = run_simulation(strategy)


for i in range(len(trades)):

    match i:
        case 0: string = "ZI strategy + Battery before CDA"
        case 1: string = "ZI strategy + Battery after CDA"
        case 2: string = "EoB strategy + Battery before CDA"
        case 3: string = "EoB strategy + Battery after CDA"

    # average price
    average_price[i] = calculate_average_price(trades[i])
    print("Average price for " + string + f": {average_price[i]}")

    # price dispersion
    price_dispersion[i] = calculate_price_dispersion(trades[i], average_price[i])
    print("Price dispersion for " + string + f": {price_dispersion[i]}")

    # payment reduction
    payment_reduction[i] = calculate_payment_reduction(trades[i], traditional_buyers, provider_buy)
    print("Payment reduction for " + string + f": {payment_reduction[i]}")

    # income increase
    income_increase[i] = calculate_income_increase(trades[i], traditional_sellers, provider_sell)
    print("Income increase for " + string + f": {income_increase[i]}")

    # community welfare
    welfare[i] = calculate_community_welfare(trades[i], traditional_sellers, traditional_buyers, provider_buy, provider_sell)
    print("Community welfare for " + string + f": {welfare[i]}")
