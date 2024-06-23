import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# time arrays and scalars
time_slots = 96
time = np.linspace(0, 24, time_slots*5)

# Estimated Values for L1 and L2 (acc. to source-paper)
time_points = np.arange(25)
L1_values = np.array([500, 425, 375, 350, 350, 350, 375, 500, 600, 575, 525, 500, 515, 515, 515, 550, 600, 700, 915, 1010, 975, 915, 850, 675, 475])
L2_values = np.array([400, 350, 350, 325, 300, 300, 325, 400, 475, 550, 625, 675, 725, 760, 740, 685, 650, 700, 825, 850, 850, 800, 740, 575, 400])

# Smoothed Values
cs_L1 = CubicSpline(time_points, L1_values)
cs_L2 = CubicSpline(time_points, L2_values)

# Load Profiles L1
L1_1 = cs_L1(time)
L1_2 = L1_1 * 1.25
L1_3 = L1_1 * 1.5

# Load Profiles L2
L2_1 = cs_L2(time)
L2_2 = L2_1 * 1.25
L2_3 = L2_1 * 1.5

# PV Generation Curve (adapted from Paper Source)
G1 = (3333.333333333 * np.exp(-((time - 12) ** 2) / 8)  + 5 * np.random.normal(size=time.size)) * (time > 6) * (time < 18) + 20 * np.random.normal(size=time.size) * (time > 9) * (time < 16)


# Plot
fig, ax1 = plt.subplots(figsize=(10, 6))

ax1.plot(time, L1_1, label='L1-1', color='red')
ax1.plot(time, L1_2, label='L1-2', linestyle='--', color='red')
ax1.plot(time, L1_3, label='L1-3', linestyle=':', color='red')
ax1.plot(time, L2_1, label='L2-1', color='blue')
ax1.plot(time, L2_2, label='L2-2', linestyle='--', color='blue')
ax1.plot(time, L2_3, label='L2-3', linestyle=':', color='blue')

ax1.set_xlabel('Time (h)')
ax1.set_ylabel('Load power (W)')
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