# players_data.py
import csv
import os
import random
from models import Player

IPL_TEAMS_LIST = [
    "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru",
    "Kolkata Knight Riders", "Sunrisers Hyderabad", "Rajasthan Royals",
    "Delhi Capitals", "Gujarat Titans", "Lucknow Super Giants", "Punjab Kings"
]

def get_initial_player_pool():
    pool = []
    csv_path = "players.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Missing custom file map sheet logic at target location: '{csv_path}'")
        
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip()
            role = row['role'].strip()
            base_ovr = int(row['base_ovr'])
            batting_ovr = int(row['batting_ovr'])
            bowling_ovr = int(row['bowling_ovr'])
            is_overseas = row['is_overseas'].strip().lower() == 'true'
            age = int(row['age'])
            
            # Catch new columns or apply defaults if rows drop short
            batting_hand = row.get('batting_hand', 'Right').strip()
            bowling_hand = row.get('bowling_hand', 'Right').strip()
            batting_archetype = row.get('batting_archetype', 'Strike Rotator').strip()
            bowling_phase = row.get('bowling_phase', 'Flexible').strip()
            bowling_type = row.get('bowling_type', 'None').strip()
            strengths = row.get('strengths', '').strip()
            weaknesses = row.get('weaknesses', '').strip()
            
            pool.append(Player(name, role, base_ovr, batting_ovr, bowling_ovr, is_overseas, age, batting_hand, bowling_hand, batting_archetype, bowling_phase, bowling_type, strengths, weaknesses))
            
    total_required = 180
    current_count = len(pool)
    
    if current_count < total_required:
        needed = total_required - current_count
        roles_pool = ["Batsman", "Bowler (Fast)", "Bowler (Spin)", "All-Rounder", "Wicketkeeper"]
        for i in range(needed):
            role = random.choice(roles_pool)
            is_os = random.random() < 0.25
            age = random.randint(18, 25)
            b_hand = random.choice(["Right", "Left"])
            bo_hand = random.choice(["Right", "Left"]) if "Bowler" in role or role == "All-Rounder" else "None"
            
            if role == "Batsman":
                bat_ovr, bowl_ovr = random.randint(68, 75), random.randint(10, 25)
                batting_archetype = random.choice(["Aggressor", "Anchor", "Strike Rotator"])
                strengths = "Developing top-order batting profile"
                weaknesses = "Still adapting to elite T20 matchups"
            elif "Bowler" in role:
                bat_ovr, bowl_ovr = random.randint(10, 22), random.randint(68, 75)
                batting_archetype = "Defensive Tailender"
                strengths = "Defensive tail batting and strike support"
                weaknesses = "Limited boundary range against specialist bowling"
            elif role == "Wicketkeeper":
                bat_ovr, bowl_ovr = random.randint(68, 75), random.randint(10, 12)
                batting_archetype = random.choice(["Aggressor", "Strike Rotator"])
                strengths = "Developing keeper-batter profile"
                weaknesses = "Role still depends on team balance"
            else:
                bat_ovr, bowl_ovr = random.randint(64, 72), random.randint(64, 72)
                batting_archetype = random.choice(["Strike Rotator", "Lower-order Hitter", "Finisher"])
                strengths = "Useful two-way T20 skill set"
                weaknesses = "Role depends heavily on match context"
                
            base_ovr = max(bat_ovr, bowl_ovr) if role != "All-Rounder" else (bat_ovr + bowl_ovr) // 2
            
            pool.append(Player(f"Domestic_Prospect_{i+1}", role, base_ovr, bat_ovr, bowl_ovr, is_os, age, b_hand, bo_hand, batting_archetype, "Flexible", "None", strengths, weaknesses))
            
    return pool
