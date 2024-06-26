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
#strategies = [zi_strategy, eob_strategy]
trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(10))
#trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(2)] for _ in range(10))
#trades, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(6))

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
    print_sim = True        # false if no debugging needed
    if print_sim:
        print("-" * 50)
        print(f"Processing simulation with strategies {strategy[0].__name__} and " + strategy[1])

    for d in range(1, days + 1):
        alpha[d] = weather(alpha[d-1])
        market = CDAMarket(initialize_participants(alpha[d]), otc_contracts, min_price, max_price)
        print_day = True if print_sim and (d == 2 or d == 7 or d == 14) else False
        if print_day: print(f"Processing day {d} with weather {alpha[d]}...")

        for time_slot in range(time_slots):
            print_slot = True if print_day and (time_slot == 30 or time_slot == 48) else False
            if print_slot: print(f"Processing time slot {time_slot}...")
            market.deduce_prosumer_supply(time_slot, strategy[1])
            #market.deduce_prosumer_supply(time_slot,'')
            x, y = market.traditional_prices(time_slot)
            traditional_buyers += x
            traditional_sellers += y
            market.apply_otc_contracts(time_slot)
            
            for round in range(15):  # 15 rounds per 15-minute time slot
                printer = True if print_slot and (round == 1 or round == 8) else False
                if printer: print(f"Processing round {round}...")
                #market.collect_orders(strategy[0], time_slot, round, 15)
                market.collect_orders(strategy[0], time_slot, round, 15, printer)
                trades = market.match_orders(time_slot, printer)
                #if printer:   
                #    for participant in market.participants:
                #        print(f"Participant {participant.id}: Demand={participant.energy_demand[time_slot]}, Supply={participant.energy_supply[time_slot]}, Revenue={participant.revenue}, Cost={participant.cost}")
                trade_history.extend(trades)

            #market.clear_market(strategy[1])
            market.clear_market(strategy[1], printer)
            provider_buy += market.provider_buy
            provider_sell += market.provider_sell

    return trade_history, provider_buy, provider_sell, traditional_buyers, traditional_sellers

# run simulation with ZI and EOB strategies and battery strategies
for trade_s in range(len(strategies[0])):
    for bat_s in range(len(strategies[1])):
        strategy = (strategies[0][trade_s], strategies[1][bat_s])  # trading and battery storage strategies for this round
        trades[2*trade_s + bat_s], provider_buy[2*trade_s + bat_s], provider_sell[2*trade_s + bat_s], traditional_buyers[2*trade_s + bat_s], traditional_sellers[2*trade_s + bat_s] = run_simulation(strategy)
        #trades[2*trade_s + bat_s], provider_buy, provider_sell, traditional_buyers, traditional_sellers = run_simulation(strategy)

#for trade_s in range(len(strategies)):
#    trades[trade_s], provider_buy[trade_s], provider_sell[trade_s], traditional_buyers[trade_s], traditional_sellers[trade_s] = run_simulation(strategies[trade_s])


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
    payment_reduction[i] = calculate_payment_reduction(trades[i], traditional_buyers[i], provider_buy[i])
    print("Payment reduction for " + string + f": {payment_reduction[i]}")

    # income increase
    income_increase[i] = calculate_income_increase(trades[i], traditional_sellers[i], provider_sell[i])
    print("Income increase for " + string + f": {income_increase[i]}")

    # community welfare
    welfare[i] = calculate_community_welfare(trades[i], traditional_sellers[i], traditional_buyers[i], provider_buy[i], provider_sell[i])
    print("Community welfare for " + string + f": {welfare[i]}")
