// Mirrors backend/app/auth/schemas.py, backend/app/careers/schemas.py

export interface UserOut {
  id: string;
  email: string | null;
  display_name: string | null;
  has_apple_link: boolean;
  has_google_link: boolean;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: UserOut;
  tokens: TokenPair;
}

export type Difficulty = 'easy' | 'medium' | 'hard';
export type DraftPoolType = 'current' | 'alltime' | 'rosters2026' | 'international_current';
export type Competition = 'ipl' | 'international';
export type MatchFormat = 't20' | 'odi' | 'test';
export type CareerMode = 'league' | 'tournament' | 'bilateral';

export interface CareerCreateRequest {
  name: string;
  user_team_name: string;
  difficulty?: Difficulty;
  draft_pool_type?: DraftPoolType;
  competition?: Competition;
  match_format?: MatchFormat;
  career_mode?: CareerMode;
  series_length?: number | null;
  opponent_name?: string | null;
}

export interface CareerSummary {
  id: string;
  name: string;
  user_team_name: string;
  difficulty: Difficulty;
  draft_pool_type: DraftPoolType;
  competition: Competition;
  match_format: MatchFormat;
  career_mode: CareerMode;
  series_length: number | null;
  phase: string;
  season_year: number;
  completed_seasons: number;
  status_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface CareerDetail extends CareerSummary {
  state: Record<string, unknown>;
}

export interface MatchSummary {
  id: string;
  season_year: number;
  round_num: number | null;
  stage: string;
  team1_name: string;
  team2_name: string;
  toss_winner: string | null;
  toss_decision: string | null;
  result_summary: string | null;
  winner_name: string | null;
  played_at: string;
}

export interface MatchDetail extends MatchSummary {
  team1_score: Record<string, unknown> | null;
  team2_score: Record<string, unknown> | null;
  motm_player_id: string | null;
  motm_player_name: string | null;
}

export interface MatchBallOut {
  innings: number;
  over_num: number;
  ball_num: number;
  batter_id: string | null;
  batter_name: string | null;
  bowler_id: string | null;
  bowler_name: string | null;
  runs: number;
  extras: Record<string, unknown> | null;
  wicket: Record<string, unknown> | null;
  commentary: string | null;
}

export interface MatchBallsOut {
  match_id: string;
  balls: MatchBallOut[];
}

// Season

export interface LeadershipRequest {
  captain: string;
  vice: string;
  wicketkeeper?: string;
}

export interface PresetsRequest {
  batting_order?: string[];
  bowling_order?: string[];
  starting_xi?: string[] | null;
  impact_sub_name?: string | null;
  wicketkeeper?: string;
}

export interface RetentionRequest {
  players: string[];
}

export interface MatchCompleteResponse {
  phase: string;
  round_num: number;
  season_year: number;
  status_message: string | null;
}

// Live match actions — body shapes mirror apply_action() in
// backend/app/live_match/service.py, which forwards to LiveMatch methods.

export interface TossActionBody {
  decision: string;
}

export interface LineupActionBody {
  xi?: string[];
  batting_order?: string[];
  bowling_order?: string[];
  intents?: Record<string, unknown>;
  save?: boolean;
  context?: 'batting' | 'bowling';
  wicketkeeper?: string;
}

export interface PlayOverActionBody {
  bowler?: string;
  balls?: number;
  stop_on_wicket?: boolean;
}

export interface AggressionActionBody {
  batting?: Record<string, unknown>;
  bowling?: Record<string, unknown>;
}

export interface NextBatterActionBody {
  name: string;
}

export interface SuperOverLineupActionBody {
  batters?: string[];
  bowler?: string;
}

export interface ImpactSubActionBody {
  out?: string;
  in?: string;
}

// League payload — mirrors LeagueState.payload() in
// packages/sim_engine/src/cricket_sim_engine/sim/league_state.py.

/** Mirrors LeagueState.player_dict(). */
export interface PlayerDict {
  name: string;
  role: string;
  age: number;
  team: string;
  base_ovr: number;
  ovr: number;
  bat: number;
  bowl: number;
  form: number;
  overseas: boolean;
  ovr_progression: string;
  bat_progression: string;
  bowl_progression: string;
  batting_hand: string;
  bowling_hand: string;
  preferred_position: number;
  batting_archetype: string;
  bowling_phase: string;
  bowling_type: string;
  allrounder_style: string;
  strengths: string;
  weaknesses: string;
  phase_fit_powerplay: string;
  phase_fit_middle: string;
  phase_fit_death: string;
  // batting stats
  runs: number;
  balls: number;
  outs: number;
  avg: number;
  sr: number;
  hs: number;
  hs_against: string;
  fours: number;
  sixes: number;
  boundaries: number;
  fifties: number;
  hundreds: number;
  // bowling stats
  wickets: number;
  runs_conceded: number;
  balls_bowled: number;
  econ: number;
  bowling_avg: number;
  bowling_sr: number;
  maidens: number;
  motm: number;
  best_bowling: string;
  best_bowling_against: string;
  // fielding
  catches: number;
  stumpings: number;
  runouts: number;
  games: number;
  team_wins: number;
  mvp: number;
  // present on live-match bowler dicts (live_bowler_dict)
  match_econ?: number | string;
  match_overs?: string;
  match_wickets?: number;
  [key: string]: unknown;
}

/** Mirrors LeagueState.team_dict(). */
export interface TeamDict {
  name: string;
  abbr: string;
  home: string;
  primary: string;
  accent: string;
  points: number;
  wins: number;
  losses: number;
  played: number;
  nrr: number;
  captain: string;
  vice_captain: string;
  saved_batting_order: string[];
  saved_bowling_order: string[];
  starting_xi: string[];
  impact_sub_name: string;
  saved_wicketkeeper: string;
  suggested_batting_order: string[];
  suggested_bowling_order: string[];
  roster: PlayerDict[];
}

/** One fixture: a (team1, team2) tuple for a round. */
export type ScheduleFixture = [string, string];

/** One round of fixtures. */
export type ScheduleRound = ScheduleFixture[];

export interface PlayoffMatch {
  name: string;
  team1: string;
  team2: string;
  status: 'pending' | 'locked' | 'complete';
  winner?: string;
  loser?: string;
}

export interface BatStatsLine {
  name: string;
  dismissal: string;
  runs: number;
  balls: number;
  fours: number;
  sixes: number;
  [key: string]: unknown;
}

export interface BowlStatsLine {
  name: string;
  runs: number;
  balls: number;
  wickets: number;
  maidens: number;
  overs: string;
  econ: number;
  [key: string]: unknown;
}

/** Mirrors LeagueState.innings_card(). */
export interface InningsCard {
  team: string;
  against: string;
  score: string;
  batting: BatStatsLine[];
  bowling: BowlStatsLine[];
  full_batting: BatStatsLine[];
  full_bowling: BowlStatsLine[];
  impact_sub: string;
  over_log: OverLogEntry[];
}

/** Mirrors one entry of LiveMatch.simulate_super_over_innings(). */
export interface SuperOverInningsCard {
  team: string;
  runs: number;
  wickets: number;
  balls: number;
  bowler: string;
  batting: { name: string; runs: number; balls: number; fours: number; sixes: number }[];
  bowling: { name: string; runs: number; wickets: number; balls: number; overs: string; econ: number }[];
  events: OverEvent[];
  score: string;
}

export interface SuperOverCard {
  batting_first: string;
  batting_second: string;
  innings: SuperOverInningsCard[];
  winner: string;
  message: string;
}

/** One ball event, as produced by LiveMatch.play_ball()/over_log entries. */
export interface OverEvent {
  kind: 'wicket' | 'runs' | 'innings_end';
  label: string;
  runs?: number;
  description?: string;
  batter?: string;
  bowler?: string;
  [key: string]: unknown;
}

/** One completed over, as appended to `over_log`. */
export interface OverLogEntry {
  over: number;
  bowler: string;
  events: OverEvent[];
  runs: number;
}

/** Mirrors the `card` built in LiveMatch (match_log / fixture_results entries). */
export interface MatchCard {
  round: number;
  stage: string;
  team1: string;
  team2: string;
  venue: string;
  toss: string;
  winner: string;
  margin: string;
  summary: string;
  motm: string;
  innings: InningsCard[];
  impact_subs: unknown[];
  super_over: SuperOverCard | null;
}

/** Mirrors LeagueState.archive_season() entries. */
export interface SeasonHistoryEntry {
  season: number;
  champion: string;
  runner_up: string;
  mvp: PlayerDict;
  points_table: TeamDict[];
  batting: PlayerDict[];
  bowling: PlayerDict[];
  /** Mirrors LeagueState.leaderboards() — absent on seasons archived before this field was added. */
  leaderboards?: Record<string, PlayerDict[]>;
  playoffs: { name: string; winner: string; loser: string }[];
}

/** Mirrors LiveMatch.live_score_payload(). */
export interface LiveScorePayload {
  scoreline: string;
  runs: number;
  wickets: number;
  balls: number;
  target: number | null;
  batting_team: string;
  bowling_team: string;
  batting_team_color?: string;
  bowling_team_color?: string;
  user_bowling: boolean;
  user_batting: boolean;
  striker: string;
  non_striker: string;
  partnership: string;
  phase: string;
  active_bowler: string;
  pending_next_batter: boolean;
  striker_aggression: number;
  non_striker_aggression: number;
  bowler_aggression: number;
  current_over: OverEvent[];
  next_batter_options: PlayerDict[];
  last_wicket: OverEvent | null;
  bat_stats: BatStatsLine[];
  bowl_stats: BowlStatsLine[];
  over_log: OverLogEntry[];
}

export interface ImpactPayload {
  xi: PlayerDict[];
  bench: PlayerDict[];
  default_out: string;
  default_in: string;
}

export interface SuperOverSetupPayload {
  message: string;
  batting_first: string;
  batting_second: string;
  batters: PlayerDict[];
  bowlers: PlayerDict[];
  innings: SuperOverInningsCard[];
  winner: string;
}

/** Mirrors LiveMatch.payload(). */
export interface LiveMatchPayload {
  status: string;
  stage: string;
  team1: string;
  team2: string;
  toss_winner: string;
  decision: string | null;
  message: string;
  user_toss: boolean;
  // Test-specific fields (undefined for T20/ODI)
  match_format?: MatchFormat;
  current_day?: number;
  current_session?: number;
  sessions_per_day?: number;
  pending_session_break?: boolean;
  follow_on_available?: boolean;
  followed_on?: boolean;
  can_declare?: boolean;
  lineup_context: '' | 'batting' | 'bowling';
  impact_context: '' | 'bat_to_bowl' | 'bowl_to_bat';
  suggested: PlayerDict[];
  saved_xi: string[];
  saved_wicketkeeper: string;
  lineup_xi: string[];
  impact_sub_name: string;
  swap_notice: string;
  saved_order: string[];
  saved_bowling_order: string[];
  score: LiveScorePayload | null;
  available_bowlers: PlayerDict[];
  impact: ImpactPayload | null;
  super_over: SuperOverSetupPayload | SuperOverCard | null;
  innings: InningsCard[];
  card: MatchCard | null;
}

export interface DraftHistoryEntry {
  season: number;
  type: string;
  round: number;
  pick: number;
  team: string;
  player: string;
  ovr: number;
  role: string;
}

export interface LeaguePayload {
  save_exists: boolean;
  save_name: string | null;
  phase: string;
  season: number;
  completed_seasons: number;
  draft_type: string;
  round: number;
  user_team: string | null;
  difficulty: string;
  draft_pool_type: string;
  competition: Competition;
  match_format: MatchFormat;
  career_mode: CareerMode;
  series_length: number | null;
  bilateral_wins: Record<string, number>;
  bilateral_match_num: number;
  status: string | null;
  teams: TeamDict[];
  standings: TeamDict[];
  squad_size: number;
  retention_limit: number;
  draft: {
    round: number;
    pick: number;
    current_team: string;
    started: boolean;
    user_pick_position: number;
    available: PlayerDict[];
    history: DraftHistoryEntry[];
    needs: Record<string, number>;
  };
  retention: { players: PlayerDict[] };
  schedule: ScheduleRound[];
  playoffs: PlayoffMatch[];
  playoff_index: number;
  match_log: MatchCard[];
  fixture_results: MatchCard[];
  live_match: LiveMatchPayload | null;
  history: SeasonHistoryEntry[];
  tables: { batting: PlayerDict[]; bowling: PlayerDict[] };
  leaderboards: Record<string, PlayerDict[]>;
}
