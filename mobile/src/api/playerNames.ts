import { apiClient } from '@/api/client';

export interface PlayerNamesImportResult {
  /** How many players the saved file renames. */
  renamed: number;
}

export const playerNamesApi = {
  /** Every player name in the game, with any override already applied. */
  exportCsv: () =>
    apiClient.get<string>('/auth/me/player-names.csv', { responseType: 'text' }),

  /**
   * Save name overrides. They apply to careers created from now on — an
   * existing career's names are already baked into its saved lineups and
   * scorecards.
   *
   * A rejected file throws an ApiError whose `details` lists every problem, so
   * the UI can show them all at once.
   */
  importCsv: (csv: string) =>
    apiClient.post<PlayerNamesImportResult>('/auth/me/player-names.csv', { csv }),
};
