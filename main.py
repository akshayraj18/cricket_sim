# main.py
import random
import json
import os
from players_data import IPL_TEAMS_LIST, get_initial_player_pool
from models import Team, Player, DraftEngine
from engine import MatchEngine

SAVE_FILE = "save_state.json"

def display_comprehensive_leaderboards(teams):
    all_players = []
    for t in teams: all_players.extend(t.roster)
    
    print("\n" + "="*60 + "\n          IPL STATISTICAL HUB LEADERBOARDS           \n" + "="*60)
    print(" [1] Orange Cap (Most Runs)")
    print(" [2] Purple Cap (Most Wickets)")
    print(" [3] Power Hitters (Most Sixes)")
    print(" [4] Boundary Masters (Most Fours)")
    print(" [5] Highest Strike Rate (Min 50 balls)")
    print(" [6] Best Economy Rate (Min 36 balls)")
    print(" [7] Back to Main Hub Menu")
    
    choice = input("\nSelect leaderboard metric index ID: ").strip()
    
    if choice == "1":
        all_players.sort(key=lambda p: p.stats.get("runs", 0), reverse=True)
        print("\n--- ORANGE CAP RANKINGS (TOP 15) ---")
        print(f" {'Pos':<3} | {'Player Name':<20} | {'Franchise':<15} | {'Runs':<5} | {'HS':<4} | {'100s':<4} | {'50s':<4} |")
        print("-" * 72)
        for i, p in enumerate(all_players[:15], 1): 
            print(f" {i:>2}  | {p.name:<20} | {p.team_name[:15]:<15} | {p.stats.get('runs',0):<5} | {p.stats.get('highest_score',0):<4} | {p.stats.get('hundreds',0):<4} | {p.stats.get('fifties',0):<4} |")
    elif choice == "2":
        all_players.sort(key=lambda p: p.stats.get("wickets", 0), reverse=True)
        print("\n--- PURPLE CAP RANKINGS (TOP 15) ---")
        for i, p in enumerate(all_players[:15], 1): 
            print(f" {i:>2}. {p.name:<22} | Team: {p.team_name[:15]:<15} | Wickets: {p.stats.get('wickets',0):<3} | Econ: {p.bowling_economy:.2f}")
    elif choice == "3":
        all_players.sort(key=lambda p: p.stats.get("sixes", 0), reverse=True)
        print("\n--- MOST SIXES HIT (TOP 15) ---")
        for i, p in enumerate(all_players[:15], 1): 
            print(f" {i:>2}. {p.name:<22} | Team: {p.team_name[:15]:<15} | Sixes: {p.stats.get('sixes',0)}")
    elif choice == "4":
        all_players.sort(key=lambda p: p.stats.get("fours", 0), reverse=True)
        print("\n--- MOST FOURS HIT (TOP 15) ---")
        for i, p in enumerate(all_players[:15], 1): 
            print(f" {i:>2}. {p.name:<22} | Team: {p.team_name[:15]:<15} | Fours: {p.stats.get('fours',0)}")
    elif choice == "5":
        filtered = [p for p in all_players if p.stats.get("balls_faced", 0) >= 50]
        filtered.sort(key=lambda p: p.batting_strike_rate, reverse=True)
        print("\n--- HIGHEST STRIKE RATES (TOP 15) ---")
        for i, p in enumerate(filtered[:15], 1): 
            print(f" {i:>2}. {p.name:<22} | Team: {p.team_name[:15]:<15} | SR: {p.batting_strike_rate:.2f} | Runs: {p.stats.get('runs',0)}")
    elif choice == "6":
        filtered = [p for p in all_players if p.stats.get("balls_bowled", 0) >= 36]
        filtered.sort(key=lambda p: p.bowling_economy)
        print("\n--- BEST ECONOMY RATES (TOP 15) ---")
        for i, p in enumerate(filtered[:15], 1): 
            print(f" {i:>2}. {p.name:<22} | Team: {p.team_name[:15]:<15} | Econ: {p.bowling_economy:.2f} | Wkts: {p.stats.get('wickets',0)}")

