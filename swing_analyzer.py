import json
import math
import os
import sys
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs

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


# -----------------------------
# Tempo-first utilities
# -----------------------------

def _magnitude3(x: float, y: float, z: float) -> float:
    return math.sqrt(x * x + y * y + z * z)


def smooth_ema(values: List[float], alpha: float = 0.2) -> List[float]:
    """Simple exponential moving average (no external deps)."""
    if not values:
        return []
    out = [values[0]]
    for v in values[1:]:
        out.append(alpha * v + (1 - alpha) * out[-1])
    return out


def detect_start(gyro_mag: List[float], hz: float, threshold_deg_s: float = 45.0, min_ms: int = 100) -> int:
    """First index where gyro magnitude stays above threshold for min_ms."""
    if not gyro_mag:
        return 0
    min_len = max(1, int((min_ms / 1000.0) * hz))
    above = [g > threshold_deg_s for g in gyro_mag]
    run = 0
    for i, ok in enumerate(above):
        run = run + 1 if ok else 0
        if run >= min_len:
            return i - min_len + 1
    # fallback: peak location
    return max(range(len(gyro_mag)), key=lambda i: gyro_mag[i])


def detect_top(gyro_axis: List[float], start_idx: int) -> int:
    """Detect the top as first zero-crossing after start (sign flip)."""
    if not gyro_axis:
        return 0
    s = max(0, start_idx)
    prev = gyro_axis[s] if s < len(gyro_axis) else 0.0
    for i in range(s + 1, len(gyro_axis)):
        cur = gyro_axis[i]
        if prev == 0:
            prev = cur
            continue
        if (prev > 0 and cur <= 0) or (prev < 0 and cur >= 0):
            return i
        prev = cur
    # fallback: global min after start (change of direction likely)
    tail = gyro_axis[s:]
    return s + (min(range(len(tail)), key=lambda i: tail[i]))


def detect_impact(accel_mag: List[float], hz: float, threshold_g: float = 10.0, refractory_ms: int = 25, start_from: int = 0) -> int:
    """Detect first large spike in acceleration magnitude after top."""
    if not accel_mag:
        return 0
    thr = threshold_g * 9.81
    i0 = max(0, start_from)
    refractory = max(1, int((refractory_ms / 1000.0) * hz))
    i = i0
    while i < len(accel_mag):
        if accel_mag[i] >= thr:
            # find local peak within refractory window
            j_end = min(len(accel_mag), i + refractory)
            peak_idx = i
            peak_val = accel_mag[i]
            for j in range(i + 1, j_end):
                if accel_mag[j] > peak_val:
                    peak_val = accel_mag[j]
                    peak_idx = j
            return peak_idx
        i += 1
    # fallback: global max
    return max(range(len(accel_mag)), key=lambda k: accel_mag[k])


def compute_tempo(samples: List[Dict], primary_axis: str = 'gyro_y',
                  start_threshold_deg_s: float = 5.0, start_min_ms: int = 100,
                  impact_threshold_g: float = 1.5, refractory_ms: int = 25,
                  allow_fallback: bool = True) -> Dict:
    """Compute start/top/impact indices and tempo metrics for one swing's samples."""
    if not samples:
        raise ValueError('No samples provided')

    # derive sampling rate
    dt = estimate_dt(samples)
    hz = 1.0 / max(dt, 1e-6)

    # build signals
    gx = [s.get('gyro_x', 0.0) for s in samples]
    gy = [s.get('gyro_y', 0.0) for s in samples]
    gz = [s.get('gyro_z', 0.0) for s in samples]
    ax = [s.get('accel_x', 0.0) for s in samples]
    ay = [s.get('accel_y', 0.0) for s in samples]
    az = [s.get('accel_z', 0.0) for s in samples]

    gyro_mag = [_magnitude3(gx[i], gy[i], gz[i]) for i in range(len(samples))]
    accel_mag = [_magnitude3(ax[i], ay[i], az[i]) for i in range(len(samples))]

    # smooth
    gyro_mag_s = smooth_ema(gyro_mag, alpha=0.2)
    accel_mag_s = smooth_ema(accel_mag, alpha=0.2)

    axis_map = {
        'gyro_x': gx,
        'gyro_y': gy,
        'gyro_z': gz,
    }
    axis = axis_map.get(primary_axis, gy)
    axis_s = smooth_ema(axis, alpha=0.2)

    start_idx = detect_start(gyro_mag_s, hz, start_threshold_deg_s, start_min_ms)
    # Provisional top from smoothed axis zero-cross
    top_idx = detect_top(axis_s, start_idx)
    print(f"DEBUG: Axis {primary_axis}, Start: {start_idx}, Provisional Top: {top_idx}")

    # Provisional impact using accel magnitude after provisional top; if that is pathological, we will recompute
    impact_idx = detect_impact(accel_mag_s, hz, impact_threshold_g, refractory_ms, start_from=top_idx + 1)

    # Sanity check: ensure downswing duration is plausible; otherwise choose top as argmin of gyro magnitude between start and impact
    dt = estimate_dt(samples)
    if impact_idx <= start_idx:
        impact_idx = detect_impact(accel_mag_s, hz, impact_threshold_g, refractory_ms, start_from=start_idx)
    downswing_dt = max(0.0, (impact_idx - max(start_idx, top_idx)) * dt)
    print(f"DEBUG: Axis {primary_axis}, Impact: {impact_idx}, Downswing: {downswing_dt:.3f}s, Fallback: {allow_fallback and (downswing_dt < 0.12 or downswing_dt > 0.6)}")

    if allow_fallback and (downswing_dt < 0.12 or downswing_dt > 0.6):
        a = max(start_idx + 1, 0)
        b = max(a + 1, min(len(gyro_mag_s) - 1, impact_idx - 1))
        if b > a:
            rel_min = min(range(a, b), key=lambda i: gyro_mag_s[i])
            top_idx = rel_min
            print(f"DEBUG: Axis {primary_axis}, Fallback Top: {top_idx}")
            # recompute duration after fallback top
            downswing_dt = max(0.0, (impact_idx - top_idx) * dt)

    start_ts = start_idx * dt
    top_ts = top_idx * dt
    impact_ts = impact_idx * dt

    backswing_s = max(0.0, top_ts - start_ts)
    downswing_s = max(1e-6, impact_ts - top_ts)
    ratio = backswing_s / downswing_s

    return {
        'start_idx': start_idx,
        'top_idx': top_idx,
        'impact_idx': impact_idx,
        'timestamps': {
            'start': round(start_ts, 6),
            'top': round(top_ts, 6),
            'impact': round(impact_ts, 6),
        },
        'backswing_s': round(backswing_s, 6),
        'downswing_s': round(downswing_s, 6),
        'ratio': round(ratio, 3),
        'sampling_hz': round(hz, 3),
    }


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


