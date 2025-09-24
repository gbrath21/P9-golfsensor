import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ANALYZER_BASE_URL, USE_SIMULATED_DATA, SIMULATED_DATA_URL, TEMPO_URL } from '../config';

export default function SwingsListScreen() {
  const [loading, setLoading] = useState(true);
  const [swings, setSwings] = useState([]);

  const mapTempoItem = (item, idx) => {
    const index = typeof item?.index === 'number' ? item.index : idx;
    const meta = item?.metadata || {};
    return {
      index,
      metadata: { num_samples: meta.num_samples },
      backswing_s: item?.backswing_s,
      downswing_s: item?.downswing_s,
      ratio: item?.ratio,
      timestamps: item?.timestamps,
    };
  };

  const fetchAll = async () => {
    try {
      setLoading(true);
      const tryFetch = async (url) => {
        const sep = url.includes('?') ? '&' : '?';
        const bust = `${sep}cb=${Date.now()}`;
        const res = await fetch(url + bust, { cache: 'no-store' });
        const data = await res.json();
        const list = Array.isArray(data) ? data : Array.isArray(data?.swings) ? data.swings : null;
        if (!list) throw new Error('Unexpected response shape from ' + url);
        return list;
      };

      let list = null;

      // Primary: if dev flag is on and URL provided, use simulated data first
      if (USE_SIMULATED_DATA && SIMULATED_DATA_URL) {
        try {
          list = await tryFetch(SIMULATED_DATA_URL);
          console.log('[Swings] Loaded simulated data from', SIMULATED_DATA_URL);
        } catch (e) {
          console.warn('[Swings] Failed to load simulated data, falling back to analyzer:', e?.message);
        }
      }

      // Secondary: analyzer API (use TEMPO_URL so axis/params are honored)
      if (!list) {
        try {
          list = await tryFetch(TEMPO_URL);
          console.log('[Swings] Loaded from analyzer at', TEMPO_URL);
        } catch (e) {
          console.warn('[Swings] Analyzer fetch failed:', e?.message);
        }
      }

      // Final fallback: if analyzer failed but simulated URL exists, try it
      if (!list && SIMULATED_DATA_URL) {
        list = await tryFetch(SIMULATED_DATA_URL);
        console.log('[Swings] Loaded simulated data as fallback from', SIMULATED_DATA_URL);
      }

      if (!list) throw new Error('No data sources available. Check ANALYZER_BASE_URL or SIMULATED_DATA_URL.');
      const tempoList = list.map((it, i) => mapTempoItem(it, i));
      setSwings(tempoList);
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const renderItem = ({ item, index }) => (
    <View style={styles.card}>
      <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
        <Text style={styles.title}>Swing #{(typeof item.index === 'number' ? item.index : index) + 1}</Text>
        <TouchableOpacity onPress={fetchAll}>
          <Text style={styles.refresh}>Refresh</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.row}><Text style={styles.label}>Backswing</Text><Text style={styles.value}>{typeof item.backswing_s === 'number' ? item.backswing_s.toFixed(3) : '—'} s</Text></View>
      <View style={styles.row}><Text style={styles.label}>Downswing</Text><Text style={styles.value}>{typeof item.downswing_s === 'number' ? item.downswing_s.toFixed(3) : '—'} s</Text></View>
      <View style={styles.row}><Text style={styles.label}>Tempo</Text><Text style={styles.value}>{typeof item.ratio === 'number' ? item.ratio.toFixed(2) : '—'} : 1</Text></View>
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
          keyExtractor={(item, idx) => String(item.id ?? item.index ?? idx)}
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
