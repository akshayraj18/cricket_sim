"""Shared constants for the league simulation: persistence, sizing, and seed data.

`TEAM_META` and the name-component lists are presentation/generation data used
across `LiveMatch` and `LeagueState`; the numeric constants govern save-file
location, squad sizing, and the retention-window cycle.
"""

SAVE_FILE = "ui_save_state.pkl"
SAVES_DIR = "saves"
SQUAD_SIZE = 25

# Per-format match parameters. `balls_per_innings` is the hard cap for a
# single innings (Test bowls out or declares well before its theoretical
# 450-over ceiling in practice, but the cap still bounds the engine loop).
# `bowler_overs_cap` is the max overs one bowler may bowl in an innings
# (T20's IPL-style 4-over cap; ODI's 10; Test has none, capped here at the
# innings-balls ceiling instead so `available_bowlers` filtering still works).
# `phase_boundaries` are (start_over_exclusive_of_powerplay, start_over_of_death)
# cutoffs consumed by `innings_phase`.
MATCH_FORMAT_CONFIG = {
    "t20": {
        "overs_per_innings": 20,
        "balls_per_innings": 120,
        "innings_per_side": 1,
        "bowler_overs_cap": 4,
        "phase_boundaries": (6, 15),
        "follow_on_margin": None,
        "allows_draw": False,
        "days": 1,
        "sessions_per_day": 1,
        "overs_per_session": 20,
    },
    "odi": {
        "overs_per_innings": 50,
        "balls_per_innings": 300,
        "innings_per_side": 1,
        "bowler_overs_cap": 10,
        "phase_boundaries": (10, 40),
        "follow_on_margin": None,
        "allows_draw": False,
        "days": 1,
        "sessions_per_day": 1,
        "overs_per_session": 50,
    },
    "test": {
        # A Test innings is not limited to a day's play — sides routinely bat
        # 100-130 overs. At 90 the innings was being guillotined at roughly 315
        # runs, which capped first-innings totals below a realistic 300-350 no
        # matter how the scoring rate was tuned. 110 overs leaves room for a big
        # innings while still fitting four innings inside the 450 overs that
        # 5 days x 3 sessions x 30 overs provides — which is also what lets a
        # match run out of time and draw.
        "overs_per_innings": 110,
        "balls_per_innings": 660,
        "innings_per_side": 2,
        "bowler_overs_cap": 90,
        "phase_boundaries": (10, 70),
        "follow_on_margin": 200,
        "allows_draw": True,
        "days": 5,
        "sessions_per_day": 3,
        "overs_per_session": 30,
    },
}


def format_config(match_format):
    """`MATCH_FORMAT_CONFIG` entry for `match_format`, defaulting to T20 for unset/unknown values (keeps existing IPL careers behaving exactly as before)."""
    return MATCH_FORMAT_CONFIG.get(match_format or "t20", MATCH_FORMAT_CONFIG["t20"])
# Max overseas players allowed in a full squad (IPL rule is 8; we allow 9). This
# is the SQUAD cap enforced during the mega draft — distinct from the on-field
# limit of 4 overseas in any playing XI (see live_match / set_user_xi).
MAX_OVERSEAS_SQUAD = 9
RETAIN_NORMAL = 11
RETAIN_RESET = 5

