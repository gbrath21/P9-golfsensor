import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useClub } from '../context/ClubContext';
import { useStats } from '../context/StatsContext';
import { ANALYZER_BASE_URL } from '../config';

export default function StartRoundScreen({ navigation }) {
  const { selectedClub } = useClub();
  const { setStats } = useStats();
  const [loading, setLoading] = useState(false);

  const onStartHole = () => {
    // Placeholder: In the future, hook this to your simulator/engine or a live sensor stream
    alert('Starting hole with ' + (selectedClub || 'no club selected'));
  };

  const saveMockStats = () => {
    // Simple mocked values with slight randomness
    const baseSpeed = selectedClub === 'Driver' ? 105 : 85;
    const clubSpeed = baseSpeed + (Math.random() * 6 - 3);
    const launchAngle = 12 + (Math.random() * 6 - 3); // deg
    const attackAngle = selectedClub === 'Driver' ? 2 + (Math.random() * 2 - 1) : -3 + (Math.random() * 2 - 1);
    const clubPath = (Math.random() * 6 - 3); // -3 to +3 deg

    setStats({
      clubSpeed,
      launchAngle,
      attackAngle,
      clubPath,
      updatedAt: new Date().toISOString(),
    });

    navigation.navigate('SwingStats');
  };

  const fetchAnalyzerStats = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${ANALYZER_BASE_URL}/metrics`);
      const data = await res.json();
      if (data && !data.error) {
        setStats({
          clubSpeed: data.clubSpeed_mph ?? data.clubSpeed_mps * 2.23694,
          launchAngle: data.launchAngle_deg,
          attackAngle: data.attackAngle_deg,
          clubPath: data.clubPath_deg,
          updatedAt: data.updatedAt || new Date().toISOString(),
        });
        navigation.navigate('SwingStats');
      } else {
        alert('Analyzer error: ' + (data && data.error ? data.error : 'Unknown error'));
      }
    } catch (e) {
      alert('Failed to contact analyzer server. Is it running?');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.header}>Start a New Round</Text>
      <Text style={styles.subtitle}>Selected Club: {selectedClub || 'None'}</Text>

      <TouchableOpacity style={styles.primaryBtn} onPress={onStartHole}>
        <Text style={styles.primaryBtnText}>Start Hole</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryBtn} onPress={saveMockStats}>
        <Text style={styles.secondaryBtnText}>Save Mock Swing Stats ➜</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryBtn} onPress={() => navigation.navigate('SwingStats')}>
        <Text style={styles.secondaryBtnText}>View Swing Stats</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.secondaryBtn} onPress={fetchAnalyzerStats} disabled={loading}>
        <Text style={styles.secondaryBtnText}>{loading ? 'Contacting Analyzer…' : 'Fetch Stats from Analyzer'}</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, justifyContent: 'center', backgroundColor: '#0b132b' },
  header: { fontSize: 24, fontWeight: '700', color: 'white', textAlign: 'center', marginBottom: 8 },
  subtitle: { fontSize: 16, color: '#b0c4de', textAlign: 'center', marginBottom: 24 },
  primaryBtn: { backgroundColor: '#1c7ed6', padding: 16, borderRadius: 12, marginTop: 8, marginBottom: 12 },
  primaryBtnText: { color: 'white', fontSize: 18, textAlign: 'center', fontWeight: '600' },
  secondaryBtn: { backgroundColor: '#2a2f4f', padding: 16, borderRadius: 12, marginTop: 12 },
  secondaryBtnText: { color: 'white', fontSize: 18, textAlign: 'center' },
});
