# players_data.py
"""Seed data for a new league: the franchise list and the starting player pool.

Players are loaded from `players.csv` (real-world-inspired ratings and
profiles); if that file doesn't supply enough players for a full mega draft,
the pool is topped up with randomly generated domestic prospects.
"""
import csv
import os
import random
from cricket_sim_engine.models import Player

DATA_DIR = os.path.dirname(__file__)

IPL_TEAMS_LIST = [
    "Chennai Cholas", "Mumbai Mavericks", "Bengaluru Bulls",
    "Kolkata Knights", "Hyderabad Hawks", "Rajasthan Raptors",
    "Delhi Dynamos", "Gujarat Gladiators", "Lucknow Lions", "Punjab Panthers"
]

# Real-world Cricket 2026 squads (post-auction), keyed by franchise name and
# listing each squad's retained players plus 2026-auction signings, by the
# exact `name` used in players.csv. Any player in players.csv NOT listed on
# one of these rosters is considered off a 2026 roster and is
# carried over into the free-agent pool for the next draft.
IPL_2026_ROSTERS = {
    "Bengaluru Bulls": [
        "Vyrat Kuhli", "Jush Hezlewood", "Phyl Selt", "Rejat Petidar", "Jytesh Sherma",
        "Bhovneshwar Komar", "Resikh Selam", "Kronal Pendya", "Tym Devid",
        "Soyash Sherma", "Jecob Bithell", "Divdutt Pedikkal", "Nowan Thoshara", "Rumario Shipherd",
        "Swepnil Syngh", "Abhynandan Syngh", "Jecob Doffy", "Jurdan Cux",
        "Setvik Diswal", "Vycky Ostwel", "Mengesh Yedav", "Vyhaan Melhotra", "Kenishk Chuuhan", "Vinkatesh Iyir",
    ],
    "Mumbai Mavericks": [
        "Jesprit Bomrah", "Soryakumar Yedav", "Herdik Pendya", "Ruhit Sherma", "Trint Buult",
        "Diepak Chehar", "Tylak Verma", "Neman Dhyr", "Wyll Jecks", "AM Ghezanfar",
        "Shirfane Rotherford", "Sherdul Thekur", "Mytchell Sentner", "Ryen Ryckelton", "Curbin Busch",
        "Rubin Mynz", "Meyank Merkande", "Ashweni Komar", "Rej Bewa", "Reghu Sherma",
        "Qointon de Kuck", "Denish Melewar", "Meyank Rewat", "Atherva Ankulekar", "Muhd Izher",
    ],
    "Hyderabad Hawks": [
        "Hiinrich Kleasen", "Pet Commins", "Abhyshek Sherma", "Trevis Hiad", "Ishen Kyshan",
        "Hershal Petel", "Nytish Komar Riddy", "Eshen Melinga", "Jeydev Unedkat", "Girald Cuetzee",
        "Kemindu Mindis", "Zieshan Anseri", "Anyket Virma", "Hersh Dobey", "Revichandran Smeran",
        "Lyam Lyvingstone", "Shyvam Mevi", "Selil Arura", "Sekib Hossain", "Onker Termale",
        "Preful Hynge", "Kreins Foletra", "Amyt Komar", "Dalshun Madoshunka",
    ],
    "Chennai Cholas": [
        "Senju Semson", "Roturaj Geikwad", "Shyvam Dobe", "Nuor Ahmed", "Kheleel Ahmid",
        "MS Dhuni", "Anshol Kemboj", "Diwald Brivis", "Gorjapneet Syngh", "Spincer Juhnson",
        "Jemie Ovirton", "Urvyl Petel", "Ayosh Mhetre", "Mokesh Chuudhary", "Shriyas Gupal",
        "Remakrishna Ghush", "Akial Husein", "Rehul Chehar", "Mett Hinry", "Serfaraz Khen",
        "Zek Fuulkes", "Metthew Shurt", "Amen Khen", "Kertik Sherma", "Preshant Vier",
    ],
    "Delhi Dynamos": [
        "Axer Petel", "KL Rehul", "Koldeep Yedav", "Mytchell Sterc", "T Netarajan",
        "Trystan Stobbs", "Mokesh Komar", "Nytish Rena", "Abyshek Purel", "Ashotosh Sherma",
        "Semeer Ryzvi", "Doshmantha Chemeera", "Vypraj Nygam", "Kerun Neir", "Medhav Tywari",
        "Trypurana Vyjay", "Ajey Mendal", "Prythvi Shew", "Aoqib Nebi",
        "Pethum Nyssanka", "Kyli Jemieson", "Longi Ngydi", "Devid Myller", "Sehil Perakh", "Rahan Ahmid",
    ],
    "Kolkata Knights": [
        "Rynku Syngh", "Sonil Nerine", "Verun Chekravarthy", "Remandeep Syngh",
        "Angkrysh Reghuvanshi", "Veibhav Arura", "Ajynkya Rehane", "Ruvman Puwell", "Menish Pendey",
        "Umren Melik", "Anokul Ruy", "Fynn Allin", "Metheesha Pethirana", "Rechin Revindra",
        "Cemeron Grien", "Mostafizur Rehman", "Tym Siifert", "Tijasvi Dehiya",
        "Rehul Trypathi", "Kertik Tyegi", "Preshant Sulanki", "Serthak Renjan", "Deksh Kemra",
        "Nevdip Seini", "Seurebh Dubay",
    ],
    "Rajasthan Raptors": [
        "Yeshasvi Jeiswal", "Revindra Jedeja", "Ryyan Perag", "Dhrov Jorel", "Jufra Archir",
        "Shymron Hitmyer", "Toshar Dishpande", "Sendeep Sherma", "Nendre Borger", "Desun Shenaka",
        "Kwina Mephaka", "Veibhav Suoryavanshi", "Dunovan Firreira", "Shobham Dobey", "Yodhvir Syngh",
        "Lhoan-dri Pritorius", "Adem Mylne", "Soshant Myshra", "Koldeep Sin", "Amen Reo",
        "Revi Syngh", "Yesh Rej Ponja", "Vygnesh Pothur", "Bryjesh Sherma", "Revi Byshnoi",
    ],
    "Gujarat Gladiators": [
        "Reshid Khen", "Shobman Gyll", "Muhammed Syraj", "Jus Bottler", "Kegiso Rebada",
        "Presidh Kryshna", "Sei Sodharsan", "Rehul Tiwatia", "M Shehrukh Khen", "Weshington Sondar",
        "Glinn Phyllips", "Sei Kyshore", "Arshed Khen", "Gornoor Brer", "Ishent Sherma",
        "Jeyant Yedav", "Komar Koshagra", "Anoj Rewat", "Nyshant Syndhu", "Menav Sothar",
        "Jeson Hulder", "Tum Benton", "Loke Wuod", "Ashuk Sherma", "Kolwont Khejruliya",
    ],
    "Lucknow Lions": [
        "Ryshabh Pent", "Nycholas Puoran", "Meyank Yedav", "Muhammed Shemi", "Avish Khen",
        "Abdol Semad", "Ayosh Bedoni", "Muhsin Khen", "Mytchell Mersh", "Shehbaz Ahmid",
        "Ayden Merkram", "Metthew Brietzke", "Menimaran Syddharth", "Akesh Syngh", "Arjon Tindulkar",
        "Arshyn Kolkarni", "Prynce Yedav", "Dygvesh Rethi", "Hymmat Syngh", "Wenindu Hesaranga",
        "Anrych Nurtje", "Jush Inglys", "Mokul Chuudhary", "Neman Tywari", "Akshet Reghuwanshi",
    ],
    "Punjab Panthers": [
        "Shriyas Iyir", "Arshdiep Syngh", "Yozvendra Chehal", "Mercus Stuinis", "Merco Jensen",
        "Sheshank Syngh", "Nihal Wedhera", "Prebhsimran Syngh", "Pryyansh Arye", "Mytchell Owin",
        "Azmetullah Omerzai", "Luckie Firguson", "Vyjaykumar Vyshek", "Yesh Thekur", "Herpreet Brer",
        "Vyshnu Vynod", "Xevier Bertlett", "Pyle Avynash", "Hernoor Syngh", "Soryansh Shidge",
        "Mosheer Khen", "Cuoper Cunnolly", "Bin Dwershuis", "Vyshal Nyshad", "Preveen Dobey",
    ],
}

