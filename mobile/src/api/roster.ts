import { apiClient } from '@/api/client';

/** What the server did with an imported roster file. */
export interface RosterImportReport {
  renamed: number;
  rerated: number;
  unchanged: number;
  /** Rows whose `team` column was edited — team moves are not supported. */
  ignored_team_changes: number;
  errors: string[];
}

export const rosterApi = {
  /** The career's whole-league roster as CSV text. */
  exportCsv: (careerId: string) =>
    apiClient.get<string>(`/careers/${careerId}/roster.csv`, { responseType: 'text' }),

  /**
   * Apply an edited roster CSV.
   *
   * Rejected files throw an ApiError whose `details` lists every problem, so the
   * UI can show all of them at once rather than making the user fix one per try.
   */
  importCsv: (careerId: string, csv: string) =>
    apiClient.post<RosterImportReport>(`/careers/${careerId}/roster.csv`, { csv }),
};
