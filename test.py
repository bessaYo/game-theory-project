import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline

# Zeitachse von 0 bis 24 Stunden in Schritten von 0.1 Stunden
time_slots = 96
time = np.linspace(0, 24, time_slots*5)

# Geschätzte Werte für L1-1 und L2-1
time_points = np.arange(25)
L1_1_values = np.array([500, 425, 375, 350, 350, 350, 375, 500, 600, 575, 525, 500, 515, 515, 515, 550, 600, 700, 915, 1010, 975, 915, 850, 675, 475])
L2_1_values = np.array([400, 350, 350, 325, 300, 300, 325, 400, 475, 550, 625, 675, 725, 760, 740, 685, 650, 700, 825, 850, 850, 800, 740, 575, 400])


# Geglättete Werte
cs_L1_1 = CubicSpline(time_points, L1_1_values)
cs_L2_1 = CubicSpline(time_points, L2_1_values)

# Verbrauchskurven L1
L1_1 = cs_L1_1(time)
L1_2 = L1_1 * 1.25
L1_3 = L1_1 * 1.5

# Verbrauchskurven L2
L2_1 = cs_L2_1(time)
L2_2 = L2_1 * 1.25
L2_3 = L2_1 * 1.5

# PV-Erzeugungskurve
G1 = (1440 * np.exp(-((time - 12) ** 2) / 8)  + 5 * np.random.normal(size=time.size)) * (time > 6) * (time < 18) + 20 * np.random.normal(size=time.size) * (time > 9) * (time < 16)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(time, L1_1, label='L1-1')
plt.plot(time, L1_2, label='L1-2', linestyle='--')
plt.plot(time, L1_3, label='L1-3', linestyle=':')
plt.plot(time, L2_1, label='L2-1')
plt.plot(time, L2_2, label='L2-2', linestyle='--')
plt.plot(time, L2_3, label='L2-3', linestyle=':')
plt.plot(time, G1, label='G1', color='orange')

plt.xlabel('Time (h)')
plt.ylabel('Load power (W)')
plt.ylim(0, 1600)
plt.twinx()
plt.ylabel('PV power (W)')
plt.ylim(0, 4000)
plt.legend(loc='best')
plt.title('One-day load consumption and PV generation profiles')
plt.grid()
plt.show()
