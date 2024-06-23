import numpy as np
import matplotlib.pyplot as plt

# Time windows
time_slots = 288  # 288 5 minutes intervalls per day
time_points = np.linspace(0, 24, time_slots)


def create_load_profile(base_load, morning_peak, evening_peak, time_points):
    morning_profile = base_load + morning_peak * np.exp(-0.5 * ((time_points - 7) / 1.5)**2)
    evening_profile = base_load + evening_peak * np.exp(-0.5 * ((time_points - 18) / 2.0)**2)
    daily_profile = morning_profile + evening_profile - base_load
    return daily_profile

# Peaks
base_load_L1 = 0.3
morning_peak_L1 = 0.5
evening_peak_L1 = 0.7

base_load_L2 = 0.2
morning_peak_L2 = 0.4
evening_peak_L2 = 0.6

# Basic profiles
base_profile_L1 = create_load_profile(base_load_L1, morning_peak_L1, evening_peak_L1, time_points)
base_profile_L2 = create_load_profile(base_load_L2, morning_peak_L2, evening_peak_L2, time_points)

# Deviations
deviation_25_L1 = base_profile_L1 * 1.25
deviation_50_L1 = base_profile_L1 * 1.50

deviation_25_L2 = base_profile_L2 * 1.25
deviation_50_L2 = base_profile_L2 * 1.50

# Load profiles dictionary
load_profiles = {
    'L1-1': base_profile_L1,
    'L1-2': deviation_25_L1,
    'L1-3': deviation_50_L1,
    'L2-1': base_profile_L2,
    'L2-2': deviation_25_L2,
    'L2-3': deviation_50_L2
}

# PV-Profile
def create_pv_profile(time_points):
    morning_profile = 0.5 * np.exp(-0.5 * ((time_points - 9) / 2.0)**2)
    afternoon_profile = 1.5 * np.exp(-0.5 * ((time_points - 12) / 1.5)**2)
    daily_profile = np.clip(morning_profile + afternoon_profile, 0, None)
    return daily_profile

pv_profile = create_pv_profile(time_points)

# Visualization of Load and PV Profiles
# plt.figure(figsize=(14, 7))
# for key, profile in load_profiles.items():
#     plt.plot(time_points, profile, label=key)
# plt.plot(time_points, pv_profile, label='PV Profile', linestyle='--', color='black')
# plt.xlabel('Time of Day (hours)')
# plt.ylabel('Load / Generation (kW)')
# plt.legend()
# plt.title('Load and PV Profiles')
# plt.show()
