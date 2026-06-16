"""Shared constants for the league simulation: persistence, sizing, and seed data.

`TEAM_META` and the name-component lists are presentation/generation data used
across `LiveMatch` and `LeagueState`; the numeric constants govern save-file
location, squad sizing, and the retention-window cycle.
"""

SAVE_FILE = "ui_save_state.pkl"
SAVES_DIR = "saves"
SQUAD_SIZE = 25
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
    meta = TEAM_META.get(meta_name) or TEAM_META.get(name)
    if meta:
        return meta
    fallback = dict(_DEFAULT_TEAM_META)
    fallback["abbr"] = str(name)[:3].upper()
    return fallback
