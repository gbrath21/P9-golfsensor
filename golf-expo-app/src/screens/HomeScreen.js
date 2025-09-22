import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useClub } from '../context/ClubContext';

export default function HomeScreen({ navigation }) {
  const { selectedClub } = useClub();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Welcome to Golf Companion</Text>
      <Text style={styles.subtitle}>Your selected club: {selectedClub || 'None'}</Text>

      <TouchableOpacity style={styles.primaryBtn} onPress={() => navigation.navigate('StartRound')}>
        <Text style={styles.primaryBtnText}>Start Round</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryBtn} onPress={() => navigation.navigate('SelectClub')}>
        <Text style={styles.secondaryBtnText}>Choose Club</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryBtn} onPress={() => navigation.navigate('SwingStats')}>
        <Text style={styles.secondaryBtnText}>View Swing Stats</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: 'center', backgroundColor: '#0b132b' },
  title: { fontSize: 28, fontWeight: '700', color: 'white', textAlign: 'center', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#b0c4de', textAlign: 'center', marginBottom: 24 },
  primaryBtn: { backgroundColor: '#1c7ed6', padding: 16, borderRadius: 12, marginBottom: 12 },
  primaryBtnText: { color: 'white', fontSize: 18, textAlign: 'center', fontWeight: '600' },
  secondaryBtn: { backgroundColor: '#2a2f4f', padding: 16, borderRadius: 12, marginTop: 12 },
  secondaryBtnText: { color: 'white', fontSize: 18, textAlign: 'center' },
});
