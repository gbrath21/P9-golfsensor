// Base URL for the local swing analyzer dev server
// Default assumes the analyzer is running on the same machine as Metro at port 5001
// Change this to your computer's LAN IP if testing on a physical device, e.g. 'http://192.168.1.23:5001'
export const ANALYZER_BASE_URL = 'http://192.168.0.175:5001';

// When true, the app will fetch swings from a simulated JSON file served over HTTP on your LAN
// Example: Start a simple server in the folder containing `simulated_sensor_data.json`:
//   python3 -m http.server 8000
// Then set SIMULATED_DATA_URL to: 'http://<your-lan-ip>:8000/simulated_sensor_data.json'
export const USE_SIMULATED_DATA = true;

// Select which gyro axis to use for detecting the top of the swing.
// Change ONLY this to try different axes: 'gyro_x' | 'gyro_y' | 'gyro_z'
export const TEMPO_AXIS = 'gyro_y';
// Enable fallback top detection (1) or disable (0) to test axis sensitivity
export const TEMPO_FALLBACK = 0;
// Tempo-first endpoint used by the app
export const TEMPO_URL = `${ANALYZER_BASE_URL}/all-tempo?axis=${encodeURIComponent(TEMPO_AXIS)}&fallback=${TEMPO_FALLBACK}`;

// Use the tempo endpoint for simulated data as well so both paths share the same axis/params
// Must be accessible from your phone on the same Wi‑Fi.
export const SIMULATED_DATA_URL = TEMPO_URL;


