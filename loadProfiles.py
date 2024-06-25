from scipy.interpolate import CubicSpline
import numpy as np


# Time windows
time_slots = 96  # 96 15-minute intervals per day
time = np.linspace(0, 24, time_slots + 1)[:-1]  # Creates 96 points over 24 hours

# Time points for the original data, 25 Werte von 0 bis 24 Stunden
time_points = np.linspace(0, 24, 25)

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

print(L1_1)