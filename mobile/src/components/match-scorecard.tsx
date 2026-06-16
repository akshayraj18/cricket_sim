import { StyleSheet, View } from 'react-native';

import { MatchCard } from '@/api/types';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Pill } from '@/components/ui/pill';
import { getContrastText, Radius, Spacing, TeamColors, teamAbbr } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

import { BattingCardTable, BowlingCardTable } from './live-match-hub';

/**
 * Build the Player of the Match's match figures from the innings cards:
 * batting "R (B)" if they batted, bowling "W/R (O)" if they bowled, both
 * joined with "·" if they did both. Returns "" if no figures are found.
 */
function motmFigures(card: MatchCard): string {
  const name = card.motm;
  if (!name) return '';
  let bat: string | null = null;
  let bowl: string | null = null;
  for (const inn of card.innings) {
    const batLine = (inn.full_batting?.length ? inn.full_batting : inn.batting).find((b) => b.name === name);
    if (batLine && batLine.balls > 0) bat = `${batLine.runs} (${batLine.balls})`;
    const bowlLine = (inn.full_bowling?.length ? inn.full_bowling : inn.bowling).find((b) => b.name === name);
    if (bowlLine && (bowlLine.balls ?? 0) > 0) bowl = `${bowlLine.wickets}/${bowlLine.runs} (${bowlLine.overs})`;
  }
  return [bat, bowl].filter(Boolean).join(' · ');
}

export function MatchScorecard({
  card,
  onComplete,
  canComplete,
  accent,
}: {
  card: MatchCard;
  onComplete?: () => void;
  /** True for an active live-match final scorecard (shows "Return to Season"); false for a historic scorecard. */
  canComplete: boolean;
  accent?: string;
}) {
  const theme = useTheme();
  // Color the scoreboard with the winning team's color, regardless of which
  // team the user controls — so a CSK vs SRH result reads as a CSK-colored
  // card even if the user's team is something else.
  const winnerColor = TeamColors[card.winner]?.primary ?? accent ?? theme.green;
  const scoreboardText = getContrastText(winnerColor);
  const scoreboardTextDim = scoreboardText === '#ffffff' ? 'rgba(255,255,255,0.85)' : 'rgba(26,20,4,0.7)';

  return (
    <View style={styles.container}>
      <View style={[styles.scoreboard, { backgroundColor: winnerColor }]}>
        <ThemedText style={[styles.scoreboardSmall, { color: scoreboardTextDim }]}>
          {card.venue ? `${card.venue} · ` : ''}Toss: {card.toss}
        </ThemedText>
        <ThemedText style={[styles.scoreboardLine, { color: scoreboardText }]}>
          {teamAbbr(card.winner)} {card.margin}
        </ThemedText>
        {card.motm ? (
          <ThemedText style={[styles.scoreboardMessage, { color: scoreboardText }]}>
            Player of the Match: {card.motm}
            {motmFigures(card) ? ` — ${motmFigures(card)}` : ''}
          </ThemedText>
        ) : null}
        {onComplete && (
          <Button
            label={canComplete ? 'Return to Season' : 'Back to Match Centre'}
            variant="secondary"
            onPress={onComplete}
            style={styles.completeButton}
          />
        )}
      </View>

      {card.impact_subs?.length ? (
        <Card>
          <ThemedText style={styles.panelTitle}>Impact Subs</ThemedText>
          <View style={styles.pillRow}>
            {card.impact_subs.map((sub, i) => (
              <Pill key={i} label={String(sub)} />
            ))}
          </View>
        </Card>
      ) : null}

      {card.innings.map((inn, i) => (
        <Card key={i}>
          <ThemedText style={styles.panelTitle}>
            {teamAbbr(inn.team)} {inn.score}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.subtitle}>
            vs {teamAbbr(inn.against)}
            {inn.impact_sub ? ` · Impact: ${inn.impact_sub}` : ''}
          </ThemedText>
          <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
            Batting
          </ThemedText>
          <BattingCardTable bats={inn.full_batting?.length ? inn.full_batting : inn.batting} />
          <ThemedText themeColor="textFaint" style={[styles.sectionLabel, { marginTop: Spacing.three }]}>
            Bowling
          </ThemedText>
          <BowlingCardTable bowls={inn.full_bowling?.length ? inn.full_bowling : inn.bowling} />
        </Card>
      ))}

      {card.super_over?.innings?.length ? (
        <Card>
          <ThemedText style={styles.panelTitle}>Super Over</ThemedText>
          {card.super_over.innings.map((inn, i) => (
            <View key={i} style={styles.superOverInnings}>
              <ThemedText style={styles.subtitleStrong}>
                {teamAbbr(inn.team)} {inn.score}
              </ThemedText>
              <View style={styles.overLogBalls}>
                {inn.events.map((e, j) => (
                  <View
                    key={j}
                    style={[
                      styles.ballChip,
                      { borderColor: theme.border, backgroundColor: e.kind === 'wicket' ? theme.red : theme.badgeBg },
                    ]}>
                    <ThemedText style={[styles.ballChipText, e.kind === 'wicket' && { color: '#fff' }]}>
                      {e.label}
                    </ThemedText>
                  </View>
                ))}
              </View>
              <BattingCardTable bats={inn.batting.map((b) => ({ ...b, dismissal: '' }))} />
              <BowlingCardTable bowls={inn.bowling.map((b) => ({ ...b, maidens: 0 }))} />
            </View>
          ))}
        </Card>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: Spacing.three,
  },
  scoreboard: {
    borderRadius: Radius.md,
    padding: Spacing.three,
    gap: 4,
  },
  scoreboardSmall: {
    fontSize: 12,
    fontWeight: '600',
  },
  scoreboardLine: {
    fontSize: 24,
    fontWeight: '800',
  },
  scoreboardMessage: {
    fontSize: 13,
  },
  completeButton: {
    marginTop: Spacing.two,
    alignSelf: 'flex-start',
    flex: 0,
    paddingHorizontal: Spacing.four,
  },
  panelTitle: {
    fontSize: 15,
    fontWeight: '800',
    marginBottom: 2,
  },
  subtitle: {
    fontSize: 12,
    marginBottom: Spacing.two,
  },
  subtitleStrong: {
    fontSize: 14,
    fontWeight: '800',
    marginBottom: 6,
  },
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: 4,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  superOverInnings: {
    marginBottom: Spacing.three,
  },
  overLogBalls: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: Spacing.two,
  },
  ballChip: {
    minWidth: 26,
    height: 26,
    borderRadius: Radius.sm,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  ballChipText: {
    fontSize: 11,
    fontWeight: '800',
  },
});
