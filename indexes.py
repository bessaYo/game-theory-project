import numpy as np

# calculate the average price of trades
def calculate_average_price(trades):
    if not trades:
        return 0
    total_quantity = sum(trade[2] for trade in trades)
    total_value = sum(trade[2] * trade[3] for trade in trades)
    return total_value / total_quantity if total_quantity > 0 else 0

# calculate the standard deviation of trade prices from their average
def calculate_price_dispersion(trades, average_price):
    if not trades:
        return 0
    n = len(trades)
    variance = sum((trade[3] - average_price) ** 2 for trade in trades) / n
    return np.sqrt(variance)

# calculate the reduction in payment due to trading at market prices compared to the fallback buying price
def calculate_payment_reduction(trades, traditional_buyers, provider_buy):
    original_total = traditional_buyers
    after_total = sum(trade[2] * trade[3] for trade in trades) + provider_buy
    return ((original_total - after_total) / original_total) * 100 if original_total > 0 else 0

# calculate the increase in income due to trading at market prices compared to the fallback selling price
def calculate_income_increase(trades, traditional_sellers, provider_sell):
    original_total = traditional_sellers
    after_total = sum(trade[2] * trade[3] for trade in trades) + provider_sell
    return ((after_total - original_total) / original_total) * 100 if original_total > 0 else 0

# calculate the overall community welfare change considering both matched and unmatched trades
def calculate_community_welfare(trades, traditional_sellers, traditional_buyers, provider_buy, provider_sell):
    buyers_original = traditional_buyers
    buyers_after = sum(trade[2] * trade[3] for trade in trades) + provider_buy

    sellers_original = traditional_sellers
    sellers_after = sum(trade[2] * trade[3] for trade in trades) + provider_sell

    original_net = buyers_original - sellers_original
    after_net = buyers_after - sellers_after
    if original_net != 0:
        return abs(((original_net - after_net) / original_net)) * 100
    else:
        return 0

