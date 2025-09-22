import json
import os
import time
import random
import math
 


def create_simulated_swing_data(num_samples, total_duration_s):
    """
    Generates synthetic IMU data for a golf swing motion.
    The motion is divided into key phases: address, backswing, downswing, follow-through.


    Args:
        num_samples (int): The total number of data points to generate.
        total_duration_s (float): The total duration of the swing in seconds.


    Returns:
        tuple: (data, sim_meta). data is a list of dicts with sensor readings; sim_meta describes the chosen profile.
    """
    # Simulate a golf swing motion by defining key phases
    # Times are in seconds. Adjust these to change the swing characteristics.
    t_address = 0.5
    t_backswing_end = 2.0
    t_downswing_end = 2.5
    t_impact = 2.6
    t_finish = 4.0


    # Generate timestamps without NumPy (equivalent to np.linspace(0, total_duration_s, num_samples))
    if num_samples <= 1:
        time_stamps = [0.0]
    else:
        dt = total_duration_s / (num_samples - 1)
        time_stamps = [i * dt for i in range(num_samples)]
    data = []

    # Choose a swing quality profile to create variety
    profiles = ['good', 'okay', 'bad']
    profile = random.choices(profiles, weights=[0.4, 0.35, 0.25], k=1)[0]

    if profile == 'good':
        gyro_scale = random.uniform(1.15, 1.3)
        accel_scale = random.uniform(1.05, 1.15)
        noise_accel_range = 0.05
        noise_gyro_range = 0.03
        # Slight downward attack
        y_attack_bias = random.uniform(-0.8, -0.4)  # m/s^2 added during downswing
        # Modest club path bias (±2–4 deg approx.)
        path_bias = random.choice([-1, 1]) * random.uniform(0.5, 1.2)  # applied to accel_x mostly
        # Impact spike moderate/clean
        accel_spike_base = random.uniform(6.0, 8.0)
        gyro_spike_base = random.uniform(20.0, 24.0)
        # Launch slightly efficient
        launch_multiplier = random.uniform(1.0, 1.2)
    elif profile == 'okay':
        gyro_scale = random.uniform(1.0, 1.15)
        accel_scale = random.uniform(0.95, 1.05)
        noise_accel_range = 0.10
        noise_gyro_range = 0.05
        # Shallow or steep
        if random.random() < 0.5:
            y_attack_bias = random.uniform(-0.6, -0.2)
            launch_multiplier = random.uniform(1.2, 1.5)  # higher launch
        else:
            y_attack_bias = random.uniform(-1.8, -1.2)
            launch_multiplier = random.uniform(0.8, 1.0)  # slightly lower launch
        # Noticeable path (±5–7 deg approx.)
        path_bias = random.choice([-1, 1]) * random.uniform(1.5, 2.5)
        accel_spike_base = random.uniform(5.0, 7.0)
        gyro_spike_base = random.uniform(15.0, 22.0)
    else:  # bad
        gyro_scale = random.uniform(0.85, 1.0)
        accel_scale = random.uniform(0.85, 0.95)
        noise_accel_range = 0.20
        noise_gyro_range = 0.08
        # Topping (up) or fat (very down)
        if random.random() < 0.5:
            y_attack_bias = random.uniform(0.5, 1.5)   # slight up
            launch_multiplier = random.uniform(0.7, 0.9)  # low bullets
        else:
            y_attack_bias = random.uniform(-2.5, -3.5)  # steep down
            launch_multiplier = random.uniform(1.4, 1.8)  # sky-ball
        # Big path (±8–12 deg approx.)
        path_bias = random.choice([-1, 1]) * random.uniform(2.5, 4.0)
        # Impact spike unstable: very low or very high
        if random.random() < 0.5:
            accel_spike_base = random.uniform(3.0, 5.0)
            gyro_spike_base = random.uniform(10.0, 16.0)
        else:
            accel_spike_base = random.uniform(8.0, 12.0)
            gyro_spike_base = random.uniform(24.0, 32.0)

    sim_meta = {
        'profile': profile,
        'gyro_scale': round(gyro_scale, 3),
        'accel_scale': round(accel_scale, 3),
        'y_attack_bias': round(y_attack_bias, 3),
        'path_bias': round(path_bias, 3),
        'accel_spike_base': round(accel_spike_base, 3),
        'gyro_spike_base': round(gyro_spike_base, 3),
        'launch_multiplier': round(launch_multiplier, 3),
    }


    # Gyroscope and Accelerometer values for a simple golf swing model
    # These are simplified models using sine and ramp functions.
    for i, t in enumerate(time_stamps):
        # Simulate sensor drift (slow, linear increase)
        drift_x = t * 0.01
        drift_y = t * 0.02
        drift_z = t * 0.015
        
        # Simulate random noise (profile dependent)
        noise_accel = random.uniform(-noise_accel_range, noise_accel_range)
        noise_gyro = random.uniform(-noise_gyro_range, noise_gyro_range)

        # Impact spike: short Gaussian pulse centered at impact
        # Width ~ 0.01s (about 2-3 samples at current dt), small amplitude to create a noticeable but brief spike
        spike_sigma = 0.01
        # Slight randomization to make each swing unique
        accel_spike_amp = accel_spike_base * (1.0 + random.uniform(-0.1, 0.1))
        gyro_spike_amp = gyro_spike_base * (1.0 + random.uniform(-0.1, 0.1))
        impact_factor = math.exp(-((t - t_impact) ** 2) / (2.0 * spike_sigma ** 2))


        # Gyroscope data: Angular velocity during the swing
        if t_address < t < t_backswing_end:
            # Backswing
            gyro_x = (-15 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_x + noise_gyro
            gyro_y = (10 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_y + noise_gyro
            gyro_z = (20 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_z + noise_gyro
        elif t_backswing_end <= t < t_impact:
            # Downswing
            gyro_x = (30 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_x + noise_gyro
            gyro_y = (-40 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_y + noise_gyro
            gyro_z = (-50 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_z + noise_gyro
        elif t_impact <= t < t_finish:
            # Follow-through (motion slows down)
            gyro_x = (10 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_x + noise_gyro
            gyro_y = (15 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_y + noise_gyro
            gyro_z = (-10 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_z + noise_gyro
        else:
            # Address and Finish (static)
            gyro_x, gyro_y, gyro_z = drift_x + noise_gyro, drift_y + noise_gyro, drift_z + noise_gyro

        # Add gyro impact spike (primarily in z and x, slight in y)
        gyro_x += 0.3 * gyro_spike_amp * impact_factor + 0.05 * path_bias * impact_factor
        gyro_y += -0.2 * gyro_spike_amp * impact_factor
        gyro_z += 0.5 * gyro_spike_amp * impact_factor


        # Accelerometer data: Linear acceleration
        # We assume gravity is on the Y-axis for simplicity (-9.8 m/s^2)
        if t_address < t < t_backswing_end:
            accel_x = 5 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
            accel_y = -9.8 + 2 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
            accel_z = 3 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
        elif t_backswing_end <= t < t_impact:
            accel_x = 10 * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + noise_accel
            accel_y = -9.8 - 5 * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + noise_accel + y_attack_bias
            accel_z = -15 * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + noise_accel
        elif t_impact <= t < t_finish:
            accel_x = -5 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
            accel_y = -9.8 + 3 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
            accel_z = 5 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
        else:
            accel_x, accel_y, accel_z = noise_accel, -9.8 + noise_accel, noise_accel

        # Apply overall profile scales
        accel_x *= accel_scale
        accel_y *= accel_scale
        accel_z *= accel_scale

        # Apply club path bias mainly as lateral accel_x during downswing and a bit around impact
        if t_backswing_end <= t < t_finish:
            accel_x += path_bias * (0.6 if t < t_impact else 0.3)

        # Add accel impact spike (primarily in y, slight in x/z)
        accel_x += 0.4 * accel_spike_amp * impact_factor
        accel_y += 1.0 * accel_spike_amp * impact_factor * launch_multiplier
        accel_z += 0.3 * accel_spike_amp * impact_factor


        data.append({
            'timestamp': t,
            'accel_x': accel_x, 'accel_y': accel_y, 'accel_z': accel_z,
            'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z
        })


    # ---- Post-process scaling to hit a target club speed (kph) ----
    # Estimate speed from peak gyro magnitude with a simple mapping
    GYRO_TO_KPH = 1.5  # tuning constant mapping gyro peak to kph

    def est_kph(samples):
        peak = 0.0
        for s in samples:
            gmag = math.sqrt(s['gyro_x']**2 + s['gyro_y']**2 + s['gyro_z']**2)
            if gmag > peak:
                peak = gmag
        return peak * GYRO_TO_KPH

    before_kph = est_kph(data)
    # Target realistic 5-iron club speed ranges (mph -> kph)
    # Good: 75–85 mph (121–137 kph)
    # Okay: 72–82 mph (116–132 kph)
    # Bad: 65–80 mph (105–129 kph) – allow slightly wider variation
    if profile == 'good':
        target_kph = random.uniform(121.0, 137.0)
    elif profile == 'okay':
        target_kph = random.uniform(116.0, 132.0)
    else:
        target_kph = random.uniform(100.0, 128.0)
    scale = (target_kph / before_kph) if before_kph > 1e-6 else 1.0

    # Scale gyro strongly and accel proportionally, but keep gravity baseline (-9.8 in Y) unchanged
    for s in data:
        s['gyro_x'] *= scale
        s['gyro_y'] *= scale
        s['gyro_z'] *= scale
        # dynamic acceleration components
        ax_dyn = s['accel_x']
        ay_dyn = s['accel_y'] + 9.8  # remove gravity baseline
        az_dyn = s['accel_z']
        ax_dyn *= scale
        ay_dyn *= scale
        az_dyn *= scale
        s['accel_x'] = ax_dyn
        s['accel_y'] = -9.8 + ay_dyn
        s['accel_z'] = az_dyn

    after_kph = est_kph(data)

    sim_meta.update({
        'speed_target_kph': round(target_kph, 1),
        'speed_est_before_kph': round(before_kph, 1),
        'speed_est_after_kph': round(after_kph, 1),
        'gyro_to_kph': GYRO_TO_KPH,
        'scale_applied': round(scale, 3),
    })

    return data, sim_meta


def save_swing_to_json(filename, samples, metadata=None):
    """Appends a swing (samples + optional metadata) to a JSON file.

    File format: a JSON array of swing objects
    [{
        "metadata": {...},
        "samples": [ {timestamp, accel_x, ...}, ... ]
    }, ...]
    """
    swing_entry = {
        "metadata": metadata or {},
        "samples": samples,
    }

    # Load existing data if file exists and is valid
    existing = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                content = f.read().strip()
                if content:
                    loaded = json.loads(content)
                    if isinstance(loaded, list):
                        existing = loaded
        except Exception:
            # If file is corrupted or not a list, start fresh
            existing = []

    existing.append(swing_entry)

    # Write back pretty-printed for easier inspection
    with open(filename, 'w') as f:
        json.dump(existing, f, indent=2)


if __name__ == '__main__':
    print("Generating simulated golf swing data...")
    num_samples = 500
    total_duration_s = 5.0
    simulated_data, sim_meta = create_simulated_swing_data(num_samples=num_samples, total_duration_s=total_duration_s)
    output_file = 'simulated_sensor_data.json'
    metadata = {
        "generated_at": time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime()),
        "num_samples": num_samples,
        "total_duration_s": total_duration_s,
        "sim_profile": sim_meta,
    }
    save_swing_to_json(output_file, simulated_data, metadata)
    print(f"Simulation complete. Swing appended to {output_file}")
