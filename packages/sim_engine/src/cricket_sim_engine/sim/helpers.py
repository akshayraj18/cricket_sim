"""Role/phase classification utilities shared by `LiveMatch` and `LeagueState`.

These small, stateless helpers answer questions like "does this player count
as a batter for XI-balancing purposes?" or "what T20 phase is over 11?" — used
throughout lineup selection, CPU XI logic, and scorecard/UI labelling.
"""


def is_batting_role(player):
    """Whether this player's primary role gives them a recognised batting slot."""
    return player.role in ("Batsman", "Wicketkeeper", "All-Rounder")


def is_bowling_role(player):
    """Whether this player's primary role gives them a recognised bowling slot."""
    return "Bowler" in player.role or player.role == "All-Rounder"


def allrounder_counts_as_bat(player):
    """Whether an all-rounder should be treated as a specialist batter for this XI (their batting rates at least as high as their bowling)."""
    return player.role == "All-Rounder" and player.current_batting >= player.current_bowling


def allrounder_counts_as_bowl(player):
    """Whether an all-rounder should be treated as a specialist bowler for this XI (their bowling rates at least as high as their batting)."""
    return player.role == "All-Rounder" and player.current_bowling >= player.current_batting


def batting_slot_player(player):
    """Whether this player should occupy a "batter" slot when balancing an XI."""
    return player.role in ("Batsman", "Wicketkeeper") or allrounder_counts_as_bat(player)


def bowling_slot_player(player):
    """Whether this player should occupy a "bowler" slot when balancing an XI."""
    return "Bowler" in player.role or allrounder_counts_as_bowl(player)


def counts_as_batter(player):
    """Whether this player can be selected into a batting line-up at all (role-wise)."""
    return player.role in ("Batsman", "Wicketkeeper", "All-Rounder")


def counts_as_bowler(player):
    """Whether this player can be selected into a bowling plan.

    Primary bowlers/all-rounders always qualify. Batsmen and wicketkeepers
    with bowling_ovr >= 65 also qualify as genuine part-time options (e.g.
    Sachin Tendulkar 65-68, Chris Gayle 68-72, Viv Richards 68). The
    phase-fit score naturally deprioritises them vs specialist bowlers. The
    65 floor keeps out players who essentially never bowl (Kohli, Dhoni,
    Root etc. sit at 10-20).
    """
    if "Bowler" in player.role or player.role == "All-Rounder":
        return True
    return getattr(player, "bowling_ovr", 0) >= 65


def ordinal(number):
    """Render an integer with its English ordinal suffix, e.g. 1 -> "1st", 12 -> "12th"."""
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def bowling_kind(player):
    """Classify a bowler's `bowling_type` as "spin", "pace", or "part-time" (no real bowling type)."""
    bowling_type = getattr(player, "bowling_type", "")
    if any(word in bowling_type for word in ("Spin", "Orthodox", "Leg", "Off")):
        return "spin"
    if bowling_type and bowling_type != "None":
        return "pace"
    return "part-time"


def is_wicketkeeper_option(player):
    """Whether this player can be selected as the team's designated wicketkeeper."""
    return player.role == "Wicketkeeper"


def ensure_stat_fields(player):
    """Backfill any season-stat keys missing from `player.stats` with their defaults.

    Lets older save files (created before a stat was added, e.g. `motm` or
    `catches`) load cleanly without a `KeyError` — new keys just appear with
    neutral starting values.
    """
    defaults = {
        "maidens": 0,
        "motm": 0,
        "best_bowling_wickets": 0,
        "best_bowling_runs": 999,
        "best_bowling_against": "",
        "highest_score_against": "",
        "catches": 0,
        "stumpings": 0,
        "runouts": 0,
        "games": 0,
        "team_wins": 0,
    }
    for key, value in defaults.items():
        player.stats.setdefault(key, value)


def innings_phase(over_num, phase_boundaries=(6, 15)):
    """Classify a (zero-indexed) over number into Powerplay/Middle Overs/Death Overs using `phase_boundaries` (start-of-middle, start-of-death) — defaults to the standard T20 cutoffs (6, 15)."""
    powerplay_end, death_start = phase_boundaries
    if over_num < powerplay_end:
        return "Powerplay"
    if over_num < death_start:
        return "Middle Overs"
    return "Death Overs"


def phase_fit_label(player, phase):
    """Describe, in a few short tags, why this player suits (or doesn't) the given match phase.

    Used by the UI to explain CPU lineup/bowling-plan choices to the user —
    e.g. a death-overs specialist bowling at the death gets tagged "bowling
    phase, death skill".
    """
    batting = getattr(player, "batting_archetype", "Strike Rotator")
    bowling_phase = getattr(player, "bowling_phase", "Flexible")
    bowling_type = getattr(player, "bowling_type", "None")
    notes = []
    if (batting == "Aggressor" and phase == "Powerplay") or (batting in ("Strike Rotator", "Spin Specialist") and phase == "Middle Overs") or (batting == "Finisher" and phase == "Death Overs"):
        notes.append("batting strength")
    if bowling_phase == phase:
        notes.append("bowling phase")
    if phase == "Powerplay" and "Swing" in bowling_type:
        notes.append("new-ball movement")
    if phase == "Middle Overs" and ("Spin" in bowling_type or "Orthodox" in bowling_type):
        notes.append("middle-over spin")
    if phase == "Death Overs" and ("Variations" in bowling_type or "Fast" in bowling_type):
        notes.append("death skill")
    return ", ".join(notes)


def expanded_batting_archetype(player):
    """Map a player's stored `batting_archetype` to a more descriptive UI label.

    A few archetypes (notably "Aggressor") get split into more specific
    flavours based on the player's rating, giving the frontend richer
    descriptions without storing extra data per player.
    """
    archetype = getattr(player, "batting_archetype", "Strike Rotator")
    if archetype == "Aggressor":
        return "Aggressive Opener" if player.current_batting >= 70 else "Pace Specialist"
    if archetype == "Strike Rotator":
        return "Middle-over Rotator"
    if archetype == "Lower-order Hitter":
        return "Lower-order Hitter"
    if archetype == "Defensive Tailender":
        return "Defensive Tailender"
    return archetype


def expanded_bowling_phase(player):
    """Map a bowler's stored `bowling_phase`/`bowling_type` to a descriptive UI label (e.g. "Mystery Spinner", "Death-over Specialist")."""
    phase = getattr(player, "bowling_phase", "Flexible")
    btype = getattr(player, "bowling_type", "")
    if "Mystery" in btype:
        return "Mystery Spinner" if bowling_kind(player) == "spin" else "Mystery Pace"
    if phase == "New Ball":
        return "New-ball Bowler"
    if phase == "Death Overs":
        return "Death-over Specialist"
    if phase == "Middle Overs" and bowling_kind(player) == "spin":
        return "Middle-over Spinner"
    if phase == "Part-time":
        return "Part-time Option"
    return phase
