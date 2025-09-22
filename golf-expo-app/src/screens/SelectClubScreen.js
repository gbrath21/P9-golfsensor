import React from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useClub } from '../context/ClubContext';

const CLUBS = [
  'Driver',
  '3 Wood',
  '5 Wood',
  '3 Iron', '4 Iron', '5 Iron', '6 Iron', '7 Iron', '8 Iron', '9 Iron',
  'Pitching Wedge', 'Gap Wedge', 'Sand Wedge', 'Lob Wedge',
  'Putter',
];

export default function SelectClubScreen({ navigation }) {
  const { selectedClub, setSelectedClub } = useClub();

  const onSelect = (club) => {
    setSelectedClub(club);
    navigation.goBack();
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity style={[styles.item, selectedClub === item && styles.itemSelected]} onPress={() => onSelect(item)}>
      <Text style={[styles.itemText, selectedClub === item && styles.itemTextSelected]}>{item}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={CLUBS}
        keyExtractor={(item) => item}
        renderItem={renderItem}
        ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        contentContainerStyle={{ padding: 16 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0b132b' },
  item: { padding: 16, borderRadius: 10, backgroundColor: '#2a2f4f' },
  itemSelected: { backgroundColor: '#1c7ed6' },
  itemText: { color: 'white', fontSize: 16 },
  itemTextSelected: { color: 'white', fontWeight: '700' },
});
