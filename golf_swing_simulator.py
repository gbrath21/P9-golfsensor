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
        y_attack_bias = random.uniform(-0.8, -0.4)
        path_bias = random.choice([-1, 1]) * random.uniform(0.5, 1.2)
        accel_spike_base = random.uniform(6.0, 8.0)
        gyro_spike_base = random.uniform(20.0, 24.0)
        launch_multiplier = random.uniform(1.0, 1.2)
    elif profile == 'okay':
        gyro_scale = random.uniform(1.0, 1.15)
        accel_scale = random.uniform(0.95, 1.05)
        noise_accel_range = 0.10
        noise_gyro_range = 0.05
        if random.random() < 0.5:
            y_attack_bias = random.uniform(-0.6, -0.2)
            launch_multiplier = random.uniform(1.2, 1.5)
        else:
            y_attack_bias = random.uniform(-1.8, -1.2)
            launch_multiplier = random.uniform(0.8, 1.0)
        path_bias = random.choice([-1, 1]) * random.uniform(1.5, 2.5)
        accel_spike_base = random.uniform(5.0, 7.0)
        gyro_spike_base = random.uniform(15.0, 22.0)
    else:  # bad
        gyro_scale = random.uniform(0.85, 1.0)
        accel_scale = random.uniform(0.85, 0.95)
        noise_accel_range = 0.20
        noise_gyro_range = 0.08
        if random.random() < 0.5:
            y_attack_bias = random.uniform(0.5, 1.5)
            launch_multiplier = random.uniform(0.7, 0.9)
        else:
            y_attack_bias = random.uniform(-2.5, -3.5)
            launch_multiplier = random.uniform(1.4, 1.8)
        path_bias = random.choice([-1, 1]) * random.uniform(2.5, 4.0)
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

    for i, t in enumerate(time_stamps):
        drift_x = t * 0.01
        drift_y = t * 0.02
        drift_z = t * 0.015
        
        noise_accel = random.uniform(-noise_accel_range, noise_accel_range)
        noise_gyro = random.uniform(-noise_gyro_range, noise_gyro_range)

        spike_sigma = 0.01
        accel_spike_amp = accel_spike_base * (1.0 + random.uniform(-0.1, 0.1))
        gyro_spike_amp = gyro_spike_base * (1.0 + random.uniform(-0.1, 0.1))
        impact_factor = math.exp(-((t - t_impact) ** 2) / (2.0 * spike_sigma ** 2))

        accel_factor = 0.0
        # Gyroscope data
        if t_address < t < t_backswing_end:
            gyro_x = (-15 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_x + noise_gyro
            gyro_y = (10 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_y + noise_gyro
            gyro_z = (20 * gyro_scale) * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + drift_z + noise_gyro
        elif t_backswing_end <= t < t_impact:
            gyro_x = (30 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_x + noise_gyro
            gyro_y = (-40 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_y + noise_gyro
            gyro_z = (-50 * gyro_scale) * math.sin((t - t_backswing_end) * math.pi / (t_downswing_end - t_backswing_end)) + drift_z + noise_gyro
        elif t_impact <= t < t_finish:
            gyro_x = (10 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_x + noise_gyro
            gyro_y = (15 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_y + noise_gyro
            gyro_z = (-10 * gyro_scale) * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + drift_z + noise_gyro
        else:
            gyro_x, gyro_y, gyro_z = drift_x + noise_gyro, drift_y + noise_gyro, drift_z + noise_gyro

        gyro_x += 0.3 * gyro_spike_amp * impact_factor + 0.05 * path_bias * impact_factor
        gyro_y += -0.2 * gyro_spike_amp * impact_factor
        gyro_z += 0.5 * gyro_spike_amp * impact_factor

        # Accelerometer data
        if t_address < t < t_backswing_end:
            accel_x = 5 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
            accel_y = -9.8 + 2 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
            accel_z = 3 * math.sin((t - t_address) * math.pi / (t_backswing_end - t_address)) + noise_accel
        elif t_backswing_end <= t < t_impact:
            # Downswing: build a vector whose mean dynamic Y component aligns with y_attack_bias.
            progress = (t - t_backswing_end) / (t_downswing_end - t_backswing_end)
            accel_factor = math.sin(progress * math.pi / 2)

            # Forward acceleration dominates the horizontal magnitude; lateral component follows path bias.
            forward_peak = 14.0
            lateral_peak = 0.25 * path_bias
            base_forward = -forward_peak * accel_factor
            base_lateral = lateral_peak * accel_factor

            horizontal_mag = math.sqrt(base_forward * base_forward + base_lateral * base_lateral)
            attack_slope = math.tan(math.radians(y_attack_bias))
            vertical_dynamic = horizontal_mag * attack_slope

            accel_x = base_lateral + noise_accel
            accel_y = -9.8 + vertical_dynamic + noise_accel
            accel_z = base_forward + noise_accel
        elif t_impact <= t < t_finish:
            accel_x = -5 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
            accel_y = -9.8 + 3 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
            accel_z = 5 * math.sin((t - t_impact) * math.pi / (t_finish - t_impact)) + noise_accel
        else:
            accel_x, accel_y, accel_z = noise_accel, -9.8 + noise_accel, noise_accel

        accel_x *= accel_scale
        accel_y *= accel_scale
        accel_z *= accel_scale

        if t_backswing_end <= t < t_finish:
            if t < t_impact:
                phase_scale = 0.18 + 0.22 * accel_factor
            else:
                phase_scale = 0.12
            accel_x += path_bias * phase_scale

        accel_x += 0.4 * accel_spike_amp * impact_factor
        accel_y += 1.0 * accel_spike_amp * impact_factor * launch_multiplier
        accel_z += 0.3 * accel_spike_amp * impact_factor

        data.append({
            'timestamp': t,
            'accel_x': accel_x, 'accel_y': accel_y, 'accel_z': accel_z,
            'gyro_x': gyro_x, 'gyro_y': gyro_y, 'gyro_z': gyro_z
        })

    GYRO_TO_KPH = 1.5

    def est_kph(samples):
        peak = 0.0
        for s in samples:
            gmag = math.sqrt(s['gyro_x']**2 + s['gyro_y']**2 + s['gyro_z']**2)
            if gmag > peak:
                peak = gmag
        return peak * GYRO_TO_KPH

    before_kph = est_kph(data)
    if profile == 'good':
        target_kph = random.uniform(121.0, 137.0)
    elif profile == 'okay':
        target_kph = random.uniform(116.0, 132.0)
    else:
        target_kph = random.uniform(100.0, 128.0)
    scale = (target_kph / before_kph) if before_kph > 1e-6 else 1.0

    for s in data:
        s['gyro_x'] *= scale
        s['gyro_y'] *= scale
        s['gyro_z'] *= scale
        ax_dyn = s['accel_x']
        ay_dyn = s['accel_y'] + 9.8
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
    swing_entry = {
        "metadata": metadata or {},
        "samples": samples,
    }
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
            existing = []
    existing.append(swing_entry)
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