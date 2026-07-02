# international_data.py
"""Current (2026) international cricket rosters for 10 nations across 3 formats.

Real player names are used here; an IP-safe rename pass (initial-preserving
convention from scripts/ip_safe_rename.py) is explicitly deferred per product
decision and will be applied before a public release containing this data.

Each nation has a T20I, ODI, and Test squad of ~18 players.  Ratings are
calibrated to the same 0-100 scale used by players.csv / players_alltime.csv:
  base_ovr  = overall quality floor
  batting_ovr / bowling_ovr = specialist ceiling
is_overseas is always False for national-team data (no overseas cap concept).
natural_slot corresponds to batting position 1-11.
"""

from cricket_sim_engine.models import Player

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _p(name, role, base_ovr, bat_ovr, bowl_ovr, age,
       bat_hand, bowl_hand, bat_arch, bowl_phase, bowl_type,
       strengths, weaknesses, slot):
    """Build a Player, setting preferred_position from slot."""
    p = Player(name, role, base_ovr, bat_ovr, bowl_ovr,
               False,  # is_overseas — always False for national squads
               age, bat_hand, bowl_hand, bat_arch, bowl_phase,
               bowl_type, strengths, weaknesses)
    p.preferred_position = slot
    return p


# ---------------------------------------------------------------------------
# INDIA
# ---------------------------------------------------------------------------

