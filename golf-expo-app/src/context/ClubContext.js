import React, { createContext, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

const ClubContext = createContext({ selectedClub: null, setSelectedClub: () => {} });

export const ClubProvider = ({ children }) => {
  const [selectedClub, setSelectedClub] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem('selectedClub');
        if (stored) setSelectedClub(stored);
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  useEffect(() => {
    (async () => {
      try {
        if (selectedClub) await AsyncStorage.setItem('selectedClub', selectedClub);
      } catch (e) {
        // ignore
      }
    })();
  }, [selectedClub]);

  return (
    <ClubContext.Provider value={{ selectedClub, setSelectedClub }}>
      {children}
    </ClubContext.Provider>
  );
};

export const useClub = () => useContext(ClubContext);