INDIAN_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Ishan", "Kabir", "Reyansh", "Rohan",
    "Sai", "Vihaan", "Ayaan", "Dev", "Kiaan", "Krish", "Neel", "Pranav",
    "Rahul", "Rudra", "Shivam", "Yash", "Arnav", "Dhruv", "Harsh", "Manav",
]
INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Yadav", "Reddy", "Iyer", "Nair", "Verma",
    "Rana", "Gill", "Khan", "Choudhary", "Deshmukh", "Pawar", "Saxena", "Shetty",
    "Tripathi", "Mishra", "Bishnoi", "Thakur", "Gaikwad", "Sundar", "Varma", "Jaiswal",
]
OVERSEAS_FIRST_NAMES = [
    "Liam", "Noah", "Oliver", "Jack", "Harry", "Mason", "Ethan", "Lucas",
    "James", "Logan", "Theo", "Oscar", "Finn", "Dylan", "Archie", "Cooper",
    "Caleb", "Riley", "Max", "Jude", "Leo", "Sam", "Ben", "Tom",
]
OVERSEAS_LAST_NAMES = [
    "Smith", "Brown", "Wilson", "Taylor", "Anderson", "Johnson", "Williams", "Miller",
    "Thompson", "Walker", "Clark", "Robinson", "Campbell", "Bennett", "Carter", "Morgan",
    "Phillips", "Turner", "Hughes", "Edwards", "Fletcher", "Marsh", "Allen", "Wright",
]


# Fictional, IP-safe franchises. We keep the real *city* (cities aren't
# trademarked) but invent the team name, abbreviation, generic mascot, colors,
# and venue so nothing infringes a real IPL franchise's trademarks. Users can
# rename any team to whatever they like via the in-app roster editor.
TEAM_META = {
    "Chennai Cholas": {"abbr": "CHE", "home": "Chennai Cricket Ground", "primary": "#e8a013", "accent": "#0f2a5c"},
    "Mumbai Mavericks": {"abbr": "MUM", "home": "Marine Drive Oval", "primary": "#1f6feb", "accent": "#f0c419"},
    "Bengaluru Bulls": {"abbr": "BLR", "home": "Garden City Stadium", "primary": "#9b1d3a", "accent": "#1c1c24"},
    "Kolkata Knights": {"abbr": "KOL", "home": "Riverside Gardens", "primary": "#6b3fa0", "accent": "#e0b94a"},
    "Hyderabad Hawks": {"abbr": "HYD", "home": "Deccan Arena", "primary": "#e8602c", "accent": "#143d59"},
    "Rajasthan Raptors": {"abbr": "RAJ", "home": "Pink City Stadium", "primary": "#c2185b", "accent": "#0e9aa7"},
    "Delhi Dynamos": {"abbr": "DEL", "home": "Capital Cricket Ground", "primary": "#0b6e6e", "accent": "#f24236"},
    "Gujarat Gladiators": {"abbr": "GUJ", "home": "Sabarmati Stadium", "primary": "#1a2238", "accent": "#d4943a"},
    "Lucknow Lions": {"abbr": "LKO", "home": "Awadh Cricket Ground", "primary": "#0f8a8a", "accent": "#f2a541"},
    "Punjab Panthers": {"abbr": "PUN", "home": "Five Rivers Stadium", "primary": "#5a3e8e", "accent": "#e8505b"},
}

INTERNATIONAL_TEAMS_LIST = [
    "India", "Australia", "England", "New Zealand", "South Africa",
    "Pakistan", "Sri Lanka", "West Indies", "Bangladesh", "Afghanistan",
]

INTERNATIONAL_TEAM_META = {
    "India":        {"abbr": "IND", "home": "Narendra Modi Stadium",     "primary": "#0a63b0", "accent": "#f0821e"},
    "Australia":    {"abbr": "AUS", "home": "Melbourne Cricket Ground",  "primary": "#f4d000", "accent": "#004f9e"},
    "England":      {"abbr": "ENG", "home": "Lord's Cricket Ground",     "primary": "#003e8e", "accent": "#d4001a"},
    "New Zealand":  {"abbr": "NZL", "home": "Eden Park",                 "primary": "#000000", "accent": "#c8102e"},
    "South Africa": {"abbr": "SA",  "home": "Newlands Cricket Ground",   "primary": "#007c45", "accent": "#f4b942"},
    "Pakistan":     {"abbr": "PAK", "home": "National Stadium Karachi",  "primary": "#005d2e", "accent": "#ffffff"},
    "Sri Lanka":    {"abbr": "SL",  "home": "R. Premadasa Stadium",      "primary": "#00338d", "accent": "#f1c40f"},
    "West Indies":  {"abbr": "WI",  "home": "Kensington Oval",           "primary": "#7b0000", "accent": "#f7c94e"},
    "Bangladesh":   {"abbr": "BAN", "home": "Mirpur National Stadium",   "primary": "#006a4e", "accent": "#f42a41"},
    "Afghanistan":  {"abbr": "AFG", "home": "Kabul International Stadium","primary": "#003580", "accent": "#d32011"},
}

