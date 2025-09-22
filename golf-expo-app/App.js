import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import HomeScreen from './src/screens/HomeScreen';
import SelectClubScreen from './src/screens/SelectClubScreen';
import StartRoundScreen from './src/screens/StartRoundScreen';
import { ClubProvider } from './src/context/ClubContext';
import { StatsProvider } from './src/context/StatsContext';
import SwingStatsScreen from './src/screens/SwingStatsScreen';
import SwingsListScreen from './src/screens/SwingsListScreen';

const Stack = createNativeStackNavigator();

export default function App() {
  return (
    <ClubProvider>
      <StatsProvider>
        <NavigationContainer>
          <Stack.Navigator initialRouteName="SwingsList">
            <Stack.Screen name="SwingsList" component={SwingsListScreen} options={{ title: 'All Swings' }} />
            <Stack.Screen name="Home" component={HomeScreen} options={{ title: 'Golf Companion' }} />
            <Stack.Screen name="SelectClub" component={SelectClubScreen} options={{ title: 'Choose Club' }} />
            <Stack.Screen name="StartRound" component={StartRoundScreen} options={{ title: 'Start Round' }} />
            <Stack.Screen name="SwingStats" component={SwingStatsScreen} options={{ title: 'Swing Stats' }} />
          </Stack.Navigator>
        </NavigationContainer>
      </StatsProvider>
    </ClubProvider>
  );
}
