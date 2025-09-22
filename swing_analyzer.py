import json
import math
import os
import sys
from typing import List, Dict, Tuple

"""
Pure-Python swing analyzer that reads the latest swing from simulated_sensor_data.json
and computes approximate metrics: Club Speed, Launch Angle, Attack Angle, Club Path, Spin Rate (approx.).

Assumptions/Notes:
- Gravity is assumed along negative Y (-9.8 m/s^2) in the global frame.
- Orientation/sensor fusion is NOT implemented; accelerations are treated in a simplified manner.
- Integration is naive (no drift correction), suitable only for demonstration with synthetic data.
- Input file format (created by golf_swing_simulator.py):
  [ { "metadata": {...}, "samples": [ {timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z}, ... ] }, ...]
- Output: prints metrics and writes latest_swing_stats.json for app consumption.
"""


def load_latest_swing(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Expected a non-empty JSON array of swings")
    swing = data[-1]
    samples = swing.get('samples', [])
    if not samples:
        raise ValueError("Latest swing contains no samples")
    return samples


def load_all_swings(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list) or len(data) == 0:
        raise ValueError("Expected a non-empty JSON array of swings")
    return data


def estimate_dt(samples: List[Dict]) -> float:
    # Use timestamps if available; fall back to average spacing
    times = [s.get('timestamp', None) for s in samples]
    times = [t for t in times if isinstance(t, (int, float))]
    if len(times) >= 2:
        # average delta
        diffs = [t2 - t1 for t1, t2 in zip(times[:-1], times[1:])]
        # guard against zeros
        diffs = [d for d in diffs if d > 0]
        if diffs:
            return sum(diffs) / len(diffs)
    # default to 1/100 s if unknown
    return 0.01


def find_impact_index(samples: List[Dict]) -> int:
    # Peak gyroscope magnitude heuristic
    max_mag = -1.0
    idx = 0
    for i, s in enumerate(samples):
        gx, gy, gz = s['gyro_x'], s['gyro_y'], s['gyro_z']
        mag = math.sqrt(gx*gx + gy*gy + gz*gz)
        if mag > max_mag:
            max_mag = mag
            idx = i
    return idx


def integrate_velocity(samples: List[Dict], dt: float) -> List[Tuple[float, float, float]]:
    """Legacy full-trace integration (kept for reference)."""
    v = [(0.0, 0.0, 0.0)] * len(samples)
    vx, vy, vz = 0.0, 0.0, 0.0
    for i in range(1, len(samples)):
        ax = samples[i]['accel_x']
        ay = samples[i]['accel_y']
        az = samples[i]['accel_z']
        eff_ax, eff_ay, eff_az = ax, ay + 9.8, az
        vx += eff_ax * dt
        vy += eff_ay * dt
        vz += eff_az * dt
        v[i] = (vx, vy, vz)
    return v


def integrate_velocity_preimpact(samples: List[Dict], impact_idx: int, dt: float, pre_window_s: float = 0.06) -> Tuple[float, float, float]:
    """
    Integrate velocity over a short window that ENDS just BEFORE impact.
    We exclude the impact sample to avoid the large upward spike in accel_y
    that represents ball launch. Gravity is removed and the window is
    detrended to limit drift.
    """
    n = len(samples)
    win_len = max(1, int(pre_window_s / max(dt, 1e-6)))
    start = max(0, impact_idx - win_len)
    end = max(0, impact_idx - 1)  # strictly pre-impact

    if end < start:
        return (0.0, 0.0, 0.0)

    # Baseline-subtracted integration: remove the first sample value in the window
    ax0 = samples[start]['accel_x']
    ay0 = samples[start]['accel_y'] + 9.8
    az0 = samples[start]['accel_z']

    vx = vy = vz = 0.0
    for i in range(start, end + 1):
        eff_ax = samples[i]['accel_x'] - ax0
        eff_ay = (samples[i]['accel_y'] + 9.8) - ay0
        eff_az = samples[i]['accel_z'] - az0
        vx += eff_ax * dt
        vy += eff_ay * dt
        vz += eff_az * dt

    return (vx, vy, vz)


def calculate_club_speed_from_gyro_global(samples: List[Dict]) -> float:
    """
    Estimate clubhead speed from global PEAK gyro magnitude (matches simulator targeting).
    Returns speed in m/s.
    """
    omega = 0.0
    for i in range(len(samples)):
        gx, gy, gz = samples[i].get('gyro_x', 0.0), samples[i].get('gyro_y', 0.0), samples[i].get('gyro_z', 0.0)
        m = math.sqrt(gx*gx + gy*gy + gz*gz)
        if m > omega:
            omega = m
    # Calibration: same mapping used by simulator targeting (GYRO_TO_KPH=1.5)
    kph = 1.5 * omega
    return kph / 3.6


def calculate_attack_angle(velocity_at_impact: Tuple[float, float, float]) -> float:
    vx, vy, vz = velocity_at_impact
    horiz = math.sqrt(vx*vx + vz*vz)
    if horiz == 0:
        return 90.0 if vy > 0 else -90.0
    return math.degrees(math.atan2(vy, horiz))


def estimate_angles_from_preimpact_accel(samples: List[Dict], impact_idx: int, dt: float, pre_window_s: float = 0.06) -> Tuple[float, float]:
    """
    Estimate attack angle and club path using the MEAN dynamic acceleration
    vector in a short window BEFORE impact. This is more stable with our
    synthetic data than integrating velocity.

    - Remove gravity from Y using (ay + 9.8)
    - Exclude the final 2 samples before impact to avoid the rising impact spike
    - Attack = atan2(mean_ay, sqrt(mean_ax^2 + mean_az^2))
    - Path   = atan2(mean_ax, -mean_az)    # forward ~ -Z in simulator
    """
    n = len(samples)
    win_len = max(3, int(pre_window_s / max(dt, 1e-6)))
    end = max(0, impact_idx - 2)
    start = max(0, end - win_len + 1)

    if end < start:
        return 0.0, 0.0

    ax_sum = ay_sum = az_sum = 0.0
    count = 0
    for i in range(start, end + 1):
        ax_sum += samples[i]['accel_x']
        ay_sum += samples[i]['accel_y'] + 9.8
        az_sum += samples[i]['accel_z']
        count += 1

    if count == 0:
        return 0.0, 0.0

    mean_ax = ax_sum / count
    mean_ay = ay_sum / count
    mean_az = az_sum / count

    horiz = math.sqrt(mean_ax * mean_ax + mean_az * mean_az)
    attack_deg = math.degrees(math.atan2(mean_ay, max(horiz, 1e-6)))
    path_deg = math.degrees(math.atan2(mean_ax, -mean_az))
    return attack_deg, path_deg

def calculate_club_path_from_velocity(v_imp: Tuple[float, float, float]) -> float:
    """
    Club path = heading angle of the horizontal velocity vector at impact.
    Angle is measured in the X-Z plane relative to +Z (target line),
    positive when moving to the golfer's right (+X) i.e., in-to-out for RH.
    """
    vx, _, vz = v_imp
    # Forward axis in simulator downswing is along -Z (accel_z is largely negative),
    # so measure heading relative to +forward = -vz
    return math.degrees(math.atan2(vx, -vz))


def approximate_launch_and_spin(club_speed_mps: float, attack_angle_deg: float) -> Tuple[float, float]:
    # Very rough demo model (not physically accurate)
    launch_angle = 10.0 + 0.4 * attack_angle_deg + 0.05 * club_speed_mps
    spin_rpm = 2500.0 + 40.0 * attack_angle_deg + 8.0 * club_speed_mps
    return launch_angle, spin_rpm


def analyze(samples: List[Dict], club_length_m: float) -> Dict:
    dt = estimate_dt(samples)
    impact_idx = find_impact_index(samples)
    # Angles from pre-impact mean acceleration (robust to spikes)
    attack_angle_deg, club_path_deg = estimate_angles_from_preimpact_accel(samples, impact_idx, dt, pre_window_s=0.06)
    # Speed from global peak gyro magnitude (calibrated to simulator)
    club_speed_mps = calculate_club_speed_from_gyro_global(samples)
    launch_angle_deg, spin_rpm = approximate_launch_and_spin(club_speed_mps, attack_angle_deg)

    return {
        "clubSpeed_mps": round(club_speed_mps, 2),
        "clubSpeed_mph": round(club_speed_mps * 2.23694, 1),
        "clubSpeed_kph": round(club_speed_mps * 3.6, 1),
        "attackAngle_deg": round(attack_angle_deg, 1),
        "clubPath_deg": round(club_path_deg, 1),
        "launchAngle_deg": round(launch_angle_deg, 1),
        "spinRate_rpm": int(round(spin_rpm)),
        "impactIndex": impact_idx,
    }


# -----------------------------
# Swing segmentation utilities
# -----------------------------

def compute_gyro_mag(samples: List[Dict]) -> List[float]:
    mags = []
    for s in samples:
        gx, gy, gz = s.get('gyro_x', 0.0), s.get('gyro_y', 0.0), s.get('gyro_z', 0.0)
        mags.append(math.sqrt(gx*gx + gy*gy + gz*gz))
    return mags


def segment_swings(
    samples: List[Dict],
    dt: float,
    start_threshold: float = 25.0,
    end_threshold: float = 10.0,
    min_swing_duration_s: float = 0.3,
    min_gap_s: float = 0.2,
) -> List[List[Dict]]:
    """
    Segment continuous IMU samples into individual swings using gyro magnitude hysteresis.

    - start when gyro |w| exceeds start_threshold
    - end when it falls below end_threshold and stays low for min_gap_s
    - discard segments shorter than min_swing_duration_s
    """
    mags = compute_gyro_mag(samples)
    min_len = max(1, int(min_swing_duration_s / max(dt, 1e-6)))
    gap_len = max(1, int(min_gap_s / max(dt, 1e-6)))

    swings = []
    in_swing = False
    start_idx = 0
    below_end_count = 0

    for i, m in enumerate(mags):
        if not in_swing:
            if m >= start_threshold:
                in_swing = True
                start_idx = i
                below_end_count = 0
        else:
            if m < end_threshold:
                below_end_count += 1
                if below_end_count >= gap_len:
                    end_idx = max(start_idx, i - gap_len + 1)
                    segment = samples[start_idx:end_idx+1]
                    if len(segment) >= min_len:
                        swings.append(segment)
                    in_swing = False
                    below_end_count = 0
            else:
                below_end_count = 0

    # Close trailing swing if ends near file end
    if in_swing:
        segment = samples[start_idx:]
        if len(segment) >= min_len:
            swings.append(segment)

    return swings


def load_flat_samples(path: str) -> List[Dict]:
    with open(path, 'r') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError('Expected a JSON array of sample objects')
    return data


def write_swings(path: str, swings: List[List[Dict]]):
    out = []
    for seg in swings:
        out.append({
            "metadata": {
                "num_samples": len(seg),
                "generated_by": "segmenter",
            },
            "samples": seg,
        })
    with open(path, 'w') as f:
        json.dump(out, f, indent=2)


def run_once() -> Dict:
    # Defaults from your request: height 185 cm, weight 80 kg, 5-iron length ~38 inches (0.9652 m)
    height_cm = 185
    weight_kg = 80
    club_length_m = 0.9652

    src = os.path.join(os.path.dirname(__file__), 'simulated_sensor_data.json')
    samples = load_latest_swing(src)
    metrics = analyze(samples, club_length_m)

    payload = {
        "updatedAt": __import__('time').strftime('%Y-%m-%dT%H:%M:%S%z', __import__('time').localtime()),
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "club_length_m": club_length_m,
        **metrics,
    }

    # Save for the app to consume later if desired
    out_path = os.path.join(os.path.dirname(__file__), 'latest_swing_stats.json')
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)

    return payload


