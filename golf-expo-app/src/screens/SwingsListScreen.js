import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { ANALYZER_BASE_URL, USE_SIMULATED_DATA, SIMULATED_DATA_URL } from '../config';

export default function SwingsListScreen() {
  const [loading, setLoading] = useState(true);
  const [swings, setSwings] = useState([]);

  const toNumber = (v) => {
    if (typeof v === 'number') return isFinite(v) ? v : undefined;
    if (typeof v === 'string') {
      // Extract leading numeric content, tolerate units like 'kph', '°', ' mph'
      const cleaned = v.trim().replace(/[^0-9+\-\.eE]/g, ' ').split(/\s+/)[0];
      const n = Number(cleaned);
      return typeof n === 'number' && isFinite(n) ? n : undefined;
    }
    return undefined;
  };

  const get = (obj, path) => {
    try {
      return path.split('.').reduce((o, k) => (o == null ? undefined : o[k]), obj);
    } catch {
      return undefined;
    }
  };

  const firstDefined = (obj, candidates) => {
    for (const p of candidates) {
      const v = typeof p === 'function' ? p(obj) : get(obj, p);
      if (v !== undefined && v !== null) return v;
    }
    return undefined;
  };

  const normalizeSwing = (item, idx) => {
    // Index / ID
    const index = typeof item?.index === 'number' ? item.index : (typeof item?.id === 'number' ? item.id : idx);

    // Samples metadata
    const numSamples = firstDefined(item, [
      'metadata.num_samples',
      'num_samples',
      'samples',
      'metadata.samples',
    ]);
    const metadata = { num_samples: toNumber(numSamples) ?? numSamples ?? undefined };

    // Club speed (kph). Try multiple common shapes and units
    const speedMps = firstDefined(item, [
      'clubSpeed_mps',
      'club_speed_mps',
      'metrics.club.speed_mps',
      'club.speed_mps',
      'metrics.speed_mps',
    ]);
    const speedMph = firstDefined(item, [
      'clubSpeed_mph',
      'club_speed_mph',
      'metrics.club.speed_mph',
      'club.speed_mph',
      'metrics.speed_mph',
    ]);
    const speedKphRaw = firstDefined(item, [
      'clubSpeed_kph',
      'club_speed_kph',
      'clubSpeedKph',
      'metrics.club.speed_kph',
      'club.speed_kph',
      'metrics.speed_kph',
      'speed_kph',
      'speed',
    ]);
    const speedKph =
      toNumber(speedKphRaw) ??
      (toNumber(speedMps) !== undefined ? toNumber(speedMps) * 3.6 : undefined) ??
      (toNumber(speedMph) !== undefined ? toNumber(speedMph) * 1.60934 : undefined);

    // Angles (deg)
    const launchDeg = toNumber(firstDefined(item, [
      'launchAngle_deg',
      'launch_angle_deg',
      'launchAngle',
      'launch_angle',
      'angles.launch_deg',
      'metrics.launch_deg',
    ]));

    const attackDeg = toNumber(firstDefined(item, [
      'attackAngle_deg',
      'attack_angle_deg',
      'attackAngle',
      'attack_angle',
      'angles.attack_deg',
      'metrics.attack_deg',
    ]));

    const pathDeg = toNumber(firstDefined(item, [
      'clubPath_deg',
      'club_path_deg',
      'clubPath',
      'club_path',
      'angles.path_deg',
      'metrics.path_deg',
    ]));

    return {
      index,
      metadata,
      clubSpeed_kph: speedKph,
      launchAngle_deg: launchDeg,
      attackAngle_deg: attackDeg,
      clubPath_deg: pathDeg,
      // keep original for debugging if needed
      __raw: item,
    };
  };

  const normalizeList = (list) => list.map((it, i) => normalizeSwing(it, i));

  const fetchAll = async () => {
    try {
      setLoading(true);
      const tryFetch = async (url) => {
        const res = await fetch(url);
        const data = await res.json();
        // Accept either an array or an object with { swings: [...] }
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

      // Secondary: analyzer API
      if (!list) {
        try {
          list = await tryFetch(`${ANALYZER_BASE_URL}/all-metrics`);
          console.log('[Swings] Loaded from analyzer at', ANALYZER_BASE_URL);
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
      const normalized = normalizeList(list);
      if (__DEV__) {
        try {
          console.log('[Swings] Raw sample:', JSON.stringify(list[0], null, 2));
          console.log('[Swings] Normalized sample:', normalized[0]);
        } catch {}
      }
      setSwings(normalized);
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
      <Text style={styles.meta}>Samples: {item.metadata?.num_samples ?? '—'}</Text>
      <View style={styles.row}><Text style={styles.label}>Club Speed</Text><Text style={styles.value}>{typeof item.clubSpeed_kph === 'number' ? item.clubSpeed_kph.toFixed(1) : '—'} kph</Text></View>
      <View style={styles.row}><Text style={styles.label}>Launch Angle</Text><Text style={styles.value}>{typeof item.launchAngle_deg === 'number' ? item.launchAngle_deg.toFixed(1) : '—'}°</Text></View>
      <View style={styles.row}><Text style={styles.label}>Attack Angle</Text><Text style={styles.value}>{typeof item.attackAngle_deg === 'number' ? item.attackAngle_deg.toFixed(1) : '—'}°</Text></View>
      <View style={styles.row}><Text style={styles.label}>Club Path</Text><Text style={styles.value}>{typeof item.clubPath_deg === 'number' ? item.clubPath_deg.toFixed(1) : '—'}°</Text></View>
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
