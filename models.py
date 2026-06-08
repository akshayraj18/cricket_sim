# models.py
import random

class Player:
    def __init__(self, name, role, base_ovr, batting_ovr, bowling_ovr, is_overseas, age, batting_hand="Right", bowling_hand="Right", batting_archetype="Strike Rotator", bowling_phase="Flexible", bowling_type="None", strengths="", weaknesses=""):
        self.name = name
        self.role = role
        self.base_ovr = base_ovr
        self.batting_ovr = batting_ovr
        self.bowling_ovr = bowling_ovr
        self.is_overseas = is_overseas
        self.age = age
        self.batting_hand = batting_hand
        self.bowling_hand = bowling_hand
        self.batting_archetype = batting_archetype
        self.bowling_phase = bowling_phase
        self.bowling_type = bowling_type
        self.strengths = strengths
        self.weaknesses = weaknesses
        self.form = 5
        self.intent = "Normal"
        self.team_name = "Unassigned"
        self.reset_stats()

    def reset_stats(self):
        self.stats = {
            "runs": 0, "balls_faced": 0, "outs": 0, "highest_score": 0,
            "fours": 0, "sixes": 0, "fifties": 0, "hundreds": 0,
            "wickets": 0, "runs_conceded": 0, "balls_bowled": 0,
            "maidens": 0, "motm": 0, "best_bowling_wickets": 0,
            "best_bowling_runs": 999,
            "catches": 0, "stumpings": 0, "runouts": 0
        }

    @property
    def form_impact(self):
        # Keep form as a confidence modifier, not a player rewrite. A 1-10 form
        # band now moves OVR by roughly -4 to +5, which keeps match results
        # believable across a season.
        return self.form - 5

    @property
    def current_batting(self):
        return max(1, min(100, int(self.batting_ovr + self.form_impact)))

    @property
    def current_bowling(self):
        return max(1, min(100, int(self.bowling_ovr + self.form_impact)))

    @property
    def current_ovr(self):
        return max(1, min(100, int(max(self.base_ovr, self.batting_ovr, self.bowling_ovr) + self.form_impact)))

    @property
    def batting_strike_rate(self):
        if self.stats["balls_faced"] == 0: return 0.0
        return (self.stats["runs"] / self.stats["balls_faced"]) * 100

    @property
    def bowling_economy(self):
        if self.stats["balls_bowled"] == 0: return 0.0
        return (self.stats["runs_conceded"] / (self.stats["balls_bowled"] / 6))

    def apply_game_performance_on_form(self, specialized_impact):
        if specialized_impact > 0:
            if self.age <= 23:
                adjusted = specialized_impact + 0.35
            elif self.age <= 28:
                adjusted = specialized_impact + 0.15
            elif self.age >= 35:
                adjusted = specialized_impact * 0.65
            else:
                adjusted = specialized_impact
        else:
            if self.age <= 23:
                adjusted = specialized_impact * 1.20
            elif self.age >= 35:
                adjusted = specialized_impact * 0.70
            else:
                adjusted = specialized_impact
        self.form = max(1, min(10, self.form + adjusted))

    def apply_offseason_progression(self):
        if self.age <= 21:
            growth = random.choices([1, 2, 3, 4, 5], weights=[1, 3, 4, 3, 1])[0]
        elif self.age <= 25:
            growth = random.choices([0, 1, 2, 3, 4], weights=[1, 3, 4, 2, 1])[0]
        elif self.age <= 30:
            growth = random.choices([-1, 0, 1, 2], weights=[1, 3, 3, 1])[0]
        elif self.age <= 34:
            growth = random.choices([-2, -1, 0, 1], weights=[2, 3, 2, 1])[0]
        else:
            growth = random.choices([-5, -4, -3, -2, -1], weights=[1, 2, 3, 3, 1])[0]
        self.batting_ovr = max(1, min(100, self.batting_ovr + growth))
        self.bowling_ovr = max(1, min(100, self.bowling_ovr + growth))
        self.base_ovr = max(self.batting_ovr, self.bowling_ovr)
        self.age += 1
        self.form = 5


