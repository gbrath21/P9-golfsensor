import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ANALYZER_BASE_URL } from '../config';

export default function SwingsListScreen() {
  const [loading, setLoading] = useState(true);
  const [swings, setSwings] = useState([]);

  const fetchAll = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${ANALYZER_BASE_URL}/all-metrics`);
      const data = await res.json();
      if (Array.isArray(data)) setSwings(data);
      else throw new Error(data?.error || 'Unexpected response');
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={styles.title}>Swing #{item.index + 1}</Text>
        <TouchableOpacity onPress={fetchAll}>
          <Text style={styles.refresh}>Refresh</Text>
        </TouchableOpacity>
      </View>
      <Text style={styles.meta}>Samples: {item.metadata?.num_samples ?? '—'}</Text>
      <View style={styles.row}><Text style={styles.label}>Club Speed</Text><Text style={styles.value}>{item.clubSpeed_kph?.toFixed(1)} kph</Text></View>
      <View style={styles.row}><Text style={styles.label}>Launch Angle</Text><Text style={styles.value}>{item.launchAngle_deg?.toFixed(1)}°</Text></View>
      <View style={styles.row}><Text style={styles.label}>Attack Angle</Text><Text style={styles.value}>{item.attackAngle_deg?.toFixed(1)}°</Text></View>
      <View style={styles.row}><Text style={styles.label}>Club Path</Text><Text style={styles.value}>{item.clubPath_deg?.toFixed(1)}°</Text></View>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.container}> 
        <ActivityIndicator size="large" color="#1c7ed6" />
        <Text style={{ color: 'white', marginTop: 12 }}>Loading swings…</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {swings.length === 0 ? (
        <Text style={styles.empty}>No swings found. Generate some in the simulator.</Text>
      ) : (
        <FlatList
          data={swings}
          keyExtractor={(item) => String(item.index)}
          renderItem={renderItem}
          contentContainerStyle={{ padding: 16 }}
          ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0b132b', justifyContent: 'center' },
  empty: { color: '#b0c4de', textAlign: 'center' },
  card: { backgroundColor: '#2a2f4f', borderRadius: 12, padding: 16 },
  title: { color: 'white', fontSize: 18, fontWeight: '700' },
  meta: { color: '#b0c4de', marginTop: 4, marginBottom: 10 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 6, borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: '#3e4670' },
  label: { color: '#b0c4de' },
  value: { color: 'white', fontWeight: '600' },
  refresh: { color: '#9ad0ff' },
});
