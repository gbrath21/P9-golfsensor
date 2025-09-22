import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

/*
Shape of stats:
{
  clubSpeed: number,         // mph
  launchAngle: number,       // degrees
  attackAngle: number,       // degrees
  clubPath: number,          // degrees (in-to-out +, out-to-in -)
  updatedAt: string          // ISO timestamp
}
*/

const StatsContext = createContext({
  stats: null,
  setStats: () => {},
  clearStats: () => {},
});

export const StatsProvider = ({ children }) => {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const raw = await AsyncStorage.getItem('swingStats');
        if (raw) setStats(JSON.parse(raw));
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        if (stats) {
          await AsyncStorage.setItem('swingStats', JSON.stringify(stats));
        }
      } catch (e) {
        // ignore
      }
    })();
  }, [stats]);

  const clearStats = async () => {
    setStats(null);
    try { await AsyncStorage.removeItem('swingStats'); } catch {}
  };

  return (
    <StatsContext.Provider value={{ stats, setStats, clearStats }}>
      {children}
    </StatsContext.Provider>
  );
};

export const useStats = () => useContext(StatsContext);
