import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from cricket_sim_engine.players_data import IPL_TEAMS_LIST
from cricket_sim_engine.sim.league_state import LeagueState
from cricket_sim_engine.sim.player_names import apply_name_overrides

from app.db.models.user import User
from app.db.models.career import Career, Match as MatchRow, MatchBall as MatchBallRow, Player as PlayerRow, Team as TeamRow

VALID_DIFFICULTIES = ("easy", "medium", "hard")
VALID_DRAFT_POOL_TYPES = ("current", "alltime", "rosters2026", "international_current", "alltime_t20_intl", "alltime_odi", "alltime_test")

# `card["stage"]` values produced by the engine -> `matches.stage` values.
STAGE_NAMES = {
    "League": "league",
    "Qualifier 1": "qualifier1",
    "Eliminator": "eliminator",
    "Qualifier 2": "qualifier2",
    "Semifinal 1": "semifinal1",
    "Semifinal 2": "semifinal2",
    "Final": "final",
}


def _player_id(career_id: uuid.UUID, player_name: str) -> uuid.UUID:
    """Deterministic `players.id` for `player_name` within `career_id`.

    `_sync_teams_and_players` deletes and re-inserts every player row on each
    save, so a random `uuid.uuid4()` per row would orphan any stored
    references (e.g. `matches.motm_player_id`) the next time a save runs.
    Deriving the ID from `(career_id, name)` keeps it stable across saves.
    """
    return uuid.uuid5(career_id, player_name)


class CareerError(Exception):
    pass


class CareerNotFoundError(CareerError):
    pass


def build_league_state(
    user_team_name: str,
    difficulty: str,
    draft_pool_type: str,
    competition: str = "ipl",
    match_format: str = "t20",
    career_mode: str = "league",
    series_length: int | None = None,
    opponent_name: str | None = None,
    player_name_overrides: dict[str, str] | None = None,
) -> LeagueState:
    if difficulty not in VALID_DIFFICULTIES:
        raise CareerError(f"Difficulty must be one of {VALID_DIFFICULTIES}.")
    if draft_pool_type not in VALID_DRAFT_POOL_TYPES:
        raise CareerError(f"Draft pool type must be one of {VALID_DRAFT_POOL_TYPES}.")
    if match_format not in ("t20", "odi", "test"):
        raise CareerError("match_format must be t20, odi, or test.")

    league = LeagueState()

    if competition == "international":
        if career_mode == "bilateral":
            if not opponent_name:
                raise CareerError("opponent_name is required for bilateral series.")
            sl = series_length if series_length in (1, 3, 5) else 3
            try:
                league.new_bilateral_series(
                    user_team_name, opponent_name,
                    match_format=match_format, series_length=sl,
                    difficulty=difficulty, draft_pool=draft_pool_type,
                )
            except ValueError as exc:
                raise CareerError(str(exc)) from exc
        else:
            try:
                league.new_international_tournament(
                    user_team_name, match_format=match_format,
                    career_mode=career_mode, difficulty=difficulty,
                    draft_pool=draft_pool_type,
                )
            except ValueError as exc:
                raise CareerError(str(exc)) from exc
    else:
        if user_team_name not in IPL_TEAMS_LIST:
            raise CareerError("Choose a valid cricket franchise.")
        if draft_pool_type == "rosters2026":
            league.new_league_with_rosters(user_team_name, difficulty)
        else:
            league.new_league(user_team_name, difficulty, draft_pool=draft_pool_type, match_format=match_format)

    # Apply the user's saved player names. Done here, at creation, because a
    # brand-new career has no saved lineups, leadership or match history
    # referencing the old names yet — so a plain assignment is safe, whereas the
    # same rename mid-career has to go through LeagueState.rename_player.
    apply_name_overrides(league, player_name_overrides)
    return league


def _career_fields_from_state(league: LeagueState) -> dict:
    return {
        "user_team_name": league.user_team_name,
        "difficulty": league.difficulty,
        "draft_pool_type": league.draft_pool_type,
        "competition": getattr(league, "competition", "ipl"),
        "match_format": getattr(league, "match_format", "t20"),
        "career_mode": getattr(league, "career_mode", "league"),
        "series_length": getattr(league, "series_length", None),
        "phase": league.phase,
        "season_year": league.season_year,
        "completed_seasons": league.completed_seasons,
        "retention_limit": league.retention_limit,
        "status_message": league.status_message,
        "state_blob": league.to_dict(),
    }


