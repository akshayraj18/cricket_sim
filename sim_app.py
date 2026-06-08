import os
import pickle
import random

from engine import MatchEngine
from models import Player, Team
from players_data import IPL_TEAMS_LIST, get_initial_player_pool


SAVE_FILE = "ui_save_state.pkl"
SQUAD_SIZE = 21
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


TEAM_META = {
    "Chennai Super Kings": {"abbr": "CSK", "home": "MA Chidambaram Stadium", "primary": "#f7c948", "accent": "#22409a"},
    "Mumbai Indians": {"abbr": "MI", "home": "Wankhede Stadium", "primary": "#045093", "accent": "#d1ab3e"},
    "Royal Challengers Bengaluru": {"abbr": "RCB", "home": "M. Chinnaswamy Stadium", "primary": "#da1818", "accent": "#111111"},
    "Kolkata Knight Riders": {"abbr": "KKR", "home": "Eden Gardens", "primary": "#3a225d", "accent": "#c6a76f"},
    "Sunrisers Hyderabad": {"abbr": "SRH", "home": "Rajiv Gandhi Intl. Stadium", "primary": "#f26522", "accent": "#1f1f1f"},
    "Rajasthan Royals": {"abbr": "RR", "home": "Sawai Mansingh Stadium", "primary": "#e91e8f", "accent": "#254aa5"},
    "Delhi Capitals": {"abbr": "DC", "home": "Arun Jaitley Stadium", "primary": "#17479e", "accent": "#ef1b23"},
    "Gujarat Titans": {"abbr": "GT", "home": "Narendra Modi Stadium", "primary": "#1b2133", "accent": "#b69249"},
    "Lucknow Super Giants": {"abbr": "LSG", "home": "Ekana Cricket Stadium", "primary": "#00a3e0", "accent": "#f28c28"},
    "Punjab Kings": {"abbr": "PBKS", "home": "New PCA Stadium", "primary": "#d71920", "accent": "#b7b7b7"},
}


def is_batting_role(player):
    return player.role in ("Batsman", "Wicketkeeper", "All-Rounder")


def is_bowling_role(player):
    return "Bowler" in player.role or player.role == "All-Rounder"


def allrounder_counts_as_bat(player):
    return player.role == "All-Rounder" and player.current_batting >= player.current_bowling


def allrounder_counts_as_bowl(player):
    return player.role == "All-Rounder" and player.current_bowling >= player.current_batting


def batting_slot_player(player):
    return player.role in ("Batsman", "Wicketkeeper") or allrounder_counts_as_bat(player)


def bowling_slot_player(player):
    return "Bowler" in player.role or allrounder_counts_as_bowl(player)


def counts_as_batter(player):
    return player.role in ("Batsman", "Wicketkeeper", "All-Rounder")


def counts_as_bowler(player):
    return "Bowler" in player.role or player.role == "All-Rounder"


def ordinal(number):
    if 10 <= number % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def bowling_kind(player):
    bowling_type = getattr(player, "bowling_type", "")
    if any(word in bowling_type for word in ("Spin", "Orthodox", "Leg", "Off")):
        return "spin"
    if bowling_type and bowling_type != "None":
        return "pace"
    return "part-time"


def is_wicketkeeper_option(player):
    return player.role == "Wicketkeeper"


def ensure_stat_fields(player):
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


def innings_phase(over_num):
    if over_num < 6:
        return "Powerplay"
    if over_num < 15:
        return "Middle Overs"
    return "Death Overs"


def phase_fit_label(player, phase):
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


