import numpy as np

def calculate_average_price(trades):
    if not trades:
        return 0
    total_quantity = sum(trade['quantity'] for trade in trades)
    total_value = sum(trade['price'] * trade['quantity'] for trade in trades)
    return total_value / total_quantity if total_quantity > 0 else 0

def calculate_price_dispersion(trades, average_price):
    if not trades:
        return 0
    n = len(trades)
    variance = sum((trade['price'] - average_price) ** 2 for trade in trades) / n
    return np.sqrt(variance)

def calculate_payment_reduction(buyers_original, buyers_after):
    original_total = sum(buyers_original)
    after_total = sum(buyers_after)
    return ((original_total - after_total) / original_total) * 100 if original_total > 0 else 0

def calculate_income_increase(sellers_original, sellers_after):
    original_total = sum(sellers_original)
    after_total = sum(sellers_after)
    return ((after_total - original_total) / original_total) * 100 if original_total > 0 else 0

def calculate_community_welfare(buyers_original, sellers_original, buyers_after, sellers_after):
    original_net = sum(buyers_original) - sum(sellers_original)
    after_net = sum(buyers_after) - sum(sellers_after)
    return ((original_net - after_net) / original_net) * 100 if original_net != 0 else 0
