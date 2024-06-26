import numpy as np
from scipy.interpolate import CubicSpline
import matplotlib.pyplot as plt


# Time windows
time_slots = 96  # 96 15-minute intervals per day
time = np.linspace(0, 24, time_slots + 1)[:-1]  # Creates 96 points over 24 hours
days = 14
alpha = np.ones(days + 1)

# Time points for the original data, 25 Werte von 0 bis 24 Stunden
time_points = np.arange(25)

# Load values from your example
L1_values = np.array([500, 425, 375, 350, 350, 350, 375, 500, 600, 575, 525, 500, 515, 515, 515, 550, 600, 700, 915, 1010, 975, 915, 850, 675, 475])
L2_values = np.array([400, 350, 350, 325, 300, 300, 325, 400, 475, 550, 625, 675, 725, 760, 740, 685, 650, 700, 825, 850, 850, 800, 740, 575, 400])

# Create cubic splines
cs_L1 = CubicSpline(time_points, L1_values)
cs_L2 = CubicSpline(time_points, L2_values)

# Evaluate the cubic splines at the time array
L1_profile = cs_L1(time)
L2_profile = cs_L2(time)

# Deviation profiles
L1_1, L1_2, L1_3 = L1_profile, L1_profile * 1.25, L1_profile * 1.5
L2_1, L2_2, L2_3 = L2_profile, L2_profile * 1.25, L2_profile * 1.5

L1_1 = np.round(L1_1, 3)
L1_2 = np.round(L1_2, 3)
L1_3 = np.round(L1_3, 3)
L2_1 = np.round(L2_1, 3)
L2_2 = np.round(L2_2, 3)
L2_3 = np.round(L2_3, 3)

# Store load profiles in a list
load_profiles = [L1_1, L1_2, L1_3, L2_1, L2_2, L2_3]

# PV Generation Curve G1
scale_factor = 3333.333333333
time_peak = 12
width = 8

G1 = scale_factor * np.exp(-((time - time_peak) ** 2) / width)
G1 += 5 * np.random.normal(size=time.size) * ((time > 6) & (time < 18))
G1 += 20 * np.random.normal(size=time.size) * ((time > 9) & (time < 16))

G1 = np.round(G1, 3)

# function to determine weather each day
def weather(alpha_prev_day):
    #alpha = abs(1 - abs(np.random.normal(loc = alpha_prev_day)))     # better for seed(0)
    alpha = abs(np.random.normal(loc = alpha_prev_day))     # better w/o seed
    return 1 if alpha > 1 else alpha

# Plot
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(time, L1_1, label='L1-1', color='red')
ax1.plot(time, L1_2, label='L1-2', linestyle='--', color='red')
ax1.plot(time, L1_3, label='L1-3', linestyle=':', color='red')
ax1.plot(time, L2_1, label='L2-1', color='blue')
ax1.plot(time, L2_2, label='L2-2', linestyle='--', color='blue')
ax1.plot(time, L2_3, label='L2-3', linestyle=':', color='blue')

ax1.set_xlabel('Time (h)')
ax1.set_ylabel('Load powers (W)')
ax1.set_ylim(0, 1600)

# Zweite Y-Achse für G1
ax2 = ax1.twinx()
ax2.plot(time, G1, label='G1', color='orange')
ax2.set_ylabel('PV power (W)')
ax2.set_ylim(0, 4000)

# Legende für beide Y-Achsen
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='best')

plt.title('One-day load consumption and PV generation profiles')
plt.grid()
plt.show()


# Umwandeln in kWh pro 15-Minuten-Intervall
def power_to_kwh(power_profile):
    # Jedes Intervall ist 15 Minuten lang, was 0,25 Stunden entspricht
    return np.round(power_profile * 0.25 / 1000, 3)

# Berechnung der kWh für jedes Profil
load_profiles = [power_to_kwh(profile) for profile in load_profiles]
G1 = power_to_kwh(G1)

# Ausgabe der kWh-Profile
for i, profile in enumerate(load_profiles, 1):
    print(f"L{i}-1 kWh: {profile}")

print(f"G1 kWh: {G1}")