class LiveMatch:
    def __init__(self, league, team1, team2, stage):
        self.league = league
        self.team1 = team1
        self.team2 = team2
        self.stage = stage
        self.engine = MatchEngine(team1, team2, league.user_team_name, getattr(league, "difficulty", "hard"))
        self.engine.fast_sim_active = True
        self.toss_winner = random.choice([team1, team2])
        self.decision = None
        self.status = "toss"
        self.message = f"{self.toss_winner.name} won the toss."
        self.inn1_bat = None
        self.inn1_bowl = None
        self.xis = {}
        self.batting_orders = {}
        self.bowling_pools = {}
        self.bowling_plan_for = {}
        self.wicketkeepers = {}
        self.current_innings = 1
        self.target = None
        self.innings = []
        self.score = None
        self.card = None
        self.pending_second_lineup = False
        self.super_over = None
        self.impact_subs = []
        if self.toss_winner.name != league.user_team_name:
            self.choose_toss(random.choice(["bat", "bowl"]))

    def choose_toss(self, decision):
        if self.status != "toss":
            raise ValueError("Toss is already complete.")
        if decision not in ("bat", "bowl"):
            raise ValueError("Choose bat or bowl.")
        self.decision = decision
        toss_loser = self.team2 if self.toss_winner == self.team1 else self.team1
        self.inn1_bat = self.toss_winner if decision == "bat" else toss_loser
        self.inn1_bowl = toss_loser if decision == "bat" else self.toss_winner
        self.status = "lineup"
        self.message = f"{self.toss_winner.name} chose to {decision} first."
        self.auto_cpu_xis()

    def auto_cpu_xis(self):
        for team in (self.team1, self.team2):
            if team.name != self.league.user_team_name:
                xi = self.league.smart_cpu_xi(team)
                self.xis[team.name] = xi
                self.batting_orders[team.name] = self.league.smart_batting_order(xi)
                self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
                self.bowling_plan_for[team.name] = []
                self.wicketkeepers[team.name] = self.default_keeper(team, xi)

    def default_keeper(self, team, xi):
        saved = getattr(team, "saved_wicketkeeper_name", "")
        keeper = next((p for p in xi if p.name == saved and is_wicketkeeper_option(p)), None)
        if keeper:
            return keeper
        return sorted([p for p in xi if is_wicketkeeper_option(p)], key=lambda p: p.current_batting, reverse=True)[0] if any(is_wicketkeeper_option(p) for p in xi) else xi[0]

    def default_batting_order(self, xi):
        return self.league.smart_batting_order(xi)

    def suggested_roster(self, bowling_first=False):
        team = self.league.user_team()
        if bowling_first:
            return sorted(team.roster, key=lambda p: (0 if is_bowling_role(p) else 1, -p.current_bowling, -p.current_ovr))
        return sorted(team.roster, key=lambda p: (0 if is_batting_role(p) else 1, -p.current_batting, -p.current_ovr))

    def set_user_xi(self, names, batting_order=None, bowling_order=None, intents=None, save=False, context="batting", wicketkeeper_name=""):
        if self.status not in ("lineup", "batting_order"):
            raise ValueError("Lineup selection is not open.")
        team = self.league.user_team()
        if self.status == "batting_order" and team.name in self.xis:
            xi = self.xis[team.name]
        else:
            xi = [next((p for p in team.roster if p.name == name), None) for name in names]
            xi = [p for p in xi if p]
        if len(xi) != 11:
            raise ValueError("Pick exactly 11 players.")
        if sum(1 for p in xi if p.is_overseas) > 4:
            raise ValueError("Playing XI cannot include more than 4 overseas players.")
        if context == "batting" and len([p for p in xi if counts_as_batter(p)]) < 6:
            raise ValueError("Batting First XI needs at least 6 batting options including all-rounders and wicketkeepers.")
        if context == "bowling" and len([p for p in xi if counts_as_bowler(p)]) < 5:
            raise ValueError("Bowling First XI needs at least 5 bowling options including all-rounders.")
        for player in xi:
            player.intent = (intents or {}).get(player.name, "Normal")
        order_names = batting_order or names
        order = [next((p for p in xi if p.name == name), None) for name in order_names]
        order = [p for p in order if p]
        if len(order) != 11:
            order = self.default_batting_order(xi)
        self.xis[team.name] = xi
        keeper = next((p for p in xi if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None) or self.default_keeper(team, xi)
        self.wicketkeepers[team.name] = keeper
        self.batting_orders[team.name] = order
        self.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
        self.set_bowling_plan(team, bowling_order or [])
        if save:
            team.saved_playing_xi_names = [p.name for p in xi]
            team.saved_wicketkeeper_name = keeper.name
            team.saved_batting_order_names = [p.name for p in order]
            if bowling_order:
                team.saved_bowling_over_names = list(bowling_order)
        if self.status == "batting_order":
            self.start_second_innings()
            return
        self.start_first_innings_if_ready()

    def set_bowling_plan(self, team, names):
        valid = [p.name for p in self.bowling_pools.get(team.name, [])]
        clean = [name for name in names if name in valid]
        if len(clean) == 20 and all(clean.count(name) <= 4 for name in set(clean)):
            self.bowling_plan_for[team.name] = clean
        else:
            self.bowling_plan_for[team.name] = []

    def start_first_innings_if_ready(self):
        if self.team1.name in self.xis and self.team2.name in self.xis:
            self.start_innings(self.inn1_bat, self.inn1_bowl, self.batting_orders[self.inn1_bat.name], self.bowling_pools[self.inn1_bowl.name])

    def start_innings(self, batting_team, bowling_team, batting_order, bowling_pool):
        self.score = {
            "batting_team": batting_team,
            "bowling_team": bowling_team,
            "batting_order": batting_order,
            "bowling_pool": bowling_pool,
            "runs": 0,
            "wickets": 0,
            "balls": 0,
            "striker_idx": 0,
            "non_striker_idx": 1,
            "last_bowler": None,
            "overs_tracked": {},
            "bat_stats": {p.name: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in batting_order},
            "bowl_stats": {p.name: {"runs": 0, "wickets": 0, "balls": 0} for p in bowling_pool},
            "dismissals": {},
            "partnership_runs": 0,
            "partnership_balls": 0,
            "over_log": [],
            "current_over_events": [],
            "active_bowler": None,
            "batting_aggression": {p.name: 3 for p in batting_order},
            "bowling_aggression": {p.name: 2 for p in bowling_pool},
            "pending_next_batter": False,
        }
        self.status = "over"
        self.message = f"{batting_team.name} innings started. Pick the next bowler."

    def available_bowlers(self):
        if self.status != "over" or not self.score:
            return []
        tracked = self.score["overs_tracked"]
        last = self.score["last_bowler"]
        options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < 4 and p != last]
        if not options:
            options = [p for p in self.score["bowling_pool"] if tracked.get(p.name, 0) < 4]
        if not options:
            options = list(self.score["bowling_pool"])
        phase = innings_phase(self.score["balls"] // 6)
        return sorted(options, key=lambda p: self.bowler_phase_score(p, phase), reverse=True)

    def cpu_bowler(self):
        return self.available_bowlers()[0]

    def bowler_phase_score(self, player, phase):
        score = player.current_bowling
        bowling_type = getattr(player, "bowling_type", "")
        bowling_phase = getattr(player, "bowling_phase", "Flexible")
        if bowling_phase == phase:
            score += 8
        if phase in ("Powerplay", "Death Overs") and ("Fast" in bowling_type or "Swing" in bowling_type or "Medium" in bowling_type or "Seam" in bowling_type):
            score += 5
        if phase == "Middle Overs" and ("Spin" in bowling_type or "Orthodox" in bowling_type or "Leg" in bowling_type or "Off" in bowling_type):
            score += 6
        if phase == "Death Overs" and "Variations" in bowling_type:
            score += 5
        return score

    def ensure_active_bowler(self, bowler_name=None, auto=False):
        if self.status != "over":
            raise ValueError("No over is ready.")
        if self.score.get("active_bowler") and self.score["balls"] % 6 != 0:
            return self.score["active_bowler"]
        bowling_team = self.score["bowling_team"]
        user_bowling = bowling_team.name == self.league.user_team_name and not auto
        bowler = None
        if user_bowling:
            planned = self.planned_bowler_name()
            chosen_name = bowler_name or planned
            bowler = next((p for p in self.available_bowlers() if p.name == chosen_name), None)
            if not bowler and not bowler_name:
                bowler = self.available_bowlers()[0]
            if not bowler:
                raise ValueError("Choose an eligible bowler.")
        else:
            bowler = self.cpu_bowler()

        self.score["last_bowler"] = bowler
        self.score["overs_tracked"][bowler.name] = self.score["overs_tracked"].get(bowler.name, 0) + 1
        self.score["active_bowler"] = bowler
        self.score["current_over_events"] = []
        return bowler

    def play_over(self, bowler_name=None, auto=False, max_balls=6, stop_on_wicket=True):
        if self.status != "over":
            raise ValueError("No over is ready.")
        if self.innings_is_over():
            self.finish_innings()
            return
        bowler = self.ensure_active_bowler(bowler_name, auto)
        start_balls = self.score["balls"]
        end_ball = min(((start_balls // 6) + 1) * 6, start_balls + max_balls, 120)
        self.score["last_event_wicket"] = False
        while self.score["balls"] < end_ball and not self.innings_is_over():
            if self.target and self.score["runs"] >= self.target:
                break
            event = self.play_ball(bowler)
            self.score["current_over_events"].append(event)
            self.score["last_event_wicket"] = event["kind"] == "wicket"
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name and self.score["wickets"] < 10 and self.score["balls"] < 120:
                self.score["pending_next_batter"] = True
                self.status = "next_batter"
                self.message = f"{event['description']}. Choose who comes in next."
                return
            if event["kind"] == "wicket" and stop_on_wicket and not auto and self.score["batting_team"].name == self.league.user_team_name:
                break

        if self.score["balls"] % 6 == 0 or self.score["balls"] >= 120 or self.innings_is_over() or (self.target and self.score["runs"] >= self.target):
            self.close_current_over()

        if self.score["balls"] >= 120 or self.innings_is_over() or (self.target and self.score["runs"] >= self.target):
            self.finish_innings()
        else:
            marker = "End of over" if self.score["balls"] % 6 == 0 else "Ball complete"
            self.message = f"{marker} {self.score['balls'] // 6}.{self.score['balls'] % 6}: {self.scoreline()}."

    def innings_is_over(self):
        if not self.score:
            return False
        order_len = len(self.score.get("batting_order", []))
        all_out_wickets = min(10, max(0, order_len - 1))
        return self.score.get("wickets", 0) >= all_out_wickets

    def close_current_over(self):
        bowler = self.score.get("active_bowler")
        events = list(self.score.get("current_over_events", []))
        if bowler and events:
            over_runs = sum(e.get("runs", 0) for e in events)
            over_number = (self.score["balls"] + 5) // 6
            self.score["over_log"].append({"over": over_number, "bowler": bowler.name, "events": events, "runs": over_runs})
        self.score["active_bowler"] = None
        self.score["current_over_events"] = []

    def set_aggression(self, batting=None, bowling=None):
        if not self.score:
            return
        for name, value in (batting or {}).items():
            if name in self.score["batting_aggression"]:
                self.score["batting_aggression"][name] = max(1, min(5, int(value)))
        for name, value in (bowling or {}).items():
            if name in self.score["bowling_aggression"]:
                self.score["bowling_aggression"][name] = max(1, min(5, int(value)))

    def select_next_batter(self, name):
        if self.status != "next_batter" or not self.score.get("pending_next_batter"):
            raise ValueError("No wicket is waiting for a next batter.")
        order = self.score["batting_order"]
        next_idx = self.score["striker_idx"]
        chosen_idx = next((i for i, p in enumerate(order) if p.name == name and i >= next_idx), None)
        if chosen_idx is None:
            raise ValueError("Choose an available batter who has not batted yet.")
        order[next_idx], order[chosen_idx] = order[chosen_idx], order[next_idx]
        self.score["pending_next_batter"] = False
        self.status = "over"
        if self.score["balls"] % 6 == 0:
            self.close_current_over()
        self.message = f"{order[next_idx].name} walks in next. {self.scoreline()}."

    def planned_bowler_name(self):
        team_name = self.score["bowling_team"].name
        plan = self.bowling_plan_for.get(team_name, [])
        over_index = self.score["balls"] // 6
        if over_index < len(plan):
            return plan[over_index]
        return None

    def play_ball(self, bowler):
        batting_order = self.score["batting_order"]
        if self.innings_is_over() or self.score["striker_idx"] >= len(batting_order):
            self.score["wickets"] = max(self.score["wickets"], min(10, max(0, len(batting_order) - 1)))
            return {"kind": "innings_end", "label": "", "runs": 0}
        striker = batting_order[self.score["striker_idx"]]
        self.score["bat_stats"].setdefault(striker.name, {"runs": 0, "balls": 0, "fours": 0, "sixes": 0})
        self.score["bowl_stats"].setdefault(bowler.name, {"runs": 0, "wickets": 0, "balls": 0})
        over_num = self.score["balls"] // 6
        phase = innings_phase(over_num)
        striker.match_phase = phase
        bowler.match_phase = phase
        striker.batting_aggression = self.score["batting_aggression"].get(striker.name, 3)
        bowler.bowling_aggression = self.score["bowling_aggression"].get(bowler.name, 2)
        outcome = self.engine.simulate_ball(striker, bowler)
        self.score["balls"] += 1
        self.score["partnership_balls"] += 1
        self.score["bat_stats"][striker.name]["balls"] += 1
        self.score["bowl_stats"][bowler.name]["balls"] += 1
        striker.stats["balls_faced"] += 1
        bowler.stats["balls_bowled"] += 1
        if outcome == "W":
            dismissal = self.resolve_dismissal(striker, bowler)
            self.score["wickets"] += 1
            striker.stats["outs"] += 1
            if dismissal["bowler_gets_wicket"]:
                bowler.stats["wickets"] += 1
                self.score["bowl_stats"][bowler.name]["wickets"] += 1
            self.score["partnership_runs"] = 0
            self.score["partnership_balls"] = 0
            self.score["striker_idx"] = max(self.score["striker_idx"], self.score["non_striker_idx"]) + 1
            self.score["dismissals"][striker.name] = dismissal["description"]
            return {"kind": "wicket", "label": "W", **dismissal}
        runs = int(outcome)
        self.score["runs"] += runs
        self.score["partnership_runs"] += runs
        self.score["bat_stats"][striker.name]["runs"] += runs
        self.score["bowl_stats"][bowler.name]["runs"] += runs
        striker.stats["runs"] += runs
        bowler.stats["runs_conceded"] += runs
        if runs == 4:
            striker.stats["fours"] += 1
            self.score["bat_stats"][striker.name]["fours"] += 1
        elif runs == 6:
            striker.stats["sixes"] += 1
            self.score["bat_stats"][striker.name]["sixes"] += 1
        if runs in (1, 3):
            self.score["striker_idx"], self.score["non_striker_idx"] = self.score["non_striker_idx"], self.score["striker_idx"]
        if self.score["balls"] % 6 == 0:
            self.score["striker_idx"], self.score["non_striker_idx"] = self.score["non_striker_idx"], self.score["striker_idx"]
        return {"kind": "runs", "runs": runs, "label": outcome}

    def resolve_dismissal(self, striker, bowler):
        keeper = self.wicketkeepers.get(self.score["bowling_team"].name) or next((p for p in self.xis[self.score["bowling_team"].name] if is_wicketkeeper_option(p)), None)
        fielders = [p for p in self.xis[self.score["bowling_team"].name] if p != bowler]
        is_spin = "Spin" in getattr(bowler, "bowling_type", "") or "Orthodox" in getattr(bowler, "bowling_type", "") or "Spin" in bowler.role
        roll = random.random()
        batting_aggression = self.score["batting_aggression"].get(striker.name, 3)
        runout_cutoff = 0.18 + max(0, batting_aggression - 3) * 0.04
        if is_spin and keeper and roll < 0.14:
            keeper.stats["stumpings"] += 1
            return {
                "dismissal": "stumped",
                "batter": striker.name,
                "bowler": bowler.name,
                "fielder": keeper.name,
                "description": f"{striker.name} st {keeper.name} b {bowler.name}",
                "bowler_gets_wicket": True,
            }
        if roll < runout_cutoff:
            fielder = random.choice(fielders) if fielders else bowler
            fielder.stats["runouts"] += 1
            return {
                "dismissal": "run out",
                "batter": striker.name,
                "bowler": bowler.name,
                "fielder": fielder.name,
                "description": f"{striker.name} run out ({fielder.name})",
                "bowler_gets_wicket": False,
            }
        catcher_pool = ([keeper] * 2 if keeper else []) + fielders
        catcher = random.choice(catcher_pool) if catcher_pool else bowler
        catcher.stats["catches"] += 1
        return {
            "dismissal": "caught",
            "batter": striker.name,
            "bowler": bowler.name,
            "fielder": catcher.name,
            "description": f"{striker.name} c {catcher.name} b {bowler.name}",
            "bowler_gets_wicket": True,
        }

    def scoreline(self):
        overs = f"{self.score['balls'] // 6}.{self.score['balls'] % 6}"
        return f"{self.score['batting_team'].name} {self.score['runs']}/{self.score['wickets']} ({overs})"

    def finish_innings(self):
        batting_team = self.score["batting_team"]
        bowling_team = self.score["bowling_team"]
        runs = self.score["runs"]
        wickets = self.score["wickets"]
        balls = self.score["balls"]
        for name, data in self.score["bat_stats"].items():
            player = next((p for p in self.score["batting_order"] if p.name == name), None)
            if not player:
                continue
            if data["runs"] > player.stats["highest_score"]:
                player.stats["highest_score"] = data["runs"]
                player.stats["highest_score_against"] = bowling_team.name
            if data["runs"] >= 100:
                player.stats["hundreds"] += 1
            elif data["runs"] >= 50:
                player.stats["fifties"] += 1
        final_balls = 120 if wickets == 10 else balls
        batting_team.runs_scored += runs
        batting_team.balls_faced += final_balls
        bowling_team.runs_conceded += runs
        bowling_team.balls_bowled += final_balls
        self.innings.append({
            "team": batting_team,
            "bowling_team": bowling_team,
            "runs": runs,
            "wickets": wickets,
            "balls": balls,
            "bat_stats": self.score["bat_stats"],
            "bowl_stats": self.score["bowl_stats"],
            "batting_order": [p.name for p in self.score["batting_order"]],
            "dismissals": dict(self.score.get("dismissals", {})),
        })
        if self.current_innings == 1:
            self.current_innings = 2
            self.target = runs + 1
            self.status = "impact"
            self.message = f"Innings break. Target is {self.target}. Use one Impact Player sub if you want."
        else:
            self.complete_match()

    def setup_super_over(self):
        self.super_over = {
            "batting_first": self.inn1_bowl,
            "batting_second": self.inn1_bat,
            "batters": {},
            "bowlers": {},
            "innings": [],
            "winner": "",
            "message": f"Match tied. Super Over: {self.inn1_bowl.name} bat first.",
        }
        for team in (self.team1, self.team2):
            if team.name != self.league.user_team_name:
                self.super_over["batters"][team.name] = self.cpu_super_batters(team)
                self.super_over["bowlers"][team.name] = self.cpu_super_bowler(team)
        self.status = "super_over_setup"
        self.message = self.super_over["message"]

    def cpu_super_batters(self, team):
        xi = self.xis.get(team.name, self.league.smart_cpu_xi(team))
        return sorted(xi, key=lambda p: (p.current_batting + (8 if getattr(p, "batting_archetype", "") in ("Finisher", "Aggressor") else 0), p.current_ovr), reverse=True)[:3]

    def cpu_super_bowler(self, team):
        pool = [p for p in self.xis.get(team.name, []) if is_bowling_role(p)] or self.xis.get(team.name, [])
        return sorted(pool, key=lambda p: (self.bowler_phase_score(p, "Death Overs"), p.current_ovr), reverse=True)[0]

    def auto_missing_super_over_lineups(self):
        for team in (self.team1, self.team2):
            self.super_over["batters"].setdefault(team.name, self.cpu_super_batters(team))
            self.super_over["bowlers"].setdefault(team.name, self.cpu_super_bowler(team))

    def set_super_over_lineup(self, batter_names, bowler_name):
        if self.status != "super_over_setup":
            raise ValueError("Super Over selection is not open.")
        team = self.league.user_team()
        xi = self.xis.get(team.name, [])
        batters = [next((p for p in xi if p.name == name), None) for name in batter_names]
        batters = [p for p in batters if p]
        if len(batters) != 3 or len({p.name for p in batters}) != 3:
            raise ValueError("Pick exactly three unique Super Over batters.")
        bowlers = [p for p in xi if is_bowling_role(p)]
        bowler = next((p for p in bowlers if p.name == bowler_name), None)
        if not bowler:
            raise ValueError("Pick one eligible Super Over bowler.")
        self.super_over["batters"][team.name] = batters
        self.super_over["bowlers"][team.name] = bowler
        self.play_super_over()

    def play_super_over(self):
        first_team = self.super_over["batting_first"]
        second_team = self.super_over["batting_second"]
        first = self.simulate_super_over_innings(first_team, self.super_over["bowlers"][second_team.name])
        second = self.simulate_super_over_innings(second_team, self.super_over["bowlers"][first_team.name], target=first["runs"] + 1)
        self.super_over["innings"] = [first, second]
        if second["runs"] >= first["runs"] + 1:
            winner = second_team
            loser = first_team
            margin = "won in the Super Over"
        elif first["runs"] > second["runs"]:
            winner = first_team
            loser = second_team
            margin = "won in the Super Over"
        else:
            winner = first_team if random.random() < 0.5 else second_team
            loser = second_team if winner == first_team else first_team
            margin = "won the tied Super Over on the reserve tiebreak"
        self.super_over["winner"] = winner.name
        self.finalize_match(winner, loser, margin)

    def simulate_super_over_innings(self, batting_team, bowler, target=None):
        batters = self.super_over["batters"][batting_team.name]
        striker_idx, non_striker_idx, next_idx = 0, 1, 2
        runs = wickets = balls = 0
        batting = {p.name: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in batters}
        bowling = {bowler.name: {"runs": 0, "wickets": 0, "balls": 0}}
        events = []
        while balls < 6 and wickets < 2 and (not target or runs < target):
            striker = batters[striker_idx]
            striker.match_phase = "Death Overs"
            bowler.match_phase = "Death Overs"
            striker.batting_aggression = 5
            bowler.bowling_aggression = 3
            outcome = self.engine.simulate_ball(striker, bowler)
            balls += 1
            batting[striker.name]["balls"] += 1
            bowling[bowler.name]["balls"] += 1
            if outcome == "W":
                wickets += 1
                bowling[bowler.name]["wickets"] += 1
                events.append({"kind": "wicket", "label": "W", "description": f"{striker.name} out b {bowler.name}"})
                if wickets < 2:
                    striker_idx = next_idx
                continue
            ball_runs = int(outcome)
            runs += ball_runs
            batting[striker.name]["runs"] += ball_runs
            bowling[bowler.name]["runs"] += ball_runs
            if ball_runs == 4:
                batting[striker.name]["fours"] += 1
            if ball_runs == 6:
                batting[striker.name]["sixes"] += 1
            events.append({"kind": "runs", "label": outcome, "runs": ball_runs})
            if ball_runs in (1, 3):
                striker_idx, non_striker_idx = non_striker_idx, striker_idx
        return {
            "team": batting_team.name,
            "runs": runs,
            "wickets": wickets,
            "balls": balls,
            "bowler": bowler.name,
            "batting": [{"name": n, **d} for n, d in batting.items()],
            "bowling": [{"name": bowler.name, **bowling[bowler.name], "overs": f"0.{balls}", "econ": round(bowling[bowler.name]["runs"] / (balls / 6), 2) if balls else 0}],
            "events": events,
            "score": f"{runs}/{wickets}",
        }

    def apply_impact_sub(self, out_name=None, in_name=None, auto=False):
        user_team = self.league.user_team()
        if self.status != "impact":
            raise ValueError("Impact sub is only available at innings break.")
        if out_name and in_name:
            xi = self.xis[user_team.name]
            bench = [p for p in user_team.roster if p not in xi]
            out_player = next((p for p in xi if p.name == out_name), None)
            in_player = next((p for p in bench if p.name == in_name), None)
            if not out_player or not in_player:
                raise ValueError("Choose one player from XI and one from bench.")
            new_xi = [in_player if p == out_player else p for p in xi]
            if sum(1 for p in new_xi if p.is_overseas) > 4:
                raise ValueError("Impact sub would break the overseas limit.")
            self.xis[user_team.name] = new_xi
            order = [p for p in self.batting_orders[user_team.name] if p != out_player]
            if in_player not in order:
                order.append(in_player)
            self.batting_orders[user_team.name] = order[:11]
            self.bowling_pools[user_team.name] = [p for p in new_xi if is_bowling_role(p)] or new_xi
            if self.wicketkeepers.get(user_team.name) == out_player or self.wicketkeepers.get(user_team.name) not in new_xi:
                self.wicketkeepers[user_team.name] = self.default_keeper(user_team, new_xi)
            self.impact_subs.append(f"{user_team.name}: {out_player.name} out, {in_player.name} in")
        if auto:
            self.start_second_innings()
        else:
            self.prepare_second_innings()

    def prepare_second_innings(self):
        user_team = self.league.user_team()
        if user_team == self.inn1_bowl:
            self.status = "batting_order"
            self.message = "Set your batting order for the chase."
            return
        self.start_innings(self.inn1_bowl, self.inn1_bat, self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name])

    def start_second_innings(self):
        self.start_innings(self.inn1_bowl, self.inn1_bat, self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name])

    def complete_match(self):
        first = self.innings[0]
        second = self.innings[1]
        if second["runs"] >= first["runs"] + 1:
            winner = self.inn1_bowl
            loser = self.inn1_bat
            margin = f"won by {10 - second['wickets']} wickets"
        elif first["runs"] > second["runs"]:
            winner = self.inn1_bat
            loser = self.inn1_bowl
            margin = f"won by {first['runs'] - second['runs']} runs"
        else:
            self.setup_super_over()
            return
        self.finalize_match(winner, loser, margin)

    def finalize_match(self, winner, loser, margin):
        first = self.innings[0]
        second = self.innings[1]
        winner.wins += 1
        winner.points += 2
        loser.losses += 1
        involved_by_team = {winner.name: set(), loser.name: set()}
        for innings in (first, second):
            involved_by_team.setdefault(innings["team"].name, set()).update(innings.get("batting_order", []))
            involved_by_team.setdefault(innings["bowling_team"].name, set()).update(innings.get("bowl_stats", {}).keys())
        seen_players = set()
        for name in involved_by_team.get(winner.name, set()):
            player = self.league.find_player_anywhere(name)
            if not player:
                continue
            ensure_stat_fields(player)
            player.stats["games"] += 1
            player.stats["team_wins"] += 1
            seen_players.add(player.name)
        for name in involved_by_team.get(loser.name, set()):
            player = self.league.find_player_anywhere(name)
            if not player:
                continue
            ensure_stat_fields(player)
            if player.name not in seen_players:
                player.stats["games"] += 1
        all_bat = {**first["bat_stats"], **second["bat_stats"]}
        all_bowl = {**first["bowl_stats"], **second["bowl_stats"]}
        players = [
            p for name in set().union(*involved_by_team.values())
            for p in [self.league.find_player_anywhere(name)] if p
        ]
        motm = self.league.select_motm(all_bat, all_bowl, players, winner)
        ensure_stat_fields(motm)
        motm.stats["motm"] += 1
        self.league.update_bowling_bests(self.bowling_pools[self.inn1_bowl.name], first["bowl_stats"], self.inn1_bat.name)
        self.league.update_bowling_bests(self.bowling_pools[self.inn1_bat.name], second["bowl_stats"], self.inn1_bowl.name)
        self.engine.eval_match_performances_for_form(self.batting_orders[self.inn1_bat.name], self.bowling_pools[self.inn1_bowl.name], first["bat_stats"], first["bowl_stats"])
        self.engine.eval_match_performances_for_form(self.batting_orders[self.inn1_bowl.name], self.bowling_pools[self.inn1_bat.name], second["bat_stats"], second["bowl_stats"])
        self.card = {
            "round": self.league.round_num,
            "stage": self.stage,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "venue": TEAM_META[self.team1.name]["home"],
            "toss": f"{self.toss_winner.name} chose to {self.decision}",
            "winner": winner.name,
            "margin": margin,
            "summary": f"{winner.name} {margin}",
            "motm": motm.name,
            "innings": [self.league.innings_card(first), self.league.innings_card(second)],
            "impact_subs": list(self.impact_subs),
            "super_over": self.super_over_card(),
        }
        self.league.match_log.append(self.card)
        if not hasattr(self.league, "fixture_results"):
            self.league.fixture_results = []
        self.league.fixture_results.append(self.card)
        self.status = "complete"
        self.message = self.card["summary"]

    def payload(self):
        user_team = self.league.user_team()
        innings_payload = []
        for inn in self.innings:
            innings_payload.append(self.league.innings_card(inn))
        suggested_players = self.suggested_roster(self.lineup_context() == "bowling")
        if self.status == "batting_order" and user_team.name in self.xis:
            suggested_players = self.xis[user_team.name]
        return {
            "status": self.status,
            "stage": self.stage,
            "team1": self.team1.name,
            "team2": self.team2.name,
            "toss_winner": self.toss_winner.name,
            "decision": self.decision,
            "message": self.message,
            "user_toss": self.status == "toss" and self.toss_winner.name == user_team.name,
            "lineup_context": self.lineup_context(),
            "impact_context": self.impact_context(),
            "suggested": [self.league.player_dict(p) for p in suggested_players],
            "saved_xi": user_team.saved_playing_xi_names,
            "saved_wicketkeeper": getattr(user_team, "saved_wicketkeeper_name", ""),
            "batting_first_xi": getattr(user_team, "saved_batting_first_xi_names", []) or self.league.smart_batting_first_xi(user_team),
            "bowling_first_xi": getattr(user_team, "saved_bowling_first_xi_names", []) or self.league.smart_bowling_first_xi(user_team),
            "saved_order": user_team.saved_batting_order_names,
            "saved_bowling_order": getattr(user_team, "saved_bowling_over_names", []),
            "score": self.live_score_payload(),
            "available_bowlers": [self.live_bowler_dict(p) for p in self.available_bowlers()],
            "impact": self.impact_payload(),
            "super_over": self.super_over_payload(),
            "innings": innings_payload,
            "card": self.card,
        }

    def live_bowler_dict(self, player):
        data = self.score["bowl_stats"].get(player.name, {}) if self.score else {}
        payload = self.league.player_dict(player)
        balls = data.get("balls", 0)
        runs = data.get("runs", 0)
        payload["match_econ"] = round(runs / (balls / 6), 2) if balls else "-"
        payload["match_overs"] = f"{balls // 6}.{balls % 6}"
        payload["match_wickets"] = data.get("wickets", 0)
        return payload

    def lineup_context(self):
        if self.status not in ("lineup", "batting_order"):
            return ""
        if self.status == "batting_order":
            return "batting"
        user = self.league.user_team()
        if user == self.inn1_bowl:
            return "bowling"
        return "batting"

    def impact_context(self):
        if self.status != "impact":
            return ""
        user = self.league.user_team()
        return "bat_to_bowl" if user == self.inn1_bat else "bowl_to_bat"

    def live_score_payload(self):
        if not self.score:
            return None
        order = self.score["batting_order"]
        striker = order[min(self.score["striker_idx"], len(order) - 1)] if order else None
        non_striker = order[min(self.score["non_striker_idx"], len(order) - 1)] if order else striker
        striker_name = striker.name if striker else ""
        non_striker_name = non_striker.name if non_striker else ""
        return {
            "scoreline": self.scoreline(),
            "runs": self.score["runs"],
            "wickets": self.score["wickets"],
            "balls": self.score["balls"],
            "target": self.target,
            "batting_team": self.score["batting_team"].name,
            "bowling_team": self.score["bowling_team"].name,
            "user_bowling": self.score["bowling_team"].name == self.league.user_team_name,
            "user_batting": self.score["batting_team"].name == self.league.user_team_name,
            "striker": striker_name,
            "non_striker": non_striker_name,
            "partnership": f"{self.score['partnership_runs']} off {self.score['partnership_balls']}",
            "phase": innings_phase(self.score["balls"] // 6),
            "active_bowler": self.score["active_bowler"].name if self.score.get("active_bowler") else "",
            "pending_next_batter": self.score.get("pending_next_batter", False),
            "striker_aggression": self.score["batting_aggression"].get(striker_name, 3),
            "non_striker_aggression": self.score["batting_aggression"].get(non_striker_name, 3),
            "bowler_aggression": self.score["bowling_aggression"].get(self.score["active_bowler"].name, 2) if self.score.get("active_bowler") else 2,
            "current_over": self.score.get("current_over_events", []),
            "next_batter_options": [self.league.player_dict(p) for p in self.score["batting_order"][self.score["striker_idx"]:] if self.score.get("pending_next_batter")],
            "last_wicket": self.score.get("current_over_events", [])[-1] if self.score.get("current_over_events", []) and self.score.get("current_over_events", [])[-1].get("kind") == "wicket" else None,
            "bat_stats": [{"name": n, "dismissal": self.score.get("dismissals", {}).get(n, ""), **d} for n, d in self.score["bat_stats"].items()],
            "bowl_stats": [{"name": n, **d, "overs": f"{d['balls'] // 6}.{d['balls'] % 6}", "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0} for n, d in self.score["bowl_stats"].items()],
            "over_log": self.score["over_log"][-6:],
        }

    def impact_payload(self):
        if self.status != "impact":
            return None
        user = self.league.user_team()
        xi = self.xis[user.name]
        bench = [p for p in user.roster if p not in xi]
        return {
            "xi": [self.league.player_dict(p) for p in xi],
            "bench": [self.league.player_dict(p) for p in bench],
        }

    def super_over_payload(self):
        if self.status != "super_over_setup" or not self.super_over:
            return self.super_over_card()
        user = self.league.user_team()
        xi = self.xis.get(user.name, [])
        return {
            "message": self.super_over["message"],
            "batting_first": self.super_over["batting_first"].name,
            "batting_second": self.super_over["batting_second"].name,
            "batters": [self.league.player_dict(p) for p in sorted(xi, key=lambda p: p.current_batting, reverse=True)],
            "bowlers": [self.league.player_dict(p) for p in sorted([p for p in xi if is_bowling_role(p)], key=lambda p: p.current_bowling, reverse=True)],
            "innings": self.super_over.get("innings", []),
            "winner": self.super_over.get("winner", ""),
        }

    def super_over_card(self):
        if not self.super_over:
            return None
        return {
            "batting_first": self.super_over["batting_first"].name,
            "batting_second": self.super_over["batting_second"].name,
            "innings": list(self.super_over.get("innings", [])),
            "winner": self.super_over.get("winner", ""),
            "message": self.super_over.get("message", ""),
        }


class LeagueState:
    def __init__(self):
        self.phase = "title"
        self.season_year = 2026
        self.completed_seasons = 0
        self.difficulty = "hard"
        self.user_team_name = ""
        self.player_pool = []
        self.teams = []
        self.draft_type = "mega"
        self.draft_order = []
        self.draft_round = 1
        self.draft_index = 0
        self.draft_started = False
        self.pick_num = 1
        self.draft_history = []
        self.round_num = 1
        self.schedule = []
        self.match_log = []
        self.fixture_results = []
        self.playoff_matches = []
        self.playoff_index = 0
        self.playoff_results = []
        self.pending_playoff_top_four = []
        self.season_history = []
        self.status_message = "Create a league or load your saved IPL universe."
        self.live_match = None
        self.retention_limit = RETAIN_NORMAL
        self.last_standings = []

    def save(self):
        with open(SAVE_FILE, "wb") as handle:
            pickle.dump(self, handle)

    @classmethod
    def load(cls):
        if not os.path.exists(SAVE_FILE):
            raise ValueError("No local UI save exists yet.")
        with open(SAVE_FILE, "rb") as handle:
            state = pickle.load(handle)
        state.migrate()
        return state

    def migrate(self):
        self.fixture_results = getattr(self, "fixture_results", [])
        self.match_log = getattr(self, "match_log", [])
        self.playoff_results = getattr(self, "playoff_results", [])
        self.pending_playoff_top_four = getattr(self, "pending_playoff_top_four", [])
        self.draft_started = getattr(self, "draft_started", self.phase != "draft" or bool(self.draft_history))
        self.last_standings = getattr(self, "last_standings", [])
        self.retention_limit = getattr(self, "retention_limit", RETAIN_NORMAL)
        self.difficulty = getattr(self, "difficulty", "hard")
        if self.difficulty not in ("easy", "medium", "hard"):
            self.difficulty = "hard"
        try:
            current_player_data = {p.name: p for p in get_initial_player_pool()}
        except Exception:
            current_player_data = {}
        if getattr(self, "live_match", None):
            if getattr(self.live_match, "engine", None):
                self.live_match.engine.difficulty = self.difficulty
                self.live_match.engine.user_team_name = self.user_team_name
            self.live_match.super_over = getattr(self.live_match, "super_over", None)
            self.live_match.impact_subs = getattr(self.live_match, "impact_subs", [])
            self.live_match.pending_second_lineup = getattr(self.live_match, "pending_second_lineup", False)
            if getattr(self.live_match, "score", None):
                self.live_match.score.setdefault("active_bowler", None)
                self.live_match.score.setdefault("current_over_events", [])
                self.live_match.score.setdefault("pending_next_batter", False)
                self.live_match.score.setdefault("batting_aggression", {p.name: 3 for p in self.live_match.score.get("batting_order", [])})
                self.live_match.score.setdefault("bowling_aggression", {p.name: 2 for p in self.live_match.score.get("bowling_pool", [])})
        for team in getattr(self, "teams", []):
            team.saved_playing_xi_names = getattr(team, "saved_playing_xi_names", [])
            team.saved_batting_first_xi_names = getattr(team, "saved_batting_first_xi_names", [])
            team.saved_bowling_first_xi_names = getattr(team, "saved_bowling_first_xi_names", [])
            team.saved_bat_to_bowl_sub = getattr(team, "saved_bat_to_bowl_sub", {"out": "", "in": ""})
            team.saved_bowl_to_bat_sub = getattr(team, "saved_bowl_to_bat_sub", {"out": "", "in": ""})
            team.saved_wicketkeeper_name = getattr(team, "saved_wicketkeeper_name", "")
            team.saved_batting_order_names = getattr(team, "saved_batting_order_names", [])
            team.saved_bowling_over_names = getattr(team, "saved_bowling_over_names", [])
            for player in team.roster:
                ensure_stat_fields(player)
                current = current_player_data.get(player.name)
                if current:
                    player.batting_archetype = current.batting_archetype
                    player.bowling_phase = current.bowling_phase
                    player.bowling_type = current.bowling_type
                    player.strengths = current.strengths
                    player.weaknesses = current.weaknesses
                player.base_ovr = max(player.batting_ovr, player.bowling_ovr)
        for player in getattr(self, "player_pool", []):
            ensure_stat_fields(player)
            current = current_player_data.get(player.name)
            if current:
                player.batting_archetype = current.batting_archetype
                player.bowling_phase = current.bowling_phase
                player.bowling_type = current.bowling_type
                player.strengths = current.strengths
                player.weaknesses = current.weaknesses
            player.base_ovr = max(player.batting_ovr, player.bowling_ovr)
        known_names = {p.name for p in getattr(self, "player_pool", [])}
        for team in getattr(self, "teams", []):
            known_names.update(p.name for p in team.roster)
        for player in current_player_data.values():
            if player.name not in known_names:
                player.team_name = "Unassigned"
                ensure_stat_fields(player)
                self.player_pool.append(player)

    def new_league(self, user_team_name, difficulty="hard"):
        if user_team_name not in IPL_TEAMS_LIST:
            raise ValueError("Choose a valid IPL franchise.")
        self.__init__()
        self.season_year = 2026
        self.difficulty = difficulty if difficulty in ("easy", "medium", "hard") else "hard"
        self.user_team_name = user_team_name
        self.player_pool = get_initial_player_pool()
        self.teams = [Team(name) for name in IPL_TEAMS_LIST]
        self.phase = "draft"
        self.draft_type = "mega"
        self.draft_order = list(self.teams)
        random.shuffle(self.draft_order)
        self.draft_started = False
        self.match_log = []
        self.fixture_results = []
        self.live_match = None
        user_pick = self.draft_order.index(self.user_team()) + 1
        self.status_message = f"{user_team_name} enter a blank-franchise mega draft on {self.difficulty.title()} mode. You draft {ordinal(user_pick)}. Start the draft when ready."

    def build_schedule(self):
        schedule = []
        for _ in range(14):
            teams = list(self.teams)
            random.shuffle(teams)
            schedule.append([(teams[i].name, teams[i + 1].name) for i in range(0, len(teams), 2)])
        return schedule

    def user_team(self):
        return self.find_team(self.user_team_name)

    def find_team(self, name):
        return next(t for t in self.teams if t.name == name)

    def standings(self, reverse=True):
        return sorted(self.teams, key=lambda t: (t.points, t.net_run_rate, t.wins), reverse=reverse)

    def current_draft_order(self):
        if self.draft_type == "mega" and self.draft_round % 2 == 0:
            return list(reversed(self.draft_order))
        return list(self.draft_order)

    def current_draft_team(self):
        if self.phase != "draft":
            return None
        return self.current_draft_order()[self.draft_index]

    def start_draft(self):
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        self.draft_started = True
        self.status_message = "Mega draft live. Squads are 21 players."
        self.cpu_until_user()

    def roster_needs(self, team):
        return {
            "wk": max(0, 2 - sum(1 for p in team.roster if is_wicketkeeper_option(p))),
            "bat": max(0, 9 - sum(1 for p in team.roster if batting_slot_player(p))),
            "bowl": max(0, 9 - sum(1 for p in team.roster if bowling_slot_player(p))),
            "ar": max(0, 2 - sum(1 for p in team.roster if p.role == "All-Rounder")),
            "fast": max(0, 4 - sum(1 for p in team.roster if p.role == "Bowler (Fast)")),
            "spin": max(0, 3 - sum(1 for p in team.roster if p.role == "Bowler (Spin)")),
        }

    def draft_score(self, team, player):
        needs = self.roster_needs(team)
        picks_left = SQUAD_SIZE - len(team.roster)
        score = player.current_ovr * 10 + max(0, 30 - player.age) * 1.6
        role_counts = {
            "wk": sum(1 for p in team.roster if is_wicketkeeper_option(p)),
            "bat": sum(1 for p in team.roster if p.role == "Batsman"),
            "bowl": sum(1 for p in team.roster if bowling_slot_player(p)),
            "ar": sum(1 for p in team.roster if p.role == "All-Rounder"),
        }
        if is_wicketkeeper_option(player):
            score += 8 if needs["wk"] else 0
        if player.role == "All-Rounder":
            two_way_value = (player.current_batting + player.current_bowling) * 0.30
            elite_side = max(player.current_batting, player.current_bowling) * 0.22
            score += two_way_value + elite_side + needs["ar"] * 16
            score += min(needs["bat"], 1) * 7 + min(needs["bowl"], 1) * 7
            if role_counts["ar"] >= 4:
                score -= 25 + (role_counts["ar"] - 3) * 20
        elif is_batting_role(player):
            score += player.current_batting * 0.30 + needs["bat"] * 7
            if role_counts["bat"] >= 8:
                score -= 25
        elif is_bowling_role(player):
            score += player.current_bowling * 0.30 + needs["bowl"] * 7
            if role_counts["bowl"] >= 8:
                score -= 25
        if player.role == "Bowler (Fast)":
            score += needs["fast"] * 5
        if player.role == "Bowler (Spin)":
            score += needs["spin"] * 5
        overseas = sum(1 for p in team.roster if p.is_overseas)
        if player.is_overseas and overseas >= 8:
            score -= 70
        if player.is_overseas and overseas >= 10:
            score -= 999
        if picks_left <= sum(needs.values()) and not self.player_matches_need(player, needs):
            score -= 65
        return score + random.uniform(-10, 10)

    def player_matches_need(self, player, needs):
        return (
            (is_wicketkeeper_option(player) and needs["wk"]) or
            (player.role == "All-Rounder" and needs["ar"]) or
            (batting_slot_player(player) and needs["bat"]) or
            (bowling_slot_player(player) and needs["bowl"]) or
            (player.role == "Bowler (Fast)" and needs["fast"]) or
            (player.role == "Bowler (Spin)" and needs["spin"])
        )

    def cpu_pick(self, team):
        candidates = sorted(self.player_pool, key=lambda p: self.draft_score(team, p), reverse=True)
        self.draft_player(team, candidates[0])

    def draft_player(self, team, player):
        self.player_pool.remove(player)
        team.roster.append(player)
        player.team_name = team.name
        self.draft_history.append({
            "season": self.season_year,
            "type": self.draft_type,
            "round": self.draft_round,
            "pick": self.pick_num,
            "team": team.name,
            "player": player.name,
            "ovr": player.current_ovr,
            "role": player.role,
        })
        self.pick_num += 1
        self.draft_index += 1
        if self.draft_index >= len(self.draft_order):
            self.draft_index = 0
            self.draft_round += 1
        if all(len(t.roster) >= SQUAD_SIZE for t in self.teams):
            self.start_regular_season()

    def capture_season_baselines(self):
        for player in self.all_players():
            player.season_start_ovr = player.current_ovr
            player.season_start_bat = player.current_batting
            player.season_start_bowl = player.current_bowling

    def cpu_until_user(self):
        while self.phase == "draft":
            team = self.current_draft_team()
            if team.name == self.user_team_name:
                return
            self.cpu_pick(team)

    def user_pick(self, player_name):
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        player = next((p for p in self.player_pool if p.name == player_name), None)
        if not player:
            raise ValueError("Player is no longer available.")
        self.draft_player(self.current_draft_team(), player)
        self.cpu_until_user()

    def autodraft_user_pick(self):
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        team = self.current_draft_team()
        if team.name != self.user_team_name:
            self.cpu_until_user()
            team = self.current_draft_team()
        self.cpu_pick(team)
        self.cpu_until_user()

    def autodraft_to_end(self):
        if self.phase != "draft":
            raise ValueError("Draft room is closed.")
        if not getattr(self, "draft_started", True):
            self.start_draft()
        while self.phase == "draft":
            self.cpu_pick(self.current_draft_team())

    def start_regular_season(self):
        self.phase = "season"
        self.round_num = 1
        self.schedule = self.build_schedule()
        self.live_match = None
        self.match_log = []
        self.fixture_results = []
        self.playoff_matches = []
        self.playoff_results = []
        self.playoff_index = 0
        self.pending_playoff_top_four = []
        for team in self.teams:
            if not team.captain or team.captain not in team.roster:
                team.auto_assign_cpu_leadership()
        self.capture_season_baselines()
        self.status_message = f"IPL {self.season_year} league stage is ready."

    def set_leadership(self, captain_name, vice_name, wicketkeeper_name=""):
        team = self.user_team()
        captain = next((p for p in team.roster if p.name == captain_name), None)
        vice = next((p for p in team.roster if p.name == vice_name), None)
        if not captain or not vice or captain == vice:
            raise ValueError("Choose two different players from your squad.")
        team.captain = captain
        team.vice_captain = vice
        if wicketkeeper_name:
            keeper = next((p for p in team.roster if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None)
            if not keeper:
                raise ValueError("Choose an eligible wicketkeeper from your squad.")
            team.saved_wicketkeeper_name = keeper.name

    def set_user_presets(self, batting_order, bowling_order, batting_first_xi=None, bowling_first_xi=None, bat_to_bowl=None, bowl_to_bat=None, wicketkeeper_name=""):
        team = self.user_team()
        roster_names = {p.name for p in team.roster}
        for attr, names in (("saved_batting_first_xi_names", batting_first_xi or []), ("saved_bowling_first_xi_names", bowling_first_xi or [])):
            clean_xi = [name for name in names if name in roster_names]
            if clean_xi:
                if len(clean_xi) != 11 or len(set(clean_xi)) != 11:
                    raise ValueError("Saved XI presets must contain 11 unique squad players.")
                players = [next(p for p in team.roster if p.name == name) for name in clean_xi]
                if sum(1 for p in players if p.is_overseas) > 4:
                    raise ValueError("Saved XI presets cannot include more than 4 overseas players.")
                if attr == "saved_batting_first_xi_names" and len([p for p in players if counts_as_batter(p)]) < 6:
                    raise ValueError("Batting First XI needs at least 6 batting options including all-rounders and wicketkeepers.")
                if attr == "saved_bowling_first_xi_names" and len([p for p in players if counts_as_bowler(p)]) < 5:
                    raise ValueError("Bowling First XI needs at least 5 bowling options including all-rounders.")
                setattr(team, attr, clean_xi)
        if batting_first_xi and bowling_first_xi:
            bat_set = set([name for name in batting_first_xi if name in roster_names])
            bowl_set = set([name for name in bowling_first_xi if name in roster_names])
            if len(bat_set) == 11 and len(bowl_set) == 11 and len(bat_set - bowl_set) > 1:
                raise ValueError("Batting First XI and Bowling First XI can be identical or differ by only one impact-sub player.")
        if bat_to_bowl:
            team.saved_bat_to_bowl_sub = {"out": bat_to_bowl.get("out", ""), "in": bat_to_bowl.get("in", "")}
        if bowl_to_bat:
            team.saved_bowl_to_bat_sub = {"out": bowl_to_bat.get("out", ""), "in": bowl_to_bat.get("in", "")}
        manual_bat_to_bowl = bool((bat_to_bowl or {}).get("out") and (bat_to_bowl or {}).get("in"))
        manual_bowl_to_bat = bool((bowl_to_bat or {}).get("out") and (bowl_to_bat or {}).get("in"))
        if batting_first_xi and bowling_first_xi and (not manual_bat_to_bowl or not manual_bowl_to_bat):
            bat_only = next((name for name in batting_first_xi if name not in bowling_first_xi), "")
            bowl_only = next((name for name in bowling_first_xi if name not in batting_first_xi), "")
            if bat_only and bowl_only:
                if not manual_bat_to_bowl:
                    team.saved_bat_to_bowl_sub = {"out": bat_only, "in": bowl_only}
                if not manual_bowl_to_bat:
                    team.saved_bowl_to_bat_sub = {"out": bowl_only, "in": bat_only}
        if wicketkeeper_name:
            keeper = next((p for p in team.roster if p.name == wicketkeeper_name and is_wicketkeeper_option(p)), None)
            if not keeper:
                raise ValueError("Choose an eligible wicketkeeper from your squad.")
            team.saved_wicketkeeper_name = wicketkeeper_name
        batting = [name for name in batting_order if name in roster_names]
        if batting and (len(batting) != 11 or len(set(batting)) != 11):
            raise ValueError("Default batting order must contain 11 unique squad players.")
        bowlers = {p.name for p in team.roster if is_bowling_role(p)}
        bowling = [name for name in bowling_order if name in bowlers]
        if bowling and len(bowling) != 20:
            raise ValueError("Default bowling plan must contain 20 overs, or leave it blank.")
        if bowling and any(bowling.count(name) > 4 for name in set(bowling)):
            raise ValueError("No bowler can bowl more than 4 overs.")
        if bowling and any(bowling[i] == bowling[i - 1] for i in range(1, len(bowling))):
            raise ValueError("A bowler cannot bowl consecutive overs.")
        team.saved_batting_order_names = batting or list(getattr(team, "saved_batting_first_xi_names", []))
        team.saved_bowling_over_names = bowling

    def default_bowling_plan(self, team):
        saved = list(getattr(team, "saved_bowling_over_names", []))
        if saved:
            return saved
        xi_names = list(getattr(team, "saved_bowling_first_xi_names", [])) or self.smart_bowling_first_xi(team)
        xi = [next((p for p in team.roster if p.name == name), None) for name in xi_names]
        xi = [p for p in xi if p]
        bowlers = sorted([p for p in xi if is_bowling_role(p)], key=lambda p: p.current_bowling, reverse=True)
        if not bowlers:
            bowlers = sorted(team.roster, key=lambda p: p.current_bowling, reverse=True)[:5]
        if len(bowlers) < 5:
            return []
        def best_for_phase(phase, used, last_name):
            candidates = [p for p in bowlers if used.get(p.name, 0) < 4]
            non_repeat = [p for p in candidates if p.name != last_name]
            if non_repeat:
                candidates = non_repeat
            return sorted(candidates, key=lambda p: self.bowler_phase_score(p, phase), reverse=True)[0]
        if not bowlers:
            return []
        used = {}
        plan = []
        for over in range(20):
            phase = innings_phase(over)
            bowler = best_for_phase(phase, used, plan[-1] if plan else "")
            plan.append(bowler.name)
            used[bowler.name] = used.get(bowler.name, 0) + 1
        return plan

    def default_batting_order(self, team):
        if len(team.roster) < 11:
            return []
        xi_names = getattr(team, "saved_batting_first_xi_names", []) or self.smart_batting_first_xi(team)
        xi = [next((p for p in team.roster if p.name == name), None) for name in xi_names]
        xi = [p for p in xi if p]
        return [p.name for p in self.smart_batting_order(xi)]

    def bowler_phase_score(self, player, phase):
        score = player.current_bowling
        kind = bowling_kind(player)
        bowling_phase = getattr(player, "bowling_phase", "Flexible")
        bowling_type = getattr(player, "bowling_type", "")
        if bowling_phase == phase:
            score += 9
        if phase in ("Powerplay", "Death Overs") and kind == "pace":
            score += 5
        if phase == "Middle Overs" and kind == "spin":
            score += 7
        if phase == "Death Overs" and "Variations" in bowling_type:
            score += 5
        if "Mystery" in bowling_phase or "Mystery" in bowling_type:
            score += 2
        return score

    def batting_phase_score(self, player, phase):
        score = player.current_batting
        archetype = getattr(player, "batting_archetype", "")
        if phase == "Powerplay" and archetype in ("Aggressive Opener", "Aggressor", "Pace Specialist"):
            score += 10
        elif phase == "Powerplay" and archetype == "Anchor":
            score += 5
        elif phase == "Middle Overs" and archetype in ("Middle-over Rotator", "Strike Rotator", "Spin Specialist"):
            score += 9
        elif phase == "Death Overs" and archetype in ("Finisher", "Lower-order Hitter"):
            score += 11
        elif archetype == "Defensive Tailender":
            score -= 18
        if phase.lower().split()[0] in getattr(player, "strengths", "").lower():
            score += 3
        return score

    def smart_batting_order(self, players):
        remaining = list(dict.fromkeys(players))
        order = []

        def archetype(player):
            return getattr(player, "batting_archetype", "")

        def batting_capable(player):
            return counts_as_batter(player) or (player.current_batting >= 65 and archetype(player) != "Defensive Tailender")

        def is_tail(player):
            return archetype(player) == "Defensive Tailender" or not batting_capable(player)

        def pick_one(predicate, phase, fallback=True):
            nonlocal remaining
            pool = [p for p in remaining if predicate(p)]
            if not pool and fallback:
                pool = [p for p in remaining if not is_tail(p)]
            if not pool and fallback:
                pool = list(remaining)
            if not pool:
                return None
            chosen = sorted(pool, key=lambda p: (self.batting_phase_score(p, phase), p.current_batting, p.current_ovr), reverse=True)[0]
            order.append(chosen)
            remaining.remove(chosen)
            return chosen

        opener = lambda p: archetype(p) in ("Aggressor", "Aggressive Opener", "Pace Specialist", "Anchor", "Strike Rotator", "Middle-over Rotator") and batting_capable(p)
        top_middle = lambda p: archetype(p) in ("Aggressor", "Aggressive Opener", "Pace Specialist", "Anchor", "Strike Rotator", "Middle-over Rotator", "Spin Specialist") and batting_capable(p)
        middle = lambda p: archetype(p) in ("Anchor", "Strike Rotator", "Middle-over Rotator", "Spin Specialist") and batting_capable(p)
        finisher = lambda p: archetype(p) in ("Finisher", "Lower-order Hitter", "Lower-order Power Hitter") and batting_capable(p)

        pick_one(opener, "Powerplay")
        pick_one(opener, "Powerplay")
        pick_one(top_middle, "Middle Overs")
        pick_one(middle, "Middle Overs")
        pick_one(middle, "Middle Overs")
        pick_one(lambda p: finisher(p) or middle(p), "Death Overs")
        pick_one(lambda p: finisher(p) or (batting_capable(p) and not is_tail(p)), "Death Overs")
        pick_one(lambda p: finisher(p) or (batting_capable(p) and not is_tail(p)), "Death Overs")

        tail = sorted(remaining, key=lambda p: (is_tail(p), -p.current_batting, -p.current_ovr))
        for player in tail:
            if len(order) >= 11:
                break
            order.append(player)

        return order[:11]

    def smart_cpu_xi(self, team):
        roster = list(team.roster)
        selected = []

        def add(player):
            if player and player not in selected and len(selected) < 11:
                selected.append(player)

        for leader in (team.captain, team.vice_captain):
            if leader in roster:
                add(leader)

        keepers = sorted([p for p in roster if is_wicketkeeper_option(p)], key=lambda p: (p.current_batting, p.current_ovr), reverse=True)
        add(keepers[0] if keepers else None)

        batters = sorted([p for p in roster if p not in selected and counts_as_batter(p)], key=lambda p: (
            self.batting_phase_score(p, "Powerplay") + self.batting_phase_score(p, "Middle Overs") + self.batting_phase_score(p, "Death Overs"),
            p.current_batting,
            p.current_ovr,
        ), reverse=True)
        for player in batters:
            if len([p for p in selected if counts_as_batter(p)]) >= 6:
                break
            add(player)

        bowlers = sorted([p for p in roster if p not in selected and counts_as_bowler(p)], key=lambda p: (
            self.bowler_phase_score(p, "Powerplay") + self.bowler_phase_score(p, "Middle Overs") + self.bowler_phase_score(p, "Death Overs"),
            p.current_bowling,
            p.current_ovr,
        ), reverse=True)
        for player in bowlers:
            if len([p for p in selected if counts_as_bowler(p)]) >= 5:
                break
            add(player)

        remaining = sorted([p for p in roster if p not in selected], key=lambda p: p.current_ovr, reverse=True)
        for player in remaining:
            add(player)

        return self.enforce_role_balance(selected, roster, min_batters=6, min_bowlers=5)

    def smart_batting_first_xi(self, team):
        roster = list(team.roster)
        selected = []
        keepers = sorted([p for p in roster if is_wicketkeeper_option(p)], key=lambda p: p.current_batting, reverse=True)
        if keepers:
            selected.append(keepers[0])
        bat_pool = sorted([p for p in roster if p not in selected], key=lambda p: self.batting_phase_score(p, "Powerplay") + self.batting_phase_score(p, "Middle Overs") + self.batting_phase_score(p, "Death Overs"), reverse=True)
        for p in bat_pool:
            if len([x for x in selected if is_batting_role(x)]) >= 7:
                break
            selected.append(p)
        bowl_pool = sorted([p for p in roster if p not in selected and is_bowling_role(p)], key=lambda p: self.bowler_phase_score(p, "Death Overs") + p.current_bowling, reverse=True)
        selected.extend(bowl_pool[:11 - len(selected)])
        selected.extend([p for p in roster if p not in selected][:11 - len(selected)])
        return [p.name for p in self.enforce_role_balance(selected, roster, min_batters=6, min_bowlers=4)]

    def smart_bowling_first_xi(self, team):
        roster = list(team.roster)
        bat_names = getattr(team, "saved_batting_first_xi_names", []) or self.smart_batting_first_xi(team)
        selected = [next((p for p in roster if p.name == name), None) for name in bat_names]
        selected = [p for p in selected if p]
        protected_batters = set(bat_names[:5])
        bench_bowlers = sorted([p for p in roster if p not in selected and counts_as_bowler(p)], key=lambda p: p.current_bowling, reverse=True)
        if not bench_bowlers:
            bench_bowlers = sorted([p for p in roster if p not in selected], key=lambda p: p.current_ovr, reverse=True)
        replace_window = [p for p in selected[5:7] if p.name not in protected_batters]
        replaceable = [p for p in replace_window if not counts_as_bowler(p)] or replace_window or sorted([p for p in selected if p.name not in protected_batters], key=lambda p: (p.current_batting, p.current_ovr))
        if bench_bowlers and replaceable:
            selected[selected.index(replaceable[0])] = bench_bowlers[0]
        selected.extend([p for p in roster if p not in selected][:11 - len(selected)])
        balanced = self.enforce_role_balance(selected, roster, min_batters=5, min_bowlers=5)
        if len(set(p.name for p in balanced) & set(bat_names)) == 11:
            bench = [p for p in sorted(roster, key=lambda p: (counts_as_bowler(p), p.current_bowling, p.current_ovr), reverse=True) if p.name not in bat_names]
            for candidate in bench:
                for idx in (6, 5, 7, 8, 9, 10):
                    trial = list(balanced)
                    trial[idx] = candidate
                    if len({p.name for p in trial}) == 11 and sum(1 for p in trial if p.is_overseas) <= 4 and len([p for p in trial if counts_as_bowler(p)]) >= 5:
                        balanced = trial
                        break
                if len(set(p.name for p in balanced) & set(bat_names)) == 10:
                    break
        return [p.name for p in balanced]

    def enforce_xi_limits(self, selected, roster):
        selected = selected[:11]
        while sum(1 for p in selected if p.is_overseas) > 4:
            overseas = [p for p in selected if p.is_overseas]
            remove = sorted(overseas, key=lambda p: p.current_ovr)[0]
            selected.remove(remove)
            domestic = next((p for p in sorted(roster, key=lambda p: p.current_ovr, reverse=True) if not p.is_overseas and p not in selected), None)
            if domestic:
                selected.append(domestic)
            else:
                break
        return selected[:11]

    def enforce_role_balance(self, selected, roster, min_batters=0, min_bowlers=0):
        selected = list(dict.fromkeys(selected))[:11]
        pool = sorted([p for p in roster if p not in selected], key=lambda p: p.current_ovr, reverse=True)
        def add_for(predicate, remove_key):
            nonlocal selected, pool
            candidate = next((p for p in pool if predicate(p)), None)
            if not candidate:
                return False
            removable = sorted([p for p in selected if not predicate(p)], key=remove_key)
            if not removable:
                return False
            out = removable[0]
            selected.remove(out)
            selected.append(candidate)
            pool.remove(candidate)
            pool.append(out)
            return True
        while len([p for p in selected if counts_as_batter(p)]) < min_batters:
            if not add_for(counts_as_batter, lambda p: p.current_batting):
                break
        while len([p for p in selected if counts_as_bowler(p)]) < min_bowlers:
            if not add_for(counts_as_bowler, lambda p: p.current_bowling):
                break
        return self.enforce_xi_limits(selected, roster)

    def default_impact_subs(self, team):
        bat_xi = set(getattr(team, "saved_batting_first_xi_names", []) or self.smart_batting_first_xi(team))
        bowl_xi = set(getattr(team, "saved_bowling_first_xi_names", []) or self.smart_bowling_first_xi(team))
        bat_only = list(bat_xi - bowl_xi)
        bowl_only = list(bowl_xi - bat_xi)
        if bat_only and bowl_only:
            return {
                "bat_to_bowl": {"out": bat_only[0], "in": bowl_only[0]},
                "bowl_to_bat": {"out": bowl_only[0], "in": bat_only[0]},
            }
        bench_after_bat = [p for p in team.roster if p.name not in bat_xi]
        bench_after_bowl = [p for p in team.roster if p.name not in bowl_xi]
        bat_out = sorted([p for p in team.roster if p.name in bat_xi], key=lambda p: p.current_bowling)[0] if bat_xi else None
        bowl_in = sorted([p for p in bench_after_bat if is_bowling_role(p)], key=lambda p: p.current_bowling, reverse=True)
        bowl_out = sorted([p for p in team.roster if p.name in bowl_xi], key=lambda p: p.current_batting)[0] if bowl_xi else None
        bat_in = sorted([p for p in bench_after_bowl if is_batting_role(p)], key=lambda p: p.current_batting, reverse=True)
        return {
            "bat_to_bowl": {"out": bat_out.name if bat_out else "", "in": bowl_in[0].name if bowl_in else ""},
            "bowl_to_bat": {"out": bowl_out.name if bowl_out else "", "in": bat_in[0].name if bat_in else ""},
        }

    def begin_match_day(self, interactive=True):
        if self.phase not in ("season", "playoffs"):
            raise ValueError("Match centre is not open.")
        if self.live_match and self.live_match.status != "complete":
            return
        if self.phase == "season":
            self.match_log = []
            fixtures = self.schedule[self.round_num - 1]
            user_fixture = next(pair for pair in fixtures if self.user_team_name in pair)
            for team_a, team_b in fixtures:
                if (team_a, team_b) == user_fixture:
                    continue
                self.simulate_match_auto(self.find_team(team_a), self.find_team(team_b), "League")
            if interactive:
                self.live_match = LiveMatch(self, self.find_team(user_fixture[0]), self.find_team(user_fixture[1]), "League")
            else:
                self.simulate_match_auto(self.find_team(user_fixture[0]), self.find_team(user_fixture[1]), "League")
                self.round_num += 1
                if self.round_num > 14:
                    self.finish_league_stage()
        else:
            match = self.playoff_matches[self.playoff_index]
            if match["status"] == "locked":
                self.unlock_playoff_match()
                match = self.playoff_matches[self.playoff_index]
            if self.user_team_name not in (match["team1"], match["team2"]):
                raise ValueError("Your team is not in the next playoff. Use Quick Sim Next Playoff.")
            self.live_match = LiveMatch(self, self.find_team(match["team1"]), self.find_team(match["team2"]), match["name"])

    def complete_live_match(self):
        if not self.live_match or self.live_match.status != "complete":
            raise ValueError("Live match is not complete.")
        if self.phase == "season":
            self.round_num += 1
            if self.round_num > 14:
                self.finish_league_stage()
        else:
            self.record_playoff_result(self.live_match.card["winner"])
        self.live_match = None

    def simulate_match_auto(self, team1, team2, stage):
        match = LiveMatch(self, team1, team2, stage)
        if match.status == "toss":
            match.choose_toss(random.choice(["bat", "bowl"]))
        for team in (team1, team2):
            if team.name not in match.xis:
                if team.name == self.user_team_name:
                    preset_names = getattr(team, "saved_batting_first_xi_names", []) if team == match.inn1_bat else getattr(team, "saved_bowling_first_xi_names", [])
                    xi = [next((p for p in team.roster if p.name == name), None) for name in preset_names]
                    xi = [p for p in xi if p]
                    if len(xi) != 11:
                        xi_names = self.smart_batting_first_xi(team) if team == match.inn1_bat else self.smart_bowling_first_xi(team)
                        xi = [next(p for p in team.roster if p.name == name) for name in xi_names]
                else:
                    xi = self.smart_cpu_xi(team)
                match.xis[team.name] = xi
                saved_order = getattr(team, "saved_batting_order_names", []) if team.name == self.user_team_name else []
                order = [next((p for p in xi if p.name == name), None) for name in saved_order]
                order = [p for p in order if p]
                match.batting_orders[team.name] = order if len(order) == 11 else self.smart_batting_order(xi)
                match.bowling_pools[team.name] = [p for p in xi if is_bowling_role(p)] or xi
                if team.name == self.user_team_name:
                    match.set_bowling_plan(team, getattr(team, "saved_bowling_over_names", []))
        match.start_first_innings_if_ready()
        while match.status == "over":
            match.play_over(auto=True)
        if match.status == "impact":
            match.apply_impact_sub(auto=True)
        while match.status == "over":
            match.play_over(auto=True)
        if match.status == "super_over_setup":
            match.auto_missing_super_over_lineups()
            match.play_super_over()
        return match.card

    def simulate_current_round(self):
        if self.phase == "season":
            if self.live_match:
                if self.live_match.status != "complete":
                    card = self.simulate_match_auto(self.live_match.team1, self.live_match.team2, self.live_match.stage)
                    self.live_match = None
                else:
                    card = self.live_match.card
                    self.live_match = None
                self.round_num += 1
                if self.round_num > 14:
                    self.finish_league_stage()
                else:
                    self.status_message = f"Round {self.round_num - 1} completed, including {card['team1']} vs {card['team2']}."
                return
            self.match_log = []
            completed = []
            for team_a, team_b in self.schedule[self.round_num - 1]:
                card = self.simulate_match_auto(self.find_team(team_a), self.find_team(team_b), "League")
                completed.append(card)
            self.round_num += 1
            if self.round_num > 14:
                self.finish_league_stage()
            else:
                user_card = next((card for card in completed if self.user_team_name in (card["team1"], card["team2"])), None)
                if user_card:
                    self.status_message = f"Round {self.round_num - 1} quick-simmed all 5 matches, including {user_card['team1']} vs {user_card['team2']}."
                else:
                    self.status_message = f"Round {self.round_num - 1} quick-simmed all 5 matches."
        elif self.phase == "playoffs":
            match = self.playoff_matches[self.playoff_index]
            if match["status"] == "locked":
                self.unlock_playoff_match()
                match = self.playoff_matches[self.playoff_index]
            card = self.simulate_match_auto(self.find_team(match["team1"]), self.find_team(match["team2"]), match["name"])
            self.record_playoff_result(card["winner"])

    def finish_league_stage(self):
        self.last_standings = self.standings()
        self.pending_playoff_top_four = [t.name for t in self.last_standings[:4]]
        self.phase = "league_complete"
        self.live_match = None
        qualified = self.user_team_name in self.pending_playoff_top_four
        self.status_message = "League stage complete. Review the table and season stats, then start playoffs." if qualified else "League stage complete. Your team missed the top four; review the season, then start or quick-sim playoffs."

    def start_playoffs(self):
        if self.phase != "league_complete":
            raise ValueError("Playoffs are not ready to start.")
        top_names = self.pending_playoff_top_four or [t.name for t in self.standings()[:4]]
        self.setup_playoffs([self.find_team(name) for name in top_names])
        self.match_log = []
        self.live_match = None
        self.status_message = "Playoffs are ready. Enter the Match Hub if your team is playing, or quick-sim playoff matches one at a time."

    def setup_playoffs(self, top_four):
        p1, p2, p3, p4 = top_four
        self.phase = "playoffs"
        self.playoff_index = 0
        self.playoff_results = []
        self.playoff_matches = [
            {"name": "Qualifier 1", "team1": p1.name, "team2": p2.name, "status": "pending"},
            {"name": "Eliminator", "team1": p3.name, "team2": p4.name, "status": "pending"},
            {"name": "Qualifier 2", "team1": "", "team2": "", "status": "locked"},
            {"name": "Final", "team1": "", "team2": "", "status": "locked"},
        ]

    def record_playoff_result(self, winner):
        match = self.playoff_matches[self.playoff_index]
        loser = match["team2"] if winner == match["team1"] else match["team1"]
        match.update({"status": "complete", "winner": winner, "loser": loser})
        self.playoff_results.append({"name": match["name"], "winner": winner, "loser": loser})
        self.playoff_index += 1
        if self.playoff_index >= len(self.playoff_matches):
            self.archive_season(winner, loser)
            self.phase = "season_end"
            self.status_message = f"{winner} are IPL {self.season_year} champions. Retention window is next."
        else:
            self.unlock_playoff_match()
            self.status_message = "Playoff match complete. Review scorecards, then continue to the next playoff when ready."

    def unlock_playoff_match(self):
        if self.playoff_index == 2 and self.playoff_matches[2]["status"] == "locked":
            self.playoff_matches[2].update({"team1": self.playoff_results[0]["loser"], "team2": self.playoff_results[1]["winner"], "status": "pending"})
        if self.playoff_index == 3 and self.playoff_matches[3]["status"] == "locked":
            self.playoff_matches[3].update({"team1": self.playoff_results[0]["winner"], "team2": self.playoff_results[2]["winner"], "status": "pending"})

    def open_retention(self):
        if self.phase != "season_end":
            raise ValueError("Retention opens after the season ends.")
        self.completed_seasons += 1
        self.retention_limit = RETAIN_RESET if self.completed_seasons % 2 == 0 else RETAIN_NORMAL
        self.phase = "retention"
        self.status_message = f"Retention window: keep {self.retention_limit} players."

    def submit_retentions(self, names):
        if self.phase != "retention":
            raise ValueError("Retention window is closed.")
        if len(names) != self.retention_limit:
            raise ValueError(f"Choose exactly {self.retention_limit} players.")
        reverse_order = self.standings(reverse=False)
        user_team = self.user_team()
        for team in self.teams:
            if team == user_team:
                keep = [next((p for p in team.roster if p.name == name), None) for name in names]
                keep = [p for p in keep if p]
            else:
                keep = sorted(team.roster, key=lambda p: (self.mvp_score(p), p.current_ovr, -p.age), reverse=True)[:self.retention_limit]
            release = [p for p in team.roster if p not in keep]
            for player in release:
                player.team_name = "Unassigned"
            self.player_pool.extend(release)
            team.roster = keep
            team.captain = team.captain if team.captain in keep else None
            team.vice_captain = team.vice_captain if team.vice_captain in keep else None
            team.points = team.wins = team.losses = 0
            team.runs_scored = team.balls_faced = team.runs_conceded = team.balls_bowled = 0
            for player in team.roster:
                player.apply_offseason_progression()
                player.reset_stats()
            for player in release:
                player.apply_offseason_progression()
                player.reset_stats()
        self.add_regens()
        self.season_year += 1
        self.phase = "draft"
        self.draft_type = "retention"
        self.draft_order = reverse_order
        self.draft_round = 1
        self.draft_index = 0
        self.pick_num = 1
        self.draft_history = []
        self.round_num = 1
        self.playoff_matches = []
        self.playoff_results = []
        self.live_match = None
        self.status_message = "Post-retention draft is reverse standings, no snake."
        self.cpu_until_user()

    def add_regens(self):
        for i in range(30):
            role = random.choice(["Batsman", "Bowler (Fast)", "Bowler (Spin)", "All-Rounder", "Wicketkeeper"])
            if role == "Batsman":
                bat, bowl = random.randint(62, 75), random.randint(8, 22)
            elif role == "Wicketkeeper":
                bat, bowl = random.randint(61, 74), random.randint(8, 14)
            elif "Bowler" in role:
                bat, bowl = random.randint(8, 24), random.randint(62, 75)
            else:
                bat, bowl = random.randint(58, 73), random.randint(58, 73)
            base = max(bat, bowl) if role != "All-Rounder" else (bat + bowl) // 2
            is_overseas = random.random() < 0.2
            batting_archetype = "Aggressor" if role in ("Batsman", "Wicketkeeper") and bat >= 70 else ("Finisher" if role == "All-Rounder" else "Defensive Tailender")
            bowling_phase = "Middle Overs" if "Spin" in role else ("New Ball" if "Fast" in role else ("Flexible" if role == "All-Rounder" else "Part-time"))
            bowling_type = "Left-arm Orthodox" if role == "Bowler (Spin)" else ("Right-arm Fast" if role == "Bowler (Fast)" else ("Right-arm Medium" if role == "All-Rounder" else "None"))
            self.player_pool.append(Player(
                self.generated_name(is_overseas), role, base, bat, bowl, is_overseas,
                random.randint(18, 21), random.choice(["Right", "Left"]),
                random.choice(["Right", "Left"]) if role not in ("Batsman", "Wicketkeeper") else "None",
                batting_archetype, bowling_phase, bowling_type,
                "Emerging talent with adaptable T20 skills",
                "Unproven against elite pressure moments",
            ))

    def generated_name(self, is_overseas):
        existing = {p.name for p in self.player_pool}
        for team in self.teams:
            existing.update(p.name for p in team.roster)
        first_names = OVERSEAS_FIRST_NAMES if is_overseas else INDIAN_FIRST_NAMES
        last_names = OVERSEAS_LAST_NAMES if is_overseas else INDIAN_LAST_NAMES
        for _ in range(20):
            candidate = f"{random.choice(first_names)} {random.choice(last_names)} *"
            if candidate not in existing:
                return candidate
        return f"{random.choice(first_names)} {random.choice(last_names)} {random.randint(2, 99)} *"

    def select_motm(self, batting, bowling, players, winner):
        lookup = {p.name: p for p in players}
        for player in self.all_players() + list(getattr(self, "player_pool", [])):
            lookup.setdefault(player.name, player)
        scores = {}
        for name, data in batting.items():
            scores[name] = scores.get(name, 0) + data["runs"] + data["fours"] * 2 + data["sixes"] * 3 + (15 if data["runs"] >= 50 else 0) + (25 if data["runs"] >= 100 else 0)
        for name, data in bowling.items():
            econ = data["runs"] / (data["balls"] / 6) if data["balls"] else 12
            scores[name] = scores.get(name, 0) + data["wickets"] * 30 + max(0, 8 - econ) * 5 + (18 if data["wickets"] >= 4 else 0)
        scores = {name: score for name, score in scores.items() if lookup.get(name)}
        if not scores:
            return sorted(winner.roster, key=lambda p: p.current_ovr, reverse=True)[0]
        winning_scores = {name: score for name, score in scores.items() if lookup[name].team_name == winner.name}
        if not winning_scores:
            return lookup[max(scores, key=scores.get)]
        winning_name = max(winning_scores, key=winning_scores.get)
        overall_name = max(scores, key=scores.get)
        overall_player = lookup[overall_name]
        legacy_bat = batting.get(overall_name, {}).get("runs", 0) >= 100
        legacy_bowl = bowling.get(overall_name, {}).get("wickets", 0) >= 5
        winning_notable = winning_scores[winning_name] >= 55
        if overall_player.team_name != winner.name and (legacy_bat or legacy_bowl) and not winning_notable and scores[overall_name] >= winning_scores[winning_name] + 35:
            return overall_player
        return lookup[winning_name]

    def update_bowling_bests(self, bowlers, stats, against_name=""):
        for player in bowlers:
            ensure_stat_fields(player)
            data = stats.get(player.name)
            if data and (data["wickets"] > player.stats["best_bowling_wickets"] or (data["wickets"] == player.stats["best_bowling_wickets"] and data["runs"] < player.stats["best_bowling_runs"])):
                player.stats["best_bowling_wickets"] = data["wickets"]
                player.stats["best_bowling_runs"] = data["runs"]
                player.stats["best_bowling_against"] = against_name

    def innings_card(self, innings):
        batting = sorted(innings["bat_stats"].items(), key=lambda x: (x[1]["runs"], -x[1]["balls"]), reverse=True)[:4]
        bowling = sorted(
            innings["bowl_stats"].items(),
            key=lambda x: (x[1]["wickets"], -(x[1]["runs"] / (x[1]["balls"] / 6) if x[1]["balls"] else 99)),
            reverse=True,
        )[:4]
        batting_order = innings.get("batting_order", [])
        dismissals = innings.get("dismissals", {})
        full_batting = [
            {"name": n, "dismissal": dismissals.get(n, "not out" if innings["bat_stats"][n].get("balls", 0) else "did not bat"), **innings["bat_stats"][n]}
            for n in batting_order if n in innings["bat_stats"]
        ]
        full_bowling = [
            {"name": n, **d, "overs": f"{d['balls'] // 6}.{d['balls'] % 6}", "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0}
            for n, d in innings["bowl_stats"].items()
        ]
        return {
            "team": innings["team"].name,
            "against": innings["bowling_team"].name,
            "score": f"{innings['runs']}/{innings['wickets']}",
            "batting": [{"name": n, **d} for n, d in batting],
            "bowling": [{"name": n, **d, "econ": round(d["runs"] / (d["balls"] / 6), 2) if d["balls"] else 0} for n, d in bowling],
            "full_batting": full_batting,
            "full_bowling": full_bowling,
            "impact_sub": innings.get("impact_sub", ""),
        }

    def archive_season(self, champion, runner_up):
        mvp = self.leaderboard(lambda p: self.mvp_score(p), True, None, 1)[0]
        self.season_history.append({
            "season": self.season_year,
            "champion": champion,
            "runner_up": runner_up,
            "mvp": mvp,
            "points_table": [self.team_dict(t) for t in self.standings()],
            "batting": self.batting_table()[:15],
            "bowling": self.bowling_table()[:15],
            "playoffs": list(self.playoff_results),
        })

    def mvp_score(self, player):
        ensure_stat_fields(player)
        s = player.stats
        batting = s["runs"] + s["fours"] * 2 + s["sixes"] * 3 + s["fifties"] * 8 + s["hundreds"] * 18
        if s["balls_faced"] >= 30:
            batting += max(0, player.batting_strike_rate - 135) * 0.25
        bowling = s["wickets"] * 26
        if s["balls_bowled"] >= 18:
            bowling += max(0, 8.2 - player.bowling_economy) * 8
        bowling += max(0, s["best_bowling_wickets"] - 2) * 12
        fielding = s["catches"] * 4 + s["stumpings"] * 7 + s["runouts"] * 8
        win_share = s.get("team_wins", 0) * 4 + max(0, s.get("games", 0) - s.get("team_wins", 0)) * 1
        return batting + bowling + fielding + s["motm"] * 35 + win_share

    def all_players(self):
        players = []
        for team in self.teams:
            players.extend(team.roster)
        return players

    def find_player_anywhere(self, name):
        for player in self.all_players():
            if player.name == name:
                return player
        for player in getattr(self, "player_pool", []):
            if player.name == name:
                return player
        return None

    def player_dict(self, player):
        ensure_stat_fields(player)
        s = player.stats
        avg = s["runs"] / s["outs"] if s["outs"] else float(s["runs"])
        bowl_avg = s["runs_conceded"] / s["wickets"] if s["wickets"] else 0
        bowl_sr = s["balls_bowled"] / s["wickets"] if s["wickets"] else 0
        strength_note = getattr(player, "strengths", "")
        weakness_note = getattr(player, "weaknesses", "")
        if s["balls_faced"] >= 30 and player.batting_strike_rate >= 155:
            strength_note = "In-season boundary tempo trending up"
        elif s["balls_faced"] >= 30 and player.batting_strike_rate < 115:
            weakness_note = "In-season scoring tempo under pressure"
        if s["balls_bowled"] >= 18 and player.bowling_economy and player.bowling_economy <= 7.2:
            strength_note = "In-season control and wicket pressure"
        elif s["balls_bowled"] >= 18 and player.bowling_economy >= 10:
            weakness_note = "In-season expensive spells against hitters"
        bowling_type = getattr(player, "bowling_type", "None")
        allrounder_style = ""
        if player.role == "All-Rounder":
            allrounder_style = "Spin AR" if any(x in bowling_type for x in ("Spin", "Orthodox", "Leg", "Off")) else "Pace AR"
        return {
            "name": player.name, "role": player.role, "age": player.age, "team": player.team_name,
            "base_ovr": player.base_ovr, "ovr": player.current_ovr, "bat": player.current_batting,
            "bowl": player.current_bowling, "form": round(player.form, 1), "overseas": player.is_overseas,
            "ovr_progression": f"{getattr(player, 'season_start_ovr', player.base_ovr)} -> {player.current_ovr}",
            "bat_progression": f"{getattr(player, 'season_start_bat', player.batting_ovr)} -> {player.current_batting}",
            "bowl_progression": f"{getattr(player, 'season_start_bowl', player.bowling_ovr)} -> {player.current_bowling}",
            "batting_hand": player.batting_hand, "bowling_hand": player.bowling_hand,
            "batting_archetype": expanded_batting_archetype(player),
            "bowling_phase": expanded_bowling_phase(player),
            "bowling_type": getattr(player, "bowling_type", "None"),
            "allrounder_style": allrounder_style,
            "strengths": strength_note,
            "weaknesses": weakness_note,
            "phase_fit_powerplay": phase_fit_label(player, "Powerplay"),
            "phase_fit_middle": phase_fit_label(player, "Middle Overs"),
            "phase_fit_death": phase_fit_label(player, "Death Overs"),
            "runs": s["runs"], "balls": s["balls_faced"], "outs": s["outs"], "avg": round(avg, 2),
            "sr": round(player.batting_strike_rate, 2), "hs": s["highest_score"], "fours": s["fours"],
            "hs_against": s.get("highest_score_against", ""),
            "sixes": s["sixes"], "boundaries": s["fours"] + s["sixes"], "fifties": s["fifties"],
            "hundreds": s["hundreds"], "wickets": s["wickets"], "runs_conceded": s["runs_conceded"],
            "balls_bowled": s["balls_bowled"], "econ": round(player.bowling_economy, 2),
            "bowling_avg": round(bowl_avg, 2), "bowling_sr": round(bowl_sr, 2),
            "maidens": s["maidens"], "motm": s["motm"], "best_bowling": self.best_bowling_label(player),
            "best_bowling_against": s.get("best_bowling_against", ""),
            "catches": s["catches"], "stumpings": s["stumpings"], "runouts": s["runouts"],
            "games": s.get("games", 0), "team_wins": s.get("team_wins", 0),
            "mvp": round(self.mvp_score(player), 1),
        }

    def best_bowling_label(self, player):
        ensure_stat_fields(player)
        wkts = player.stats["best_bowling_wickets"]
        runs = player.stats["best_bowling_runs"]
        return f"{wkts}/{runs}" if wkts else "-"

    def team_dict(self, team):
        meta = TEAM_META[team.name]
        saved_batting = list(getattr(team, "saved_batting_order_names", []))
        saved_bowling = list(getattr(team, "saved_bowling_over_names", []))
        roster_ready = len(team.roster) >= 11
        batting_first_xi = (list(getattr(team, "saved_batting_first_xi_names", [])) or self.smart_batting_first_xi(team)) if roster_ready else []
        bowling_first_xi = (list(getattr(team, "saved_bowling_first_xi_names", [])) or self.smart_bowling_first_xi(team)) if roster_ready else []
        impact_defaults = self.default_impact_subs(team) if roster_ready else {"bat_to_bowl": {"out": "", "in": ""}, "bowl_to_bat": {"out": "", "in": ""}}
        return {
            "name": team.name, "abbr": meta["abbr"], "home": meta["home"], "primary": meta["primary"], "accent": meta["accent"],
            "points": team.points, "wins": team.wins, "losses": team.losses, "played": team.games_played,
            "nrr": round(team.net_run_rate, 3), "captain": team.captain.name if team.captain else "",
            "vice_captain": team.vice_captain.name if team.vice_captain else "",
            "saved_batting_order": saved_batting,
            "saved_bowling_order": saved_bowling,
            "batting_first_xi": batting_first_xi,
            "bowling_first_xi": bowling_first_xi,
            "saved_wicketkeeper": getattr(team, "saved_wicketkeeper_name", ""),
            "bat_to_bowl_sub": getattr(team, "saved_bat_to_bowl_sub", impact_defaults["bat_to_bowl"]) or impact_defaults["bat_to_bowl"],
            "bowl_to_bat_sub": getattr(team, "saved_bowl_to_bat_sub", impact_defaults["bowl_to_bat"]) or impact_defaults["bowl_to_bat"],
            "suggested_batting_order": saved_batting or (self.default_batting_order(team) if roster_ready else []),
            "suggested_bowling_order": saved_bowling or (self.default_bowling_plan(team) if roster_ready else []),
            "roster": [self.player_dict(p) for p in sorted(team.roster, key=lambda x: x.current_ovr, reverse=True)],
        }

    def leaderboard(self, key, reverse=True, minimum=None, limit=20):
        players = self.all_players()
        if minimum:
            stat, value = minimum
            players = [p for p in players if p.stats.get(stat, 0) >= value]
        ranked = sorted(players, key=key, reverse=reverse)
        if limit is not None:
            ranked = ranked[:limit]
        return [self.player_dict(p) for p in ranked]

    def batting_table(self):
        return self.leaderboard(lambda p: (p.stats["runs"], self.mvp_score(p)), True, ("balls_faced", 1), None)

    def bowling_table(self):
        return self.leaderboard(lambda p: (p.stats["wickets"], self.mvp_score(p)), True, ("balls_bowled", 1), None)

    def payload(self):
        available = sorted(self.player_pool, key=lambda p: p.current_ovr, reverse=True)
        current = self.current_draft_team()
        user = self.user_team() if self.teams and self.user_team_name else None
        return {
            "save_exists": os.path.exists(SAVE_FILE),
            "phase": self.phase, "season": self.season_year, "completed_seasons": self.completed_seasons,
            "draft_type": self.draft_type, "round": self.round_num, "user_team": self.user_team_name,
            "difficulty": self.difficulty,
            "status": self.status_message, "teams": [self.team_dict(t) for t in self.teams],
            "standings": [self.team_dict(t) for t in self.standings()] if self.teams else [],
            "squad_size": SQUAD_SIZE, "retention_limit": self.retention_limit,
            "draft": {
                "round": self.draft_round, "pick": self.pick_num, "current_team": current.name if current else "",
                "started": getattr(self, "draft_started", True),
                "user_pick_position": self.draft_order.index(user) + 1 if user and user in self.draft_order else 0,
                "available": [self.player_dict(p) for p in available],
                "history": self.draft_history[-120:],
                "needs": self.roster_needs(user) if user and self.phase == "draft" else {},
            },
            "retention": {"players": [self.player_dict(p) for p in user.roster] if user else []},
            "schedule": self.schedule, "playoffs": self.playoff_matches, "playoff_index": self.playoff_index,
            "match_log": self.match_log[-40:], "fixture_results": getattr(self, "fixture_results", [])[-120:],
            "live_match": self.live_match.payload() if self.live_match else None,
            "history": self.season_history,
            "tables": {"batting": self.batting_table() if self.teams else [], "bowling": self.bowling_table() if self.teams else []},
            "leaderboards": self.leaderboards() if self.teams else {},
        }

    def leaderboards(self):
        return {
            "orange_cap": self.leaderboard(lambda p: p.stats["runs"], limit=50),
            "purple_cap": self.leaderboard(lambda p: p.stats["wickets"], limit=50),
            "sixes": self.leaderboard(lambda p: p.stats["sixes"], limit=50),
            "fours": self.leaderboard(lambda p: p.stats["fours"], limit=50),
            "boundaries": self.leaderboard(lambda p: p.stats["fours"] + p.stats["sixes"], limit=50),
            "highest_score": self.leaderboard(lambda p: p.stats["highest_score"], limit=50),
            "strike_rate": self.leaderboard(lambda p: p.batting_strike_rate, True, ("balls_faced", 30), 50),
            "economy": self.leaderboard(lambda p: p.bowling_economy or 99, False, ("balls_bowled", 18), 50),
            "best_figures": self.leaderboard(lambda p: (p.stats.get("best_bowling_wickets", 0), -p.stats.get("best_bowling_runs", 999)), limit=50),
            "catches": self.leaderboard(lambda p: p.stats["catches"], limit=50),
            "stumpings": self.leaderboard(lambda p: p.stats["stumpings"], limit=50),
            "runouts": self.leaderboard(lambda p: p.stats["runouts"], limit=50),
            "mvp": self.leaderboard(lambda p: self.mvp_score(p), limit=50),
        }