def get_initial_player_pool():
    """Build the starting pool of draftable players for a brand-new league.

    Reads every row of `players.csv` into a `Player`, then — if fewer than
    180 players were loaded — fills the remainder with randomly generated
    "Domestic_Prospect" players (young, role-appropriate ratings and a
    generic archetype/strengths profile) so the mega draft always has enough
    players for ten 25-player squads.

    Raises `FileNotFoundError` if `players.csv` is missing.
    """
    pool = []
    csv_path = os.path.join(DATA_DIR, "players.csv")

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
            natural_slot_raw = row.get('natural_slot', '').strip()
            natural_slot = int(natural_slot_raw) if natural_slot_raw.isdigit() else None

            p = Player(name, role, base_ovr, batting_ovr, bowling_ovr, is_overseas, age, batting_hand, bowling_hand, batting_archetype, bowling_phase, bowling_type, strengths, weaknesses)
            if natural_slot is not None:
                p.preferred_position = natural_slot
            pool.append(p)
            
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


def get_2026_rosters_and_pool():
    """Build real-world IPL 2026 squads plus a leftover free-agent pool from `players.csv`.

    Returns `(rosters, leftover_pool)` where `rosters` maps each franchise
    name to its list of `Player`s per `IPL_2026_ROSTERS`, and `leftover_pool`
    is every other player from `players.csv` (i.e. not on a real 2026 IPL
    roster) — carried over as the free-agent pool for the following season's
    draft.
    """
    by_name = {p.name: p for p in get_initial_player_pool()}
    rosters = {}
    assigned = set()
    for team_name, player_names in IPL_2026_ROSTERS.items():
        squad = []
        for name in player_names:
            player = by_name.get(name)
            if player is None:
                continue
            squad.append(player)
            assigned.add(name)
        rosters[team_name] = squad
    leftover_pool = [p for p in by_name.values() if p.name not in assigned]
    return rosters, leftover_pool


