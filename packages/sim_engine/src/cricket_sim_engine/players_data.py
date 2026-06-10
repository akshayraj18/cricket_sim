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
    "Chennai Super Kings", "Mumbai Indians", "Royal Challengers Bengaluru",
    "Kolkata Knight Riders", "Sunrisers Hyderabad", "Rajasthan Royals",
    "Delhi Capitals", "Gujarat Titans", "Lucknow Super Giants", "Punjab Kings"
]

# Real-world IPL 2026 squads (post-auction), keyed by franchise name and
# listing each squad's retained players plus 2026-auction signings, by the
# exact `name` used in players.csv. Any player in players.csv NOT listed on
# one of these rosters is considered off an IPL roster for 2026 and is
# carried over into the free-agent pool for the next draft.
IPL_2026_ROSTERS = {
    "Royal Challengers Bengaluru": [
        "Virat Kohli", "Josh Hazlewood", "Phil Salt", "Rajat Patidar", "Jitesh Sharma",
        "Bhuvneshwar Kumar", "Rasikh Salam", "Krunal Pandya", "Yash Dayal", "Tim David",
        "Suyash Sharma", "Jacob Bethell", "Devdutt Padikkal", "Nuwan Thushara", "Romario Shepherd",
        "Swapnil Singh", "Abhinandan Singh", "Jacob Duffy", "Jordan Cox",
        "Satvik Deswal", "Vicky Ostwal", "Mangesh Yadav", "Vihaan Malhotra", "Kanishk Chouhan",
    ],
    "Mumbai Indians": [
        "Jasprit Bumrah", "Suryakumar Yadav", "Hardik Pandya", "Rohit Sharma", "Trent Boult",
        "Deepak Chahar", "Tilak Varma", "Naman Dhir", "Will Jacks", "AM Ghazanfar",
        "Sherfane Rutherford", "Shardul Thakur", "Mitchell Santner", "Ryan Rickelton", "Corbin Bosch",
        "Robin Minz", "Mayank Markande", "Ashwani Kumar", "Raj Bawa", "Raghu Sharma",
        "Quinton de Kock", "Danish Malewar", "Mayank Rawat", "Atharva Ankolekar", "Mohd Izhar",
    ],
    "Sunrisers Hyderabad": [
        "Heinrich Klaasen", "Pat Cummins", "Abhishek Sharma", "Travis Head", "Ishan Kishan",
        "Harshal Patel", "Nitish Kumar Reddy", "Eshan Malinga", "Jaydev Unadkat", "Brydon Carse",
        "Kamindu Mendis", "Zeeshan Ansari", "Aniket Verma", "Harsh Dubey", "Ravichandran Smaran",
        "Liam Livingstone", "Shivam Mavi", "Salil Arora", "Sakib Hussain", "Onkar Tarmale",
        "Praful Hinge", "Krains Fuletra", "Jack Edwards", "Amit Kumar",
    ],
    "Chennai Super Kings": [
        "Sanju Samson", "Ruturaj Gaikwad", "Shivam Dube", "Noor Ahmad", "Khaleel Ahmed",
        "MS Dhoni", "Anshul Kamboj", "Dewald Brevis", "Gurjapneet Singh", "Nathan Ellis",
        "Jamie Overton", "Urvil Patel", "Ayush Mhatre", "Mukesh Choudhary", "Shreyas Gopal",
        "Ramakrishna Ghosh", "Akeal Hosein", "Rahul Chahar", "Matt Henry", "Sarfaraz Khan",
        "Zak Foulkes", "Matthew Short", "Aman Khan", "Kartik Sharma", "Prashant Veer",
    ],
    "Delhi Capitals": [
        "Axar Patel", "KL Rahul", "Kuldeep Yadav", "Mitchell Starc", "T Natarajan",
        "Tristan Stubbs", "Mukesh Kumar", "Nitish Rana", "Abishek Porel", "Ashutosh Sharma",
        "Sameer Rizvi", "Dushmantha Chameera", "Vipraj Nigam", "Karun Nair", "Madhav Tiwari",
        "Tripurana Vijay", "Ajay Mandal", "Ben Duckett", "Prithvi Shaw", "Auqib Nabi",
        "Pathum Nissanka", "Kyle Jamieson", "Lungi Ngidi", "David Miller", "Sahil Parakh",
    ],
    "Kolkata Knight Riders": [
        "Rinku Singh", "Sunil Narine", "Varun Chakravarthy", "Harshit Rana", "Ramandeep Singh",
        "Angkrish Raghuvanshi", "Vaibhav Arora", "Ajinkya Rahane", "Rovman Powell", "Manish Pandey",
        "Umran Malik", "Anukul Roy", "Finn Allen", "Matheesha Pathirana", "Rachin Ravindra",
        "Cameron Green", "Mustafizur Rahman", "Akash Deep", "Tim Seifert", "Tejasvi Dahiya",
        "Rahul Tripathi", "Kartik Tyagi", "Prashant Solanki", "Sarthak Ranjan", "Daksh Kamra",
    ],
    "Rajasthan Royals": [
        "Yashasvi Jaiswal", "Ravindra Jadeja", "Riyan Parag", "Dhruv Jurel", "Jofra Archer",
        "Shimron Hetmyer", "Tushar Deshpande", "Sandeep Sharma", "Nandre Burger", "Sam Curran",
        "Kwena Maphaka", "Vaibhav Sooryavanshi", "Donovan Ferreira", "Shubham Dubey", "Yudhvir Singh",
        "Lhuan-dre Pretorius", "Adam Milne", "Sushant Mishra", "Kuldeep Sen", "Aman Rao",
        "Ravi Singh", "Yash Raj Punja", "Vignesh Puthur", "Brijesh Sharma",
    ],
    "Gujarat Titans": [
        "Rashid Khan", "Shubman Gill", "Mohammed Siraj", "Jos Buttler", "Kagiso Rabada",
        "Prasidh Krishna", "Sai Sudharsan", "Rahul Tewatia", "M Shahrukh Khan", "Washington Sundar",
        "Glenn Phillips", "Sai Kishore", "Arshad Khan", "Gurnoor Brar", "Ishant Sharma",
        "Jayant Yadav", "Kumar Kushagra", "Anuj Rawat", "Nishant Sindhu", "Manav Suthar",
        "Jason Holder", "Tom Banton", "Luke Wood", "Ashok Sharma", "Prithvi Raj",
    ],
    "Lucknow Super Giants": [
        "Rishabh Pant", "Nicholas Pooran", "Mayank Yadav", "Mohammed Shami", "Avesh Khan",
        "Abdul Samad", "Ayush Badoni", "Mohsin Khan", "Mitchell Marsh", "Shahbaz Ahmed",
        "Aiden Markram", "Matthew Breetzke", "Manimaran Siddharth", "Akash Singh", "Arjun Tendulkar",
        "Arshin Kulkarni", "Prince Yadav", "Digvesh Rathi", "Himmat Singh", "Wanindu Hasaranga",
        "Anrich Nortje", "Josh Inglis", "Mukul Choudhary", "Naman Tiwari", "Akshat Raghuwanshi",
    ],
    "Punjab Kings": [
        "Shreyas Iyer", "Arshdeep Singh", "Yuzvendra Chahal", "Marcus Stoinis", "Marco Jansen",
        "Shashank Singh", "Nehal Wadhera", "Prabhsimran Singh", "Priyansh Arya", "Mitchell Owen",
        "Azmatullah Omarzai", "Lockie Ferguson", "Vijaykumar Vyshak", "Yash Thakur", "Harpreet Brar",
        "Vishnu Vinod", "Xavier Bartlett", "Pyla Avinash", "Harnoor Singh", "Suryansh Shedge",
        "Musheer Khan", "Cooper Connolly", "Ben Dwarshuis", "Vishal Nishad", "Praveen Dubey",
    ],
}

def get_initial_player_pool():
    """Build the starting pool of draftable players for a brand-new league.

    Reads every row of `players.csv` into a `Player`, then — if fewer than
    180 players were loaded — fills the remainder with randomly generated
    "Domestic_Prospect" players (young, role-appropriate ratings and a
    generic archetype/strengths profile) so the mega draft always has enough
    players for ten 21-player squads.

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
