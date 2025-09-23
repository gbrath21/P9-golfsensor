// Base URL for the local swing analyzer dev server
// Default assumes the analyzer is running on the same machine as Metro at port 5001
// Change this to your computer's LAN IP if testing on a physical device, e.g. 'http://192.168.1.23:5001'
export const ANALYZER_BASE_URL = 'http://192.168.0.175:5001';

// When true, the app will fetch swings from a simulated JSON file served over HTTP on your LAN
// Example: Start a simple server in the folder containing `simulated_sensor_data.json`:
//   python3 -m http.server 8000
// Then set SIMULATED_DATA_URL to: 'http://<your-lan-ip>:8000/simulated_sensor_data.json'
export const USE_SIMULATED_DATA = true;

// Full URL to the simulated data JSON. Must be accessible from your phone on the same Wi‑Fi.
// Tip: find your LAN IP on macOS with: ipconfig getifaddr en0
export const SIMULATED_DATA_URL = 'http://192.168.0.175:5001/all-metrics';
