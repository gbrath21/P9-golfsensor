# P9-Simulator

Synthetic golf swing dataset + analyzer + Expo demo app.

This repository contains three parts:

- `golf_swing_simulator.py` – Generates simulated IMU-like samples for a golf swing and appends them to `simulated_sensor_data.json` along with a metadata block describing the swing profile.
- `swing_analyzer.py` – A small web service that parses swings and reports metrics (Club Speed, Attack Angle, Club Path, Launch Angle, Spin). Serves JSON over HTTP for the demo app.
- `golf-expo-app/` – An Expo/React Native app that lists swings from `simulated_sensor_data.json` and fetches metrics from the analyzer service.

## Quick start

### 1) Create a virtual environment (optional but recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Run the analyzer server

```bash
python3 swing_analyzer.py --serve
```

- Server URL: http://127.0.0.1:5001
- Endpoints:
  - `GET /all-metrics` – Computes metrics for every swing found in `simulated_sensor_data.json` and returns a list.

### 3) Generate some swings

Run multiple times to append several swings with varied profiles:

```bash
python3 golf_swing_simulator.py
```

This will create or append to `simulated_sensor_data.json` at the repository root.

### 4) Run the Expo app

In another terminal:

```bash
cd golf-expo-app
npm install   # or: yarn
npx expo start
```

- The app will request metrics from the analyzer server. Be sure the server is running before opening the app.

## Project structure

```
P9-Simulator/
├── golf-expo-app/             # Expo app (React Native)
├── golf_swing_simulator.py    # Data generator for simulated swings
├── swing_analyzer.py          # Analyzer + web service (port 5001)
├── simulated_sensor_data.json # Generated swings (gitignored)
└── .gitignore
```

## Development notes

- The simulator randomizes swing profile params for each run, keeping club speed in realistic ranges; the analyzer derives angles using pre-impact windows for robustness.
- `simulated_sensor_data.json` is gitignored by default to avoid large diffs.