class Team:
    def __init__(self, name):
        self.name = name
        self.roster = []
        self.points = 0
        self.wins = 0
        self.losses = 0
        self.runs_scored = 0
        self.balls_faced = 0
        self.runs_conceded = 0
        self.balls_bowled = 0
        self.captain = None
        self.vice_captain = None
        self.saved_playing_xi_names = []
        self.saved_batting_first_xi_names = []
        self.saved_bowling_first_xi_names = []
        self.saved_bat_to_bowl_sub = {"out": "", "in": ""}
        self.saved_bowl_to_bat_sub = {"out": "", "in": ""}
        self.saved_wicketkeeper_name = ""
        self.saved_batting_order_names = []
        self.saved_bowling_over_names = []

    @property
    def games_played(self):
        return self.wins + self.losses

    @property
    def net_run_rate(self):
        overs_faced = self.balls_faced / 6 if self.balls_faced > 0 else 1.0
        overs_bowled = self.balls_bowled / 6 if self.balls_bowled > 0 else 1.0
        return (self.runs_scored / overs_faced) - (self.runs_conceded / overs_bowled)

    def cpu_auto_select_xi(self):
        sorted_roster = sorted(self.roster, key=lambda p: p.current_ovr, reverse=True)
        playing_xi = []
        overseas_count = 0
        
        if self.captain:
            playing_xi.append(self.captain)
            if self.captain.is_overseas: overseas_count += 1
        if self.vice_captain and self.vice_captain not in playing_xi:
            if not (self.vice_captain.is_overseas and overseas_count >= 4):
                playing_xi.append(self.vice_captain)
                if self.vice_captain.is_overseas: overseas_count += 1

        wk = next((p for p in sorted_roster if p.role == "Wicketkeeper"), None)
        if wk and wk not in playing_xi:
            if not (wk.is_overseas and overseas_count >= 4):
                playing_xi.append(wk)
                if wk.is_overseas: overseas_count += 1
                
        for p in sorted_roster:
            if p in playing_xi: continue
            if len(playing_xi) == 11: break
            if p.is_overseas and overseas_count >= 4: continue
            playing_xi.append(p)
            if p.is_overseas: overseas_count += 1
            
        return playing_xi[:11]

    def user_select_xi_interactively(self, bowling_first=False):
        if self.saved_playing_xi_names:
            available_saved = [p for p in self.roster if p.name in self.saved_playing_xi_names]
            if len(available_saved) == 11:
                carry_over = input(f"\n[Memory] Load your Playing XI from the previous match? (y/n): ").strip().lower()
                if carry_over == 'y':
                    return available_saved

        print(f"\n" + "="*60 + f"\n    SELECT PLAYING XI SQUAD : {self.name.upper()}     \n" + "="*60)
        
        if bowling_first:
            sorted_roster = sorted(self.roster, key=lambda p: (
                0 if "Bowler" in p.role else (1 if p.role == "All-Rounder" else 2),
                -p.current_bowling
            ))
        else:
            sorted_roster = sorted(self.roster, key=lambda p: (
                0 if (p.role == "Batsman" or p.role == "Wicketkeeper") else (1 if p.role == "All-Rounder" else 2),
                -p.current_batting
            ))

        for idx, p in enumerate(sorted_roster):
            leader = " [C]" if p == self.captain else (" [VC]" if p == self.vice_captain else "")
            print(f" [{idx:>2}] {p.name:<22} | {p.role:<13} | BAT OVR: {p.current_batting:<2} | BOWL OVR: {p.current_bowling:<2} | {p.batting_hand[0]}B-{p.bowling_hand[0]}W{leader}")
            
        selected_xi = []
        if self.captain: selected_xi.append(self.captain)
        if self.vice_captain and self.vice_captain not in selected_xi: selected_xi.append(self.vice_captain)
        
        while len(selected_xi) < 11:
            print(f"\n Lineup Pool ({len(selected_xi)}/11): {[p.name for p in selected_xi]}")
            try:
                choice = int(input(" Enter selection index row number: "))
                if choice < 0 or choice >= len(sorted_roster): continue
                player = sorted_roster[choice]
                if player in selected_xi: continue
                
                os_count = sum(1 for p in selected_xi if p.is_overseas)
                if player.is_overseas and os_count >= 4:
                    print(" Limit Intercept! Maximum 4 overseas slots permitted.")
                    continue
                selected_xi.append(player)
            except ValueError:
                pass
                
        self.saved_playing_xi_names = [p.name for p in selected_xi]
        return selected_xi

    def assign_leadership_roles_interactively(self):
        print(f"\n=== APPOINT LEADERSHIP FOR {self.name.upper()} ===")
        for idx, p in enumerate(self.roster):
            print(f" [{idx:>2}] {p.name:<22} | OVR: {p.current_ovr:<2} | {p.role}")
        while True:
            try:
                c_idx = int(input("\nSelect Captain Index ID: "))
                vc_idx = int(input("Select Vice-Captain Index ID: "))
                if c_idx != vc_idx and 0 <= c_idx < len(self.roster) and 0 <= vc_idx < len(self.roster):
                    self.captain = self.roster[c_idx]
                    self.vice_captain = self.roster[vc_idx]
                    break
            except ValueError:
                pass
            print("Selection invalid.")

    def auto_assign_cpu_leadership(self):
        sorted_r = sorted(self.roster, key=lambda p: p.current_ovr, reverse=True)
        self.captain = sorted_r[0]
        self.vice_captain = sorted_r[1]


