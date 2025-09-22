# Golf Companion (Expo)

A simple Expo-based mobile app to act as the platform/display for golfers. It includes:

- Home screen with quick actions
- Choose Club screen to select the current club
- Start Round screen showing the selected club (ready to extend with swing data, sensors, etc.)

## Getting Started

Prerequisites:
- Node.js LTS
- npm or yarn
- Expo CLI (installed automatically via npx)

From the project root:

```bash
# install dependencies
cd golf-expo-app
npm install

# run the app
npm run start
# or
npx expo start
```

Use the QR code in the terminal to open the app on your device with Expo Go, or press i/a to launch on iOS/Android simulator.

## Project Structure

```
/golf-expo-app
  App.js
  app.json
  package.json
  babel.config.js
  /src
    /context
      ClubContext.js
    /screens
      HomeScreen.js
      SelectClubScreen.js
      StartRoundScreen.js
```

## Next Steps

- Wire the Start Round screen to your swing simulator/engine or real sensor stream.
- Add round tracking (holes, score, fairways/greens in regulation, putts, etc.).
- Persist round state and history.
- Add beautiful charts for swing metrics.
