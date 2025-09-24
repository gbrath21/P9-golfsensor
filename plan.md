# Tempo-First Implementation Plan

This plan pivots the project to focus primarily on swing tempo: backswing time, downswing time, and the tempo ratio.

## Goals
- Compute and display swing tempo (backswing_s, downswing_s, ratio).
- Robust, deterministic event detection for start, top, impact from IMU data.
- Keep the LAN workflow working on iPhone (Expo app + local Python server).

## Backend (Python)

### 1) `swing_analyzer.py` — tempo-first refactor
- **Preprocessing utilities**
  - Add `butter_lowpass(cutoff_hz=50, fs=1000, order=2)` and `apply_filter(signal, b, a)`.
  - Compute magnitudes: `gyro_mag = sqrt(gx^2 + gy^2 + gz^2)`, `accel_mag = sqrt(ax^2 + ay^2 + az^2)`.
- **Event detection**
  - `detect_start(gyro_mag, threshold_deg_s=45, min_ms=100)` — sustained rotation above threshold with debounce.
  - `detect_top(gyro_axis, start_idx)` — zero-crossing or sign flip on the primary swing axis after `start_idx`.
  - `detect_impact(accel_mag, threshold_g=10, refractory_ms=20-30)` — first high-g spike with refractory window.
- **Tempo computation**
  - `T_back = T_top - T_start`
  - `T_down = T_impact - T_top`
  - `tempo_ratio = T_back / T_down`
- **HTTP endpoints (CORS on)**
  - `GET /events` → `{ start_idx, top_idx, impact_idx, timestamps: {start, top, impact}, sampling_hz }`
  - `GET /tempo` → `{ backswing_s, downswing_s, ratio, timestamps: {...}, sampling_hz }`
  - `GET /all-tempo` → array of the above for each swing in `simulated_sensor_data.json`
- **De-scope legacy metrics**
  - Keep old endpoints for now but mark deprecated. New app calls the tempo endpoints exclusively.

### 2) `golf_swing_simulator.py` — embed ground truth
- In each swing `metadata`, add:
  - `"gt": { "start_idx": ..., "top_idx": ..., "impact_idx": ... }`
  - `"sampling_hz": 1000` and `"num_samples"` already present.
- Optionally produce small fixtures (3–5 swings) for tests.

### 3) Response format for lists
- For `/all-tempo`: 
```json
{
  "index": 0,
  "backswing_s": 0.81,
  "downswing_s": 0.27,
  "ratio": 3.0,
  "timestamps": { "start": 12.300, "top": 13.110, "impact": 13.380 },
  "sampling_hz": 1000,
  "metadata": { "num_samples": 500 }
}
```

## Frontend (Expo app)

### 4) `golf-expo-app/src/config.js`
- Keep LAN base URL.
- Add `TEMPO_URL = `${ANALYZER_BASE_URL}/all-tempo``.
- Keep optional `USE_SIMULATED_DATA` pointing to `TEMPO_URL` when testing.

### 5) `golf-expo-app/src/screens/SwingsListScreen.js`
- Fetch `TEMPO_URL` (fallback to `${ANALYZER_BASE_URL}/all-tempo`).
- Render per swing:
  - Title: `Swing #n`
  - `Samples: metadata.num_samples`
  - `Backswing: <backswing_s.toFixed(3)> s`
  - `Downswing: <downswing_s.toFixed(3)> s`
  - `Tempo: <ratio.toFixed(2)> : 1`
- Remove club speed/angles UI and the heavy normalization used for old metrics.
- Keep robust `keyExtractor` (`item.id ?? item.index ?? idx`).

### 6) Optional: `TempoDetailScreen.js`
- Route params: `{ index, backswing_s, downswing_s, ratio, timestamps }`.
- (Stretch) Minimal sparkline of `gyro_mag` / `accel_mag` highlighting start/top/impact.

### 7) Optional: `SettingsScreen.js`
- Adjustable thresholds using AsyncStorage:
  - `start_threshold_deg_s` (default 45), `start_min_ms` (100)
  - `impact_threshold_g` (10), `refractory_ms` (20–30)
  - `primary_axis` (e.g., `gy`)
- Pass settings via query params to `/events` and `/tempo` or persist a config file for the analyzer.

## Validation & Testing

### 8) Unit tests (Python)
- Add `tests/`:
  - `test_events_detection.py` — validate start/top/impact vs simulator ground truth.
  - `test_tempo_calculation.py` — check tempo ratio and duration sums; tolerances ±10 ms.

### 9) Bench diagnostics
- Include quality indicators in `/events`:
  - `{ start_snr, top_zero_cross_conf, impact_peak_g }`.

### 10) Documentation
- Update `README.md`:
  - How to run `python3 swing_analyzer.py --serve` (binds to `0.0.0.0`).
  - Explain endpoints and example payloads.
  - App configuration (`ANALYZER_BASE_URL`, `TEMPO_URL`) and iPhone-on-LAN checklist.

## Execution Order
1. Backend refactor in `swing_analyzer.py` (preprocess, event detection, `/tempo` & `/all-tempo`).
2. Simulator ground-truth fields in `golf_swing_simulator.py`.
3. Update app’s `config.js` and `SwingsListScreen.js` to consume `/all-tempo`.
4. Add unit tests and sample fixtures.
5. Optional detail/settings screens.
6. Update `README.md` and validate on iPhone via LAN.

## Acceptance Criteria
- From iPhone on LAN, list shows swings with non-empty `Backswing s`, `Downswing s`, and `Tempo X:1`.
- `/events` aligns within ±10 ms of simulator GT on fixtures.
- Threshold changes (if implemented) affect results after reload.