def serve(host: str = '127.0.0.1', port: int = 5001):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def _set_headers(self, status=200):
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_GET(self):
            if self.path == '/metrics':
                try:
                    payload = run_once()
                    self._set_headers(200)
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                except Exception as e:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            elif self.path == '/all-metrics':
                try:
                    src = os.path.join(os.path.dirname(__file__), 'simulated_sensor_data.json')
                    swings = load_all_swings(src)
                    out = []
                    for idx, swing in enumerate(swings):
                        samples = swing.get('samples', [])
                        metrics = analyze(samples, 0.9652)
                        out.append({
                            "index": idx,
                            "metadata": swing.get('metadata', {}),
                            **metrics,
                        })
                    self._set_headers(200)
                    self.wfile.write(json.dumps(out).encode('utf-8'))
                except Exception as e:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Not found"}).encode('utf-8'))

    httpd = HTTPServer((host, port), Handler)
    print(f"Swing Analyzer server running at http://{host}:{port} (GET /metrics)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def main():
    args = sys.argv[1:]
    if args and args[0] == '--serve':
        serve()
        return

    if args and args[0] == '--segment':
        if len(args) < 3:
            print('Usage: swing_analyzer.py --segment <input_flat.json> <output_swings.json>')
            sys.exit(1)
        inp, outp = args[1], args[2]
        samples = load_flat_samples(inp)
        dt = estimate_dt(samples)
        swings = segment_swings(samples, dt)
        write_swings(outp, swings)
        print(f'Segmented {len(swings)} swing(s) to {outp}')
        return

    payload = run_once()
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
