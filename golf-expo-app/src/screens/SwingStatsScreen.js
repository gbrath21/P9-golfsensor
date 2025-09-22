import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useStats } from '../context/StatsContext';

export default function SwingStatsScreen() {
  const { stats } = useStats();

  return (
    <View style={styles.container}>
      {stats ? (
        <>
          <Text style={styles.title}>Latest Swing</Text>
          <Text style={styles.meta}>Updated: {new Date(stats.updatedAt).toLocaleString()}</Text>

          <View style={styles.card}>
            <Row label="Club Speed" value={`${stats.clubSpeed.toFixed(1)} mph`} />
            <Row label="Launch Angle" value={`${stats.launchAngle.toFixed(1)}°`} />
            <Row label="Attack Angle" value={`${stats.attackAngle.toFixed(1)}°`} />
            <Row label="Club Path" value={`${stats.clubPath.toFixed(1)}°`} />
          </View>
        </>
      ) : (
        <>
          <Text style={styles.title}>No swing stats yet</Text>
          <Text style={styles.meta}>Start a round and record a swing to see stats here.</Text>
        </>
      )}
    </View>
  );
}

const Row = ({ label, value }) => (
  <View style={styles.row}>
    <Text style={styles.rowLabel}>{label}</Text>
    <Text style={styles.rowValue}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: { flex: 1, padding: 24, backgroundColor: '#0b132b' },
  title: { fontSize: 24, fontWeight: '700', color: 'white', marginBottom: 6 },
  meta: { fontSize: 14, color: '#b0c4de', marginBottom: 16 },
  card: { backgroundColor: '#2a2f4f', borderRadius: 12, padding: 16 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#3e4670' },
  rowLabel: { color: '#b0c4de', fontSize: 16 },
  rowValue: { color: 'white', fontSize: 16, fontWeight: '600' },
});
