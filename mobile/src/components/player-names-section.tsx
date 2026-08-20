/**
 * Settings section for substituting your own player names.
 *
 * Two columns — the shipped name and what you want to call the player — so the
 * file is trivial to edit and there is nothing to get wrong beyond the names
 * themselves. Overrides are stored against the account and applied when a NEW
 * career is created; that limitation is stated in the popup rather than left
 * for the user to discover, because "I renamed everyone and nothing changed"
 * is the obvious way to be confused by this.
 *
 * The instructions live in an Alert shown after each action rather than inline:
 * the account sheet is 280pt wide, and a paragraph of standing help crowded out
 * everything around it for a feature most users touch once.
 */
import { useState } from 'react';
import { Alert, StyleSheet, View } from 'react-native';
import { File, Paths } from 'expo-file-system';

import { ApiError } from '@/api/client';
import { playerNamesApi } from '@/api/playerNames';
import { ThemedText } from '@/components/themed-text';
import { Button } from '@/components/ui/button';
import { Spacing } from '@/constants/theme';

/**
 * expo-sharing and expo-document-picker are NATIVE modules: they exist only in
 * a binary built after they were added. A static import throws while the module
 * graph is loading — before any component can catch it — which takes down the
 * whole screen. Loading them on demand keeps a stale binary (or a JS-only OTA
 * update that runs ahead of the native build) contained to a message.
 */
const MISSING_NATIVE = 'This needs a newer version of the app. Update and try again.';

/** Where an exported file lands, in the words the Files app itself uses. */
const IN_FILES_APP = 'Files → On My iPhone → CricSim → player-names.csv';

const EDIT_STEPS =
  `Open it in a spreadsheet and edit the "name" column. Leave "player_key" ` +
  `alone — it is how each row is matched to a player.\n\n` +
  `Then come back here and tap Import names.`;

/** Applies to new careers only — the one thing users are surprised by. */
const NEW_CAREERS_ONLY =
  'Custom names apply to new careers. Careers you have already started keep their current names.';

function loadNativeModule<T>(load: () => T): T | null {
  try {
    return load();
  } catch {
    return null;
  }
}

export function PlayerNamesSection() {
  const [busy, setBusy] = useState<'export' | 'import' | null>(null);

  const onExport = async () => {
    setBusy('export');
    try {
      const csv = await playerNamesApi.exportCsv();
      // Documents, not cache: the app declares UIFileSharingEnabled, so this
      // directory IS the app's folder in the Files app. iOS has no shared
      // Downloads folder an app may write to, so this is the closest thing to
      // "the file is now on my device" — and unlike cache, iOS will not
      // reclaim it. The share sheet below is the way to get it anywhere else.
      const file = new File(Paths.document, 'player-names.csv');
      // Replace any file left by a previous export rather than appending.
      if (file.exists) file.delete();
      file.create();
      file.write(csv);

      // Deliberate: a static import of a missing native module crashes the screen.
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      const Sharing = loadNativeModule(() => require('expo-sharing') as typeof import('expo-sharing'));
      // The file is already written, so a missing or unavailable share sheet is
      // not a failed export — it only costs the shortcut to Downloads/AirDrop.
      if (Sharing && (await Sharing.isAvailableAsync())) {
        await Sharing.shareAsync(file.uri, {
          mimeType: 'text/csv',
          dialogTitle: 'Export player names',
          UTI: 'public.comma-separated-values-text',
        });
      }

      Alert.alert(
        'Player list exported',
        `Saved to ${IN_FILES_APP}\n\n${EDIT_STEPS}\n\n${NEW_CAREERS_ONLY}`
      );
    } catch (err) {
      Alert.alert('Export failed', err instanceof Error ? err.message : 'Please try again.');
    } finally {
      setBusy(null);
    }
  };

  const onImport = async () => {
    const DocumentPicker = loadNativeModule(
      // Deliberate: a static import of a missing native module crashes the screen.
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      () => require('expo-document-picker') as typeof import('expo-document-picker')
    );
    if (!DocumentPicker) {
      Alert.alert('Import names', MISSING_NATIVE);
      return;
    }
    try {
      const picked = await DocumentPicker.getDocumentAsync({
        // CSV only: everything else is greyed out in the Files browser. iOS
        // maps this to the system UTI public.comma-separated-values-text, so
        // any real .csv — ours, Numbers', Excel's — stays selectable.
        type: 'text/csv',
        copyToCacheDirectory: true,
      });
      if (picked.canceled || !picked.assets?.length) return;

      setBusy('import');
      const csv = await new File(picked.assets[0].uri).text();
      const { renamed } = await playerNamesApi.importCsv(csv);

      Alert.alert(
        renamed === 0 ? 'Custom names cleared' : `${renamed} name${renamed === 1 ? '' : 's'} saved`,
        renamed === 0
          ? 'New careers will use the built-in names.'
          : `Start a new career to see them.\n\n${NEW_CAREERS_ONLY}`
      );
    } catch (err) {
      // Nothing was saved — the file is rejected in full if any row is bad, so
      // list every problem and the user fixes it in one pass.
      const rows = err instanceof ApiError ? (err.details ?? []) : [];
      const shown = rows.slice(0, 6).map((line) => `• ${line}`);
      if (rows.length > shown.length) shown.push(`…and ${rows.length - shown.length} more`);
      Alert.alert(
        'Import failed',
        [err instanceof Error ? err.message : 'Please try again.', ...shown].join('\n')
      );
    } finally {
      setBusy(null);
    }
  };

  return (
    <View>
      <ThemedText themeColor="textFaint" style={styles.sectionLabel}>
        PLAYER NAMES
      </ThemedText>
      <ThemedText themeColor="textDim" style={styles.help}>
        Rename any player in the game using a spreadsheet.
      </ThemedText>

      {/* Stacked, not side by side: this sheet is 280pt wide, and two buttons
          in a row truncated to "Export na…" / "Import na…". */}
      <Button
        label="Export names"
        variant="primary"
        style={styles.button}
        loading={busy === 'export'}
        disabled={busy !== null}
        onPress={onExport}
      />
      <Button
        label="Import names"
        variant="secondary"
        style={styles.button}
        loading={busy === 'import'}
        disabled={busy !== null}
        onPress={onImport}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginTop: Spacing.three,
    marginBottom: Spacing.two,
  },
  help: { fontSize: 12.5, lineHeight: 18, marginBottom: Spacing.two },
  // Button defaults to flex: 1 for side-by-side rows; stacked it must size to
  // its own content instead of stretching to fill the column.
  button: { flex: 0, marginBottom: Spacing.two },
});
