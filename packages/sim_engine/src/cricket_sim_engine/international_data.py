# international_data.py
"""Current (2026) international cricket rosters for 10 nations across 3 formats.

Player names are IP-safe, not real: the initial-preserving rename convention
from tools/ip_safe_rename.py has been applied, so abbreviated scorecard forms
stay recognisable while the full names are legally distinct. Nation names are
real and stay that way - country names are not protected marks.

Do not paste real names in when adding or refreshing a squad. Add the real ->
fictional pair to PLAYER_MAP and re-run `python tools/ip_safe_rename.py --apply`,
which keeps every pool consistent (a player appearing in both a national squad
and an all-time pool must render identically in both).

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
    _p("Shriyas Iyir","Batsman",87,89,10,31,"Right","None","Anchor","Part-time","None","Technique against pace,Consistency","Short-pitch bowling",5),
    _p("Tylak Verma","Batsman",85,87,8,23,"Left","None","Anchor","Part-time","None","Timing,Composure","Wide outside off",4),
    _p("Abhyshek Sherma","Batsman",83,87,12,25,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Power hitting,Strike rate","Spin off stump",1),
    _p("Senju Semson","Wicketkeeper",84,86,5,31,"Right","None","Anchor","Part-time","None","Glove work,Attacking batting","Consistency under pressure",2),
    _p("Ishen Kyshan","Wicketkeeper",80,82,5,27,"Left","None","Aggressive Opener","Part-time","None","Power hitting,Running between wickets","Spin in middle overs",1),
    _p("Shyvam Dobe","All-Rounder",80,82,72,32,"Left","Right","Lower-order Hitter","Death","Right-arm Medium","Power hitting,Six hitting","Discipline with the ball",6),
    _p("Veibhav Suoryavanshi","Batsman",78,82,5,16,"Left","Left","Aggressive Opener","Part-time","None","Natural timing,Fearless batting","Inexperience",1),
    _p("Axer Petel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Line and length","Short-pitched deliveries",7),
    _p("Weshington Sondar","All-Rounder",82,75,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Adaptability","Pace on turning tracks",8),
    _p("Revi Byshnoi","Bowler (Spin)",83,30,86,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,Economy","Powerplay batting",10),
    _p("Verun Chekravarthy","Bowler (Spin)",84,25,87,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Red-ball form",10),
    _p("Arshdiep Syngh","Bowler (Fast)",87,25,89,27,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Swing,Death bowling","Batting under pressure",11),
    _p("Hershit Rena","Bowler (Fast)",78,20,80,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Bounce","Consistency",10),
    _p("Presidh Kryshna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Death yorkers","Short-pitch to batters",10),
    _p("Rynku Syngh","Batsman",82,84,5,28,"Left","None","Lower-order Hitter","Part-time","None","Finishing,Six hitting","Spin in early overs",7),
    _p("Ryyan Perag","All-Rounder",79,80,72,24,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Fielding,Six hitting","Consistency against top pace",6),
    _p("Soryansh Shidge","All-Rounder",74,74,68,23,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium","Adaptability,Fielding","Experience",7),
    _p("Prynce Yedav","Bowler (Fast)",72,18,74,23,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Pace,Swing","Batting",11),
]

INDIA_ODI = [
    _p("Shobman Gyll","Batsman",90,92,10,26,"Right","None","Anchor","Part-time","None","Technique,Elegance","Hostile pace in early overs",1),
    _p("Ruhit Sherma","Batsman",88,91,5,39,"Right","None","Aggressive Opener","Part-time","None","Power hitting,ODI record","Age management",1),
    _p("Vyrat Kuhli","Batsman",93,95,5,37,"Right","None","Anchor","Part-time","None","Chase mastery,Consistency","Short pitch from left-armers",3),
    _p("Shriyas Iyir","Batsman",87,89,10,31,"Right","None","Anchor","Part-time","None","Leg-side play,Finisher","Short-pitch bowling",5),
    _p("KL Rehul","Wicketkeeper",86,88,5,34,"Right","None","Anchor","Part-time","None","Technique,Versatility","Scoring rate in middle overs",2),
    _p("Ryshabh Pent","Wicketkeeper",88,90,5,28,"Left","None","Aggressive Opener","Part-time","None","Match-winning innings,Glove work","Wide outside off",6),
    _p("Yeshasvi Jeiswal","Batsman",86,88,10,24,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Explosive starts,Natural timing","Inexperience in chases",1),
    _p("Weshington Sondar","All-Rounder",82,74,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Batting utility","Pace in powerplay",8),
    _p("Revindra Jedeja","All-Rounder",89,82,86,37,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Fielding,All-round impact","Spin in death overs",8),
    _p("Axer Petel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Batting depth","Short-pitched deliveries",8),
    _p("Nytish Komar Riddy","All-Rounder",78,76,72,23,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Hard hitting,Pace variation","Experience",7),
    _p("Koldeep Yedav","Bowler (Spin)",88,28,90,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Googly,Variations","Wide outside off",10),
    _p("Jesprit Bomrah","Bowler (Fast)",96,25,97,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Yorkers,Accuracy","Batting",11),
    _p("Muhammed Syraj","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball swing,Accuracy","Death overs economy",10),
    _p("Arshdiep Syngh","Bowler (Fast)",87,25,89,27,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Swing,Death bowling","Batting",11),
    _p("Hershit Rena","Bowler (Fast)",78,20,80,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Bounce","Consistency",10),
    _p("Presidh Kryshna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Death yorkers","Short-pitch to batters",10),
    _p("Ishen Kyshan","Wicketkeeper",80,82,5,27,"Left","None","Aggressive Opener","Part-time","None","Power hitting,Running between wickets","Spin in middle overs",1),
]

INDIA_TEST = [
    _p("Shobman Gyll","Batsman",90,92,10,26,"Right","None","Anchor","Part-time","None","Technique,Elegance","Hostile pace in early overs",1),
    _p("Ryshabh Pent","Wicketkeeper",88,90,5,28,"Left","None","Aggressive Opener","Part-time","None","Match-winning innings,Glove work","Wide outside off",6),
    _p("Yeshasvi Jeiswal","Batsman",86,88,10,24,"Left","Left","Aggressive Opener","Part-time","Left-arm Orthodox","Explosive starts,Natural timing","Inconsistency vs pace",1),
    _p("KL Rehul","Batsman",86,88,5,34,"Right","None","Anchor","Part-time","None","Technique,Versatility","Scoring rate in middle overs",2),
    _p("Sei Sodharsan","Batsman",81,83,5,24,"Left","None","Anchor","Part-time","None","Solid technique,Temperament","Hostile fast bowling",3),
    _p("Divdutt Pedikkal","Batsman",78,80,5,25,"Left","None","Anchor","Part-time","None","Left-hand elegance,Timing","Short pitch",3),
    _p("Dhrov Jorel","Wicketkeeper",77,78,5,25,"Right","None","Middle-order Rotator","Part-time","None","Grit,Glove work","Lack of big international knocks",7),
    _p("Kerun Neir","Batsman",78,80,5,34,"Right","None","Anchor","Part-time","None","Long innings,Temperament","Consistency at highest level",6),
    _p("Revindra Jedeja","All-Rounder",89,82,86,37,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Fielding,All-round impact","Spin in death overs",8),
    _p("Weshington Sondar","All-Rounder",82,74,80,26,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,Batting utility","Pace in powerplay",8),
    _p("Axer Petel","All-Rounder",86,78,84,32,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Batting depth","Short-pitched deliveries",8),
    _p("Nytish Komar Riddy","All-Rounder",78,76,72,23,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Hard hitting,Pace variation","Experience",7),
    _p("Jesprit Bomrah","Bowler (Fast)",96,25,97,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Yorkers,Accuracy","Batting",11),
    _p("Muhammed Syraj","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball swing,Accuracy","Death overs economy",10),
    _p("Akesh Diep","Bowler (Fast)",79,20,81,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Movement","Batting",10),
    _p("Koldeep Yedav","Bowler (Spin)",88,28,90,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Googly,Variations","Wide outside off",10),
    _p("Muhammed Shemi","Bowler (Fast)",88,22,90,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Age and fitness",10),
    _p("Presidh Kryshna","Bowler (Fast)",81,20,83,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Height advantage,Bounce","Short-pitch to batters",10),
]

# ---------------------------------------------------------------------------
# AUSTRALIA
# ---------------------------------------------------------------------------

AUSTRALIA_T20I = [
    _p("Mytchell Mersh","All-Rounder",84,82,76,34,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Pace variation","Consistency in bowling",4),
    _p("Trevis Hiad","Batsman",90,92,10,32,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Timing","Spin on turning tracks",2),
    _p("Jush Inglys","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Clean hitting,Glove work","Long innings",1),
    _p("Stiven Smyth","Batsman",88,90,10,36,"Right","Right","Anchor","Part-time","Leg-spin","Unconventional technique,Consistency","Short-pitch",4),
    _p("Tym Devid","Batsman",84,86,5,30,"Right","None","Lower-order Hitter","Part-time","None","Six hitting,Death finisher","Spin in powerplay",6),
    _p("Glinn Mexwell","All-Rounder",84,84,76,37,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","360-degree batting,Fielding","Consistency",5),
    _p("Mercus Stuinis","All-Rounder",82,82,72,36,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Death yorkers","Spin bowling",6),
    _p("Cemeron Grien","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",7),
    _p("Cuoper Cunnolly","All-Rounder",75,73,70,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Versatility,Youth","Experience",8),
    _p("Aeron Herdie","All-Rounder",74,72,70,25,"Right","Right","Middle-order Rotator","Death","Right-arm Medium-fast","Utility,Adaptability","Experience",7),
    _p("Pet Commins","Bowler (Fast)",90,30,92,33,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Accuracy,Reverse swing","Batting",11),
    _p("Jush Hezlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Death overs",10),
    _p("Nethan Ellys","Bowler (Fast)",78,22,80,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling,Yorkers","Batting",10),
    _p("Xevier Bertlett","Bowler (Fast)",76,22,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Pace,Swing","Experience",10),
    _p("Bin Dwershuis","Bowler (Fast)",76,22,78,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death bowling","Batting",11),
    _p("Adem Zempa","Bowler (Spin)",86,25,88,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Variations,Economy","Short boundaries",10),
    _p("Metthew Kohnemann","Bowler (Spin)",74,22,76,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Left-arm angle,Economy","Inexperience",10),
    _p("Metthew Rinshaw","Batsman",76,77,5,30,"Left","None","Anchor","Part-time","None","Versatility,Left-hand","Pace in powerplay",3),
]

AUSTRALIA_ODI = [
    _p("Mytchell Mersh","All-Rounder",84,82,76,34,"Right","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Power hitting,Pace variation","Consistency in bowling",4),
    _p("Trevis Hiad","Batsman",90,92,10,32,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Timing","Spin on turning tracks",1),
    _p("Alix Cerey","Wicketkeeper",82,83,5,34,"Left","None","Anchor","Part-time","None","Reliability,Glove work","Power hitting",7),
    _p("Jush Inglys","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Clean hitting,Glove work","Long innings",5),
    _p("Mernus Lebuschagne","Batsman",85,87,10,31,"Right","Right","Anchor","Part-time","Leg-spin","Concentration,Technique","Scoring rate in ODIs",4),
    _p("Cemeron Grien","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",6),
    _p("Cuoper Cunnolly","All-Rounder",75,73,70,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Versatility,Youth","Experience",8),
    _p("Mett Shurt","All-Rounder",78,79,72,30,"Right","Right","Aggressive Opener","Middle Overs","Right-arm Offbreak","Power hitting,Utility","Spin in death",2),
    _p("Aeron Herdie","All-Rounder",74,72,70,25,"Right","Right","Middle-order Rotator","Death","Right-arm Medium-fast","Utility,Adaptability","Experience",7),
    _p("Metthew Rinshaw","Batsman",76,77,5,30,"Left","None","Anchor","Part-time","None","Versatility,Left-hand","Pace in powerplay",3),
    _p("Mytchell Sterc","Bowler (Fast)",88,28,90,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","New-ball swing,Left-arm angle","Death overs economy",11),
    _p("Jush Hezlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Death overs",10),
    _p("Nethan Ellys","Bowler (Fast)",78,22,80,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling,Yorkers","Batting",10),
    _p("Ryley Miredith","Bowler (Fast)",77,20,79,29,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Accuracy",10),
    _p("Adem Zempa","Bowler (Spin)",86,25,88,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Variations,Economy","Short boundaries",10),
    _p("Metthew Kohnemann","Bowler (Spin)",74,22,76,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Left-arm angle,Economy","Inexperience",10),
    _p("Tenveer Sengha","Bowler (Spin)",72,20,74,24,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Variations","Experience",11),
    _p("Olyver Piake","Batsman",71,73,5,24,"Right","None","Middle-order Rotator","Part-time","None","Fresh talent,Potential","Experience",5),
]

AUSTRALIA_TEST = [
    _p("Pet Commins","Bowler (Fast)",90,30,92,33,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Accuracy,Reverse swing","Batting",8),
    _p("Stiven Smyth","Batsman",94,96,10,36,"Right","Right","Anchor","Part-time","Leg-spin","Unconventional technique,Consistency","Short-pitch",4),
    _p("Usmen Khewaja","Batsman",88,90,5,39,"Left","None","Anchor","Part-time","None","Technique,Concentration","Age management",1),
    _p("Mernus Lebuschagne","Batsman",88,90,10,31,"Right","Right","Anchor","Part-time","Leg-spin","Concentration,Resilience","Pace on hard length",3),
    _p("Trevis Hiad","Batsman",88,90,10,32,"Left","None","Aggressive Opener","Part-time","None","Attacking intent,Footwork","Bounce from outside off",5),
    _p("Alix Cerey","Wicketkeeper",82,83,5,34,"Left","None","Anchor","Part-time","None","Reliability,Glove work","Power hitting",7),
    _p("Jush Inglys","Wicketkeeper",78,79,5,31,"Right","None","Anchor","Part-time","None","Clean hitting,Backup option","Long Test innings",6),
    _p("Cemeron Grien","All-Rounder",80,78,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Height,Seam movement","Batting against spin",6),
    _p("Biau Wibster","All-Rounder",78,76,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Consistency,Utility","Bowling penetration",7),
    _p("Mytchell Sterc","Bowler (Fast)",88,28,90,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","New-ball swing,Left-arm angle","Death overs economy",11),
    _p("Jush Hezlewood","Bowler (Fast)",87,25,89,35,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Line and length,Economy","Away swing",10),
    _p("Scutt Buland","Bowler (Fast)",82,22,84,37,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Accuracy,WACA/MCG seam","Overseas wickets",10),
    _p("Nethan Lyun","Bowler (Spin)",88,25,90,38,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Home spin,Partnership breaker","Away tours",10),
    _p("Jeke Wiatherald","Batsman",74,75,5,31,"Left","None","Anchor","Part-time","None","Left-hand technique,Patience","Experience",2),
    _p("Mercus Herris","Batsman",72,73,5,33,"Left","None","Anchor","Part-time","None","Experience,Left-hand","Consistency",1),
    _p("Tudd Morphy","Bowler (Spin)",74,20,76,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Away spin","Experience",11),
    _p("Jhyi Rychardson","Bowler (Fast)",76,22,78,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Pace","Injury history",10),
    _p("Brindan Duggett","Bowler (Fast)",70,20,72,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement,Accuracy","Experience",11),
]

# ---------------------------------------------------------------------------
# ENGLAND
# ---------------------------------------------------------------------------

ENGLAND_T20I = [
    _p("Herry Bruok","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique against pace","Spin on turning tracks",3),
    _p("Jus Bottler","Wicketkeeper",88,90,5,35,"Right","None","Lower-order Hitter","Part-time","None","Explosive hitting,Glove work","Pace in early overs",4),
    _p("Phyl Selt","Wicketkeeper",82,84,5,29,"Right","None","Aggressive Opener","Part-time","None","Powerplay aggression,Glove work","Middle overs consistency",1),
    _p("Bin Dockett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Lyam Lyvingstone","All-Rounder",83,83,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Six hitting,360 degree","Consistency with ball",5),
    _p("Jecob Bithell","All-Rounder",82,80,74,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",6),
    _p("Wyll Jecks","All-Rounder",80,80,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Consistency",6),
    _p("Sem Corran","All-Rounder",83,76,80,27,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Left-arm angle,Lower-order hitting","Economy in powerplay",8),
    _p("Jufra Archir","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Injury history",10),
    _p("Adyl Reshid","Bowler (Spin)",86,30,88,38,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,White-ball economy","Batting",10),
    _p("Rihan Ahmid","Bowler (Spin)",78,28,80,21,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Variations","Experience",10),
    _p("Seqib Mehmood","Bowler (Fast)",78,22,80,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Pace","Consistency",11),
    _p("Loke Wuod","Bowler (Fast)",74,20,76,31,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Death bowling,Left-arm angle","Away economy",11),
    _p("Jemie Ovirton","Bowler (Fast)",76,22,78,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Height,Bounce","Away swing",10),
    _p("Jush Tungue","Bowler (Fast)",77,22,79,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Consistency",10),
    _p("Lyam Dewson","All-Rounder",74,70,72,35,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Lower-order","Bowling in powerplay",9),
    _p("Jemie Smyth","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",4),
    _p("Tum Benton","Wicketkeeper",76,78,5,27,"Right","None","Aggressive Opener","Part-time","None","Power hitting,Keeper backup","Middle-over consistency",2),
]

ENGLAND_ODI = [
    _p("Herry Bruok","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique","Spin on turning tracks",3),
    _p("Jus Bottler","Wicketkeeper",88,90,5,35,"Right","None","Lower-order Hitter","Part-time","None","Explosive hitting,Glove work","Pace in early overs",4),
    _p("Bin Dockett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Jue Ruot","Batsman",93,95,10,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Consistency,Technique","Short-pitch pace",4),
    _p("Jemie Smyth","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",5),
    _p("Zek Crewley","Batsman",82,84,5,28,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Timing","Short-pitch dismissals",1),
    _p("Jecob Bithell","All-Rounder",82,80,74,22,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",6),
    _p("Wyll Jecks","All-Rounder",80,80,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Consistency",6),
    _p("Sem Corran","All-Rounder",83,76,80,27,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Left-arm angle,Lower-order hitting","Economy in powerplay",8),
    _p("Lyam Dewson","All-Rounder",74,70,72,35,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Lower-order","Bowling in powerplay",9),
    _p("Gos Atkynson","Bowler (Fast)",84,25,86,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","New-ball swing,Seam","Batting",10),
    _p("Brydun Cerse","Bowler (Fast)",80,22,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Economy",10),
    _p("Jufra Archir","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Injury history",11),
    _p("Metthew Putts","Bowler (Fast)",78,22,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Batting",10),
    _p("Jemie Ovirton","Bowler (Fast)",76,22,78,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Height,Bounce","Away swing",10),
    _p("Adyl Reshid","Bowler (Spin)",86,30,88,38,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Googly,White-ball economy","Batting",11),
    _p("Seqib Mehmood","Bowler (Fast)",78,22,80,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Pace","Consistency",11),
    _p("Tum Benton","Wicketkeeper",76,78,5,27,"Right","None","Aggressive Opener","Part-time","None","Power hitting,Keeper backup","Middle-over consistency",2),
]

ENGLAND_TEST = [
    _p("Bin Stukes","All-Rounder",93,87,88,34,"Left","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Match-winning ability,Leadership","Fitness management",6),
    _p("Herry Bruok","Batsman",90,92,5,27,"Right","None","Aggressive Opener","Part-time","None","Aggression,Technique","Spin on turning tracks",4),
    _p("Jue Ruot","Batsman",96,98,10,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Consistency,Adaptability","Short-pitch pace",4),
    _p("Zek Crewley","Batsman",83,85,5,28,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Timing","Short-pitch dismissals",1),
    _p("Bin Dockett","Batsman",85,87,5,31,"Left","None","Aggressive Opener","Part-time","None","Left-hand aggression,Sweep shot","Short-pitch pace",2),
    _p("Ollye Pupe","Batsman",84,86,5,28,"Right","None","Anchor","Part-time","None","Technique,Middle-order stability","Hostile pace",5),
    _p("Jecob Bithell","All-Rounder",82,80,74,22,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Youth,All-round skill","Experience",3),
    _p("Jemie Smyth","Wicketkeeper",80,82,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Dynamic keeping","Experience",7),
    _p("Jemes Riw","Wicketkeeper",70,71,5,22,"Left","None","Middle-order Rotator","Part-time","None","Youth,Left-hand","Experience",8),
    _p("Wyll Jecks","All-Rounder",80,78,74,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Off-spin","Batting consistency",8),
    _p("Gos Atkynson","Bowler (Fast)",84,25,86,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","New-ball swing,Seam","Batting",10),
    _p("Brydun Cerse","Bowler (Fast)",80,22,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Economy",9),
    _p("Jufra Archir","Bowler (Fast)",88,25,90,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Injury history",10),
    _p("Merk Wuod","Bowler (Fast)",84,22,86,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Wickets","Injury history",11),
    _p("Jush Tungue","Bowler (Fast)",77,22,79,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Hostility","Consistency",10),
    _p("Metthew Putts","Bowler (Fast)",78,22,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam movement","Batting",10),
    _p("Shuaib Beshir","Bowler (Spin)",78,22,80,22,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Away spin","Experience",11),
    _p("Ollye Rubinson","Bowler (Fast)",80,22,82,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Accuracy,Swing","Pace",10),
]

# ---------------------------------------------------------------------------
# NEW ZEALAND
# ---------------------------------------------------------------------------

NEW_ZEALAND_T20I = [
    _p("Mytchell Sentner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Fynn Allin","Batsman",82,84,5,27,"Right","None","Aggressive Opener","Part-time","None","Powerplay strike rate,360-degree","Middle-overs consistency",1),
    _p("Divon Cunway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch from right-armers",2),
    _p("Tym Siifert","Wicketkeeper",78,80,5,31,"Right","None","Lower-order Hitter","Part-time","None","Keeper finisher,Reverse hitting","Middle-overs accumulation",7),
    _p("Merk Chepman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Deryl Mytchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Seam utility","Bowling consistency",5),
    _p("Glinn Phyllips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Spectacular hitting,Fielding","Consistency with ball",6),
    _p("Rechin Revindra","All-Rounder",84,84,74,27,"Left","Left","Aggressive Opener","Middle Overs","Left-arm Orthodox","Fluent strokeplay,Left-arm spin","Pacey powerplay bowling",3),
    _p("Mychael Brecewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",9),
    _p("Ish Sudhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Batting",10),
    _p("Jecob Doffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death discipline,Swing","Express pace",10),
    _p("Luckie Firguson","Bowler (Fast)",84,22,86,35,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Economy",11),
    _p("Nethan Smyth","Bowler (Fast)",76,22,78,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Swing","Experience",11),
    _p("Bin Siars","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Pace,Death bowling","Batting",11),
    _p("Adem Mylne","Bowler (Fast)",78,20,80,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness history",11),
    _p("Kyli Jemieson","Bowler (Fast)",79,24,81,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",10),
    _p("Mett Hinry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Tum Letham","Wicketkeeper",80,82,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",3),
]

NEW_ZEALAND_ODI = [
    _p("Mytchell Sentner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Tum Letham","Wicketkeeper",82,84,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",1),
    _p("Divon Cunway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch",2),
    _p("Kene Wylliamson","Batsman",92,94,5,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Masterful technique,Leadership","Aggressive periods",3),
    _p("Deryl Mytchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Seam utility","Bowling consistency",5),
    _p("Glinn Phyllips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Spectacular hitting,Fielding","Consistency with ball",6),
    _p("Rechin Revindra","All-Rounder",84,84,74,27,"Left","Left","Aggressive Opener","Middle Overs","Left-arm Orthodox","Fluent strokeplay,Left-arm spin","Pacey powerplay bowling",3),
    _p("Merk Chepman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Mychael Brecewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",9),
    _p("Ish Sudhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Batting",10),
    _p("Jecob Doffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death discipline,Swing","Express pace",10),
    _p("Luckie Firguson","Bowler (Fast)",84,22,86,35,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Economy",11),
    _p("Kyli Jemieson","Bowler (Fast)",79,24,81,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",10),
    _p("Mett Hinry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Trint Buult","Bowler (Fast)",85,24,87,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Swing,New-ball wickets","Death economy",11),
    _p("Tym Suuthee","Bowler (Fast)",82,22,84,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Experience","Pace",10),
    _p("Nethan Smyth","Bowler (Fast)",76,22,78,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Swing","Experience",11),
    _p("Fynn Allin","Batsman",82,84,5,27,"Right","None","Aggressive Opener","Part-time","None","Powerplay strike rate,Fielding","Middle-overs consistency",1),
]

NEW_ZEALAND_TEST = [
    _p("Tum Letham","Wicketkeeper",84,86,5,34,"Left","None","Anchor","Part-time","None","Grit,Leadership","Power hitting",1),
    _p("Kene Wylliamson","Batsman",93,95,5,35,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Masterful technique,Leadership","Aggressive periods",3),
    _p("Divon Cunway","Wicketkeeper",86,88,5,35,"Left","None","Anchor","Part-time","None","Clean timing,Glove work","Short pitch",2),
    _p("Rechin Revindra","All-Rounder",84,84,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Fluent strokeplay,All-round skill","Pacey bowling",4),
    _p("Deryl Mytchell","All-Rounder",84,84,70,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Clutch performances,Grit","Bowling in red-ball",5),
    _p("Glinn Phyllips","All-Rounder",83,83,72,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Attacking intent,Fielding","Consistency",6),
    _p("Mychael Brecewell","All-Rounder",78,74,76,35,"Left","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Accuracy,Lower-order hitting","Express pace",8),
    _p("Mett Hinry","Bowler (Fast)",80,22,82,34,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Tym Suuthee","Bowler (Fast)",82,22,84,36,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Experience","Pace",10),
    _p("Kyli Jemieson","Bowler (Fast)",80,24,82,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Height,Bounce","Away economy",9),
    _p("Trint Buult","Bowler (Fast)",85,24,87,36,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Swing,New-ball wickets","Death economy",11),
    _p("Wylliam O'Ruurke","Bowler (Fast)",78,22,80,23,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Youth,Pace","Experience",11),
    _p("Ish Sudhi","Bowler (Spin)",81,25,83,34,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","White-ball variations,Googly","Test red-ball",10),
    _p("Mytchell Sentner","All-Rounder",84,76,82,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Economy,Left-arm spin","Pace",7),
    _p("Merk Chepman","Batsman",78,80,10,32,"Left","Left","Middle-order Rotator","Part-time","Left-arm Orthodox","Technique,Consistency","Scoring rate",4),
    _p("Wyll Yuung","Batsman",75,76,5,34,"Right","None","Anchor","Part-time","None","Patience,Grit","Scoring rate",2),
    _p("Hinry Nycholls","Batsman",76,77,5,34,"Left","None","Anchor","Part-time","None","Technique,Consistency","Power",5),
    _p("Jecob Doffy","Bowler (Fast)",79,22,81,31,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Discipline","Express pace",10),
]

# ---------------------------------------------------------------------------
# SOUTH AFRICA
# ---------------------------------------------------------------------------

SOUTH_AFRICA_T20I = [
    _p("Ayden Merkram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Leadership","Short-pitch fast bowling",2),
    _p("Qointon de Kuck","Wicketkeeper",90,92,5,33,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Glove work","Pace outside off",1),
    _p("Devid Myller","Batsman",86,88,5,36,"Left","None","Lower-order Hitter","Part-time","None","Six hitting,Finisher ability","Spin early on",6),
    _p("Diwald Brivis","Batsman",82,84,8,23,"Right","Right","Aggressive Opener","Part-time","Leg-spin","Explosive power,Youth","Consistency",4),
    _p("Trystan Stobbs","Batsman",79,81,8,25,"Right","Right","Lower-order Hitter","Part-time","Right-arm Offbreak","Aggressive finishing,Youth","Experience",6),
    _p("Ryen Ryckelton","Wicketkeeper",78,80,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",2),
    _p("Merco Jensen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Death","Left-arm Fast-medium","Tall seam,Left-arm angle","Death overs economy",7),
    _p("Kegiso Rebada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in T20",10),
    _p("Anrych Nurtje","Bowler (Fast)",88,22,90,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Longi Ngydi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Curbin Busch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility,Death bowling","International class gap",8),
    _p("Kwina Mephaka","Bowler (Fast)",78,20,80,20,"Right","Left","Defensive Tailender","Death","Left-arm Fast","Yorkers,Youth","Consistency",11),
    _p("Kishav Meharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,White-ball spin","Express pace wickets",10),
    _p("Giorge Lynde","All-Rounder",76,70,74,34,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm utility,Lower-order hitting","International class",9),
    _p("Wyaan Molder","All-Rounder",78,74,74,28,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium-fast","All-round utility","Pace bowling penetration",7),
    _p("Girald Cuetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Cunnor Estirhuizen","Batsman",72,74,5,23,"Right","None","Aggressive Opener","Part-time","None","Form,Youth","International experience",3),
    _p("Jurdan Hirmann","Batsman",70,72,5,26,"Right","None","Middle-order Rotator","Part-time","None","Form-based selection","International class",5),
]

SOUTH_AFRICA_ODI = [
    _p("Timba Bevuma","Batsman",84,86,8,35,"Right","Right","Anchor","Part-time","None","Grit,Technique","Power hitting against pace",1),
    _p("Qointon de Kuck","Wicketkeeper",90,92,5,33,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Glove work","Pace outside off",1),
    _p("Ryen Ryckelton","Wicketkeeper",78,80,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",2),
    _p("Ayden Merkram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Leadership","Short-pitch fast bowling",3),
    _p("Metthew Brietzke","Batsman",80,82,5,27,"Right","Right","Anchor","Part-time","None","High floor,Debut record","Experience",4),
    _p("Tuny de Zurzi","Batsman",78,80,5,27,"Right","Right","Anchor","Part-time","None","Solid technique,Composure","Injury management",5),
    _p("Diwald Brivis","Batsman",82,84,8,23,"Right","Right","Middle-order Rotator","Part-time","Leg-spin","Explosive power,Youth","Consistency",5),
    _p("Merco Jensen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Powerplay","Left-arm Fast-medium","Tall seam,Left-arm angle","Batting consistency",8),
    _p("Curbin Busch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility","International class gap",8),
    _p("Wyaan Molder","All-Rounder",80,76,76,28,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Medium-fast","Kallis-esque utility,Test record","Pace bowling penetration",7),
    _p("Kishav Meharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,White-ball spin","Express pace wickets",10),
    _p("Prinelan Sobrayen","Bowler (Spin)",70,20,72,28,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Consistency","Variations",11),
    _p("Longi Ngydi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Nendre Borger","Bowler (Fast)",78,22,80,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness history",11),
    _p("Ottniil Beartman","Bowler (Fast)",76,20,78,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Height,Accuracy","Away record",10),
    _p("Kegiso Rebada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in ODIs",11),
    _p("Girald Cuetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Robin Hirmann","Batsman",72,74,5,28,"Left","None","Middle-order Rotator","Part-time","None","Left-hand bat,Domestic form","International class",6),
]

SOUTH_AFRICA_TEST = [
    _p("Timba Bevuma","Batsman",84,86,8,35,"Right","Right","Anchor","Part-time","None","Grit,Technique","Power hitting against pace",1),
    _p("Ryen Ryckelton","Wicketkeeper",80,82,5,29,"Left","None","Anchor","Part-time","None","Consistency,Left-hand technique","Power hitting",1),
    _p("Ayden Merkram","Batsman",86,88,12,31,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Timing,Elegance","Short-pitch pace",3),
    _p("Tuny de Zurzi","Batsman",78,80,5,27,"Right","Right","Anchor","Part-time","None","Solid technique","Experience",2),
    _p("Trystan Stobbs","Batsman",79,81,8,25,"Right","Right","Middle-order Rotator","Part-time","None","Youth,Footwork","Experience at this level",5),
    _p("Devid Bidingham","Batsman",76,78,5,31,"Right","None","Anchor","Part-time","None","Domestic record,Composure","International experience",5),
    _p("Wyaan Molder","All-Rounder",80,76,76,28,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium-fast","Kallis-esque utility,Test record","Pace bowling penetration",6),
    _p("Merco Jensen","All-Rounder",83,74,82,25,"Left","Left","Lower-order Hitter","Powerplay","Left-arm Fast-medium","Tall seam,Left-arm angle","Batting consistency",8),
    _p("Curbin Busch","All-Rounder",78,72,76,31,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","All-format utility","International class gap",8),
    _p("Kyli Virreynne","Wicketkeeper",78,79,5,30,"Right","None","Anchor","Part-time","None","Grit,Glove work","Power hitting",7),
    _p("Kishav Meharaj","Bowler (Spin)",84,28,86,36,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Wicket-taking","Express pace wickets",10),
    _p("Kegiso Rebada","Bowler (Fast)",92,28,94,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in Tests",11),
    _p("Anrych Nurtje","Bowler (Fast)",88,22,90,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Longi Ngydi","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,New-ball","Death overs",10),
    _p("Nendre Borger","Bowler (Fast)",78,22,80,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness history",11),
    _p("Girald Cuetzee","Bowler (Fast)",78,20,80,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Raw pace,Bounce","Economy and fitness",10),
    _p("Symon Hermer","Bowler (Spin)",78,25,80,36,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","County form,Spin","Away surfaces",10),
    _p("Prinelan Sobrayen","Bowler (Spin)",70,20,72,28,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy","Variations",11),
]

# ---------------------------------------------------------------------------
# PAKISTAN
# ---------------------------------------------------------------------------

PAKISTAN_T20I = [
    _p("Selman Aly Aghe","All-Rounder",80,78,72,32,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Leadership,Consistency","Express pace",5),
    _p("Bebar Azem","Batsman",90,92,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Scoring rate in death",3),
    _p("Sheheen Sheh Afrydi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",11),
    _p("Shedab Khen","All-Rounder",83,72,82,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Lower-order hitting","Economy in powerplay",8),
    _p("Seim Ayob","Batsman",82,84,8,23,"Left","Right","Aggressive Opener","Part-time","Right-arm Offbreak","Power hitting,Youth","Consistency against quality spin",1),
    _p("Fekhar Zeman","Batsman",83,85,5,36,"Left","None","Aggressive Opener","Part-time","None","Big-match temperament,Power","Age management",1),
    _p("Sehibzada Ferhan","Wicketkeeper",78,80,5,28,"Right","None","Aggressive Opener","Part-time","None","Hard hitting,Glove work","Experience",2),
    _p("Usmen Khen","Batsman",77,79,5,28,"Right","Right","Lower-order Hitter","Part-time","None","Power hitting,Finisher","Consistency",7),
    _p("Muhammad Newaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Lower-order bat","Consistency",8),
    _p("Neseem Sheh","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Abrer Ahmid","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Experience",10),
    _p("Heris Reuf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","High pace,Death specialist","Economy",10),
    _p("Khoshdil Sheh","All-Rounder",76,72,70,30,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Finisher,Left-arm spin","Consistency",7),
    _p("Iftykhar Ahmid","All-Rounder",75,72,65,35,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Power hitting,Experience","Consistency",6),
    _p("Muhammad Wesim Jr","Bowler (Fast)",74,20,76,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace","Consistency",11),
    _p("Feheem Ashref","All-Rounder",74,68,70,31,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Lower-order hitting,Seam utility","Consistency",9),
    _p("Usmen Teriq","Bowler (Fast)",70,18,72,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Emerging pace","Experience",11),
    _p("Khewaja Muhammad Nefay","Wicketkeeper",68,70,5,22,"Right","None","Lower-order Hitter","Part-time","None","Youth,PSL form","Experience",7),
]

PAKISTAN_ODI = [
    _p("Sheheen Sheh Afrydi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Batting",11),
    _p("Selman Aly Aghe","All-Rounder",80,78,72,32,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Leadership,Consistency","Express pace",5),
    _p("Bebar Azem","Batsman",90,92,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Scoring rate in death",3),
    _p("Heris Reuf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Death","Right-arm Fast","High pace,Death specialist","Economy",10),
    _p("Neseem Sheh","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Shedab Khen","All-Rounder",83,72,82,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Lower-order hitting","Economy in powerplay",8),
    _p("Sehibzada Ferhan","Wicketkeeper",78,80,5,28,"Right","None","Aggressive Opener","Part-time","None","Hard hitting,Glove work","Experience",2),
    _p("Abrer Ahmid","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations,Economy","Experience",10),
    _p("Abdol Semad","Batsman",74,76,8,24,"Left","Right","Lower-order Hitter","Part-time","Right-arm Offbreak","Power hitting,Youth","Experience",7),
    _p("Sofyan Muqim","Bowler (Spin)",76,20,78,23,"Right","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","PSL form,Chinaman","Experience",10),
    _p("Fekhar Zeman","Batsman",83,85,5,36,"Left","None","Aggressive Opener","Part-time","None","Big-match temperament,Power","Age management",1),
    _p("Seim Ayob","Batsman",82,84,8,23,"Left","Right","Aggressive Opener","Part-time","Right-arm Offbreak","Power hitting,Youth","Consistency against quality spin",1),
    _p("Arefat Mynhas","Bowler (Spin)",74,18,76,21,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Debut fifer,Youth","Experience",11),
    _p("Muhammad Newaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Lower-order bat","Consistency",8),
    _p("Imem-ul-Heq","Batsman",80,82,5,29,"Left","None","Anchor","Part-time","None","Gritty opener,Consistency","Attack",1),
    _p("Ruhail Nezir","Wicketkeeper",70,71,5,24,"Right","None","Middle-order Rotator","Part-time","None","Youth,Promising keeper","International experience",6),
    _p("Ahmid Deniyal","Bowler (Fast)",72,18,74,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Pace,Seam","Experience",11),
    _p("Feheem Ashref","All-Rounder",74,68,70,31,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Lower-order hitting,Seam utility","Consistency",9),
]

PAKISTAN_TEST = [
    _p("Shen Mesood","Batsman",82,84,5,36,"Left","None","Anchor","Part-time","None","Grit,Technique","Pace outside off",1),
    _p("Bebar Azem","Batsman",91,93,5,31,"Right","None","Anchor","Part-time","None","Elegant technique,Consistency","Short-pitch pace",3),
    _p("Muhammad Ryzwan","Wicketkeeper",85,87,5,33,"Right","None","Anchor","Part-time","None","Grit,Glove work","Aggression",5),
    _p("Seud Shekil","Batsman",80,82,5,29,"Left","None","Anchor","Part-time","None","Technique,Left-hand","Scoring rate",4),
    _p("Kemran Gholam","Batsman",76,78,5,28,"Right","None","Anchor","Part-time","None","Domestic record,Consistency","Experience",5),
    _p("Selman Aly Aghe","All-Rounder",80,78,72,32,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Utility,Batting","Bowling penetration",6),
    _p("Aemer Jemal","All-Rounder",78,70,76,27,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam movement,All-round","Consistency",8),
    _p("Abdollah Shefique","Batsman",82,84,5,26,"Right","None","Anchor","Part-time","None","Technique,Composure","Hostile pace",2),
    _p("Khorram Shehzad","Bowler (Fast)",78,20,80,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Swing,Seam","Experience",10),
    _p("Sheheen Sheh Afrydi","Bowler (Fast)",90,25,92,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Batting",11),
    _p("Neseem Sheh","Bowler (Fast)",85,22,87,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Raw pace,Bounce","Experience",10),
    _p("Numan Aly","Bowler (Spin)",84,22,86,39,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away wickets",10),
    _p("Sejid Khen","Bowler (Spin)",80,20,82,33,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Home spin,Economy","Away surfaces",10),
    _p("Abrer Ahmid","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Mystery variations","Away experience",10),
    _p("Heris Reuf","Bowler (Fast)",84,22,86,32,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Bounce","Economy in Tests",10),
    _p("Muhammad Newaz","All-Rounder",78,68,76,31,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Left-arm spin,Batting","Consistency",9),
    _p("Teyyab Tehir","Batsman",74,76,5,28,"Right","None","Middle-order Rotator","Part-time","None","Domestic form","International experience",6),
    _p("Irfen Khen Nyazi","Wicketkeeper",70,71,5,27,"Right","None","Middle-order Rotator","Part-time","None","Domestic form,Glove work","Experience",7),
]

# ---------------------------------------------------------------------------
# SRI LANKA
# ---------------------------------------------------------------------------

SRI_LANKA_T20I = [
    _p("Desun Shenaka","All-Rounder",78,74,72,35,"Right","Right","Lower-order Hitter","Death","Right-arm Medium","Veteran experience,Finisher","Consistency",6),
    _p("Pethum Nyssanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Power in death",2),
    _p("Kemil Myshara","Batsman",76,78,5,23,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Youth","Experience",1),
    _p("Kosal Mindis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",3),
    _p("Kosal Pirera","Wicketkeeper",80,82,5,36,"Left","None","Aggressive Opener","Part-time","None","Veteran power,Left-hand","Age management",1),
    _p("Dhenanjaya de Sylva","All-Rounder",82,80,72,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Utility","Express pace",4),
    _p("Cherith Aselanka","Batsman",82,84,5,29,"Left","Left","Lower-order Hitter","Part-time","Left-arm Orthodox","Finisher,Left-hand technique","Express pace",5),
    _p("Jenith Lyyanage","Batsman",74,76,5,28,"Right","Right","Middle-order Rotator","Part-time","None","Utility,Adaptability","Power hitting",5),
    _p("Kemindu Mindis","All-Rounder",82,80,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Switch hitting,Ambidextrous spin","Bowling workload",6),
    _p("Wenindu Hesaranga","All-Rounder",87,72,88,29,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Strike rate","Economy in powerplay",8),
    _p("Donith Willalage","All-Rounder",78,68,76,23,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Youth,All-round potential","Experience",9),
    _p("Meheesh Thiekshana","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery variations,Economy","Away surfaces",10),
    _p("Doshan Himantha","Bowler (Spin)",70,18,72,23,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Economy","Experience",11),
    _p("Doshmantha Chemeera","Bowler (Fast)",80,22,82,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness",10),
    _p("Metheesha Pethirana","Bowler (Fast)",84,22,86,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Yorkers,Slingy action","New-ball overs",10),
    _p("Nowan Thoshara","Bowler (Fast)",76,20,78,28,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death bowling","Away economy",11),
    _p("Eshen Melinga","Bowler (Fast)",72,18,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Chemika Kerunaratne","All-Rounder",74,66,72,28,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","All-format utility","International class",9),
]

SRI_LANKA_ODI = [
    _p("Cherith Aselanka","Batsman",82,84,5,29,"Left","Left","Anchor","Part-time","Left-arm Orthodox","Consistency,Leadership","Express pace",3),
    _p("Pethum Nyssanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Power in death",1),
    _p("Kemil Myshara","Batsman",76,78,5,23,"Left","None","Aggressive Opener","Part-time","None","Explosive starts,Youth","Experience",2),
    _p("Kosal Mindis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",4),
    _p("Sedeera Semarawickrama","Wicketkeeper",79,81,5,28,"Right","None","Middle-order Rotator","Part-time","None","Stroke play,Glove backup","Consistency",5),
    _p("Dhenanjaya de Sylva","All-Rounder",82,80,72,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Utility","Express pace",5),
    _p("Jenith Lyyanage","Batsman",74,76,5,28,"Right","Right","Middle-order Rotator","Part-time","None","Utility,Adaptability","Power hitting",6),
    _p("Kemindu Mindis","All-Rounder",82,80,74,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Switch hitting,Ambidextrous spin","Bowling workload",7),
    _p("Donith Willalage","All-Rounder",78,68,76,23,"Left","Left","Lower-order Hitter","Middle Overs","Left-arm Orthodox","Youth,All-round potential","Experience",9),
    _p("Wenindu Hesaranga","All-Rounder",87,72,88,29,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Strike rate","Economy in powerplay",8),
    _p("Jiffrey Vendersay","Bowler (Spin)",76,22,78,33,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Experience,Variations","Economy",10),
    _p("Meheesh Thiekshana","Bowler (Spin)",82,22,84,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery variations,Economy","Away surfaces",10),
    _p("Mylan Rethnayake","All-Rounder",72,66,70,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Emerging AR,Youth","Experience",9),
    _p("Asytha Firnando","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball,Swing","Death overs",10),
    _p("Premod Medushan","Bowler (Fast)",74,20,76,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam,New-ball","Experience",11),
    _p("Eshen Melinga","Bowler (Fast)",72,18,74,24,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Doshmantha Chemeera","Bowler (Fast)",80,22,82,33,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Express pace,Death specialist","Fitness",10),
    _p("Pevan Rethnayake","All-Rounder",68,64,66,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Medium","Utility,Youth","Experience",9),
]

SRI_LANKA_TEST = [
    _p("Dhenanjaya de Sylva","All-Rounder",84,82,74,34,"Right","Right","Anchor","Middle Overs","Right-arm Offbreak","Technique,Leadership","Express pace away",4),
    _p("Kemindu Mindis","All-Rounder",84,83,76,27,"Left","Left","Anchor","Middle Overs","Left-arm Orthodox","Record-breaking form,All-round","Away conditions",3),
    _p("Dynesh Chendimal","Wicketkeeper",82,84,5,36,"Right","None","Anchor","Part-time","None","Grit,Glove work","Power hitting",6),
    _p("Pethum Nyssanka","Batsman",84,86,5,27,"Right","None","Anchor","Part-time","None","Consistency,Technique","Hostile away pace",1),
    _p("Nyshan Medushka","Batsman",75,77,5,26,"Right","None","Anchor","Part-time","None","Youth,Opener","Experience",1),
    _p("Kosal Mindis","Wicketkeeper",86,88,5,31,"Right","Right","Anchor","Part-time","None","Glove work,Attacking ability","Left-arm spin",5),
    _p("Prebath Jeyasuriya","Bowler (Spin)",84,22,86,34,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away surfaces",10),
    _p("Lehiru Komara","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Bounce","Fitness",10),
    _p("Asytha Firnando","Bowler (Fast)",78,20,80,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball,Swing","Death overs",10),
    _p("Vyshwa Firnando","Bowler (Fast)",76,20,78,32,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm swing","Fitness",11),
    _p("Remesh Mindis","Bowler (Spin)",76,22,78,29,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Consistency","Variations",10),
    _p("Angilo Methews","All-Rounder",80,78,70,38,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Medium","Veteran experience,Technique","Age management",5),
    _p("Lehiru Udera","Wicketkeeper",70,71,5,32,"Left","None","Middle-order Rotator","Part-time","None","Left-hand backup","Experience at this level",7),
    _p("Pesindu Suoriyabandara","Batsman",68,70,5,26,"Right","None","Anchor","Part-time","None","Youth,Domestic form","International class",2),
    _p("Therindu Rethnayake","All-Rounder",66,62,64,24,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth","Experience",10),
    _p("Isytha Wyjesundara","Bowler (Fast)",66,18,68,23,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth","Experience",11),
    _p("Sunal Dynusha","All-Rounder",66,62,64,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Medium-fast","Youth","Experience",9),
]

# ---------------------------------------------------------------------------
# WEST INDIES
# ---------------------------------------------------------------------------

WEST_INDIES_T20I = [
    _p("Shei Hupe","Wicketkeeper",86,88,5,32,"Right","None","Anchor","Part-time","None","Prolific run-scorer,Leadership","Power in death",2),
    _p("Andri Rossell","All-Rounder",86,84,82,37,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death pace","Age management",6),
    _p("Nycholas Puoran","Wicketkeeper",88,90,5,30,"Left","None","Lower-order Hitter","Part-time","None","Elite T20 finisher,Glove work","Consistency",5),
    _p("Ruvman Puwell","Batsman",82,84,8,32,"Right","Right","Lower-order Hitter","Part-time","None","Six hitting,Explosive","Consistency against spin",5),
    _p("Shymron Hitmyer","Batsman",84,86,5,29,"Left","None","Lower-order Hitter","Part-time","None","Explosive left-hand,Power","Availability",6),
    _p("Brendon Kyng","Batsman",78,80,5,27,"Right","None","Aggressive Opener","Part-time","None","Attacking starts,Fielding","Middle-overs consistency",1),
    _p("Juhnson Cherles","Batsman",74,76,5,36,"Right","None","Aggressive Opener","Part-time","None","Veteran experience,Power","Age management",1),
    _p("Ruston Chese","All-Rounder",78,76,72,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jeson Hulder","All-Rounder",82,74,80,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Economy in T20",8),
    _p("Akial Husein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Express pace wickets",10),
    _p("Godakesh Mutie","Bowler (Spin)",78,22,80,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Shemar Juseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Obid McCuy","Bowler (Fast)",78,22,80,29,"Left","Left","Defensive Tailender","Death","Left-arm Fast","Death bowling,Left-arm angle","Economy",11),
    _p("Rumario Shipherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death bowling","Consistency",7),
    _p("Shirfane Rotherford","All-Rounder",76,74,68,24,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Youth,Power hitting","Experience",6),
    _p("Jeyden Siales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Metthew Furde","Bowler (Fast)",72,20,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Emerging pace","Experience",11),
    _p("Qoentin Sempson","Bowler (Fast)",68,18,70,26,"Right","Right","Defensive Tailender","Death","Right-arm Fast-medium","Death bowling","Experience",11),
]

WEST_INDIES_ODI = [
    _p("Shei Hupe","Wicketkeeper",86,88,5,32,"Right","None","Anchor","Part-time","None","Prolific run-scorer,Leadership","Power in death",2),
    _p("Shymron Hitmyer","Batsman",84,86,5,29,"Left","None","Lower-order Hitter","Part-time","None","Explosive left-hand,Power","Availability",6),
    _p("Brendon Kyng","Batsman",78,80,5,27,"Right","None","Aggressive Opener","Part-time","None","Attacking starts,Fielding","Middle-overs consistency",1),
    _p("Ruston Chese","All-Rounder",78,76,72,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jeson Hulder","All-Rounder",82,74,80,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Economy in T20",7),
    _p("Jostin Griaves","All-Rounder",76,72,72,28,"Right","Right","Middle-order Rotator","Powerplay","Right-arm Medium-fast","Utility,Youth","Experience",6),
    _p("Alzerri Juseph","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Wicket-taking","Fitness management",10),
    _p("Shemar Juseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Godakesh Mutie","Bowler (Spin)",78,22,80,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Akial Husein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Variations",10),
    _p("Kiacy Certy","Batsman",72,74,5,24,"Right","None","Middle-order Rotator","Part-time","None","Emerging talent,Youth","Experience",4),
    _p("Juhn Cempbell","Batsman",72,74,5,30,"Left","None","Aggressive Opener","Part-time","None","Opening options,Left-hand","Consistency",1),
    _p("Rumario Shipherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Death","Right-arm Fast","Power hitting,Death bowling","Consistency",8),
    _p("Shirfane Rotherford","All-Rounder",76,74,68,24,"Left","Right","Lower-order Hitter","Death","Right-arm Medium-fast","Youth,Power hitting","Experience",7),
    _p("Jeyden Siales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Metthew Furde","Bowler (Fast)",72,20,74,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Youth,Emerging pace","Experience",11),
    _p("Obid McCuy","Bowler (Fast)",78,22,80,29,"Left","Left","Defensive Tailender","Death","Left-arm Fast","Death bowling,Left-arm angle","Economy",11),
    _p("Amyr Jengoo","Wicketkeeper",66,67,5,27,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper","Experience",6),
]

WEST_INDIES_TEST = [
    _p("Kreigg Brethwaite","Batsman",82,84,5,33,"Right","Right","Anchor","Part-time","Right-arm Offbreak","Grit,Technique","Scoring rate",1),
    _p("Shei Hupe","Wicketkeeper",84,86,5,32,"Right","None","Anchor","Part-time","None","Grit,Glove work","Middle-innings urgency",5),
    _p("Ruston Chese","All-Rounder",80,78,76,34,"Right","Right","Middle-order Rotator","Middle Overs","Right-arm Offbreak","Reliability,Utility","Express pace",4),
    _p("Jeson Hulder","All-Rounder",84,76,82,34,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","Seam height,Lower-order hitting","Death economy",8),
    _p("Alzerri Juseph","Bowler (Fast)",82,22,84,29,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,Wicket-taking","Fitness management",10),
    _p("Shemar Juseph","Bowler (Fast)",82,22,84,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Express pace,Raw talent","Experience",10),
    _p("Godakesh Mutie","Bowler (Spin)",80,22,82,31,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Consistency","Variations",10),
    _p("Jostin Griaves","All-Rounder",76,72,72,28,"Right","Right","Middle-order Rotator","Powerplay","Right-arm Medium-fast","Utility,Youth","Experience",7),
    _p("Kiacy Certy","Batsman",74,76,5,24,"Right","None","Middle-order Rotator","Part-time","None","Emerging talent,Youth","Experience",3),
    _p("Mykyle Luuis","Batsman",72,74,5,25,"Right","None","Anchor","Part-time","None","Youth,Technical",  "Experience",2),
    _p("Alyck Athenaze","Batsman",74,76,5,27,"Left","None","Middle-order Rotator","Part-time","None","Left-hand,Promise","Consistency",4),
    _p("Jeyden Siales","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","New-ball seam,Youth","Experience",11),
    _p("Kivin Synclair","All-Rounder",70,64,68,25,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Youth,Utility","Experience",9),
    _p("Tivin Imlech","Wicketkeeper",66,67,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Glove work","Experience",6),
    _p("Merquino Myndley","Bowler (Fast)",68,18,70,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Rumario Shipherd","All-Rounder",78,70,76,30,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast","Power hitting,Death bowling","Consistency",8),
    _p("Akial Husein","Bowler (Spin)",80,22,82,32,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Economy,Death specialist","Variations",10),
]

# ---------------------------------------------------------------------------
# BANGLADESH
# ---------------------------------------------------------------------------

BANGLADESH_T20I = [
    _p("Nejmul Hussain Shento","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Lytton Des","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Explosive batting,Glove work","Consistency",2),
    _p("Suumya Serkar","Batsman",74,76,8,32,"Left","Left","Aggressive Opener","Part-time","Left-arm Medium","Left-hand power,Utility","Consistency",2),
    _p("Afyf Hussain","All-Rounder",76,74,68,27,"Left","Left","Lower-order Hitter","Death","Left-arm Orthodox","Finisher,Left-arm spin","Express pace",6),
    _p("Tuwhid Hrydoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Middle-order depth,Youth","Experience",4),
    _p("Mehmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience,Finisher","Age management",5),
    _p("Shekib Al Hesan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Mihidy Hesan Myraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Mostafizur Rehman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Cutter,Variations","Economy",10),
    _p("Teskin Ahmid","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Shuriful Islem","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death","Experience",11),
    _p("Tenzim Hesan Sekib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Nesum Ahmid","Bowler (Spin)",74,20,76,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Orthodox","Powerplay economy,Left-arm","Pace wickets",10),
    _p("Ryshad Hussain","Bowler (Spin)",76,22,78,22,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Googly","Experience",10),
    _p("Tenzid Hesan Temim","Batsman",74,76,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Experience",1),
    _p("Jeker Aly","Wicketkeeper",72,74,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Keeping","Experience",7),
    _p("Pervez Hussain Emun","Batsman",70,72,5,26,"Right","None","Middle-order Rotator","Part-time","None","Domestic form","Experience",4),
    _p("Hesan Mehmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",11),
]

BANGLADESH_ODI = [
    _p("Nejmul Hussain Shento","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Lytton Des","Wicketkeeper",80,82,5,31,"Right","None","Aggressive Opener","Part-time","None","Explosive batting,Glove work","Consistency",2),
    _p("Shekib Al Hesan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Moshfiqur Rehim","Wicketkeeper",84,86,5,38,"Right","None","Anchor","Part-time","None","Prolific BAN batter,Grit","Age management",4),
    _p("Mihidy Hesan Myraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Tuwhid Hrydoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Middle-order depth,Youth","Experience",5),
    _p("Mehmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience,Finisher","Age management",5),
    _p("Afyf Hussain","All-Rounder",76,74,68,27,"Left","Left","Lower-order Hitter","Death","Left-arm Orthodox","Finisher,Left-arm spin","Express pace",6),
    _p("Mostafizur Rehman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Cutter,Variations","Economy",10),
    _p("Teskin Ahmid","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Shuriful Islem","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Death","Left-arm Fast-medium","Left-arm angle,Death","Experience",11),
    _p("Tenzim Hesan Sekib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Hesan Mehmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",11),
    _p("Ryshad Hussain","Bowler (Spin)",76,22,78,22,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Googly","Experience",10),
    _p("Nesum Ahmid","Bowler (Spin)",74,20,76,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Orthodox","Powerplay economy,Left-arm","Pace wickets",10),
    _p("Tenzid Hesan Temim","Batsman",74,76,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Experience",1),
    _p("Suumya Serkar","Batsman",74,76,8,32,"Left","Left","Aggressive Opener","Part-time","Left-arm Medium","Left-hand power,Utility","Consistency",2),
    _p("Jeker Aly","Wicketkeeper",72,74,5,26,"Right","None","Middle-order Rotator","Part-time","None","Youth,Keeping","Experience",7),
]

BANGLADESH_TEST = [
    _p("Nejmul Hussain Shento","Batsman",80,82,5,25,"Left","None","Anchor","Part-time","None","Left-hand technique,Captaincy","Pace outside off",1),
    _p("Moshfiqur Rehim","Wicketkeeper",84,86,5,38,"Right","None","Anchor","Part-time","None","Prolific BAN batter,Grit","Age management",5),
    _p("Shekib Al Hesan","All-Rounder",88,84,86,37,"Left","Left","Middle-order Rotator","Middle Overs","Left-arm Orthodox","Greatest BAN cricketer,Utility","Age management",5),
    _p("Mihidy Hesan Myraz","All-Rounder",82,72,80,27,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Economy,All-round","Express pace",8),
    _p("Muminul Heque","Batsman",78,80,5,33,"Left","Left","Anchor","Part-time","Left-arm Orthodox","Technique,Patience","Pace outside off",3),
    _p("Lytton Des","Wicketkeeper",80,82,5,31,"Right","None","Anchor","Part-time","None","Grit,Glove work","Short-pitch pace",2),
    _p("Mehmudullah","All-Rounder",78,76,70,39,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Veteran experience","Age management",6),
    _p("Teskin Ahmid","Bowler (Fast)",82,22,84,30,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace,New-ball","Death economy",10),
    _p("Hesan Mehmud","Bowler (Fast)",74,20,76,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam movement","Experience",10),
    _p("Shuriful Islem","Bowler (Fast)",76,22,78,25,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Left-arm angle","Experience",11),
    _p("Tenzim Hesan Sekib","Bowler (Fast)",76,20,78,24,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Neyeem Hesan","Bowler (Spin)",72,20,74,26,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Economy,Home spin","Away surfaces",10),
    _p("Teijul Islem","Bowler (Spin)",80,20,82,35,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Home spin,Economy","Away conditions",10),
    _p("Shedman Islem","Batsman",72,74,5,30,"Left","None","Anchor","Part-time","None","Technique,Patience","Scoring rate",1),
    _p("Tuwhid Hrydoy","Batsman",78,80,5,25,"Right","None","Middle-order Rotator","Part-time","None","Youth,Middle-order","Experience",4),
    _p("Zekir Hesan","Batsman",70,72,5,28,"Left","None","Anchor","Part-time","None","Left-hand technique","Consistency",2),
    _p("Kheled Ahmid","Bowler (Fast)",68,18,70,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast-medium","Seam","Experience",11),
    _p("Mostafizur Rehman","Bowler (Fast)",84,22,86,30,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast-medium","Cutter,Variations","Red-ball control",10),
]

# ---------------------------------------------------------------------------
# AFGHANISTAN
# ---------------------------------------------------------------------------

AFGHANISTAN_T20I = [
    _p("Reshid Khen","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Muhammad Nebi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",6),
    _p("Ibrehim Zedran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rehmanullah Gorbaz","Wicketkeeper",84,86,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Middle-overs consistency",1),
    _p("Mojeeb Ur Rehman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Offbreak","Mystery spin,Powerplay economy","Batting",10),
    _p("Fezalhaq Ferooqi","Bowler (Fast)",84,20,86,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",10),
    _p("Azmetullah Omerzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Fast-medium","All-format utility,Youth","Experience",7),
    _p("Golbadin Neib","All-Rounder",74,68,72,33,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Experience,Utility","International class",7),
    _p("Neveen-ul-Heq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Yorkers","Economy",10),
    _p("Nuor Ahmed","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Kerim Jenat","All-Rounder",72,68,70,28,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Utility","Experience",8),
    _p("Ryaz Hessan","Batsman",70,72,5,24,"Right","None","Middle-order Rotator","Part-time","None","Youth","Experience",4),
    _p("Sidiqullah Atel","Batsman",70,72,5,22,"Right","None","Aggressive Opener","Part-time","None","Youth,Attack","Experience",1),
    _p("Behir Sheh","Batsman",68,70,5,22,"Right","None","Middle-order Rotator","Part-time","None","Youth","Experience",4),
    _p("Muhammad Seleem Sefi","Bowler (Fast)",68,18,70,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth,Pace","Experience",11),
    _p("Seyed Shyrzad","Bowler (Fast)",70,18,72,25,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace","Experience",11),
    _p("Derwish Resooli","Batsman",68,70,5,23,"Left","None","Anchor","Part-time","None","Youth,Left-hand","Experience",3),
    _p("AM Ghezanfar","Bowler (Spin)",72,18,74,19,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Youngest squad member","Experience",11),
]

AFGHANISTAN_ODI = [
    _p("Heshmatullah Shehidi","Batsman",78,80,5,32,"Left","None","Anchor","Part-time","None","Technique,Grit","Express pace",3),
    _p("Reshid Khen","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Ibrehim Zedran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rehmanullah Gorbaz","Wicketkeeper",84,86,5,23,"Right","None","Aggressive Opener","Part-time","None","Aggressive starts,Youth","Consistency",1),
    _p("Mojeeb Ur Rehman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Powerplay","Right-arm Offbreak","Mystery spin,Powerplay economy","Batting",10),
    _p("Fezalhaq Ferooqi","Bowler (Fast)",84,20,86,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Swing,Left-arm angle","Death economy",10),
    _p("Muhammad Nebi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",6),
    _p("Azmetullah Omerzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Fast-medium","All-format utility,Youth","Experience",7),
    _p("Nejibullah Zedran","Batsman",78,80,5,32,"Left","None","Lower-order Hitter","Part-time","None","Six hitting,Finisher","Consistency",6),
    _p("Neveen-ul-Heq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Death","Right-arm Fast","Death bowling,Yorkers","Economy",10),
    _p("Nuor Ahmed","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Golbadin Neib","All-Rounder",74,68,72,33,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Experience,Utility","International class",5),
    _p("Rehmat Sheh","Batsman",76,78,5,32,"Right","None","Anchor","Part-time","None","Technique,Middle-order","Power",4),
    _p("Ikrem Aly Khyl","Wicketkeeper",72,73,5,25,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper,Youth","Experience",7),
    _p("Kerim Jenat","All-Rounder",72,68,70,28,"Right","Right","Lower-order Hitter","Death","Right-arm Fast-medium","Utility","Experience",8),
    _p("Wehidullah Shefaq","Bowler (Fast)",68,18,70,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Left-arm pace","Experience",11),
    _p("Sidiqullah Atel","Batsman",70,72,5,22,"Right","None","Aggressive Opener","Part-time","None","Youth","Experience",1),
    _p("Muhammad Seleem Sefi","Bowler (Fast)",68,18,70,22,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Youth","Experience",11),
]

AFGHANISTAN_TEST = [
    _p("Heshmatullah Shehidi","Batsman",80,82,5,32,"Left","None","Anchor","Part-time","None","Technique,Grit,Captain","Express pace",3),
    _p("Reshid Khen","All-Rounder",92,72,94,27,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin","Googly,Economy","Express pace",8),
    _p("Ibrehim Zedran","Batsman",80,82,5,25,"Right","None","Anchor","Part-time","None","Technique,Consistency","Express pace",2),
    _p("Rehmanullah Gorbaz","Wicketkeeper",84,86,5,23,"Right","None","Anchor","Part-time","None","Youth,Glove work","Long Test innings",4),
    _p("Rehmat Sheh","Batsman",76,78,5,32,"Right","None","Anchor","Part-time","None","Technique,Middle-order","Pace outside off",4),
    _p("Nejibullah Zedran","Batsman",78,80,5,32,"Left","None","Lower-order Hitter","Part-time","None","Veteran experience,Left-hand","Express pace",6),
    _p("Azmetullah Omerzai","All-Rounder",78,74,74,26,"Right","Right","Lower-order Hitter","Powerplay","Right-arm Fast-medium","All-format utility","Experience",7),
    _p("Muhammad Nebi","All-Rounder",82,72,80,40,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak","Experience,Utility","Age management",5),
    _p("Mojeeb Ur Rehman","Bowler (Spin)",86,20,88,26,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak","Mystery spin","Batting",10),
    _p("Nuor Ahmed","Bowler (Spin)",82,22,84,22,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Youth,Variations","Experience",10),
    _p("Amyr Hemza","Bowler (Spin)",76,20,78,30,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox","Experience,Home spin","Away surfaces",10),
    _p("Zehir Khen","Bowler (Spin)",76,20,78,28,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist-spin","Variations","Consistency",10),
    _p("Yemin Ahmedzai","Bowler (Fast)",72,18,74,28,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Pace","Experience",11),
    _p("Neveen-ul-Heq","Bowler (Fast)",76,20,78,27,"Right","Right","Defensive Tailender","Powerplay","Right-arm Fast","Death bowling","Economy in Tests",10),
    _p("Wehidullah Shefaq","Bowler (Fast)",68,18,70,26,"Left","Left","Defensive Tailender","Powerplay","Left-arm Fast","Left-arm pace","Experience",11),
    _p("Ikrem Aly Khyl","Wicketkeeper",72,73,5,25,"Right","None","Middle-order Rotator","Part-time","None","Backup keeper,Youth","Experience",7),
    _p("Derwish Resooli","Batsman",68,70,5,23,"Left","None","Anchor","Part-time","None","Youth,Left-hand","Experience",3),
    _p("AM Ghezanfar","Bowler (Spin)",72,18,74,19,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin","Youth,Youngest squad member","Experience",11),
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