async def _sync_teams_and_players(db: AsyncSession, career_id: uuid.UUID, league: LeagueState) -> dict[str, PlayerRow]:
    """Replace the queryable teams/players rows for this career from `league`.

    These tables mirror `state_blob` for fast leaderboard/squad queries;
    `state_blob` remains the source of truth for resuming a career.

    Returns the freshly-inserted rostered players keyed by name, so callers
    can resolve match-history references (e.g. Man of the Match) to the
    new player IDs within the same transaction.
    """
    await db.execute(delete(PlayerRow).where(PlayerRow.career_id == career_id))
    await db.execute(delete(TeamRow).where(TeamRow.career_id == career_id))

    all_player_rows: dict[str, PlayerRow] = {}

    for team in league.teams:
        team_row = TeamRow(
            career_id=career_id,
            name=team.name,
            is_user_team=(team.name == league.user_team_name),
            points=team.points,
            wins=team.wins,
            losses=team.losses,
            runs_scored=team.runs_scored,
            balls_faced=team.balls_faced,
            runs_conceded=team.runs_conceded,
            balls_bowled=team.balls_bowled,
            saved_presets={
                "saved_starting_xi_names": team.saved_starting_xi_names,
                "saved_impact_sub_name": team.saved_impact_sub_name,
                "saved_batting_order_names": team.saved_batting_order_names,
                "saved_bowling_over_names": team.saved_bowling_over_names,
                "saved_wicketkeeper_name": team.saved_wicketkeeper_name,
            },
        )
        db.add(team_row)
        await db.flush()

        player_rows = {}
        for player in team.roster:
            player_row = PlayerRow(
                id=_player_id(career_id, player.name),
                career_id=career_id,
                team_id=team_row.id,
                name=player.name,
                role=player.role,
                base_ovr=player.base_ovr,
                batting_ovr=player.batting_ovr,
                bowling_ovr=player.bowling_ovr,
                is_overseas=player.is_overseas,
                age=player.age,
                batting_hand=player.batting_hand,
                bowling_hand=player.bowling_hand,
                batting_archetype=player.batting_archetype,
                bowling_phase=player.bowling_phase,
                bowling_type=player.bowling_type,
                strengths=player.strengths,
                weaknesses=player.weaknesses,
                preferred_position=player.preferred_position,
                form=player.form,
                intent=player.intent,
                season_stats=player.stats,
            )
            db.add(player_row)
            player_rows[player.name] = player_row
        await db.flush()

        if team.captain and team.captain.name in player_rows:
            team_row.captain_player_id = player_rows[team.captain.name].id
        if team.vice_captain and team.vice_captain.name in player_rows:
            team_row.vice_captain_player_id = player_rows[team.vice_captain.name].id

        all_player_rows.update(player_rows)

    # Free agents (not on any roster): persisted only in state_blob's
    # player_pool, not mirrored into the players table (they have no team_id
    # and aren't relevant to squad/leaderboard queries).

    return all_player_rows


async def _write_match_history(
    db: AsyncSession, career_id: uuid.UUID, league: LeagueState, player_rows_by_name: dict[str, PlayerRow]
) -> None:
    """Write any newly-completed matches in `league.fixture_results` to `matches`/`match_balls`.

    `fixture_results` is append-only within a season (reset only when a new
    season starts), so the count of `matches` rows already stored for this
    `(career_id, season_year)` tells us how many of `fixture_results` have
    already been written.
    """
    result = await db.execute(
        select(func.count())
        .select_from(MatchRow)
        .where(MatchRow.career_id == career_id, MatchRow.season_year == league.season_year)
    )
    already_written = result.scalar_one()
    new_cards = league.fixture_results[already_written:]

    for card in new_cards:
        toss_winner, _, toss_decision = card.get("toss", "").partition(" chose to ")
        innings_by_team = {inn["team"]: inn for inn in card.get("innings", [])}
        team1_score = innings_by_team.get(card["team1"])
        team2_score = innings_by_team.get(card["team2"])

        extra = {}
        if card.get("impact_subs"):
            extra["impact_subs"] = card["impact_subs"]
        if card.get("super_over"):
            extra["super_over"] = card["super_over"]
        if extra and team1_score is not None:
            team1_score = {**team1_score, **extra}

        motm_player = player_rows_by_name.get(card.get("motm"))

        match_row = MatchRow(
            career_id=career_id,
            season_year=league.season_year,
            round_num=card.get("round") if card.get("stage") == "League" else None,
            stage=STAGE_NAMES.get(card.get("stage"), (card.get("stage") or "").lower()),
            team1_name=card["team1"],
            team2_name=card["team2"],
            toss_winner=toss_winner or None,
            toss_decision=toss_decision or None,
            result_summary=card.get("summary"),
            winner_name=card.get("winner"),
            team1_score=team1_score,
            team2_score=team2_score,
            motm_player_id=motm_player.id if motm_player else None,
        )
        db.add(match_row)
        await db.flush()

        for innings_num, inn in enumerate(card.get("innings", []), start=1):
            for over in inn.get("over_log", []):
                bowler_row = player_rows_by_name.get(over.get("bowler"))
                for ball_num, event in enumerate(over.get("events", []), start=1):
                    if event.get("kind") == "innings_end":
                        continue
                    batter_row = player_rows_by_name.get(event.get("batter"))
                    wicket = None
                    if event.get("kind") == "wicket":
                        wicket = {k: v for k, v in event.items() if k not in ("kind", "label")}
                    db.add(MatchBallRow(
                        match_id=match_row.id,
                        innings=innings_num,
                        over_num=over["over"],
                        ball_num=ball_num,
                        batter_id=batter_row.id if batter_row else None,
                        bowler_id=bowler_row.id if bowler_row else None,
                        runs=event.get("runs", 0),
                        wicket=wicket,
                        commentary=wicket["description"] if wicket else None,
                    ))


