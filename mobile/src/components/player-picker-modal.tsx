import { FlatList, Modal, Pressable, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export interface PickerOption {
  name: string;
  subtitle?: string;
}

export function PlayerPickerModal({
  visible,
  title,
  options,
  selected,
  onSelect,
  onClose,
  allowClear,
}: {
  visible: boolean;
  title: string;
  options: PickerOption[];
  selected?: string;
  onSelect: (name: string) => void;
  onClose: () => void;
  /** If true, shows a "Clear (auto-pick)" option at the top. */
  allowClear?: boolean;
}) {
  const theme = useTheme();

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.bgCard }]} onPress={(e) => e.stopPropagation()}>
          <View style={styles.header}>
            <ThemedText style={styles.title}>{title}</ThemedText>
            <Pressable onPress={onClose} hitSlop={12}>
              <ThemedText themeColor="textDim" style={styles.close}>
                Cancel
              </ThemedText>
            </Pressable>
          </View>
          <FlatList
            data={allowClear ? [{ name: '', subtitle: 'Auto-pick' }, ...options] : options}
            keyExtractor={(item, idx) => `${item.name}-${idx}`}
            style={styles.list}
            renderItem={({ item }) => {
              const active = item.name === selected;
              return (
                <Pressable
                  onPress={() => onSelect(item.name)}
                  style={[
                    styles.option,
                    { borderBottomColor: theme.border },
                    active && { backgroundColor: theme.bgElevated },
                  ]}>
                  <ThemedText style={styles.optionName} numberOfLines={1}>
                    {item.name || 'Empty (auto-pick)'}
                  </ThemedText>
                  {item.subtitle && (
                    <ThemedText themeColor="textDim" style={styles.optionSubtitle} numberOfLines={1}>
                      {item.subtitle}
                    </ThemedText>
                  )}
                </Pressable>
              );
            }}
          />
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  sheet: {
    borderTopLeftRadius: Radius.lg,
    borderTopRightRadius: Radius.lg,
    paddingTop: Spacing.three,
    paddingHorizontal: Spacing.four,
    maxHeight: '75%',
    width: '100%',
    maxWidth: 600,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: Spacing.two,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
  },
  close: {
    fontSize: 13,
    fontWeight: '700',
  },
  list: {
    marginBottom: Spacing.four,
  },
  option: {
    paddingVertical: 12,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  optionName: {
    fontSize: 14,
    fontWeight: '700',
  },
  optionSubtitle: {
    fontSize: 11.5,
    marginTop: 2,
  },
});