INDIA_T20I = [
    _p("Shreyas Iyer","Batsman",87,89,10,31,"Right","None","Anchor","Part-time","None","Technique against pace,Consistency","Short-pitch bowling",5),
    _p("Tilak Varma","Batsman",85,87,8,23,"Left","None","Anchor","Part-time","None","Timing,Composure","Wide outside off",4),
    _p("Abhishek Sharma","Batsman",83,87,12,25,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Power hitting,Strike rate","Spin off stump",1),
    _p("Sanju Samson","Wicketkeeper",84,86,5,31,"Right","None","Anchor","Part-time","None","Glove work,Attacking batting","Consistency under pressure",2),
    _p("Ishan Kishan","Wicketkeeper",80,82,5,27,"Left","None","Aggressive Opener","Part-time","None","Power hitting,Running between wickets","Spin in middle overs",1),
    _p("Shivam Dube","All-Rounder",80,82,72,32,"Left","Right","Lower-order Hitter","Death","Right-arm Medium","Power hitting,Six hitting","Discipline with the ball",6),
    _p("Vaibhav Sooryavanshi","Batsman",78,82,5,16,"Left","Left","Aggressive Opener","Part-time","None","Natural timing,Fearless batting","Inexperience",1),
    _p("Axar Patel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Line and length","Short-pitched deliveries",7),
    _p("Washington Sundar","All-Rounder",82,75,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Adaptability","Pace on turning tracks",8),
    _p("Ravi Bishnoi","Bowler (Spin)",83,30,86,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,Economy","Powerplay batting",10),
    _p("Varun Chakravarthy","Bowler (Spin)",84,25,87,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Red-ball form",10),
    _p("Arshdeep Singh","Bowler (Fast)",87,25,89,27,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Swing,Death bowling","Batting under pressure",11),
    _p("Harshit Rana","Bowler (Fast)",78,20,80,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Bounce","Consistency",10),
    _p("Prasidh Krishna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Death yorkers","Short-pitch to batters",10),
    _p("Rinku Singh","Batsman",82,84,5,28,"Left","None","Lower-order Hitter","Part-time","None","Finishing,Six hitting","Spin in early overs",7),
    _p("Riyan Parag","All-Rounder",79,80,72,24,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Fielding,Six hitting","Consistency against top pace",6),
    _p("Suryansh Shedge","All-Rounder",74,74,68,23,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium","Adaptability,Fielding","Experience",7),
    _p("Prince Yadav","Bowler (Fast)",72,18,74,23,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Pace,Swing","Batting",11),
]

INDIA_ODI = [
    _p("Shubman Gill","Batsman",90,92,10,26,"Right","None","Anchor","Part-time","None","Technique,Elegance","Hostile pace in early overs",1),
    _p("Rohit Sharma","Batsman",88,91,5,39,"Right","None","Aggressive Opener","Part-time","None","Power hitting,ODI record","Age management",1),
    _p("Virat Kohli","Batsman",93,95,5,37,"Right","None","Anchor","Part-time","None","Chase mastery,Consistency","Short pitch from left-armers",3),
    _p("Shreyas Iyer","Batsman",87,89,10,31,"Right","None","Anchor","Part-time","None","Leg-side play,Finisher","Short-pitch bowling",5),
    _p("KL Rahul","Wicketkeeper",86,88,5,34,"Right","None","Anchor","Part-time","None","Technique,Versatility","Scoring rate in middle overs",2),
    _p("Rishabh Pant","Wicketkeeper",88,90,5,28,"Left","None","Aggressive Opener","Part-time","None","Match-winning innings,Glove work","Wide outside off",6),
    _p("Yashasvi Jaiswal","Batsman",86,88,10,24,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Explosive starts,Natural timing","Inexperience in chases",1),
    _p("Washington Sundar","All-Rounder",82,74,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Batting utility","Pace in powerplay",8),
    _p("Ravindra Jadeja","All-Rounder",89,82,86,37,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Fielding,All-round impact","Spin in death overs",8),
    _p("Axar Patel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Batting depth","Short-pitched deliveries",8),
    _p("Nitish Kumar Reddy","All-Rounder",78,76,72,23,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Hard hitting,Pace variation","Experience",7),
    _p("Kuldeep Yadav","Bowler (Spin)",88,28,90,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Googly,Variations","Wide outside off",10),
    _p("Jasprit Bumrah","Bowler (Fast)",96,25,97,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Yorkers,Accuracy","Batting",11),
    _p("Mohammed Siraj","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball swing,Accuracy","Death overs economy",10),
    _p("Arshdeep Singh","Bowler (Fast)",87,25,89,27,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Swing,Death bowling","Batting",11),
    _p("Harshit Rana","Bowler (Fast)",78,20,80,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Bounce","Consistency",10),
    _p("Prasidh Krishna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Death yorkers","Short-pitch to batters",10),
    _p("Ishan Kishan","Wicketkeeper",80,82,5,27,"Left","None","Aggressive Opener","Part-time","None","Power hitting,Running between wickets","Spin in middle overs",1),
]

INDIA_TEST = [
    _p("Shubman Gill","Batsman",90,92,10,26,"Right","None","Anchor","Part-time","None","Technique,Elegance","Hostile pace in early overs",1),
    _p("Rishabh Pant","Wicketkeeper",88,90,5,28,"Left","None","Aggressive Opener","Part-time","None","Match-winning innings,Glove work","Wide outside off",6),
    _p("Yashasvi Jaiswal","Batsman",86,88,10,24,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Explosive starts,Natural timing","Inconsistency vs pace",1),
    _p("KL Rahul","Batsman",86,88,5,34,"Right","None","Anchor","Part-time","None","Technique,Versatility","Scoring rate in middle overs",2),
    _p("Sai Sudharsan","Batsman",81,83,5,24,"Left","None","Anchor","Part-time","None","Solid technique,Temperament","Hostile fast bowling",3),
    _p("Devdutt Padikkal","Batsman",78,80,5,25,"Left","None","Anchor","Part-time","None","Left-hand elegance,Timing","Short pitch",3),
    _p("Dhruv Jurel","Wicketkeeper",77,78,5,25,"Right","None","Middle-order Rotator","Part-time","None","Grit,Glove work","Lack of big international knocks",7),
    _p("Karun Nair","Batsman",78,80,5,34,"Right","None","Anchor","Part-time","None","Long innings,Temperament","Consistency at highest level",6),
    _p("Ravindra Jadeja","All-Rounder",89,82,86,37,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Fielding,All-round impact","Spin in death overs",8),
    _p("Washington Sundar","All-Rounder",82,74,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Batting utility","Pace in powerplay",8),
    _p("Axar Patel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Batting depth","Short-pitched deliveries",8),
    _p("Nitish Kumar Reddy","All-Rounder",78,76,72,23,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Hard hitting,Pace variation","Experience",7),
    _p("Jasprit Bumrah","Bowler (Fast)",96,25,97,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Yorkers,Accuracy","Batting",11),
    _p("Mohammed Siraj","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball swing,Accuracy","Death overs economy",10),
    _p("Akash Deep","Bowler (Fast)",79,20,81,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Movement","Batting",10),
    _p("Kuldeep Yadav","Bowler (Spin)",88,28,90,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Googly,Variations","Wide outside off",10),
    _p("Mohammed Shami","Bowler (Fast)",88,22,90,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Age and fitness",10),
    _p("Prasidh Krishna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Bounce","Short-pitch to batters",10),
]

# ---------------------------------------------------------------------------
# AUSTRALIA
# ---------------------------------------------------------------------------

AUSTRALIA_T20I = [
    _p("Mitchell Marsh","All-Rounder",84,82,76,34,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Pace variation","Consistency in bowling",4),
    _p("Travis Head","Batsman",90,92,10,32,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Timing","Spin on turning tracks",2),
    _p("Josh Inglis","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Clean hitting,Glove work","Long innings",1),
    _p("Steven Smith","Batsman",88,90,10,36,"Right","Right","Anchor","Part-time","Leg-spin","Unconventional technique,Consistency","Short-pitch",4),
    _p("Tim David","Batsman",84,86,5,30,"Right","None","Lower-order Hitter","Part-time","None","Six hitting,Death finisher","Spin in powerplay",6),
    _p("Glenn Maxwell","All-Rounder",84,84,76,37,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","360-degree batting,Fielding","Consistency",5),
    _p("Marcus Stoinis","All-Rounder",82,82,72,36,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Death yorkers","Spin bowling",6),
    _p("Cameron Green","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",7),
    _p("Cooper Connolly","All-Rounder",75,73,70,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Versatility,Youth","Experience",8),
    _p("Aaron Hardie","All-Rounder",74,72,70,25,"Right","Right","Middle-order Rotator","Death","Right-arm Medium-fast","Utility,Adaptability","Experience",7),
    _p("Pat Cummins","Bowler (Fast)",90,30,92,33,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Accuracy,Reverse swing","Batting",11),
    _p("Josh Hazlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Death overs",10),
    _p("Nathan Ellis","Bowler (Fast)",78,22,80,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling,Yorkers","Batting",10),
    _p("Xavier Bartlett","Bowler (Fast)",76,22,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Pace,Swing","Experience",10),
    _p("Ben Dwarshuis","Bowler (Fast)",76,22,78,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death bowling","Batting",11),
    _p("Adam Zampa","Bowler (Spin)",86,25,88,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Variations,Economy","Short boundaries",10),
    _p("Matthew Kuhnemann","Bowler (Spin)",74,22,76,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Left-arm angle,Economy","Inexperience",10),
    _p("Matthew Renshaw","Batsman",76,77,5,30,"Left","None","Anchor","Part-time","None","Versatility,Left-hand","Pace in powerplay",3),
]

AUSTRALIA_ODI = [
    _p("Mitchell Marsh","All-Rounder",84,82,76,34,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Pace variation","Consistency in bowling",4),
    _p("Travis Head","Batsman",90,92,10,32,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Timing","Spin on turning tracks",1),
    _p("Alex Carey","Wicketkeeper",82,83,5,34,"Left","None","Anchor","Part-time","None","Reliability,Glove work","Power hitting",7),
    _p("Josh Inglis","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Clean hitting,Glove work","Long innings",5),
    _p("Marnus Labuschagne","Batsman",85,87,10,31,"Right","Right","Anchor","Part-time","Leg-spin","Concentration,Technique","Scoring rate in ODIs",4),
    _p("Cameron Green","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",6),
    _p("Cooper Connolly","All-Rounder",75,73,70,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Versatility,Youth","Experience",8),
    _p("Matt Short","All-Rounder",78,79,72,30,"Right","Right","Aggressive Opener","Middle Overs","Right-arm Offbreak","Power hitting,Utility","Spin in death",2),
    _p("Aaron Hardie","All-Rounder",74,72,70,25,"Right","Right","Middle-order Rotator","Death","Right-arm Medium-fast","Utility,Adaptability","Experience",7),
    _p("Matthew Renshaw","Batsman",76,77,5,30,"Left","None","Anchor","Part-time","None","Versatility,Left-hand","Pace in powerplay",3),
    _p("Mitchell Starc","Bowler (Fast)",88,28,90,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","New-ball swing,Left-arm angle","Death overs economy",11),
    _p("Josh Hazlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Death overs",10),
    _p("Nathan Ellis","Bowler (Fast)",78,22,80,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling,Yorkers","Batting",10),
    _p("Riley Meredith","Bowler (Fast)",77,20,79,29,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Accuracy",10),
    _p("Adam Zampa","Bowler (Spin)",86,25,88,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Variations,Economy","Short boundaries",10),
    _p("Matthew Kuhnemann","Bowler (Spin)",74,22,76,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Left-arm angle,Economy","Inexperience",10),
    _p("Tanveer Sangha","Bowler (Spin)",72,20,74,24,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Variations","Experience",11),
    _p("Oliver Peake","Batsman",71,73,5,24,"Right","None","Middle-order Rotator","Part-time","None","Fresh talent,Potential","Experience",5),
]

AUSTRALIA_TEST = [
    _p("Pat Cummins","Bowler (Fast)",90,30,92,33,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Accuracy,Reverse swing","Batting",8),
    _p("Steven Smith","Batsman",94,96,10,36,"Right","Right","Anchor","Part-time","Leg-spin","Unconventional technique,Consistency","Short-pitch",4),
    _p("Usman Khawaja","Batsman",88,90,5,39,"Left","None","Anchor","Part-time","None","Technique,Concentration","Age management",1),
    _p("Marnus Labuschagne","Batsman",88,90,10,31,"Right","Right","Anchor","Part-time","Leg-spin","Concentration,Resilience","Pace on hard length",3),
    _p("Travis Head","Batsman",88,90,10,32,"Left","None","Aggressive Opener","Part-time","None","Attacking intent,Footwork","Bounce from outside off",5),
    _p("Alex Carey","Wicketkeeper",82,83,5,34,"Left","None","Anchor","Part-time","None","Reliability,Glove work","Power hitting",7),
    _p("Josh Inglis","Wicketkeeper",78,79,5,31,"Right","None","Anchor","Part-time","None","Clean hitting,Backup option","Long Test innings",6),
    _p("Cameron Green","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",6),
    _p("Beau Webster","All-Rounder",78,76,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Consistency,Utility","Bowling penetration",7),
    _p("Mitchell Starc","Bowler (Fast)",88,28,90,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","New-ball swing,Left-arm angle","Death overs economy",11),
    _p("Josh Hazlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Away swing",10),
    _p("Scott Boland","Bowler (Fast)",82,22,84,37,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Accuracy,WACA/MCG seam","Overseas wickets",10),
    _p("Nathan Lyon","Bowler (Spin)",88,25,90,38,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Home spin,Partnership breaker","Away tours",10),
    _p("Jake Weatherald","Batsman",74,75,5,31,"Left","None","Anchor","Part-time","None","Left-hand technique,Patience","Experience",2),
    _p("Marcus Harris","Batsman",72,73,5,33,"Left","None","Anchor","Part-time","None","Experience,Left-hand","Consistency",1),
    _p("Todd Murphy","Bowler (Spin)",74,20,76,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Away spin","Experience",11),
    _p("Jhye Richardson","Bowler (Fast)",76,22,78,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Pace","Injury history",10),
    _p("Brendan Doggett","Bowler (Fast)",70,20,72,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement,Accuracy","Experience",11),
]

# ---------------------------------------------------------------------------
# ENGLAND
# ---------------------------------------------------------------------------

ENGLAND_T20I = [
    _p("Harry Brook","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique against pace","Spin on turning tracks",3),
    _p("Jos Buttler","Wicketkeeper",88,90,5,35,"Right","None","Lower-order Hitter","Part-time","None","Explosive hitting,Glove work","Pace in early overs",4),
    _p("Phil Salt","Wicketkeeper",82,84,5,29,"Right","None","Aggressive Opener","Part-time","None","Powerplay aggression,Glove work","Middle overs consistency",1),
    _p("Ben Duckett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Liam Livingstone","All-Rounder",83,83,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Six hitting,360 degree","Consistency with ball",5),
    _p("Jacob Bethell","All-Rounder",82,80,74,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",6),
    _p("Will Jacks","All-Rounder",80,80,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Consistency",6),
    _p("Sam Curran","All-Rounder",83,76,80,27,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Left-arm angle,Lower-order hitting","Economy in powerplay",8),
    _p("Jofra Archer","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Injury history",10),
    _p("Adil Rashid","Bowler (Spin)",86,30,88,38,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,White-ball economy","Batting",10),
    _p("Rehan Ahmed","Bowler (Spin)",78,28,80,21,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Variations","Experience",10),
    _p("Saqib Mahmood","Bowler (Fast)",78,22,80,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Pace","Consistency",11),
    _p("Luke Wood","Bowler (Fast)",74,20,76,31,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Death bowling,Left-arm angle","Away economy",11),
    _p("Jamie Overton","Bowler (Fast)",76,22,78,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Height,Bounce","Away swing",10),
    _p("Josh Tongue","Bowler (Fast)",77,22,79,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Consistency",10),
    _p("Liam Dawson","All-Rounder",74,70,72,35,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Lower-order","Bowling in powerplay",9),
    _p("Jamie Smith","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",4),
    _p("Tom Banton","Wicketkeeper",76,78,5,27,"Right","None","Aggressive Opener","Part-time","None","Power hitting,Keeper backup","Middle-over consistency",2),
]

ENGLAND_ODI = [
    _p("Harry Brook","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique","Spin on turning tracks",3),
    _p("Jos Buttler","Wicketkeeper",88,90,5,35,"Right","None","Lower-order Hitter","Part-time","None","Explosive hitting,Glove work","Pace in early overs",4),
    _p("Ben Duckett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Joe Root","Batsman",93,95,10,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Consistency,Technique","Short-pitch pace",4),
    _p("Jamie Smith","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",5),
    _p("Zak Crawley","Batsman",82,84,5,28,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Timing","Short-pitch dismissals",1),
    _p("Jacob Bethell","All-Rounder",82,80,74,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",6),
    _p("Will Jacks","All-Rounder",80,80,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Consistency",6),
    _p("Sam Curran","All-Rounder",83,76,80,27,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Left-arm angle,Lower-order hitting","Economy in powerplay",8),
    _p("Liam Dawson","All-Rounder",74,70,72,35,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Lower-order","Bowling in powerplay",9),
    _p("Gus Atkinson","Bowler (Fast)",84,25,86,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","New-ball swing,Seam","Batting",10),
    _p("Brydon Carse","Bowler (Fast)",80,22,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Economy",10),
    _p("Jofra Archer","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Injury history",11),
    _p("Matthew Potts","Bowler (Fast)",78,22,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Batting",10),
    _p("Jamie Overton","Bowler (Fast)",76,22,78,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Height,Bounce","Away swing",10),
    _p("Adil Rashid","Bowler (Spin)",86,30,88,38,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,White-ball economy","Batting",11),
    _p("Saqib Mahmood","Bowler (Fast)",78,22,80,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Pace","Consistency",11),
    _p("Tom Banton","Wicketkeeper",76,78,5,27,"Right","None","Aggressive Opener","Part-time","None","Power hitting,Keeper backup","Middle-over consistency",2),
]

ENGLAND_TEST = [
    _p("Ben Stokes","All-Rounder",93,87,88,34,"Left","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Match-winning ability,Leadership","Fitness management",6),
    _p("Harry Brook","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique","Spin on turning tracks",4),
    _p("Joe Root","Batsman",96,98,10,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Consistency,Adaptability","Short-pitch pace",4),
    _p("Zak Crawley","Batsman",83,85,5,28,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Timing","Short-pitch dismissals",1),
    _p("Ben Duckett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Ollie Pope","Batsman",84,86,5,28,"Right","None","Anchor","Part-time","None","Technique,Middle-order stability","Hostile pace",5),
    _p("Jacob Bethell","All-Rounder",82,80,74,22,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",3),
    _p("Jamie Smith","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",7),
    _p("James Rew","Wicketkeeper",70,71,5,22,"Left","None","Middle-order Rotator","Part-time","None","Youth,Left-hand","Experience",8),
    _p("Will Jacks","All-Rounder",80,78,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Batting consistency",8),
    _p("Gus Atkinson","Bowler (Fast)",84,25,86,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","New-ball swing,Seam","Batting",10),
    _p("Brydon Carse","Bowler (Fast)",80,22,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Economy",9),
    _p("Jofra Archer","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Injury history",10),
    _p("Mark Wood","Bowler (Fast)",84,22,86,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Wickets","Injury history",11),
    _p("Josh Tongue","Bowler (Fast)",77,22,79,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Consistency",10),
    _p("Matthew Potts","Bowler (Fast)",78,22,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Batting",10),
    _p("Shoaib Bashir","Bowler (Spin)",78,22,80,22,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Away spin","Experience",11),
    _p("Ollie Robinson","Bowler (Fast)",80,22,82,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Accuracy,Swing","Pace",10),
]

# ---------------------------------------------------------------------------
# NEW ZEALAND
# ---------------------------------------------------------------------------

NEW_ZEALAND_T20I = [
    _p("Mitchell Santner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Finn Allen","Batsman",82,84,5,27,"Right","None","Aggressive Opener","Part-time","None","Powerplay strike rate,360-degree","Middle-overs consistency",1),
    _p("Devon Conway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch from right-armers",2),
    _p("Tim Seifert","Wicketkeeper",78,80,5,31,"Right","None","Lower-order Hitter","Part-time","None","Keeper finisher,Reverse hitting","Middle-overs accumulation",7),
    _p("Mark Chapman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Daryl Mitchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Seam utility","Bowling consistency",5),
    _p("Glenn Phillips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Spectacular hitting,Fielding","Consistency with ball",6),
    _p("Rachin Ravindra","All-Rounder",84,84,74,27,"Left","Left","Aggressive Opener","Middle Overs","Left-arm Orthodox","Fluent strokeplay,Left-arm spin","Pacey powerplay bowling",3),
    _p("Michael Bracewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",9),
    _p("Ish Sodhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Batting",10),
    _p("Jacob Duffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death discipline,Swing","Express pace",10),
    _p("Lockie Ferguson","Bowler (Fast)",84,22,86,35,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Economy",11),
    _p("Nathan Smith","Bowler (Fast)",76,22,78,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Swing","Experience",11),
    _p("Ben Sears","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Pace,Death bowling","Batting",11),
    _p("Adam Milne","Bowler (Fast)",78,20,80,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness history",11),
    _p("Kyle Jamieson","Bowler (Fast)",79,24,81,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",10),
    _p("Matt Henry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Tom Latham","Wicketkeeper",80,82,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",3),
]

NEW_ZEALAND_ODI = [
    _p("Mitchell Santner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Tom Latham","Wicketkeeper",82,84,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",1),
    _p("Devon Conway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch",2),
    _p("Kane Williamson","Batsman",92,94,5,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Masterful technique,Leadership","Aggressive periods",3),
    _p("Daryl Mitchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Seam utility","Bowling consistency",5),
    _p("Glenn Phillips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Spectacular hitting,Fielding","Consistency with ball",6),
    _p("Rachin Ravindra","All-Rounder",84,84,74,27,"Left","Left","Aggressive Opener","Middle Overs","Left-arm Orthodox","Fluent strokeplay,Left-arm spin","Pacey powerplay bowling",3),
    _p("Mark Chapman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Michael Bracewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",9),
    _p("Ish Sodhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Batting",10),
    _p("Jacob Duffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death discipline,Swing","Express pace",10),
    _p("Lockie Ferguson","Bowler (Fast)",84,22,86,35,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Economy",11),
    _p("Kyle Jamieson","Bowler (Fast)",79,24,81,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",10),
    _p("Matt Henry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Trent Boult","Bowler (Fast)",85,24,87,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Swing,New-ball wickets","Death economy",11),
    _p("Tim Southee","Bowler (Fast)",82,22,84,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Experience","Pace",10),
    _p("Nathan Smith","Bowler (Fast)",76,22,78,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Swing","Experience",11),
    _p("Finn Allen","Batsman",82,84,5,27,"Right","None","Aggressive Opener","Part-time","None","Powerplay strike rate,Fielding","Middle-overs consistency",1),
]

NEW_ZEALAND_TEST = [
    _p("Tom Latham","Wicketkeeper",84,86,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",1),
    _p("Kane Williamson","Batsman",93,95,5,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Masterful technique,Leadership","Aggressive periods",3),
    _p("Devon Conway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch",2),
    _p("Rachin Ravindra","All-Rounder",84,84,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Fluent strokeplay,All-round skill","Pacey bowling",4),
    _p("Daryl Mitchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Grit","Bowling in red-ball",5),
    _p("Glenn Phillips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Attacking intent,Fielding","Consistency",6),
    _p("Michael Bracewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",8),
    _p("Matt Henry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Tim Southee","Bowler (Fast)",82,22,84,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Experience","Pace",10),
    _p("Kyle Jamieson","Bowler (Fast)",80,24,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",9),
    _p("Trent Boult","Bowler (Fast)",85,24,87,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Swing,New-ball wickets","Death economy",11),
    _p("William O'Rourke","Bowler (Fast)",78,22,80,23,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Youth,Pace","Experience",11),
    _p("Ish Sodhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Test red-ball",10),
    _p("Mitchell Santner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Mark Chapman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Will Young","Batsman",75,76,5,34,"Right","None","Anchor","Part-time","None","Patience,Grit","Scoring rate",2),
    _p("Henry Nicholls","Batsman",76,77,5,34,"Left","None","Anchor","Part-time","None","Technique,Consistency","Power",5),
    _p("Jacob Duffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Discipline","Express pace",10),
]

# ---------------------------------------------------------------------------
# SOUTH AFRICA
# ---------------------------------------------------------------------------

SOUTH_AFRICA_T20I = [
    _p("Aiden Markram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Leadership","Short-pitch fast bowling",2),
    _p("Quinton de Kock","Wicketkeeper",90,92,5,33,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Glove work","Pace outside off",1),
    _p("David Miller","Batsman",86,88,5,36,"Left","None","Lower-order Hitter","Part-time","None","Six hitting,Finisher ability","Spin early on",6),
    _p("Dewald Brevis","Batsman",82,84,8,23,"Right","Right","Aggressive Opener","Part-time","Leg-spin","Explosive power,Youth","Consistency",4),
    _p("Tristan Stubbs","Batsman",79,81,8,25,"Right","Right","Lower-order Hitter","Part-time","Right-arm Offbreak","Aggressive finishing,Youth","Experience",6),
    _p("Ryan Rickelton","Wicketkeeper",78,80,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",2),
    _p("Marco Jansen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Tall seam,Left-arm angle","Death overs economy",7),
    _p("Kagiso Rabada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in T20",10),
    _p("Anrich Nortje","Bowler (Fast)",88,22,90,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Lungi Ngidi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Corbin Bosch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility,Death bowling","International class gap",8),
    _p("Kwena Maphaka","Bowler (Fast)",78,20,80,20,"Right","Left","Defensive Tailender","Death","Left-arm Fast","Yorkers,Youth","Consistency",11),
    _p("Keshav Maharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,White-ball spin","Express pace wickets",10),
    _p("George Linde","All-Rounder",76,70,74,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm utility,Lower-order hitting","International class",9),
    _p("Wiaan Mulder","All-Rounder",78,74,74,28,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium-fast","All-round utility","Pace bowling penetration",7),
    _p("Gerald Coetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Connor Esterhuizen","Batsman",72,74,5,23,"Right","None","Aggressive Opener","Part-time","None","Form,Youth","International experience",3),
    _p("Jordan Hermann","Batsman",70,72,5,26,"Right","None","Middle-order Rotator","Part-time","None","Form-based selection","International class",5),
]

SOUTH_AFRICA_ODI = [
    _p("Temba Bavuma","Batsman",84,86,8,35,"Right","Right","Anchor","Part-time","None","Grit,Technique","Power hitting against pace",1),
    _p("Quinton de Kock","Wicketkeeper",90,92,5,33,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Glove work","Pace outside off",1),
    _p("Ryan Rickelton","Wicketkeeper",78,80,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",2),
    _p("Aiden Markram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Leadership","Short-pitch fast bowling",3),
    _p("Matthew Breetzke","Batsman",80,82,5,27,"Right","Right","Anchor","Part-time","None","High floor,Debut record","Experience",4),
    _p("Tony de Zorzi","Batsman",78,80,5,27,"Right","Right","Anchor","Part-time","None","Solid technique,Composure","Injury management",5),
    _p("Dewald Brevis","Batsman",82,84,8,23,"Right","Right","Middle-order Rotator","Part-time","Leg-spin","Explosive power,Youth","Consistency",5),
    _p("Marco Jansen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Powerplay","Left-arm Fast-medium","Tall seam,Left-arm angle","Batting consistency",8),
    _p("Corbin Bosch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility","International class gap",8),
    _p("Wiaan Mulder","All-Rounder",80,76,76,28,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium-fast","Kallis-esque utility,Test record","Pace bowling penetration",7),
    _p("Keshav Maharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,White-ball spin","Express pace wickets",10),
    _p("Prenelan Subrayen","Bowler (Spin)",70,20,72,28,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Consistency","Variations",11),
    _p("Lungi Ngidi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Nandre Burger","Bowler (Fast)",78,22,80,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness history",11),
    _p("Ottneil Baartman","Bowler (Fast)",76,20,78,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Height,Accuracy","Away record",10),
    _p("Kagiso Rabada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in ODIs",11),
    _p("Gerald Coetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Rubin Hermann","Batsman",72,74,5,28,"Left","None","Middle-order Rotator","Part-time","None","Left-hand bat,Domestic form","International class",6),
]

SOUTH_AFRICA_TEST = [
    _p("Temba Bavuma","Batsman",84,86,8,35,"Right","Right","Anchor","Part-time","None","Grit,Technique","Power hitting against pace",1),
    _p("Ryan Rickelton","Wicketkeeper",80,82,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",1),
    _p("Aiden Markram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Elegance","Short-pitch pace",3),
    _p("Tony de Zorzi","Batsman",78,80,5,27,"Right","Right","Anchor","Part-time","None","Solid technique","Experience",2),
    _p("Tristan Stubbs","Batsman",79,81,8,25,"Right","Right","Middle-order Rotator","Part-time","None","Youth,Footwork","Experience at this level",5),
    _p("David Bedingham","Batsman",76,78,5,31,"Right","None","Anchor","Part-time","None","Domestic record,Composure","International experience",5),
    _p("Wiaan Mulder","All-Rounder",80,76,76,28,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium-fast","Kallis-esque utility,Test record","Pace bowling penetration",6),
    _p("Marco Jansen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Powerplay","Left-arm Fast-medium","Tall seam,Left-arm angle","Batting consistency",8),
    _p("Corbin Bosch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility","International class gap",8),
    _p("Kyle Verreynne","Wicketkeeper",78,79,5,30,"Right","None","Anchor","Part-time","None","Grit,Glove work","Power hitting",7),
    _p("Keshav Maharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Wicket-taking","Express pace wickets",10),
    _p("Kagiso Rabada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in Tests",11),
    _p("Anrich Nortje","Bowler (Fast)",88,22,90,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Lungi Ngidi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Nandre Burger","Bowler (Fast)",78,22,80,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness history",11),
    _p("Gerald Coetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Simon Harmer","Bowler (Spin)",78,25,80,36,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","County form,Spin","Away surfaces",10),
    _p("Prenelan Subrayen","Bowler (Spin)",70,20,72,28,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy","Variations",11),
]

# ---------------------------------------------------------------------------
# PAKISTAN
# ---------------------------------------------------------------------------

PAKISTAN_T20I = [
    _p("Salman Ali Agha","All-Rounder",80,78,72,32,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Leadership,Consistency","Express pace",5),
    _p("Babar Azam","Batsman",90,92,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Scoring rate in death",3),
    _p("Shaheen Shah Afridi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",11),
    _p("Shadab Khan","All-Rounder",83,72,82,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Lower-order hitting","Economy in powerplay",8),
    _p("Saim Ayub","Batsman",82,84,8,23,"Left","Right","Aggressive Opener","Part-time","Right-arm Offbreak","Power hitting,Youth","Consistency against quality spin",1),
    _p("Fakhar Zaman","Batsman",83,85,5,36,"Left","None","Aggressive Opener","Part-time","None","Big-match temperament,Power","Age management",1),
    _p("Sahibzada Farhan","Wicketkeeper",78,80,5,28,"Right","None","Aggressive Opener","Part-time","None","Hard hitting,Glove work","Experience",2),
    _p("Usman Khan","Batsman",77,79,5,28,"Right","Right","Lower-order Hitter","Part-time","None","Power hitting,Finisher","Consistency",7),
    _p("Mohammad Nawaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Lower-order bat","Consistency",8),
    _p("Naseem Shah","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Abrar Ahmed","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Experience",10),
    _p("Haris Rauf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","High pace,Death specialist","Economy",10),
    _p("Khushdil Shah","All-Rounder",76,72,70,30,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Finisher,Left-arm spin","Consistency",7),
    _p("Iftikhar Ahmed","All-Rounder",75,72,65,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Experience","Consistency",6),
    _p("Mohammad Wasim Jr","Bowler (Fast)",74,20,76,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace","Consistency",11),
    _p("Faheem Ashraf","All-Rounder",74,68,70,31,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Lower-order hitting,Seam utility","Consistency",9),
    _p("Usman Tariq","Bowler (Fast)",70,18,72,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Emerging pace","Experience",11),
    _p("Khawaja Mohammad Nafay","Wicketkeeper",68,70,5,22,"Right","None","Lower-order Hitter","Part-time","None","Youth,PSL form","Experience",7),
]

PAKISTAN_ODI = [
    _p("Shaheen Shah Afridi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Batting",11),
    _p("Salman Ali Agha","All-Rounder",80,78,72,32,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Leadership,Consistency","Express pace",5),
    _p("Babar Azam","Batsman",90,92,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Scoring rate in death",3),
    _p("Haris Rauf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","High pace,Death specialist","Economy",10),
    _p("Naseem Shah","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Shadab Khan","All-Rounder",83,72,82,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Lower-order hitting","Economy in powerplay",8),
    _p("Sahibzada Farhan","Wicketkeeper",78,80,5,28,"Right","None","Aggressive Opener","Part-time","None","Hard hitting,Glove work","Experience",2),
    _p("Abrar Ahmed","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Experience",10),
    _p("Abdul Samad","Batsman",74,76,8,24,"Left","Right","Lower-order Hitter","Part-time","Right-arm Offbreak","Power hitting,Youth","Experience",7),
    _p("Sufyan Moqim","Bowler (Spin)",76,20,78,23,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","PSL form,Chinaman","Experience",10),
    _p("Fakhar Zaman","Batsman",83,85,5,36,"Left","None","Aggressive Opener","Part-time","None","Big-match temperament,Power","Age management",1),
    _p("Saim Ayub","Batsman",82,84,8,23,"Left","Right","Aggressive Opener","Part-time","Right-arm Offbreak","Power hitting,Youth","Consistency against quality spin",1),
    _p("Arafat Minhas","Bowler (Spin)",74,18,76,21,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Debut fifer,Youth","Experience",11),
    _p("Mohammad Nawaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Lower-order bat","Consistency",8),
    _p("Imam-ul-Haq","Batsman",80,82,5,29,"Left","None","Anchor","Part-time","None","Gritty opener,Consistency","Attack",1),
    _p("Rohail Nazir","Wicketkeeper",70,71,5,24,"Right","None","Middle-order Rotator","Part-time","None","Youth,Promising keeper","International experience",6),
    _p("Ahmed Daniyal","Bowler (Fast)",72,18,74,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Seam","Experience",11),
    _p("Faheem Ashraf","All-Rounder",74,68,70,31,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Lower-order hitting,Seam utility","Consistency",9),
]

PAKISTAN_TEST = [
    _p("Shan Masood","Batsman",82,84,5,36,"Left","None","Anchor","Part-time","None","Grit,Technique","Pace outside off",1),
    _p("Babar Azam","Batsman",91,93,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Short-pitch pace",3),
    _p("Mohammad Rizwan","Wicketkeeper",85,87,5,33,"Right","None","Anchor","Part-time","None","Grit,Glove work","Aggression",5),
    _p("Saud Shakil","Batsman",80,82,5,29,"Left","None","Anchor","Part-time","None","Technique,Left-hand","Scoring rate",4),
    _p("Kamran Ghulam","Batsman",76,78,5,28,"Right","None","Anchor","Part-time","None","Domestic record,Consistency","Experience",5),
    _p("Salman Ali Agha","All-Rounder",80,78,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Utility,Batting","Bowling penetration",6),
    _p("Aamer Jamal","All-Rounder",78,70,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam movement,All-round","Consistency",8),
    _p("Abdullah Shafique","Batsman",82,84,5,26,"Right","None","Anchor","Part-time","None","Technique,Composure","Hostile pace",2),
    _p("Khurram Shahzad","Bowler (Fast)",78,20,80,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam","Experience",10),
    _p("Shaheen Shah Afridi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Batting",11),
    _p("Naseem Shah","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Noman Ali","Bowler (Spin)",84,22,86,39,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away wickets",10),
    _p("Sajid Khan","Bowler (Spin)",80,20,82,33,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Home spin,Economy","Away surfaces",10),
    _p("Abrar Ahmed","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations","Away experience",10),
    _p("Haris Rauf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in Tests",10),
    _p("Mohammad Nawaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Batting","Consistency",9),
    _p("Tayyab Tahir","Batsman",74,76,5,28,"Right","None","Middle-order Rotator","Part-time","None","Domestic form","International experience",6),
    _p("Irfan Khan Niazi","Wicketkeeper",70,71,5,27,"Right","None","Middle-order Rotator","Part-time","None","Domestic form,Glove work","Experience",7),
]

# ---------------------------------------------------------------------------
# SRI LANKA
# ---------------------------------------------------------------------------

SRI_LANKA_T20I = [
    _p("Dasun Shanaka","All-Rounder",78,74,72,35,"Right","Right","Lower-order Hitter","Death","Right-arm Medium","Veteran experience,Finisher","Consistency",6),
    _p("Pathum Nissanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Power in death",2),
    _p("Kamil Mishara","Batsman",76,78,5,23,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Youth","Experience",1),
    _p("Kusal Mendis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",3),
    _p("Kusal Perera","Wicketkeeper",80,82,5,36,"Left","None","Aggressive Opener","Part-time","None","Veteran power,Left-hand","Age management",1),
    _p("Dhananjaya de Silva","All-Rounder",82,80,72,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Utility","Express pace",4),
    _p("Charith Asalanka","Batsman",82,84,5,29,"Left","Left","Lower-order Hitter","Part-time","Left-arm Orthodox","Finisher,Left-hand technique","Express pace",5),
    _p("Janith Liyanage","Batsman",74,76,5,28,"Right","Right","Middle-order Rotator","Part-time","None","Utility,Adaptability","Power hitting",5),
    _p("Kamindu Mendis","All-Rounder",82,80,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Switch hitting,Ambidextrous spin","Bowling workload",6),
    _p("Wanindu Hasaranga","All-Rounder",87,72,88,29,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Strike rate","Economy in powerplay",8),
    _p("Dunith Wellalage","All-Rounder",78,68,76,23,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Youth,All-round potential","Experience",9),
    _p("Maheesh Theekshana","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery variations,Economy","Away surfaces",10),
    _p("Dushan Hemantha","Bowler (Spin)",70,18,72,23,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Economy","Experience",11),
    _p("Dushmantha Chameera","Bowler (Fast)",80,22,82,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness",10),
    _p("Matheesha Pathirana","Bowler (Fast)",84,22,86,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Yorkers,Slingy action","New-ball overs",10),
    _p("Nuwan Thushara","Bowler (Fast)",76,20,78,28,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death bowling","Away economy",11),
    _p("Eshan Malinga","Bowler (Fast)",72,18,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Chamika Karunaratne","All-Rounder",74,66,72,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","All-format utility","International class",9),
]

SRI_LANKA_ODI = [
    _p("Charith Asalanka","Batsman",82,84,5,29,"Left","Left","Anchor","Part-time","Left-arm Orthodox","Consistency,Leadership","Express pace",3),
    _p("Pathum Nissanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Power in death",1),
    _p("Kamil Mishara","Batsman",76,78,5,23,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Youth","Experience",2),
    _p("Kusal Mendis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",4),
    _p("Sadeera Samarawickrama","Wicketkeeper",79,81,5,28,"Right","None","Middle-order Rotator","Part-time","None","Stroke play,Glove backup","Consistency",5),
    _p("Dhananjaya de Silva","All-Rounder",82,80,72,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Utility","Express pace",5),
    _p("Janith Liyanage","Batsman",74,76,5,28,"Right","Right","Middle-order Rotator","Part-time","None","Utility,Adaptability","Power hitting",6),
    _p("Kamindu Mendis","All-Rounder",82,80,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Switch hitting,Ambidextrous spin","Bowling workload",7),
    _p("Dunith Wellalage","All-Rounder",78,68,76,23,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Youth,All-round potential","Experience",9),
    _p("Wanindu Hasaranga","All-Rounder",87,72,88,29,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Strike rate","Economy in powerplay",8),
    _p("Jeffrey Vandersay","Bowler (Spin)",76,22,78,33,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Experience,Variations","Economy",10),
    _p("Maheesh Theekshana","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery variations,Economy","Away surfaces",10),
    _p("Milan Rathnayake","All-Rounder",72,66,70,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Emerging AR,Youth","Experience",9),
    _p("Asitha Fernando","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball,Swing","Death overs",10),
    _p("Pramod Madushan","Bowler (Fast)",74,20,76,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam,New-ball","Experience",11),
    _p("Eshan Malinga","Bowler (Fast)",72,18,74,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Dushmantha Chameera","Bowler (Fast)",80,22,82,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness",10),
    _p("Pavan Rathnayake","All-Rounder",68,64,66,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Medium","Utility,Youth","Experience",9),
]

SRI_LANKA_TEST = [
    _p("Dhananjaya de Silva","All-Rounder",84,82,74,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Leadership","Express pace away",4),
    _p("Kamindu Mendis","All-Rounder",84,83,76,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Record-breaking form,All-round","Away conditions",3),
    _p("Dinesh Chandimal","Wicketkeeper",82,84,5,36,"Right","None","Anchor","Part-time","None","Grit,Glove work","Power hitting",6),
    _p("Pathum Nissanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Hostile away pace",1),
    _p("Nishan Madushka","Batsman",75,77,5,26,"Right","None","Anchor","Part-time","None","Youth,Opener","Experience",1),
    _p("Kusal Mendis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",5),
    _p("Prabath Jayasuriya","Bowler (Spin)",84,22,86,34,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away surfaces",10),
    _p("Lahiru Kumara","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Asitha Fernando","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball,Swing","Death overs",10),
    _p("Vishwa Fernando","Bowler (Fast)",76,20,78,32,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness",11),
    _p("Ramesh Mendis","Bowler (Spin)",76,22,78,29,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Consistency","Variations",10),
    _p("Angelo Mathews","All-Rounder",80,78,70,38,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Veteran experience,Technique","Age management",5),
    _p("Lahiru Udara","Wicketkeeper",70,71,5,32,"Left","None","Middle-order Rotator","Part-time","None","Left-hand backup","Experience at this level",7),
    _p("Pasindu Sooriyabandara","Batsman",68,70,5,26,"Right","None","Anchor","Part-time","None","Youth,Domestic form","International class",2),
    _p("Tharindu Rathnayake","All-Rounder",66,62,64,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth","Experience",10),
    _p("Isitha Wijesundara","Bowler (Fast)",66,18,68,23,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth","Experience",11),
    _p("Sonal Dinusha","All-Rounder",66,62,64,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Medium-fast","Youth","Experience",9),
]

# ---------------------------------------------------------------------------
# WEST INDIES
# ---------------------------------------------------------------------------

WEST_INDIES_T20I = [
    _p("Shai Hope","Wicketkeeper",86,88,5,32,"Right","None","Anchor","Part-time","None","Prolific run-scorer,Leadership","Power in death",2),
    _p("Andre Russell","All-Rounder",86,84,82,37,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death pace","Age management",6),
    _p("Nicholas Pooran","Wicketkeeper",88,90,5,30,"Left","None","Lower-order Hitter","Part-time","None","Elite T20 finisher,Glove work","Consistency",5),
    _p("Rovman Powell","Batsman",82,84,8,32,"Right","Right","Lower-order Hitter","Part-time","None","Six hitting,Explosive","Consistency against spin",5),
    _p("Shimron Hetmyer","Batsman",84,86,5,29,"Left","None","Lower-order Hitter","Part-time","None","Explosive left-hand,Power","Availability",6),
    _p("Brandon King","Batsman",78,80,5,27,"Right","None","Aggressive Opener","Part-time","None","Attacking starts,Fielding","Middle-overs consistency",1),
    _p("Johnson Charles","Batsman",74,76,5,36,"Right","None","Aggressive Opener","Part-time","None","Veteran experience,Power","Age management",1),
    _p("Roston Chase","All-Rounder",78,76,72,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jason Holder","All-Rounder",82,74,80,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Economy in T20",8),
    _p("Akeal Hosein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Express pace wickets",10),
    _p("Gudakesh Motie","Bowler (Spin)",78,22,80,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Shamar Joseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Obed McCoy","Bowler (Fast)",78,22,80,29,"Left","Left","Defensive Tailender","Death","Left-arm Fast","Death bowling,Left-arm angle","Economy",11),
    _p("Romario Shepherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death bowling","Consistency",7),
    _p("Sherfane Rutherford","All-Rounder",76,74,68,24,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Youth,Power hitting","Experience",6),
    _p("Jayden Seales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Matthew Forde","Bowler (Fast)",72,20,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Emerging pace","Experience",11),
    _p("Quentin Sampson","Bowler (Fast)",68,18,70,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling","Experience",11),
]

WEST_INDIES_ODI = [
    _p("Shai Hope","Wicketkeeper",86,88,5,32,"Right","None","Anchor","Part-time","None","Prolific run-scorer,Leadership","Power in death",2),
    _p("Shimron Hetmyer","Batsman",84,86,5,29,"Left","None","Lower-order Hitter","Part-time","None","Explosive left-hand,Power","Availability",6),
    _p("Brandon King","Batsman",78,80,5,27,"Right","None","Aggressive Opener","Part-time","None","Attacking starts,Fielding","Middle-overs consistency",1),
    _p("Roston Chase","All-Rounder",78,76,72,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jason Holder","All-Rounder",82,74,80,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Economy in T20",7),
    _p("Justin Greaves","All-Rounder",76,72,72,28,"Right","Right","Middle-order Rotator","Powerplay","Right-arm Medium-fast","Utility,Youth","Experience",6),
    _p("Alzarri Joseph","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Wicket-taking","Fitness management",10),
    _p("Shamar Joseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Gudakesh Motie","Bowler (Spin)",78,22,80,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Akeal Hosein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Variations",10),
    _p("Keacy Carty","Batsman",72,74,5,24,"Right","None","Middle-order Rotator","Part-time","None","Emerging talent,Youth","Experience",4),
    _p("John Campbell","Batsman",72,74,5,30,"Left","None","Aggressive Opener","Part-time","None","Opening options,Left-hand","Consistency",1),
    _p("Romario Shepherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death bowling","Consistency",8),
    _p("Sherfane Rutherford","All-Rounder",76,74,68,24,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Youth,Power hitting","Experience",7),
    _p("Jayden Seales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Matthew Forde","Bowler (Fast)",72,20,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Emerging pace","Experience",11),
    _p("Obed McCoy","Bowler (Fast)",78,22,80,29,"Left","Left","Defensive Tailender","Death","Left-arm Fast","Death bowling,Left-arm angle","Economy",11),
    _p("Amir Jangoo","Wicketkeeper",66,67,5,27,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper","Experience",6),
]

WEST_INDIES_TEST = [
    _p("Kraigg Brathwaite","Batsman",82,84,5,33,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Grit,Technique","Scoring rate",1),
    _p("Shai Hope","Wicketkeeper",84,86,5,32,"Right","None","Anchor","Part-time","None","Grit,Glove work","Middle-innings urgency",5),
    _p("Roston Chase","All-Rounder",80,78,76,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jason Holder","All-Rounder",84,76,82,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Death economy",8),
    _p("Alzarri Joseph","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Wicket-taking","Fitness management",10),
    _p("Shamar Joseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Gudakesh Motie","Bowler (Spin)",80,22,82,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Justin Greaves","All-Rounder",76,72,72,28,"Right","Right","Middle-order Rotator","Powerplay","Right-arm Medium-fast","Utility,Youth","Experience",7),
    _p("Keacy Carty","Batsman",74,76,5,24,"Right","None","Middle-order Rotator","Part-time","None","Emerging talent,Youth","Experience",3),
    _p("Mikyle Louis","Batsman",72,74,5,25,"Right","None","Anchor","Part-time","None","Youth,Technical",  "Experience",2),
    _p("Alick Athanaze","Batsman",74,76,5,27,"Left","None","Middle-order Rotator","Part-time","None","Left-hand,Promise","Consistency",4),
    _p("Jayden Seales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Kevin Sinclair","All-Rounder",70,64,68,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Utility","Experience",9),
    _p("Tevin Imlach","Wicketkeeper",66,67,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Glove work","Experience",6),
    _p("Marquino Mindley","Bowler (Fast)",68,18,70,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Romario Shepherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast","Power hitting,Death bowling","Consistency",8),
    _p("Akeal Hosein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Variations",10),
]

# ---------------------------------------------------------------------------
# BANGLADESH
# ---------------------------------------------------------------------------

BANGLADESH_T20I = [
    _p("Najmul Hossain Shanto","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Litton Das","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Explosive batting,Glove work","Consistency",2),
    _p("Soumya Sarkar","Batsman",74,76,8,32,"Left","Left","Aggressive Opener","Part-time","Left-arm Medium","Left-hand power,Utility","Consistency",2),
    _p("Afif Hossain","All-Rounder",76,74,68,27,"Left","Left","Lower-order Hitter","Death","Left-arm Orthodox","Finisher,Left-arm spin","Express pace",6),
    _p("Towhid Hridoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Middle-order depth,Youth","Experience",4),
    _p("Mahmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience,Finisher","Age management",5),
    _p("Shakib Al Hasan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Mehidy Hasan Miraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Mustafizur Rahman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Cutter,Variations","Economy",10),
    _p("Taskin Ahmed","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Shoriful Islam","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death","Experience",11),
    _p("Tanzim Hasan Sakib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Nasum Ahmed","Bowler (Spin)",74,20,76,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Orthodox","Powerplay economy,Left-arm","Pace wickets",10),
    _p("Rishad Hossain","Bowler (Spin)",76,22,78,22,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Googly","Experience",10),
    _p("Tanzid Hasan Tamim","Batsman",74,76,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Experience",1),
    _p("Jaker Ali","Wicketkeeper",72,74,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Keeping","Experience",7),
    _p("Parvez Hossain Emon","Batsman",70,72,5,26,"Right","None","Middle-order Rotator","Part-time","None","Domestic form","Experience",4),
    _p("Hasan Mahmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",11),
]

BANGLADESH_ODI = [
    _p("Najmul Hossain Shanto","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Litton Das","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Explosive batting,Glove work","Consistency",2),
    _p("Shakib Al Hasan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Mushfiqur Rahim","Wicketkeeper",84,86,5,38,"Right","None","Anchor","Part-time","None","Prolific BAN batter,Grit","Age management",4),
    _p("Mehidy Hasan Miraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Towhid Hridoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Middle-order depth,Youth","Experience",5),
    _p("Mahmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience,Finisher","Age management",5),
    _p("Afif Hossain","All-Rounder",76,74,68,27,"Left","Left","Lower-order Hitter","Death","Left-arm Orthodox","Finisher,Left-arm spin","Express pace",6),
    _p("Mustafizur Rahman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Cutter,Variations","Economy",10),
    _p("Taskin Ahmed","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Shoriful Islam","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death","Experience",11),
    _p("Tanzim Hasan Sakib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Hasan Mahmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",11),
    _p("Rishad Hossain","Bowler (Spin)",76,22,78,22,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Googly","Experience",10),
    _p("Nasum Ahmed","Bowler (Spin)",74,20,76,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Orthodox","Powerplay economy,Left-arm","Pace wickets",10),
    _p("Tanzid Hasan Tamim","Batsman",74,76,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Experience",1),
    _p("Soumya Sarkar","Batsman",74,76,8,32,"Left","Left","Aggressive Opener","Part-time","Left-arm Medium","Left-hand power,Utility","Consistency",2),
    _p("Jaker Ali","Wicketkeeper",72,74,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Keeping","Experience",7),
]

BANGLADESH_TEST = [
    _p("Najmul Hossain Shanto","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Mushfiqur Rahim","Wicketkeeper",84,86,5,38,"Right","None","Anchor","Part-time","None","Prolific BAN batter,Grit","Age management",5),
    _p("Shakib Al Hasan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Mehidy Hasan Miraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Mominul Haque","Batsman",78,80,5,33,"Left","Left","Anchor","Part-time","Left-arm Orthodox","Technique,Patience","Pace outside off",3),
    _p("Litton Das","Wicketkeeper",80,82,5,31,"Right","None","Anchor","Part-time","None","Grit,Glove work","Short-pitch pace",2),
    _p("Mahmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience","Age management",6),
    _p("Taskin Ahmed","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Hasan Mahmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",10),
    _p("Shoriful Islam","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm angle","Experience",11),
    _p("Tanzim Hasan Sakib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Nayeem Hasan","Bowler (Spin)",72,20,74,26,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Home spin","Away surfaces",10),
    _p("Taijul Islam","Bowler (Spin)",80,20,82,35,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away conditions",10),
    _p("Shadman Islam","Batsman",72,74,5,30,"Left","None","Anchor","Part-time","None","Technique,Patience","Scoring rate",1),
    _p("Towhid Hridoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Middle-order","Experience",4),
    _p("Zakir Hasan","Batsman",70,72,5,28,"Left","None","Anchor","Part-time","None","Left-hand technique","Consistency",2),
    _p("Khaled Ahmed","Bowler (Fast)",68,18,70,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam","Experience",11),
    _p("Mustafizur Rahman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Cutter,Variations","Red-ball control",10),
]

# ---------------------------------------------------------------------------
# AFGHANISTAN
# ---------------------------------------------------------------------------

AFGHANISTAN_T20I = [
    _p("Rashid Khan","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Mohammad Nabi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",6),
    _p("Ibrahim Zadran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rahmanullah Gurbaz","Wicketkeeper",84,86,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Middle-overs consistency",1),
    _p("Mujeeb Ur Rahman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Offbreak","Mystery spin,Powerplay economy","Batting",10),
    _p("Fazalhaq Farooqi","Bowler (Fast)",84,20,86,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",10),
    _p("Azmatullah Omarzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Fast-medium","All-format utility,Youth","Experience",7),
    _p("Gulbadin Naib","All-Rounder",74,68,72,33,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Experience,Utility","International class",7),
    _p("Naveen-ul-Haq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Yorkers","Economy",10),
    _p("Noor Ahmad","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Karim Janat","All-Rounder",72,68,70,28,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Utility","Experience",8),
    _p("Riaz Hassan","Batsman",70,72,5,24,"Right","None","Middle-order Rotator","Part-time","None","Youth","Experience",4),
    _p("Sediqullah Atal","Batsman",70,72,5,22,"Right","None","Aggressive Opener","Part-time","None","Youth,Attack","Experience",1),
    _p("Bahir Shah","Batsman",68,70,5,22,"Right","None","Middle-order Rotator","Part-time","None","Youth","Experience",4),
    _p("Mohammad Saleem Safi","Bowler (Fast)",68,18,70,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Sayed Shirzad","Bowler (Fast)",70,18,72,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace","Experience",11),
    _p("Darwish Rasooli","Batsman",68,70,5,23,"Left","None","Anchor","Part-time","None","Youth,Left-hand","Experience",3),
    _p("AM Ghazanfar","Bowler (Spin)",72,18,74,19,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Youngest squad member","Experience",11),
]

AFGHANISTAN_ODI = [
    _p("Hashmatullah Shahidi","Batsman",78,80,5,32,"Left","None","Anchor","Part-time","None","Technique,Grit","Express pace",3),
    _p("Rashid Khan","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Ibrahim Zadran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rahmanullah Gurbaz","Wicketkeeper",84,86,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Consistency",1),
    _p("Mujeeb Ur Rahman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Offbreak","Mystery spin,Powerplay economy","Batting",10),
    _p("Fazalhaq Farooqi","Bowler (Fast)",84,20,86,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",10),
    _p("Mohammad Nabi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",6),
    _p("Azmatullah Omarzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Fast-medium","All-format utility,Youth","Experience",7),
    _p("Najibullah Zadran","Batsman",78,80,5,32,"Left","None","Lower-order Hitter","Part-time","None","Six hitting,Finisher","Consistency",6),
    _p("Naveen-ul-Haq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Yorkers","Economy",10),
    _p("Noor Ahmad","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Gulbadin Naib","All-Rounder",74,68,72,33,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Experience,Utility","International class",5),
    _p("Rahmat Shah","Batsman",76,78,5,32,"Right","None","Anchor","Part-time","None","Technique,Middle-order","Power",4),
    _p("Ikram Ali Khil","Wicketkeeper",72,73,5,25,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper,Youth","Experience",7),
    _p("Karim Janat","All-Rounder",72,68,70,28,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Utility","Experience",8),
    _p("Wahidullah Shafaq","Bowler (Fast)",68,18,70,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Left-arm pace","Experience",11),
    _p("Sediqullah Atal","Batsman",70,72,5,22,"Right","None","Aggressive Opener","Part-time","None","Youth","Experience",1),
    _p("Mohammad Saleem Safi","Bowler (Fast)",68,18,70,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth","Experience",11),
]

AFGHANISTAN_TEST = [
    _p("Hashmatullah Shahidi","Batsman",80,82,5,32,"Left","None","Anchor","Part-time","None","Technique,Grit,Captain","Express pace",3),
    _p("Rashid Khan","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Ibrahim Zadran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rahmanullah Gurbaz","Wicketkeeper",84,86,5,23,"Right","None","Anchor","Part-time","None","Youth,Glove work","Long Test innings",4),
    _p("Rahmat Shah","Batsman",76,78,5,32,"Right","None","Anchor","Part-time","None","Technique,Middle-order","Pace outside off",4),
    _p("Najibullah Zadran","Batsman",78,80,5,32,"Left","None","Lower-order Hitter","Part-time","None","Veteran experience,Left-hand","Express pace",6),
    _p("Azmatullah Omarzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","All-format utility","Experience",7),
    _p("Mohammad Nabi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",5),
    _p("Mujeeb Ur Rahman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery spin","Batting",10),
    _p("Noor Ahmad","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Amir Hamza","Bowler (Spin)",76,20,78,30,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Experience,Home spin","Away surfaces",10),
    _p("Zahir Khan","Bowler (Spin)",76,20,78,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Variations","Consistency",10),
    _p("Yamin Ahmadzai","Bowler (Fast)",72,18,74,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace","Experience",11),
    _p("Naveen-ul-Haq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Death bowling","Economy in Tests",10),
    _p("Wahidullah Shafaq","Bowler (Fast)",68,18,70,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Left-arm pace","Experience",11),
    _p("Ikram Ali Khil","Wicketkeeper",72,73,5,25,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper,Youth","Experience",7),
    _p("Darwish Rasooli","Batsman",68,70,5,23,"Left","None","Anchor","Part-time","None","Youth,Left-hand","Experience",3),
    _p("AM Ghazanfar","Bowler (Spin)",72,18,74,19,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Youngest squad member","Experience",11),
]

# ---------------------------------------------------------------------------
# Public API: get squad by nation and format
# ---------------------------------------------------------------------------

_ROSTERS = {
    "India":        {"t20": INDIA_T20I,       "odi": INDIA_ODI,       "test": INDIA_TEST},
    "Australia":    {"t20": AUSTRALIA_T20I,   "odi": AUSTRALIA_ODI,   "test": AUSTRALIA_TEST},
    "England":      {"t20": ENGLAND_T20I,     "odi": ENGLAND_ODI,     "test": ENGLAND_TEST},
    "New Zealand":  {"t20": NEW_ZEALAND_T20I, "odi": NEW_ZEALAND_ODI, "test": NEW_ZEALAND_TEST},
    "South Africa": {"t20": SOUTH_AFRICA_T20I,"odi": SOUTH_AFRICA_ODI,"test": SOUTH_AFRICA_TEST},
    "Pakistan":     {"t20": PAKISTAN_T20I,    "odi": PAKISTAN_ODI,    "test": PAKISTAN_TEST},
    "Sri Lanka":    {"t20": SRI_LANKA_T20I,   "odi": SRI_LANKA_ODI,   "test": SRI_LANKA_TEST},
    "West Indies":  {"t20": WEST_INDIES_T20I, "odi": WEST_INDIES_ODI, "test": WEST_INDIES_TEST},
    "Bangladesh":   {"t20": BANGLADESH_T20I,  "odi": BANGLADESH_ODI,  "test": BANGLADESH_TEST},
    "Afghanistan":  {"t20": AFGHANISTAN_T20I, "odi": AFGHANISTAN_ODI, "test": AFGHANISTAN_TEST},
}


def get_international_rosters(match_format: str) -> tuple[dict, list]:
    """Return (rosters_dict, leftover_pool) for the given match format.

    rosters_dict: {nation_name: [Player, ...]}
    leftover_pool: combined pool of all players (used as the draft pool when
        draft_pool_type == 'international_current')
    match_format: 't20' | 'odi' | 'test'
    """
    fmt = match_format.lower()
    rosters = {}
    all_players = []
    seen_names: set[str] = set()
    for nation, fmts in _ROSTERS.items():
        squad = fmts.get(fmt, [])
        rosters[nation] = squad
        for p in squad:
            if p.name not in seen_names:
                all_players.append(p)
                seen_names.add(p.name)
    return rosters, all_players
