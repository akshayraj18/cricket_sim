import { router } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { useLayout } from '@/hooks/use-layout';

import { AccountSheet } from '@/components/account-sheet';
import { CareerCard } from '@/components/career-card';
import { RosterCsvCard } from '@/components/roster-csv-card';
import { ThemedText } from '@/components/themed-text';
import { ContentBottomInset, Radius, Spacing } from '@/constants/theme';
import { useAuth } from '@/context/AuthContext';
import { useCareer } from '@/context/CareerContext';
import { useCareers } from '@/hooks/use-careers';
import { useTheme } from '@/hooks/use-theme';

function initials(name: string | null): string {
  if (!name) return 'GU';
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function HomeScreen() {
  const theme = useTheme();
  const { contentContainerStyle, bottomInset } = useLayout();
  const { user } = useAuth();
  const { careers, loading, error, refresh, deleteCareer } = useCareers();
  const { activeCareerId, setActiveCareerId } = useCareer();
  const activeCareer = careers.find((c) => c.id === activeCareerId) ?? null;

  const [accountVisible, setAccountVisible] = useState(false);

  const enterCareer = (careerId: string) => {
    setActiveCareerId(careerId);
    router.push('/(tabs)/season');
  };

  const confirmDelete = (careerId: string, name: string) => {
    Alert.alert('Delete career', `Delete "${name}"? This cannot be undone.`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          await deleteCareer(careerId);
          if (careerId === activeCareerId) setActiveCareerId(null);
        },
      },
    ]);
  };

  return (
    <View style={[styles.container, { backgroundColor: theme.bg }]}>
      <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
        <View style={[styles.appbar, contentContainerStyle]}>
          <View style={styles.wordmark}>
            <ThemedText style={styles.mark}>🏏</ThemedText>
            <ThemedText style={styles.wordmarkText}>CricSim</ThemedText>
          </View>
          <Pressable
            onPress={() => setAccountVisible(true)}
            style={[styles.avatar, { backgroundColor: theme.bgCard, borderColor: theme.border }]}>
            <ThemedText style={styles.avatarText}>{initials(user?.display_name ?? null)}</ThemedText>
          </Pressable>
        </View>
        <AccountSheet visible={accountVisible} onClose={() => setAccountVisible(false)} />

        <ScrollView contentContainerStyle={[styles.content, contentContainerStyle, { paddingBottom: bottomInset }]} showsVerticalScrollIndicator={false}>
          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Your Careers
          </ThemedText>

          {loading && (
            <View style={styles.loading}>
              <ActivityIndicator color={theme.green} />
            </View>
          )}

          {!loading && error && (
            <Pressable onPress={refresh}>
              <ThemedText themeColor="red">Failed to load careers. Tap to retry.</ThemedText>
            </Pressable>
          )}

          {!loading && !error && (
            <View style={styles.list}>
              {careers.map((career) => (
                <CareerCard
                  key={career.id}
                  career={career}
                  active={career.id === activeCareerId}
                  onPress={() => enterCareer(career.id)}
                  onDelete={() => confirmDelete(career.id, career.name)}
                />
              ))}

              <Pressable
                onPress={() => router.push('/new-career')}
                style={({ pressed }) => [
                  styles.newCareerTile,
                  { borderColor: theme.border },
                  pressed && styles.pressed,
                ]}>
                <View style={[styles.plus, { backgroundColor: theme.bgElevated }]}>
                  <ThemedText style={[styles.plusText, { color: theme.green }]}>＋</ThemedText>
                </View>
                <View style={styles.newCareerMeta}>
                  <ThemedText style={styles.newCareerLabel}>Start New Career</ThemedText>
                  <ThemedText themeColor="textDim" style={styles.newCareerSub}>
                    Choose a franchise, difficulty &amp; draft mode
                  </ThemedText>
                </View>
              </Pressable>

              {/* Roster CSV acts on the ACTIVE career, so it only appears once
                  one is selected — otherwise "export the roster" has no subject. */}
              {activeCareer && (
                <RosterCsvCard
                  careerId={activeCareer.id}
                  careerName={activeCareer.name}
                  onImported={refresh}
                />
              )}
            </View>
          )}
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
  },
  appbar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.three,
    paddingVertical: Spacing.two,
  },
  wordmark: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.two,
  },
  mark: {
    fontSize: 20,
  },
  wordmarkText: {
    fontWeight: '800',
    fontSize: 16,
    letterSpacing: -0.2,
  },
  avatar: {
    width: 32,
    height: 32,
    borderRadius: Radius.pill,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: {
    fontWeight: '700',
    fontSize: 12,
  },
  content: {
    paddingHorizontal: Spacing.three,
    paddingTop: Spacing.one,
    paddingBottom: ContentBottomInset,
    gap: Spacing.two,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 2,
  },
  loading: {
    paddingVertical: Spacing.five,
    alignItems: 'center',
  },
  list: {
    gap: 10,
  },
  pressed: {
    opacity: 0.7,
  },
  newCareerTile: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.three,
    borderRadius: Radius.md,
    borderWidth: 1,
    borderStyle: 'dashed',
    padding: Spacing.three,
  },
  plus: {
    width: 38,
    height: 38,
    borderRadius: Radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  plusText: {
    fontSize: 18,
    fontWeight: '700',
  },
  newCareerMeta: {
    flex: 1,
    gap: 2,
  },
  newCareerLabel: {
    fontWeight: '700',
    fontSize: 13.5,
  },
  newCareerSub: {
    fontSize: 11.5,
  },
});