def display_user_roster_table(team):
    print(f"\n=========================================================================================")
    print(f"                         COMPREHENSIVE STATS SQUAD ROSTER: {team.name.upper()}           ")
    print(f"=========================================================================================")
    print(f"| {'Player Name':<20} | {'OVR':<3} | {'Form':<4} | {'Runs':<4} | {'SR':<6} | {'4s':<3} | {'6s':<3} | {'Wkts':<4} | {'Econ':<5} |")
    print(f"|----------------------|-----|------|------|--------|-----|-----|------|-------|")
    for p in sorted(team.roster, key=lambda x: x.current_ovr, reverse=True):
        print(f"| {p.name:<20} | {p.current_ovr:<3} | {p.form:<4}/10 | {p.stats.get('runs',0):<4} | {p.batting_strike_rate:<6.1f} | {p.stats.get('fours',0):<3} | {p.stats.get('sixes',0):<3} | {p.stats.get('wickets',0):<4} | {p.bowling_economy:<5.1f} |")
    print(f"=========================================================================================")
    input("\nPress Enter to return to main central menu dashboard hub...")

def serialize_league(season_year, user_team_name, teams, player_pool):
    state = {"season_year": season_year, "user_team_name": user_team_name, "player_pool": [], "teams": []}
    for p in player_pool: state["player_pool"].append(dict(p.__dict__))
    for t in teams:
        t_data = {
            "name": t.name, "points": t.points, "wins": t.wins, "losses": t.losses,
            "runs_scored": t.runs_scored, "balls_faced": t.balls_faced, "runs_conceded": t.runs_conceded, "balls_bowled": t.balls_bowled,
            "captain": t.captain.name if t.captain else None, "vice_captain": t.vice_captain.name if t.vice_captain else None, "roster": []
        }
        for p in t.roster: t_data["roster"].append(dict(p.__dict__))
        state["teams"].append(t_data)
    with open(SAVE_FILE, "w") as f: json.dump(state, f, indent=4)

def deserialize_league():
    if not os.path.exists(SAVE_FILE): return None
    try:
        with open(SAVE_FILE, "r") as f: state = json.load(f)
        pool = []
        for p_data in state["player_pool"]:
            p = Player(p_data["name"], p_data["role"], p_data["base_ovr"], p_data["batting_ovr"], p_data["bowling_ovr"], p_data["is_overseas"], p_data["age"], p_data["batting_hand"], p_data["bowling_hand"])
            p.form = p_data.get("form", 5); p.team_name = p_data.get("team_name", "Unassigned"); p.stats = p_data.get("stats", p.stats)
            if "fours" not in p.stats: p.stats["fours"] = 0
            if "sixes" not in p.stats: p.stats["sixes"] = 0
            if "fifties" not in p.stats: p.stats["fifties"] = 0
            if "hundreds" not in p.stats: p.stats["hundreds"] = 0
            pool.append(p)
        teams = []
        for t_data in state["teams"]:
            t = Team(t_data["name"]); t.points = t_data["points"]; t.wins = t_data["wins"]; t.losses = t_data.get("losses", 0); t.runs_scored = t_data["runs_scored"]; t.balls_faced = t_data["balls_faced"]; t.runs_conceded = t_data["runs_conceded"]; t.balls_bowled = t_data["balls_bowled"]
            for p_data in t_data["roster"]:
                p = Player(p_data["name"], p_data["role"], p_data["base_ovr"], p_data["batting_ovr"], p_data["bowling_ovr"], p_data["is_overseas"], p_data["age"], p_data["batting_hand"], p_data["bowling_hand"])
                p.form = p_data.get("form", 5); p.team_name = p_data.get("team_name", t.name); p.stats = p_data.get("stats", p.stats)
                if "fours" not in p.stats: p.stats["fours"] = 0
                if "sixes" not in p.stats: p.stats["sixes"] = 0
                if "fifties" not in p.stats: p.stats["fifties"] = 0
                if "hundreds" not in p.stats: p.stats["hundreds"] = 0
                t.roster.append(p)
            if t_data["captain"]: t.captain = next((p for p in t.roster if p.name == t_data["captain"]), None)
            if t_data["vice_captain"]: t.vice_captain = next((p for p in t.roster if p.name == t_data["vice_captain"]), None)
            teams.append(t)
        return state["season_year"], state["user_team_name"], teams, pool
    except Exception: return None

def print_standings_table(teams):
    teams.sort(key=lambda x: (x.points, x.net_run_rate), reverse=True)
    print(f"\n" + "-"*85 + f"\n| {'Pos':<3} | {'Franchise Name':<28} | {'Pld':<4} | {'Pts':<4} | {'Wins':<4} | {'Loss':<4} | {'Net RR':<7} |\n" + "-"*85)
    for rank, t in enumerate(teams, 1): 
        print(f"| {rank:<3} | {t.name:<28} | {t.games_played:<4} | {t.points:<4} | {t.wins:<4} | {t.losses:<4} | {t.net_run_rate:+.3f} |")
    print("-"*85)