# City-franchise teams for the World Tournament mega draft.
# One franchise per international cricket nation, named after a city in that
# country — same alliterative city + animal/element convention as IPL teams.
# Used when career_mode="tournament" with draft_pool="alltime_world".
WORLD_TEAMS_LIST = [
    "Mumbai Monsoons", "Sydney Sharks", "London Lions", "Auckland Alpines",
    "Cape Town Cobras", "Karachi Komets", "Colombo Cyclones",
    "Kingston Kings", "Dhaka Dragons", "Kabul Kestrels",
]

WORLD_TEAM_META = {
    "Mumbai Monsoons":  {"abbr": "MBM", "home": "Mumbai World Stadium",    "primary": "#7c00d4", "accent": "#00f5c8"},
    "Sydney Sharks":    {"abbr": "SYD", "home": "Sydney Cricket Ground",   "primary": "#ff5f1f", "accent": "#1af0ff"},
    "London Lions":     {"abbr": "LON", "home": "London Cricket Arena",    "primary": "#d400a8", "accent": "#ffe600"},
    "Auckland Alpines": {"abbr": "AKL", "home": "Eden Park Auckland",      "primary": "#00b8a0", "accent": "#ff3864"},
    "Cape Town Cobras": {"abbr": "CPT", "home": "Cape Town Stadium",       "primary": "#ff9500", "accent": "#1a0066"},
    "Karachi Komets":   {"abbr": "KAR", "home": "National Stadium Karachi","primary": "#00d4ff", "accent": "#8b00ff"},
    "Colombo Cyclones": {"abbr": "CMB", "home": "R. Premadasa Stadium",    "primary": "#c8f500", "accent": "#1a0033"},
    "Kingston Kings":   {"abbr": "KNG", "home": "Kensington Oval",         "primary": "#ff0066", "accent": "#f5f500"},
    "Dhaka Dragons":    {"abbr": "DHA", "home": "Mirpur International",    "primary": "#5c00c8", "accent": "#ff8c00"},
    "Kabul Kestrels":   {"abbr": "KBL", "home": "Kabul International",     "primary": "#00e676", "accent": "#c4003c"},
}

# Neutral branding for a team whose name isn't a TEAM_META key (e.g. one the
# user renamed to something custom and that hasn't kept its original key).
_DEFAULT_TEAM_META = {
    "abbr": "",
    "home": "Cricket Stadium",
    "primary": "#3a3f4b",
    "accent": "#9aa0a6",
}


def team_meta(team):
    """Branding/venue metadata for a Team, robust to user renames.

    A renamed team keeps its original branding via `meta_name`; we look up by
    that first, then the current name, and finally fall back to neutral
    defaults (with the abbr derived from the name) so a custom name never
    raises a KeyError anywhere in the engine.
    """
    name = getattr(team, "name", team) if not isinstance(team, str) else team
    meta_name = getattr(team, "meta_name", None) if not isinstance(team, str) else None
    meta = (TEAM_META.get(meta_name) or TEAM_META.get(name)
            or INTERNATIONAL_TEAM_META.get(meta_name) or INTERNATIONAL_TEAM_META.get(name)
            or WORLD_TEAM_META.get(meta_name) or WORLD_TEAM_META.get(name))
    if meta:
        return meta
    fallback = dict(_DEFAULT_TEAM_META)
    fallback["abbr"] = str(name)[:3].upper()
    return fallback