async def create_career(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    user_team_name: str,
    difficulty: str,
    draft_pool_type: str,
    competition: str = "ipl",
    match_format: str = "t20",
    career_mode: str = "league",
    series_length: int | None = None,
    opponent_name: str | None = None,
) -> Career:
    name = name.strip()
    if not name:
        raise CareerError("Enter a career name.")

    existing = await db.execute(select(Career).where(Career.user_id == user_id, Career.name == name))
    if existing.scalar_one_or_none() is not None:
        raise CareerError(f'A career named "{name}" already exists.')

    owner = await db.get(User, user_id)
    league = build_league_state(
        user_team_name, difficulty, draft_pool_type,
        competition=competition, match_format=match_format,
        career_mode=career_mode, series_length=series_length,
        opponent_name=opponent_name,
        player_name_overrides=(owner.player_name_overrides if owner else None),
    )

    career = Career(user_id=user_id, name=name, **_career_fields_from_state(league))
    db.add(career)
    await db.flush()

    await _sync_teams_and_players(db, career.id, league)
    await db.commit()
    await db.refresh(career)
    return career


async def list_careers(db: AsyncSession, user_id: uuid.UUID) -> list[Career]:
    result = await db.execute(
        select(Career).where(Career.user_id == user_id).order_by(Career.updated_at.desc())
    )
    return list(result.scalars().all())


async def get_career(db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID) -> Career:
    result = await db.execute(select(Career).where(Career.id == career_id, Career.user_id == user_id))
    career = result.scalar_one_or_none()
    if career is None:
        raise CareerNotFoundError("Career not found.")
    return career


async def load_league_state(db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID) -> LeagueState:
    career = await get_career(db, user_id, career_id)
    return LeagueState.from_dict(career.state_blob)


async def save_league_state(
    db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID, league: LeagueState
) -> Career:
    """Persist `league`'s current state back to `career_id`.

    Any in-progress live match is discarded (not yet persisted — see the
    live-match/Redis layer); the career resumes from the match centre.
    """
    career = await get_career(db, user_id, career_id)
    league.live_match = None

    for field, value in _career_fields_from_state(league).items():
        setattr(career, field, value)

    player_rows_by_name = await _sync_teams_and_players(db, career.id, league)
    await _write_match_history(db, career.id, league, player_rows_by_name)
    await db.commit()
    await db.refresh(career)
    return career


async def delete_career(db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID) -> None:
    career = await get_career(db, user_id, career_id)
    await db.delete(career)
    await db.commit()


class MatchNotFoundError(CareerError):
    pass


async def list_matches(
    db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID, season_year: int | None = None
) -> list[MatchRow]:
    """Match history for `career_id`, most recent first, optionally filtered to one season."""
    await get_career(db, user_id, career_id)  # ownership check, 404 if missing

    query = select(MatchRow).where(MatchRow.career_id == career_id)
    if season_year is not None:
        query = query.where(MatchRow.season_year == season_year)
    result = await db.execute(query.order_by(MatchRow.played_at.desc()))
    return list(result.scalars().all())


async def get_match(db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID, match_id: uuid.UUID) -> MatchRow:
    await get_career(db, user_id, career_id)  # ownership check, 404 if missing

    result = await db.execute(select(MatchRow).where(MatchRow.id == match_id, MatchRow.career_id == career_id))
    match = result.scalar_one_or_none()
    if match is None:
        raise MatchNotFoundError("Match not found.")
    return match


async def get_match_balls(
    db: AsyncSession, user_id: uuid.UUID, career_id: uuid.UUID, match_id: uuid.UUID
) -> list[MatchBallRow]:
    match = await get_match(db, user_id, career_id, match_id)

    result = await db.execute(
        select(MatchBallRow)
        .where(MatchBallRow.match_id == match.id)
        .order_by(MatchBallRow.innings, MatchBallRow.over_num, MatchBallRow.ball_num)
    )
    return list(result.scalars().all())


async def player_names_by_id(db: AsyncSession, career_id: uuid.UUID, player_ids: set[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Resolve `players.id` -> `name` for `career_id`, for annotating match-history responses."""
    player_ids.discard(None)
    if not player_ids:
        return {}
    result = await db.execute(
        select(PlayerRow.id, PlayerRow.name).where(PlayerRow.career_id == career_id, PlayerRow.id.in_(player_ids))
    )
    return dict(result.all())
