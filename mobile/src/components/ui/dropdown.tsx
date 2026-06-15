import { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, View, type ViewStyle } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export type DropdownOption = {
  /** Stable value passed back to `onChange`. */
  value: string;
  /** Text shown in the trigger and the option row. */
  label: string;
  /** Optional color dot (e.g. a team swatch) drawn beside the label. */
  color?: string;
};

/**
 * A compact filter control: a small trigger button showing the current
 * selection, which opens a bottom-sheet list of options. Replaces long,
 * inconsistent rows of filter pills (week/team/stat filters).
 */
export function Dropdown({
  label,
  value,
  options,
  onChange,
  accentColor,
  style,
  minWidth = 120,
}: {
  /** Short prefix shown before the value, e.g. "Team" → "Team: GT". */
  label?: string;
  value: string;
  options: DropdownOption[];
  onChange: (value: string) => void;
  /** Tint for the chevron, the selected row's check, and the selected dot ring. */
  accentColor?: string;
  style?: ViewStyle;
  minWidth?: number;
}) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);

  const selected = options.find((o) => o.value === value);
  const chevron = accentColor ?? theme.textDim;

  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        style={[
          styles.trigger,
          { backgroundColor: theme.bgElevated, borderColor: theme.border, minWidth },
          style,
        ]}>
        {selected?.color ? <View style={[styles.dot, { backgroundColor: selected.color }]} /> : null}
        <ThemedText style={styles.triggerText} numberOfLines={1}>
          {label ? `${label}: ` : ''}
          <ThemedText style={[styles.triggerValue, selected?.color ? { color: selected.color } : null]}>
            {selected?.label ?? value}
          </ThemedText>
        </ThemedText>
        <ThemedText style={[styles.chevron, { color: chevron }]}>▾</ThemedText>
      </Pressable>

      <Modal visible={open} animationType="slide" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          <Pressable
            style={[styles.sheet, { backgroundColor: theme.bgCard }]}
            onPress={(e) => e.stopPropagation()}>
            <View style={styles.handle} />
            {label ? (
              <ThemedText themeColor="textFaint" style={styles.sheetTitle}>
                {label}
              </ThemedText>
            ) : null}
            <ScrollView style={styles.list} showsVerticalScrollIndicator={false}>
              {options.map((opt) => {
                const isSelected = opt.value === value;
                return (
                  <Pressable
                    key={opt.value}
                    onPress={() => {
                      onChange(opt.value);
                      setOpen(false);
                    }}
                    style={[styles.row, { borderBottomColor: theme.border }]}>
                    {opt.color ? (
                      <View style={[styles.rowDot, { backgroundColor: opt.color }]} />
                    ) : (
                      <View style={styles.rowDotSpacer} />
                    )}
                    <ThemedText
                      style={[
                        styles.rowLabel,
                        isSelected && { color: accentColor ?? theme.green, fontWeight: '800' },
                      ]}
                      numberOfLines={1}>
                      {opt.label}
                    </ThemedText>
                    {isSelected ? (
                      <ThemedText style={[styles.check, { color: accentColor ?? theme.green }]}>✓</ThemedText>
                    ) : null}
                  </Pressable>
                );
              })}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  trigger: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: Radius.sm,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  dot: {
    width: 9,
    height: 9,
    borderRadius: 999,
  },
  triggerText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '500',
  },
  triggerValue: {
    fontWeight: '500',
  },
  chevron: {
    fontSize: 12,
    fontWeight: '700',
  },
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  sheet: {
    borderTopLeftRadius: Radius.lg,
    borderTopRightRadius: Radius.lg,
    paddingHorizontal: Spacing.four,
    paddingTop: Spacing.two,
    paddingBottom: Spacing.five,
    maxHeight: '70%',
  },
  handle: {
    alignSelf: 'center',
    width: 36,
    height: 4,
    borderRadius: 999,
    backgroundColor: 'rgba(127,127,127,0.4)',
    marginBottom: Spacing.three,
  },
  sheetTitle: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: Spacing.two,
  },
  list: {
    flexGrow: 0,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
    paddingVertical: 13,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  rowDot: {
    width: 11,
    height: 11,
    borderRadius: 999,
  },
  rowDotSpacer: {
    width: 11,
  },
  rowLabel: {
    flex: 1,
    fontSize: 14.5,
    fontWeight: '600',
  },
  check: {
    fontSize: 15,
    fontWeight: '800',
  },
});
