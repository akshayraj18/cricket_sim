import { Alert, Platform } from 'react-native';

import { seasonApi } from '@/api/season';
import { LeaguePayload } from '@/api/types';

/**
 * Shows a native rename prompt for a team or player and applies it via the
 * roster-editor endpoint. Renames are global to the career (they actually
 * change the name everywhere), so the caller refreshes the league payload with
 * the returned result. Used by the "Edit Names" mode on the Squad and Stats
 * tabs to let users localize their league (e.g. restore real names).
 */
export function promptRename({
  careerId,
  kind,
  currentName,
  onRenamed,
  onError,
}: {
  careerId: string;
  kind: 'team' | 'player';
  currentName: string;
  onRenamed: (payload: LeaguePayload) => void;
  onError: (err: unknown) => void;
}) {
  const label = kind === 'team' ? 'Rename Team' : 'Rename Player';

  const apply = async (next?: string) => {
    const trimmed = (next ?? '').trim();
    if (!trimmed || trimmed === currentName) return;
    try {
      onRenamed(await seasonApi.rename(careerId, kind, currentName, trimmed));
    } catch (err) {
      onError(err);
    }
  };

  // Alert.prompt is iOS-only; on Android we'd need a custom modal. The app
  // ships iOS-first, so use the native prompt where available.
  if (Platform.OS === 'ios' && typeof Alert.prompt === 'function') {
    Alert.prompt(
      label,
      'Enter a new name. This changes it everywhere in this career.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Save', onPress: apply },
      ],
      'plain-text',
      currentName
    );
  } else {
    // Fallback: no inline text entry available — surface a friendly message.
    Alert.alert(label, 'Renaming is available on iOS.');
  }
}