class DraftEngine:
    def __init__(self, teams, player_pool):
        self.teams = teams
        self.player_pool = player_pool
        self.draft_history = []

    def run_snake_draft(self, user_team_name):
        order = list(self.teams)
        random.shuffle(order)
        round_num = 1
        global_pick_count = 1
        
        while any(len(t.roster) < 18 for t in self.teams):
            current_order = list(order) if round_num % 2 != 0 else list(reversed(order))
            for team in current_order:
                if len(team.roster) >= 18: continue
                if team.name == user_team_name: picked_player = self.user_pick(team)
                else: picked_player = self.cpu_pick(team)
                
                picked_player.team_name = team.name
                self.draft_history.append({
                    "round": round_num, "pick_num": global_pick_count, "team": team.name, "player": f"{picked_player.name} ({picked_player.current_ovr})"
                })
                global_pick_count += 1
            round_num += 1

    def cpu_pick(self, team):
        self.player_pool.sort(key=lambda p: p.current_ovr, reverse=True)
        chosen = self.player_pool.pop(0)
        team.roster.append(chosen)
        return chosen

    def user_pick(self, team):
        while True:
            print(f"\n>>>> YOUR TURN: {team.name.upper()} ({len(team.roster)}/18) <<<<")
            self.player_pool.sort(key=lambda p: p.current_ovr, reverse=True)
            
            print("\n" + "-"*85 + "\n--- TOP 20 AVAILABLE PLAYERS ---" + "\n" + "-"*85)
            for idx, p in enumerate(self.player_pool[:20]):
                print(f" [{idx+1:>2}] {p.name:<22} | OVR: {p.current_ovr:<2} | Age: {p.age:<2} | {p.role:<13} | {p.batting_hand[0]}H/{p.bowling_hand[0]}H")
            
            print("\n--- MENU CONSOLE OPTIONS ---")
            print(" [1-20] Type any row number directly to draft that player")
            print(" [S]    Search / Pick ANY player in the database by name")
            print(" [R]    View your current squad roster allocation")
            print(" [B]    Open live, updated Draft Board Matrix")
            
            action = input("\nEnter selection option: ").strip().upper()
            
            if action.isdigit():
                idx = int(action) - 1
                if 0 <= idx < 20 and idx < len(self.player_pool):
                    picked = self.player_pool.pop(idx)
                    team.roster.append(picked)
                    print(f"\n[Confirmed] You drafted: {picked.name}!")
                    return picked
                else:
                    print("Index choice out of bounds.")
            
            elif action == "S":
                query = input("Enter player name to look up: ").strip().lower()
                matches = [p for p in self.player_pool if query in p.name.lower()]
                if not matches:
                    print("\nNo available player matches that name lookup.")
                    continue
                print("\n--- REGISTRY MATCHES FOUND ---")
                for m_idx, p in enumerate(matches):
                    print(f" [{m_idx+1}] {p.name:<22} | OVR: {p.current_ovr:<2} | Age: {p.age:<2} | {p.role:<13}")
                
                sub = input("\nEnter index number to draft (or press Enter to back out): ").strip()
                if sub.isdigit() and 0 <= int(sub)-1 < len(matches):
                    picked = matches[int(sub)-1]
                    self.player_pool.remove(picked)
                    team.roster.append(picked)
                    print(f"\n[Confirmed] You drafted: {picked.name}!")
                    return picked
                    
            elif action == "R":
                print(f"\n=== SQUAD ROSTER DEPTH MAP: {team.name.upper()} ===")
                for r_idx, p in enumerate(team.roster, 1):
                    print(f" {r_idx:>2}. {p.name:<22} | OVR: {p.current_ovr:<2} | Age: {p.age:<2} | {p.role:<13}")
                input("\nPress Enter to close roster panel...")
                
            elif action == "B":
                self.print_draft_board_matrix()
                input("Press Enter to close live draft matrix panel...")
            else:
                print("Command not recognized.")

    def print_draft_board_matrix(self):
        print("\n" + "="*80)
        print("                        LIVE DRAFT BOARD MATRIX                         ")
        print("="*80)
        if not self.draft_history:
            print("  No selections have been logged yet.")
        else:
            rounds_data = {}
            for pick in self.draft_history:
                r = pick["round"]
                if r not in rounds_data: rounds_data[r] = []
                rounds_data[r].append(f"Pick {pick['pick_num']:<3} | {pick['team'][:15]:<15} -> {pick['player']}")
            for r_num, picks in sorted(rounds_data.items()):
                print(f"\n[ROUND {r_num}]")
                for p_info in picks:
                    print(f"  • {p_info}")
        print("\n" + "="*80 + "\n")
