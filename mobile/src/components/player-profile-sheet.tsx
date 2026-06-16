import { Modal, Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { PlayerDict } from '@/api/types';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.stat}>
      <ThemedText themeColor="textDim" style={styles.statLabel}>
        {label}
      </ThemedText>
      <ThemedText style={styles.statValue}>{value}</ThemedText>
    </View>
  );
}

export function PlayerProfileSheet({
  player,
  onClose,
  accentColor,
}: {
  player: PlayerDict | null;
  onClose: () => void;
  accentColor?: string;
}) {
  const theme = useTheme();

  return (
    <Modal visible={!!player} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.bgCard }]} onPress={(e) => e.stopPropagation()}>
          {player && (
            <ScrollView showsVerticalScrollIndicator={false}>
              <View style={styles.header}>
                <View style={styles.headerText}>
                  <ThemedText style={styles.name}>{player.name}</ThemedText>
                  <ThemedText themeColor="textDim" style={styles.sub}>
                    {(player.team || 'Unassigned')} · {player.overseas ? 'Overseas' : 'Indian'} · Age {player.age} ·
                    Form {player.form}
                  </ThemedText>
                </View>
                <Pressable onPress={onClose} hitSlop={12}>
                  <ThemedText themeColor="textDim" style={styles.close}>
                    Close
                  </ThemedText>
                </Pressable>
              </View>

              <View style={styles.grid}>
                <Stat label="OVR" value={player.ovr_progression || player.ovr} />
                <Stat label="Bat" value={player.bat_progression || player.bat} />
                <Stat label="Bowl" value={player.bowl_progression || player.bowl} />
                <Stat label="Role" value={player.role} />
                <Stat label="Bat Hand" value={player.batting_hand} />
                <Stat label="Bowl Hand" value={player.bowling_hand} />
                <Stat label="Bat Type" value={player.batting_archetype} />
                <Stat label="Bowl Phase" value={player.bowling_phase} />
                <Stat label="Ball" value={player.bowling_type} />
              </View>

              <View style={[styles.notes, { borderColor: theme.border }]}>
                <ThemedText style={[styles.noteLabel, { color: accentColor ?? theme.green }]}>Strength</ThemedText>
                <ThemedText themeColor="textDim" style={styles.noteText}>
                  {player.strengths || '-'}
                </ThemedText>
                <ThemedText style={[styles.noteLabel, { color: theme.red, marginTop: Spacing.two }]}>
                  Weakness
                </ThemedText>
                <ThemedText themeColor="textDim" style={styles.noteText}>
                  {player.weaknesses || '-'}
                </ThemedText>
              </View>

              <View style={styles.grid}>
                <Stat label="Runs" value={player.runs ?? 0} />
                <Stat label="SR" value={player.sr ?? 0} />
                <Stat label="HS" value={player.hs ?? 0} />
                <Stat label="Wkts" value={player.wickets ?? 0} />
                <Stat label="Econ" value={player.econ ?? 0} />
                <Stat label="MVP" value={player.mvp ?? 0} />
              </View>
            </ScrollView>
          )}
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
  },
  sheet: {
    borderTopLeftRadius: Radius.lg,
    borderTopRightRadius: Radius.lg,
    padding: Spacing.four,
    maxHeight: '85%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: Spacing.three,
  },
  headerText: {
    flex: 1,
    gap: 2,
  },
  name: {
    fontSize: 19,
    fontWeight: '800',
  },
  sub: {
    fontSize: 12,
  },
  close: {
    fontSize: 13,
    fontWeight: '700',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.two,
    marginBottom: Spacing.three,
  },
  stat: {
    minWidth: '30%',
    flexGrow: 1,
  },
  statLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    fontWeight: '700',
    marginBottom: 2,
  },
  statValue: {
    fontSize: 13,
    fontWeight: '700',
  },
  notes: {
    borderWidth: 1,
    borderRadius: Radius.sm,
    padding: Spacing.two,
    marginBottom: Spacing.three,
  },
  noteLabel: {
    fontSize: 11,
    fontWeight: '800',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  noteText: {
    fontSize: 12.5,
    marginTop: 2,
    lineHeight: 18,
  },
});
