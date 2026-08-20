/**
 * Export / import the whole-league roster as a CSV the user edits in a
 * spreadsheet — their own player names and their own ratings.
 *
 * Export writes the file to the cache directory and hands it to the share
 * sheet, because a mobile app has nowhere else to put a file the user then
 * opens in another app. Import goes through the document picker.
 */
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { File, Paths } from 'expo-file-system';

import { ApiError } from '@/api/client';
import { rosterApi, type RosterImportReport } from '@/api/roster';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

/**
 * expo-sharing and expo-document-picker are NATIVE modules, so they only exist
 * in a binary built after they were added. Importing them at the top of the
 * file makes a missing module throw while the module graph is still loading,
 * which takes down the whole screen — the home screen died with "Cannot find
 * native module 'ExpoDocumentPicker'" plus three cascading render errors.
 *
 * Loading them on demand keeps the failure contained to the button that needs
 * them, so an older binary (or a JS-only OTA update that runs ahead of the
 * native build) degrades to a clear message instead of a blank screen.
 */
const MISSING_NATIVE =
  'This needs a newer version of the app. Update from the App Store and try again.';

function loadNativeModule<T>(load: () => T): T | null {
  try {
    return load();
  } catch {
    return null;
  }
}

export function RosterCsvCard({
  careerId,
  careerName,
  accent,
  onImported,
}: {
  careerId: string;
  careerName?: string | null;
  accent?: string;
  /** Called after a successful import so the caller can refetch the league. */
  onImported: () => void;
}) {
  const theme = useTheme();
  const [busy, setBusy] = useState<'export' | 'import' | null>(null);
  const [report, setReport] = useState<RosterImportReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorRows, setErrorRows] = useState<string[]>([]);

  const reset = () => {
    setReport(null);
    setError(null);
    setErrorRows([]);
  };

  const onExport = async () => {
    reset();
    // Deliberate: a static import of a missing native module crashes the screen.
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const Sharing = loadNativeModule(() => require('expo-sharing') as typeof import('expo-sharing'));
    if (!Sharing) {
      setError(MISSING_NATIVE);
      return;
    }
    setBusy('export');
    try {
      const csv = await rosterApi.exportCsv(careerId);
      const safeName = (careerName || 'career').replace(/[^\w-]+/g, '-');
      const file = new File(Paths.cache, `${safeName}-roster.csv`);
      // Overwrite any file left by a previous export rather than appending to it.
      if (file.exists) file.delete();
      file.create();
      file.write(csv);

      if (!(await Sharing.isAvailableAsync())) {
        setError('Sharing is not available on this device.');
        return;
      }
      await Sharing.shareAsync(file.uri, {
        mimeType: 'text/csv',
        dialogTitle: 'Export roster',
        UTI: 'public.comma-separated-values-text',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setBusy(null);
    }
  };

  const onImport = async () => {
    reset();
    const DocumentPicker = loadNativeModule(
      // Deliberate: a static import of a missing native module crashes the screen.
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      () => require('expo-document-picker') as typeof import('expo-document-picker')
    );
    if (!DocumentPicker) {
      setError(MISSING_NATIVE);
      return;
    }
    try {
      const picked = await DocumentPicker.getDocumentAsync({
        // Some providers hand back a generic type for .csv, so text/* is
        // accepted too rather than hiding the user's own file from them.
        type: ['text/csv', 'text/comma-separated-values', 'text/plain'],
        copyToCacheDirectory: true,
      });
      if (picked.canceled || !picked.assets?.length) return;

      setBusy('import');
      const csv = await new File(picked.assets[0].uri).text();
      const result = await rosterApi.importCsv(careerId, csv);
      setReport(result);
      onImported();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
        setErrorRows(err.details ?? []);
      } else {
        setError(err instanceof Error ? err.message : 'Import failed');
      }
    } finally {
      setBusy(null);
    }
  };

  return (
    <Card>
      <ThemedText style={styles.title}>Roster CSV</ThemedText>
      <ThemedText themeColor="textDim" style={styles.help}>
        Export every player in this career, edit names and ratings in a spreadsheet, then import
        the file back. Leave the <ThemedText style={styles.mono}>player_key</ThemedText> column
        alone — it is how each row is matched back to a player.
      </ThemedText>

      <View style={styles.row}>
        <Button
          label={busy === 'export' ? 'Exporting…' : 'Export roster'}
          variant="primary"
          accentColor={accent}
          disabled={busy !== null}
          onPress={onExport}
        />
        <Button
          label={busy === 'import' ? 'Importing…' : 'Import roster'}
          variant="ghost"
          accentColor={accent}
          disabled={busy !== null}
          onPress={onImport}
        />
      </View>

      {busy && <ActivityIndicator color={theme.green} style={styles.spinner} />}

      {report && (
        <View style={[styles.result, { borderColor: theme.border }]}>
          <ThemedText style={styles.resultTitle}>Import applied</ThemedText>
          <ThemedText themeColor="textDim" style={styles.resultLine}>
            {report.renamed} renamed · {report.rerated} re-rated · {report.unchanged} unchanged
          </ThemedText>
          {report.ignored_team_changes > 0 && (
            <ThemedText themeColor="textDim" style={styles.resultLine}>
              {report.ignored_team_changes} team change
              {report.ignored_team_changes === 1 ? '' : 's'} ignored — players cannot be moved
              between teams from a CSV.
            </ThemedText>
          )}
        </View>
      )}

      {error && (
        <View style={[styles.result, { borderColor: theme.red }]}>
          <ThemedText themeColor="red" style={styles.resultTitle}>
            {error}
          </ThemedText>
          {/* Nothing was applied — the whole file is rejected if any row is bad,
              so the user fixes it once and re-imports. */}
          {errorRows.slice(0, 8).map((line, i) => (
            <ThemedText key={i} themeColor="textDim" style={styles.resultLine}>
              • {line}
            </ThemedText>
          ))}
          {errorRows.length > 8 && (
            <ThemedText themeColor="textFaint" style={styles.resultLine}>
              …and {errorRows.length - 8} more
            </ThemedText>
          )}
        </View>
      )}
    </Card>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 15, fontWeight: '800' },
  help: { fontSize: 12, lineHeight: 17, marginTop: 4 },
  mono: { fontFamily: 'ui-monospace', fontSize: 11 },
  row: { flexDirection: 'row', gap: Spacing.two, marginTop: Spacing.three, flexWrap: 'wrap' },
  spinner: { marginTop: Spacing.two },
  result: {
    marginTop: Spacing.three,
    padding: Spacing.two,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: Radius.sm,
    gap: 2,
  },
  resultTitle: { fontSize: 12.5, fontWeight: '700' },
  resultLine: { fontSize: 11.5, lineHeight: 16 },
});
