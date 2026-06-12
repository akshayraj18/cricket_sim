import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';

import { seasonApi } from '@/api/season';
import { LeaguePayload } from '@/api/types';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

export function RetentionHub({
  careerId,
  payload,
  accent,
  onChange,
}: {
  careerId: string;
  payload: LeaguePayload;
  accent?: string;
  onChange: (payload: LeaguePayload) => void;
}) {
  const theme = useTheme();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const limit = payload.retention_limit;
  const players = [...payload.retention.players].sort((a, b) => b.ovr - a.ovr);
  const [selected, setSelected] = useState<string[]>(players.slice(0, limit).map((p) => p.name));

  const toggle = (name: string) => {
    setSelected((prev) => {
      if (prev.includes(name)) return prev.filter((n) => n !== name);
      if (prev.length >= limit) return prev;
      return [...prev, name];
    });
  };

  const submit = async () => {
    if (selected.length !== limit) {
      setError(`Choose exactly ${limit} players to retain.`);
      return;
    }
    setError(null);
    setBusy(true);
    try {
      onChange(await seasonApi.submitRetentions(careerId, { players: selected }));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit retentions');
    } finally {
      setBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <Card>
        <ThemedText style={styles.title}>Retention Window</ThemedText>
        <ThemedText themeColor="textDim" style={styles.helpText}>
          Choose exactly {limit} players to retain. Every second off-season is a mini-reset where teams keep only 5.
        </ThemedText>
        <ThemedText themeColor={selected.length === limit ? 'green' : 'red'} style={styles.counter}>
          {selected.length} / {limit} selected
        </ThemedText>
        {error && (
          <ThemedText themeColor="red" style={styles.helpText}>
            {error}
          </ThemedText>
        )}
        <Button label="Confirm Retentions" variant="primary" accentColor={accent} loading={busy} onPress={submit} />
      </Card>

      <Card style={styles.listCard}>
        {players.map((p) => {
          const active = selected.includes(p.name);
          const swatch = accent ?? theme.green;
          return (
            <Pressable
              key={p.name}
              onPress={() => toggle(p.name)}
              style={[styles.row, { borderBottomColor: theme.border }, active && { backgroundColor: theme.bgElevated }]}>
              <View
                style={[
                  styles.checkbox,
                  { borderColor: swatch },
                  active && { backgroundColor: swatch },
                ]}
              />
              <View style={styles.flex1}>
                <ThemedText style={styles.name} numberOfLines={1}>
                  {p.name}
                </ThemedText>
                <ThemedText themeColor="textDim" style={styles.sub} numberOfLines={1}>
                  {p.role} · OVR {p.ovr} · Age {p.age} · MVP {p.mvp}
                </ThemedText>
              </View>
            </Pressable>
          );
        })}
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: Spacing.three,
    gap: Spacing.three,
    paddingBottom: Spacing.six,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4,
  },
  helpText: {
    fontSize: 12.5,
    lineHeight: 18,
    marginBottom: Spacing.two,
  },
  counter: {
    fontSize: 13,
    fontWeight: '700',
    marginBottom: Spacing.two,
  },
  listCard: {
    paddingBottom: 4,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    paddingVertical: 10,
    paddingHorizontal: Spacing.two,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  flex1: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontSize: 13.5,
    fontWeight: '700',
  },
  sub: {
    fontSize: 11,
    marginTop: 2,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 2,
    flexShrink: 0,
  },
});
