/**
 * Settings section for substituting your own player names.
 *
 * Two columns — the shipped name and what you want to call the player — so the
 * file is trivial to edit and there is nothing to get wrong beyond the names
 * themselves. Overrides are stored against the account and applied when a NEW
 * career is created; that limitation is stated in the UI rather than left for
 * the user to discover, because "I renamed everyone and nothing changed" is the
 * obvious way to be confused by this.
 */
import { useState } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { File, Paths } from 'expo-file-system';

import { ApiError } from '@/api/client';
import { playerNamesApi } from '@/api/playerNames';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Radius, Spacing } from '@/constants/theme';
import { useTheme } from '@/hooks/use-theme';

/**
 * expo-sharing and expo-document-picker are NATIVE modules: they exist only in
 * a binary built after they were added. A static import throws while the module
 * graph is loading — before any component can catch it — which takes down the
 * whole screen. Loading them on demand keeps a stale binary (or a JS-only OTA
 * update that runs ahead of the native build) contained to a message.
 */
const MISSING_NATIVE = 'This needs a newer version of the app. Update and try again.';

function loadNativeModule<T>(load: () => T): T | null {
  try {
    return load();
  } catch {
    return null;
  }
}

export function PlayerNamesSection() {
  const theme = useTheme();
  const [busy, setBusy] = useState<'export' | 'import' | null>(null);
  const [saved, setSaved] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorRows, setErrorRows] = useState<string[]>([]);

  const reset = () => {
    setSaved(null);
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
      const csv = await playerNamesApi.exportCsv();
      const file = new File(Paths.cache, 'player-names.csv');
      // Replace any file left by a previous export rather than appending.
      if (file.exists) file.delete();
      file.create();
      file.write(csv);

      if (!(await Sharing.isAvailableAsync())) {
        setError('Sharing is not available on this device.');
        return;
      }
      await Sharing.shareAsync(file.uri, {
        mimeType: 'text/csv',
        dialogTitle: 'Export player names',
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
        // Some providers report a generic type for .csv; accepting text/plain
        // avoids hiding the user's own file from them in the picker.
        type: ['text/csv', 'text/comma-separated-values', 'text/plain'],
        copyToCacheDirectory: true,
      });
      if (picked.canceled || !picked.assets?.length) return;

      setBusy('import');
      const csv = await new File(picked.assets[0].uri).text();
      const result = await playerNamesApi.importCsv(csv);
      setSaved(result.renamed);
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
    <View style={styles.section}>
      <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
        PLAYER NAMES
      </ThemedText>
      <ThemedText themeColor="textDim" style={styles.help}>
        Export the player list, edit the <ThemedText style={styles.mono}>name</ThemedText> column in
        a spreadsheet, then import it back. Leave{' '}
        <ThemedText style={styles.mono}>player_key</ThemedText> alone — it is how each row is
        matched to a player.
      </ThemedText>
      <ThemedText themeColor="textFaint" style={styles.caveat}>
        Applies to new careers. Careers you have already started keep their current names.
      </ThemedText>

      <View style={styles.row}>
        <Button
          label={busy === 'export' ? 'Exporting…' : 'Export names'}
          variant="primary"
          disabled={busy !== null}
          onPress={onExport}
        />
        <Button
          label={busy === 'import' ? 'Importing…' : 'Import names'}
          variant="ghost"
          disabled={busy !== null}
          onPress={onImport}
        />
      </View>

      {busy && <ActivityIndicator color={theme.green} style={styles.spinner} />}

      {saved !== null && (
        <View style={[styles.result, { borderColor: theme.border }]}>
          <ThemedText style={styles.resultTitle}>
            {saved === 0 ? 'Custom names cleared' : `${saved} custom name${saved === 1 ? '' : 's'} saved`}
          </ThemedText>
          <ThemedText themeColor="textDim" style={styles.resultLine}>
            {saved === 0
              ? 'New careers will use the built-in names.'
              : 'Start a new career to see them.'}
          </ThemedText>
        </View>
      )}

      {error && (
        <View style={[styles.result, { borderColor: theme.red }]}>
          <ThemedText themeColor="red" style={styles.resultTitle}>
            {error}
          </ThemedText>
          {/* Nothing was saved — the file is rejected in full if any row is bad,
              so the user fixes it once rather than one row per attempt. */}
          {errorRows.slice(0, 6).map((line, i) => (
            <ThemedText key={i} themeColor="textDim" style={styles.resultLine}>
              • {line}
            </ThemedText>
          ))}
          {errorRows.length > 6 && (
            <ThemedText themeColor="textFaint" style={styles.resultLine}>
              …and {errorRows.length - 6} more
            </ThemedText>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  section: { gap: 4 },
  sectionLabel: { fontSize: 11, fontWeight: '700', letterSpacing: 1 },
  help: { fontSize: 12, lineHeight: 17 },
  caveat: { fontSize: 11, lineHeight: 15, marginTop: 2 },
  mono: { fontFamily: 'ui-monospace', fontSize: 11 },
  row: { flexDirection: 'row', gap: Spacing.two, marginTop: Spacing.two, flexWrap: 'wrap' },
  spinner: { marginTop: Spacing.two },
  result: {
    marginTop: Spacing.two,
    padding: Spacing.two,
    borderWidth: StyleSheet.hairlineWidth,
    borderRadius: Radius.sm,
    gap: 2,
  },
  resultTitle: { fontSize: 12.5, fontWeight: '700' },
  resultLine: { fontSize: 11.5, lineHeight: 16 },
});