def run_franchise_lifecycle():
    print("=========================================================")
    print("      INITIALIZING IPL FRANCHISE SIMULATION ENGINE       ")
    print("=========================================================")
    checkpoint = deserialize_league()
    if checkpoint and input("Resume from checkpoint data? (y/n): ").strip().lower() == 'y':
        start_year, user_team_name, teams, player_pool = checkpoint
        user_team = next(t for t in teams if t.name == user_team_name)
        run_season_loop(start_year, user_team_name, user_team, teams, player_pool)
        return

    player_pool = get_initial_player_pool()
    teams = [Team(name) for name in IPL_TEAMS_LIST]
    for idx, team in enumerate(teams): print(f" [{idx}] {team.name}")
    user_team = teams[int(input("\nSelect franchise index ID: "))]
    
    DraftEngine(teams, player_pool).run_snake_draft(user_team.name)
    for team in teams:
        if team.name == user_team.name: team.assign_leadership_roles_interactively()
        else: team.auto_assign_cpu_leadership()
        
    serialize_league(2026, user_team.name, teams, player_pool)
    run_season_loop(2026, user_team.name, user_team, teams, player_pool)

def run_season_loop(start_year, user_team_name, user_team, teams, player_pool):
    for season_year in [2026, 2027, 2028]:
        if season_year < start_year: continue
        
        print(f"\n=========================================================")
        print(f"               WELCOME TO IPL SEASON {season_year}       ")
        print(f"=========================================================")
        
        for t in teams:
            t.points, t.wins, t.losses = 0, 0, 0
            t.runs_scored, t.balls_faced, t.runs_conceded, t.balls_bowled = 0, 0, 0, 0
            
        # 14-Game Regular Season Operational Frame
        for round_num in range(1, 15):
            while True:
                print(f"\n" + "="*50 + f"\n    CENTRAL DASHBOARD HUB MAIN MENU (ROUND {round_num}/14)    \n" + "="*50)
                print(" [1] Advance & Play Next Scheduled Match Day")
                print(" [2] View Current League Standings Points Table")
                print(" [3] Review Comprehensive League Leaderboards Stats")
                print(" [4] Audit Your Roster List Performance Table")
                print(" [5] Reappoint Team Captain and Vice-Captain Staff")
                
                menu_choice = input("\nSelect dashboard option: ").strip()
                if menu_choice == "1": break
                elif menu_choice == "2": print_standings_table(teams)
                elif menu_choice == "3": display_comprehensive_leaderboards(teams)
                elif menu_choice == "4": display_user_roster_table(user_team)
                elif menu_choice == "5": user_team.assign_leadership_roles_interactively()

            indices_pool = list(range(len(teams)))
            random.shuffle(indices_pool)
            for i in range(0, 10, 2):
                match_engine = MatchEngine(teams[indices_pool[i]], teams[indices_pool[i+1]], user_team_name)
                match_engine.run_match()
                
            serialize_league(season_year, user_team_name, teams, player_pool)
            
        # --- IPL DOUBLE-ELIMINATION PLAYOFF BRACKET ---
        print("\n" + "="*60 + "\n          IPL REGULAR SEASON ENDED - PLAYOFFS TIME!          \n" + "="*60)
        teams.sort(key=lambda x: (x.points, x.net_run_rate), reverse=True)
        print_standings_table(teams)
        
        p1, p2, p3, p4 = teams[0], teams[1], teams[2], teams[3]
        print(f"\nLocked Playoff Contenders:")
        print(f" • Qualifier 1: {p1.name} (1st) vs {p2.name} (2nd)")
        print(f" • Eliminator:  {p3.name} (3rd) vs {p4.name} (4th)")
        input("\nPress Enter to begin the Playoff Bracket Matches...")

        # 1. Qualifier 1 (1st vs 2nd)
        print(f"\n[PLAYOFFS] MATCH 1: QUALIFIER 1 — {p1.name} vs {p2.name}")
        q1_winner = MatchEngine(p1, p2, user_team_name).run_match()
        q1_loser = p2 if q1_winner == p1 else p1
        print(f"\n» {q1_winner.name} wins Qualifier 1 and advances straight to the Grand Final!")
        print(f"» {q1_loser.name} drops down to Qualifier 2.")
        input("\nPress Enter to proceed to the Eliminator match...")

        # 2. Eliminator (3rd vs 4th)
        print(f"\n[PLAYOFFS] MATCH 2: ELIMINATOR — {p3.name} vs {p4.name}")
        elim_winner = MatchEngine(p3, p4, user_team_name).run_match()
        elim_loser = p4 if elim_winner == p3 else p3
        print(f"\n» {elim_winner.name} wins the Eliminator and moves on to Qualifier 2.")
        print(f"» {elim_loser.name} has been knocked out of the tournament.")
        input("\nPress Enter to proceed to Qualifier 2...")

        # 3. Qualifier 2 (Loser of Q1 vs Winner of Eliminator)
        print(f"\n[PLAYOFFS] MATCH 3: QUALIFIER 2 — {q1_loser.name} vs {elim_winner.name}")
        q2_winner = MatchEngine(q1_loser, elim_winner, user_team_name).run_match()
        print(f"\n» {q2_winner.name} wins Qualifier 2 and advances to the Grand Final!")
        print(f"» {q1_loser.name if q2_winner == elim_winner else elim_winner.name} has been knocked out.")
        input("\nPress Enter to launch the Grand Final! 🏆")

        # 4. Grand Final (Winner of Q1 vs Winner of Q2)
        print(f"\n🏆" + "="*60 + "🏆\n        THE IPL GRAND FINAL CHAMPIONSHIP MATCH        \n🏆" + "="*60 + "🏆")
        print(f" Match-up: {q1_winner.name.upper()} vs {q2_winner.name.upper()}\n")
        champion = MatchEngine(q1_winner, q2_winner, user_team_name).run_match()
        
        print(f"\n🎉 " + "!"*50 + " 🎉")
        print(f"   {champion.name.upper()} ARE THE IPL {season_year} TOURNAMENT CHAMPIONS!  ")
        print(f"🎉 " + "!"*50 + " 🎉\n")
        
        # Display seasonal accolades
        display_comprehensive_leaderboards(teams)
        
        # --- OFF-SEASON TRANSITIONS LOOP ---
        if season_year != 2028:
            print("\n--- RUNNING OFF-SEASON RETENTIONS & PROGRESSIONS ---")
            for t in teams:
                for p in list(t.roster):
                    p.apply_offseason_progression()
                    if p.age > 34 and random.random() < 0.30:
                        print(f"  [Retirement] {p.name} has retired at age {p.age}")
                        if t.captain == p: t.captain = None
                        if t.vice_captain == p: t.vice_captain = None
                        t.roster.remove(p)
                    elif p.age >= 41:
                        if t.captain == p: t.captain = None
                        if t.vice_captain == p: t.vice_captain = None
                        t.roster.remove(p)

            print("\nProcessing franchise roster lists... keeping top 10 players.")
            for t in teams:
                t.roster.sort(key=lambda p: p.current_ovr, reverse=True)
                released = t.roster[10:]
                t.roster = t.roster[:10]
                player_pool.extend(released)
                
            for i in range(25):
                role = random.choice(["Batsman", "Bowler (Fast)", "Bowler (Spin)", "All-Rounder"])
                bat_ovr = random.randint(62, 70) if role in ["Batsman", "All-Rounder"] else random.randint(10, 20)
                bowl_ovr = random.randint(62, 70) if role in ["Bowler (Fast)", "Bowler (Spin)", "All-Rounder"] else random.randint(10, 20)
                base_ovr = max(bat_ovr, bowl_ovr) if role != "All-Rounder" else (bat_ovr + bowl_ovr) // 2
                b_hand = random.choice(["Right", "Left"])
                bo_hand = random.choice(["Right", "Left"]) if "Bowler" in role else "None"
                
                player_pool.append(Player(f"Regen_Prospect_{season_year}_{i+1}", role, base_ovr, bat_ovr, bowl_ovr, (random.random() < 0.20), 18, b_hand, bo_hand))
                
            teams.sort(key=lambda t: (t.points, t.net_run_rate))
            while any(len(t.roster) < 18 for t in teams):
                for team in teams:
                    if len(team.roster) >= 18: continue
                    player_pool.sort(key=lambda p: p.current_ovr, reverse=True)
                    team.roster.append(player_pool.pop(0))
            
            for team in teams:
                if team.captain not in team.roster or team.vice_captain not in team.roster:
                    if team.name == user_team_name: team.assign_leadership_roles_interactively()
                    else: team.auto_assign_cpu_leadership()

            for t in teams:
                for p in t.roster: p.reset_stats()
                
            serialize_league(season_year + 1, user_team_name, teams, player_pool)
            input("\nOff-season draft and progressions complete! Press Enter to jump to next season...")

if __name__ == "__main__":
    run_franchise_lifecycle()