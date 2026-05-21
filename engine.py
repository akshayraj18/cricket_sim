# engine.py
import random

class MatchEngine:
    def __init__(self, team1, team2, user_team_name=None):
        self.team1 = team1
        self.team2 = team2
        self.user_team_name = user_team_name
        self.fast_sim_active = False

    def simulate_ball(self, batter, bowler):
        skill_delta = (batter.current_batting - bowler.current_bowling) / 100.0
        matchup_multiplier = 1.0
        if batter.batting_hand == "Left" and "Spin" in bowler.role and bowler.bowling_hand == "Right":
            matchup_multiplier += 0.06
        elif batter.batting_hand == "Right" and "Fast" in bowler.role and bowler.bowling_hand == "Left":
            matchup_multiplier -= 0.04
        skill_delta *= matchup_multiplier

        p_wicket = 0.045 - (skill_delta * 0.025)
        p_dot = 0.360 - (skill_delta * 0.080)
        p_single, p_double, p_triple = 0.350, 0.070, 0.005
        p_four = 0.120 + (skill_delta * 0.070)
        p_six = 0.050 + (skill_delta * 0.060)

        if batter.intent == "Aggressive":
            p_wicket *= 1.60; p_six *= 1.50; p_four *= 1.30; p_dot *= 0.70
        elif batter.intent == "Defensive":
            p_wicket *= 0.40; p_dot *= 1.40; p_six *= 0.20; p_four *= 0.40; p_single *= 1.10

        prob_matrix = {"W": max(0.005, p_wicket), "0": max(0.10, p_dot), "1": max(0.05, p_single), "2": max(0.01, p_double), "3": p_triple, "4": max(0.02, p_four), "6": max(0.01, p_six)}
        choices = list(prob_matrix.keys())
        weights = [v / sum(prob_matrix.values()) for v in prob_matrix.values()]
        return random.choices(choices, weights=weights)[0]

    def configure_batting_order_and_intent(self, team, playing_xi, status_context):
        if team.name != self.user_team_name:
            for p in playing_xi: p.intent = "Normal"
            return playing_xi
            
        print(f"\n=== TACTICAL MANAGEMENT ({status_context.upper()}): {team.name.upper()} ===")
        
        if team.saved_batting_order_names:
            available_saved_order = [next((x for x in playing_xi if x.name == name), None) for name in team.saved_batting_order_names]
            if None not in available_saved_order and len(available_saved_order) == 11:
                carry_order = input(f"[Memory] Carry over your batting card order from the previous match? (y/n): ").strip().lower()
                if carry_order == 'y':
                    for p in available_saved_order: p.intent = "Normal"
                    return available_saved_order

        for p in playing_xi:
            choice = input(f" Strategy for {p.name} ({p.role}) [OVR: {p.current_ovr}] (1=Def, 2=Norm, 3=Aggr): ").strip()
            p.intent = "Defensive" if choice == "1" else ("Aggressive" if choice == "3" else "Normal")

        print(f"\n--- SET BATTING ORDER ---")
        for idx, p in enumerate(playing_xi):
            print(f" [{idx}] {p.name:<22} | {p.role:<12} | Strategy: {p.intent}")
        while True:
            try:
                indices = list(map(int, input("\nEnter 11 unique indexes separated by spaces: ").replace(',', ' ').split()))
                if len(indices) == 11 and len(set(indices)) == 11 and all(0 <= i < 11 for i in indices):
                    final_order = [playing_xi[i] for i in indices]
                    team.saved_batting_order_names = [p.name for p in final_order]
                    return final_order
            except ValueError: pass
            print("Invalid order setup. Enter exactly 11 unique space-separated numbers.")

    def select_bowler_for_over(self, team, bowling_lineup, over_num, overs_tracked, last_bowler, inning_bowler_stats):
        available = [p for p in bowling_lineup if overs_tracked.get(p.name, 0) < 4 and p != last_bowler]
        if not available: available = [p for p in bowling_lineup if overs_tracked.get(p.name, 0) < 4]
        if not available: available = bowling_lineup

        # If fast sim has been chosen, CPU logic automatically pulls the best remaining bowler
        if self.fast_sim_active or team.name != self.user_team_name:
            available.sort(key=lambda p: p.current_bowling, reverse=True)
            return available[0]
            
        print(f"\n" + "="*50 + f"\n      [MATCH DESK MENU OPTIONS: OVER {over_num+1}]      \n" + "="*50)
        print(" [1] Interactively select the next bowler for this over")
        print(" [2] Simulate the rest of this entire match instantly in the background")
        sim_choice = input("\nSelect execution path choice: ").strip()
        
        if sim_choice == "2":
            print(f"\n[System Skip] Fast-forwarding match operations using presets...")
            self.fast_sim_active = True
            available.sort(key=lambda p: p.current_bowling, reverse=True)
            return available[0]

        print(f"\n--- SELECT BOWLER FOR OVER {over_num+1} ({team.name.upper()}) ---")
        for idx, p in enumerate(available):
            b_stats = inning_bowler_stats.get(p.name, {"runs": 0, "wickets": 0, "balls": 0})
            overs = f"{b_stats['balls']//6}.{b_stats['balls']%6}"
            econ = (b_stats["runs"] / (b_stats["balls"]/6)) if b_stats["balls"] > 0 else 0.0
            print(f" [{idx}] {p.name:<22} | OVR: {p.current_bowling:<2} | Overs: {overs}/4 | Wkts: {b_stats['wickets']} | Econ: {econ:.2f}")
            
        while True:
            try:
                choice = int(input("Select bowler index: "))
                if 0 <= choice < len(available): return available[choice]
            except (ValueError, IndexError): pass

    def play_innings(self, batting_team, bowling_team, batting_lineup, bowling_pool, target=None):
        runs, wickets, balls = 0, 0, 0
        striker_idx, non_striker_idx = 0, 1
        overs_tracked = {}
        last_bowler = None
        
        inning_batter_stats = {p.name: {"runs": 0, "balls": 0, "fours": 0, "sixes": 0} for p in batting_lineup}
        inning_bowler_stats = {p.name: {"runs": 0, "wickets": 0, "balls": 0} for p in bowling_pool}
        partnership_runs = 0
        partnership_balls = 0
        
        is_user_involved = (batting_team.name == self.user_team_name or bowling_team.name == self.user_team_name)

        while balls < 120 and wickets < 10:
            over_num = balls // 6
            
            if balls % 6 == 0:
                active_bowler = self.select_bowler_for_over(bowling_team, bowling_pool, over_num, overs_tracked, last_bowler, inning_bowler_stats)
                last_bowler = active_bowler
                overs_tracked[active_bowler.name] = overs_tracked.get(active_bowler.name, 0) + 1

            striker = batting_lineup[min(striker_idx, 10)]
            non_striker = batting_lineup[min(non_striker_idx, 10)]

            outcome = self.simulate_ball(striker, active_bowler)
            balls += 1
            partnership_balls += 1
            inning_bowler_stats[active_bowler.name]["balls"] += 1
            inning_batter_stats[striker.name]["balls"] += 1

            if outcome == "W":
                wickets += 1
                striker.stats["outs"] += 1
                active_bowler.stats["wickets"] += 1
                inning_bowler_stats[active_bowler.name]["wickets"] += 1
                
                if is_user_involved and not self.fast_sim_active:
                    print(f" [BALL {over_num}.{balls%6 if balls%6!=0 else 6}] OUT! {striker.name} dismissed by {active_bowler.name}!")
                    print(f" Partnership Broken: {partnership_runs} runs off {partnership_balls} balls.")
                
                partnership_runs = 0
                partnership_balls = 0
                striker_idx = max(striker_idx, non_striker_idx) + 1
            else:
                score = int(outcome)
                runs += score
                partnership_runs += score
                
                inning_batter_stats[striker.name]["runs"] += score
                inning_bowler_stats[active_bowler.name]["runs"] += score
                
                striker.stats["runs"] += score
                active_bowler.stats["runs_conceded"] += score
                
                if score == 4:
                    striker.stats["fours"] += 1
                    inning_batter_stats[striker.name]["fours"] += 1
                if score == 6:
                    striker.stats["sixes"] += 1
                    inning_batter_stats[striker.name]["sixes"] += 1
                    
                if score in [1, 3]: striker_idx, non_striker_idx = non_striker_idx, striker_idx

            striker.stats["balls_faced"] += 1
            active_bowler.stats["balls_bowled"] += 1

            if balls % 6 == 0 and is_user_involved and not self.fast_sim_active:
                print(f"\n" + "="*60 + f"\n END OF OVER {over_num+1} | Score: {runs}/{wickets} ({batting_team.name})")
                print(f" Total Runs: {runs} | Overs: {over_num+1}.0")
                print(f"-"*60)
                b1_data = inning_batter_stats.get(striker.name, {"runs": 0, "balls": 0})
                b2_data = inning_batter_stats.get(non_striker.name, {"runs": 0, "balls": 0})
                print(f" * Batting: {striker.name:<22} {b1_data['runs']}* ({b1_data['balls']}b)")
                print(f" * Batting: {non_striker.name:<22} {b2_data['runs']} ({b2_data['balls']}b)")
                print(f" Current Partnership: {partnership_runs} runs off {partnership_balls} balls")
                print(f"-"*60)
                
                bowler_over_stats = inning_bowler_stats[active_bowler.name]
                econ = (bowler_over_stats["runs"] / (bowler_over_stats["balls"]/6)) if bowler_over_stats["balls"] > 0 else 0.0
                print(f" * Bowling: {active_bowler.name:<22} Wkts: {bowler_over_stats['wickets']} | Runs: {bowler_over_stats['runs']} | Econ: {econ:.2f}")
                if target: print(f" Target Status: Needs {target - runs} runs to win from {120 - balls} balls left.")
                print("="*60)
                input(" Press Enter to begin next over window...")

            if target and runs >= target: break

        for name, data in inning_batter_stats.items():
            player_obj = next(p for p in batting_lineup if p.name == name)
            g_runs = data["runs"]
            if g_runs > player_obj.stats["highest_score"]: player_obj.stats["highest_score"] = g_runs
            if g_runs >= 100: player_obj.stats["hundreds"] += 1
            elif g_runs >= 50: player_obj.stats["fifties"] += 1

        final_balls_faced = 120 if wickets == 10 else balls
        final_balls_bowled = 120 if wickets == 10 else balls

        batting_team.runs_scored += runs
        batting_team.balls_faced += final_balls_faced
        bowling_team.runs_conceded += runs
        bowling_team.balls_bowled += final_balls_bowled
        
        return runs, wickets, inning_batter_stats, inning_bowler_stats

    def handle_innings_break_impact_sub(self, team, active_playing_xi):
        bench = [p for p in team.roster if p not in active_playing_xi]
        if not bench: return active_playing_xi
        if self.fast_sim_active or team.name != self.user_team_name:
            active_playing_xi.sort(key=lambda p: p.current_ovr)
            bench.sort(key=lambda p: p.current_ovr, reverse=True)
            sub_out, sub_in = active_playing_xi[0], bench[0]
            os_count = sum(1 for p in active_playing_xi if p.is_overseas)
            if sub_in.is_overseas and not sub_out.is_overseas and os_count >= 4:
                dom = [p for p in bench if not p.is_overseas]
                if dom: sub_in = dom[0]
            active_playing_xi[0] = sub_in
            return active_playing_xi

        print(f"\n Would you like to call an Impact Substitution for {team.name}? (y/n): ")
        if input().strip().lower() == 'y':
            for i, p in enumerate(active_playing_xi): print(f" [{i}] {p.name} ({p.role})")
            out_idx = int(input("Index to SUB OUT: "))
            for i, p in enumerate(bench): print(f" [{i}] {p.name} ({p.role}) | {'OS' if p.is_overseas else 'Dom'}")
            in_idx = int(input("Index to SUB IN: "))
            active_playing_xi[out_idx] = bench[in_idx]
        return active_playing_xi

    def print_presentation_grade_scorecard(self, inn1_bat, inn1_bowl, r1, w1, r2, w2, b1_dict, b2_dict, bowl1_dict, bowl2_dict, match_winner, margin_str):
        print("\n" + "="*75)
        print(f"                       OFFICIAL IPL MATCH SCORECARD                         ")
        print("="*75)
        print(f" FIRST INNINGS:  {inn1_bat.name:<30} {r1}/{w1} (20.0 Ov)")
        print(f" SECOND INNINGS: {inn1_bowl.name:<30} {r2}/{w2}")
        print("-" * 75)
        
        # Parse Top 4 Batsmen for Innings 1
        sorted_bat1 = sorted(b1_dict.items(), key=lambda x: x[1]["runs"], reverse=True)[:4]
        print(f" Top Batsmen ({inn1_bat.name[:15]}):")
        for name, data in sorted_bat1:
            print(f"  • {name:<25} {data['runs']:>3} runs off {data['balls']:>2} balls (4s: {data['fours']} | 6s: {data['sixes']})")
            
        # Parse Top 4 Bowlers for Innings 1
        sorted_bowl1 = sorted(bowl1_dict.items(), key=lambda x: (x[1]["wickets"], -x[1]["runs"]), reverse=True)[:4]
        print(f"\n Top Bowlers ({inn1_bowl.name[:15]}):")
        for name, data in sorted_bowl1:
            econ = (data["runs"] / (data["balls"]/6)) if data["balls"] > 0 else 0.0
            print(f"  • {name:<25} Wickets: {data['wickets']} | Runs Conceded: {data['runs']} | Econ: {econ:.2f}")
            
        print("-" * 75)
        
        # Parse Top 4 Batsmen for Innings 2
        sorted_bat2 = sorted(b2_dict.items(), key=lambda x: x[1]["runs"], reverse=True)[:4]
        print(f" Top Batsmen ({inn1_bowl.name[:15]}):")
        for name, data in sorted_bat2:
            print(f"  • {name:<25} {data['runs']:>3} runs off {data['balls']:>2} balls (4s: {data['fours']} | 6s: {data['sixes']})")
            
        # Parse Top 4 Bowlers for Innings 2
        sorted_bowl2 = sorted(bowl2_dict.items(), key=lambda x: (x[1]["wickets"], -x[1]["runs"]), reverse=True)[:4]
        print(f"\n Top Bowlers ({inn1_bat.name[:15]}):")
        for name, data in sorted_bowl2:
            econ = (data["runs"] / (data["balls"]/6)) if data["balls"] > 0 else 0.0
            print(f"  • {name:<25} Wickets: {data['wickets']} | Runs Conceded: {data['runs']} | Econ: {econ:.2f}")
            
        print("="*75)
        print(f" ⭐ RESULT: {match_winner.name.upper()} WON {margin_str} ⭐")
        print("="*75 + "\n")
        input("Press Enter to close scorecard presentation and head back to the Hub...")

    def run_match(self):
        toss_winner = random.choice([self.team1, self.team2])
        toss_loser = self.team2 if toss_winner == self.team1 else self.team1
        
        decision = "bat"
        if toss_winner.name == self.user_team_name:
            decision = input(f"\n[Toss] You won! Choose to (bat/bowl) first: ").strip().lower()
            if decision not in ["bat", "bowl"]: decision = "bat"
        else:
            decision = random.choice(["bat", "bowl"])

        inn1_bat = toss_winner if decision == "bat" else toss_loser
        inn1_bowl = toss_loser if decision == "bat" else toss_winner

        xi_bat1 = inn1_bat.user_select_xi_interactively(bowling_first=False) if inn1_bat.name == self.user_team_name else inn1_bat.cpu_auto_select_xi()
        xi_bowl1 = inn1_bowl.user_select_xi_interactively(bowling_first=True) if inn1_bowl.name == self.user_team_name else inn1_bowl.cpu_auto_select_xi()

        bat1_lineup = self.configure_batting_order_and_intent(inn1_bat, xi_bat1, "Batting First")
        bowl1_pool = [p for p in xi_bowl1 if "Bowler" in p.role or p.role == "All-Rounder"] or xi_bowl1

        # Extract local stat return bundles
        r1, w1, b1_dict, bowl1_dict = self.play_innings(inn1_bat, inn1_bowl, bat1_lineup, bowl1_pool)
        target = r1 + 1

        xi_bat1 = self.handle_innings_break_impact_sub(inn1_bat, xi_bat1)
        xi_bowl1 = self.handle_innings_break_impact_sub(inn1_bowl, xi_bowl1)

        bat2_lineup = self.configure_batting_order_and_intent(inn1_bowl, xi_bowl1, "Chasing Target")
        bowl2_pool = [p for p in xi_bat1 if "Bowler" in p.role or p.role == "All-Rounder"] or xi_bat1

        r2, w2, b2_dict, bowl2_dict = self.play_innings(inn1_bowl, inn1_bat, bat2_lineup, bowl2_pool, target=target)
        self.eval_match_performances_for_form(bat1_lineup, bowl1_pool)
        self.eval_match_performances_for_form(bat2_lineup, bowl2_pool)

        is_user_involved = (self.team1.name == self.user_team_name or self.team2.name == self.user_team_name)

        if r2 >= target:
            inn1_bowl.wins += 1; inn1_bat.losses += 1; inn1_bowl.points += 2
            margin = f"by {10 - w2} wickets"
            if is_user_involved:
                self.print_presentation_grade_scorecard(inn1_bat, inn1_bowl, r1, w1, r2, w2, b1_dict, b2_dict, bowl1_dict, bowl2_dict, inn1_bowl, margin)
            return inn1_bowl
        else:
            inn1_bat.wins += 1; inn1_bowl.losses += 1; inn1_bat.points += 2
            margin = f"by {r1 - r2} runs"
            if is_user_involved:
                self.print_presentation_grade_scorecard(inn1_bat, inn1_bowl, r1, w1, r2, w2, b1_dict, b2_dict, bowl1_dict, bowl2_dict, inn1_bat, margin)
            return inn1_bat

    def eval_match_performances_for_form(self, lineup_bat, lineup_bowl):
        for p in lineup_bat:
            if p.stats["balls_faced"] > 0:
                if p.stats["runs"] >= 50 or (p.stats["runs"] >= 25 and p.batting_strike_rate > 160): p.apply_game_performance_on_form(1)
                elif p.stats["runs"] == 0: p.apply_game_performance_on_form(-1)
        for p in lineup_bowl:
            if p.stats["balls_bowled"] > 0:
                if p.stats["wickets"] >= 3: p.apply_game_performance_on_form(1)
                elif p.stats["runs_conceded"] >= 45 and p.stats["wickets"] == 0: p.apply_game_performance_on_form(-1)