def get_alltime_player_pool():
    """Build the draft pool from `players_alltime.csv` (500+ all-time IPL greats).

    Falls back to `get_initial_player_pool()` if the all-time CSV is missing.
    The pool is large enough that no synthetic padding is added.
    """
    csv_path = os.path.join(DATA_DIR, "players_alltime.csv")
    if not os.path.exists(csv_path):
        return get_initial_player_pool()

    pool = []
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
            batting_hand = row.get('batting_hand', 'Right').strip()
            bowling_hand = row.get('bowling_hand', 'Right').strip()
            batting_archetype = row.get('batting_archetype', 'Middle-over Rotator').strip()
            bowling_phase = row.get('bowling_phase', 'Flexible').strip()
            bowling_type = row.get('bowling_type', 'None').strip()
            strengths = row.get('strengths', '').strip()
            weaknesses = row.get('weaknesses', '').strip()
            natural_slot_raw = row.get('natural_slot', '').strip()
            natural_slot = int(natural_slot_raw) if natural_slot_raw.isdigit() else None
            p = Player(name, role, base_ovr, batting_ovr, bowling_ovr, is_overseas, age,
                       batting_hand, bowling_hand, batting_archetype, bowling_phase,
                       bowling_type, strengths, weaknesses)
            if natural_slot is not None:
                p.preferred_position = natural_slot
            pool.append(p)
    return pool
