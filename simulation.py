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
strategies = [zi_strategy, eob_strategy]
battery_option = ['CDA_bat', 'bat_CDA', 'no_bat']
trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(10))
#trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(2)] for _ in range(10))
#trades, average_price, price_dispersion, payment_reduction, income_increase, welfare = ([[] for _ in range(4)] for _ in range(6))

# add participants to the market with load profiles and prosumers additionally with pv profiles
def initialize_participants():      
    participants = []
    for i in range(num_consumers):
        m = i % 6
        profile = load_profiles[m]
        participants.append(Participant(id=f'C{i+1}', load_profile=profile))

    for i in range(num_prosumers):
        m = i % 6
        profile = load_profiles[m]      
        participants.append(Participant(id=f'P{i+1}', load_profile=profile, pv=True, pv_profile=G1, battery_capacity=5))
    return participants

def run_simulation(strategy, battery):
    trade_history = []
    provider_buy, provider_sell = 0, 0
    traditional_buyers, traditional_sellers = 0, 0
    printer = False        # false if no debugging needed
    if printer:
        print("-" * 50)
        print(f"Processing simulation with strategies {strategy.__name__} and " + battery)
        print("-" * 50)

    market = CDAMarket(initialize_participants(), otc_contracts, min_price, max_price)

    for time_slot in range(time_slots):

        if printer: print(f"Processing time slot {time_slot}...")
        market.balance_prosumer_energy(time_slot)
        market.traditional_prices(time_slot)
        if battery == 'CDA_bat' or battery == 'bat_CDA':
            market.manage_battery_storage(time_slot, battery, printer)
        market.apply_otc_contracts(time_slot)
        
        for round in range(15):  # 15 rounds per 15-minute time slot
            if printer: print(f"Processing round {round}...")
            market.collect_orders(strategy, time_slot, round, 15, printer)
            trades = market.match_orders(time_slot, printer)
            if printer:   
               for participant in market.participants:
                   print(f"Participant {participant.id}: Demand={participant.energy_demand[time_slot]}, Supply={participant.energy_supply[time_slot]}, Revenue={participant.revenue}, Cost={participant.cost}")
            trade_history.extend(trades)

        market.clear_market(battery, printer)
    
    # Update variables for metrics
    traditional_buyers += market.traditional_buyers
    traditional_sellers += market.traditional_sellers
    provider_buy += market.provider_buy
    provider_sell += market.provider_sell

    return trade_history, provider_buy, provider_sell, traditional_buyers, traditional_sellers


results = [] 

for strategy in strategies:
    for battery in battery_option:
        print(f"Running simulation for {strategy.__name__} with {battery} strategy")
        trades, provider_buy, provider_sell, traditional_buyers, traditional_sellers = run_simulation(strategy, battery)

        # Metrics
        average_price = calculate_average_price(trades)
        price_dispersion = calculate_price_dispersion(trades, average_price)
        payment_reduction = calculate_payment_reduction(trades, traditional_buyers, provider_buy)
        income_increase = calculate_income_increase(trades, traditional_sellers, provider_sell)
        community_welfare = calculate_community_welfare(trades, traditional_sellers, traditional_buyers, provider_buy, provider_sell)

        # Store results
        results.append({
            "strategy": strategy.__name__,
            "battery": battery,
            "average_price": np.round(average_price, 4),
            "price_dispersion": np.round(price_dispersion, 4),
            "payment_reduction": np.round(payment_reduction, 4),
            "income_increase": np.round(income_increase, 4),
            "community_welfare": np.round(community_welfare, 4)
        })

print("\nSimulation Results Summary:")
for result in results:
    print(f"Index for {result['strategy']} + {result['battery']}:")
    print(f"Average price: {result['average_price']}")
    print(f"Price dispersion: {result['price_dispersion']}")
    print(f"Payment reduction: {result['payment_reduction']}%")
    print(f"Income increase: {result['income_increase']}%")
    print(f"Community welfare: {result['community_welfare']}%")
    print("-" * 50) 

strategies_labels = [f"{result['strategy']} + {result['battery']}" for result in results]
price_dispersions = [result['price_dispersion'] for result in results]
payment_reductions = [result['payment_reduction'] for result in results]
income_increases = [result['income_increase'] for result in results]
community_welfares = [result['community_welfare'] for result in results]

bar_width = 0.5

# Plot für Preisdispersion
plt.figure(figsize=(10, 6))
plt.bar(strategies_labels, price_dispersions, color='navy', width=bar_width)
plt.xlabel('Strategy and Battery Configuration')
plt.ylabel('Price Dispersion (€/kWh)')
plt.title('Price Dispersion by Strategy and Battery Configuration')
plt.xticks(rotation=60)
plt.tight_layout()
plt.show()

# Plot für Zahlungsreduktion
plt.figure(figsize=(10, 6))
plt.bar(strategies_labels, payment_reductions, color='navy', width=bar_width)
plt.xlabel('Strategy and Battery Configuration')
plt.ylabel('Payment Reduction (%)')
plt.title('Payment Reduction by Strategy and Battery Configuration')
plt.xticks(rotation=60)
plt.tight_layout()
plt.show()

# Plot für Einkommenssteigerung mit unterschiedlichen Farben für positive und negative Werte
colors = ['green' if x >= 0 else 'red' for x in income_increases]
plt.figure(figsize=(10, 6))
plt.bar(strategies_labels, income_increases, color=colors, width=bar_width)
plt.xlabel('Strategy and Battery Configuration')
plt.ylabel('Income Increase (%)')
plt.title('Income Increase by Strategy and Battery Configuration')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Plot für Gemeinwohlwerte
plt.figure(figsize=(12, 6))
plt.bar(strategies_labels, community_welfares, color='navy', width=bar_width)
plt.xlabel('Strategy and Battery Configuration')
plt.ylabel('Community Welfare (%)')
plt.title('Community Welfare by Strategy and Battery Configuration')
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