def serve(host: str = '0.0.0.0', port: int = 5001):
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
            parsed = urlparse(self.path)
            path = parsed.path
            qs = parse_qs(parsed.query)

            # configurable params
            start_thr = float(qs.get('start_deg_s', [45.0])[0])
            start_min = int(qs.get('start_min_ms', [100])[0])
            impact_thr_g = float(qs.get('impact_g', [10.0])[0])
            refr_ms = int(qs.get('refractory_ms', [25])[0])
            primary = qs.get('axis', ['gyro_y'])[0]
            allow_fb = qs.get('fallback', ['1'])[0] == '1'

            if path == '/metrics':
                try:
                    payload = run_once()
                    self._set_headers(200)
                    self.wfile.write(json.dumps(payload).encode('utf-8'))
                except Exception as e:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            elif path == '/all-metrics':
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
            elif path == '/events':
                try:
                    src = os.path.join(os.path.dirname(__file__), 'simulated_sensor_data.json')
                    swings = load_all_swings(src)
                    swing = swings[-1]
                    samples = swing.get('samples', [])
                    tempo = compute_tempo(samples, primary_axis=primary,
                                           start_threshold_deg_s=start_thr,
                                           start_min_ms=start_min,
                                           impact_threshold_g=impact_thr_g,
                                           refractory_ms=refr_ms,
                                           allow_fallback=allow_fb)
                    self._set_headers(200)
                    self.wfile.write(json.dumps(tempo).encode('utf-8'))
                except Exception as e:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            elif path == '/tempo':
                try:
                    src = os.path.join(os.path.dirname(__file__), 'simulated_sensor_data.json')
                    swings = load_all_swings(src)
                    swing = swings[-1]
                    samples = swing.get('samples', [])
                    tempo = compute_tempo(samples, primary_axis=primary,
                                           start_threshold_deg_s=start_thr,
                                           start_min_ms=start_min,
                                           impact_threshold_g=impact_thr_g,
                                           refractory_ms=refr_ms,
                                           allow_fallback=allow_fb)
                    # Only keep tempo fields for compact response
                    compact = {
                        'backswing_s': tempo['backswing_s'],
                        'downswing_s': tempo['downswing_s'],
                        'ratio': tempo['ratio'],
                        'timestamps': tempo['timestamps'],
                        'sampling_hz': tempo['sampling_hz'],
                    }
                    self._set_headers(200)
                    self.wfile.write(json.dumps(compact).encode('utf-8'))
                except Exception as e:
                    self._set_headers(500)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            elif path == '/all-tempo':
                try:
                    src = os.path.join(os.path.dirname(__file__), 'simulated_sensor_data.json')
                    swings = load_all_swings(src)
                    out = []
                    for idx, swing in enumerate(swings):
                        samples = swing.get('samples', [])
                        tempo = compute_tempo(samples, primary_axis=primary,
                                               start_threshold_deg_s=start_thr,
                                               start_min_ms=start_min,
                                               impact_threshold_g=impact_thr_g,
                                               refractory_ms=refr_ms,
                                               allow_fallback=allow_fb)
                        out.append({
                            'index': idx,
                            'backswing_s': tempo['backswing_s'],
                            'downswing_s': tempo['downswing_s'],
                            'ratio': tempo['ratio'],
                            'timestamps': tempo['timestamps'],
                            'sampling_hz': tempo['sampling_hz'],
                            'metadata': swing.get('metadata', {}),
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
    print("Swing Analyzer server running:")
    try:
        import socket
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = '127.0.0.1'
    # Show helpful URLs for localhost and likely LAN address
    print(f"  Local:    http://127.0.0.1:{port}")
    print(f"  Network:  http://{local_ip}:{port}")
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
