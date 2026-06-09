"""Rebuild players_alltime.csv with:
- Prime age for each player (not 2026 age)
- OVRs based on full IPL career, not weighted toward recent years
- Sorted highest to lowest OVR
"""

# ── PRIME AGE NOTES ──────────────────────────────────────────────────────────
# Using peak/prime age: roughly the age at which a player was at their best
# in IPL. For most batters this is late 20s-early 30s. For bowlers 24-30.
# For all-time legends who played multiple eras, use their peak IPL era age.
# This means Gayle ~33, ABD ~32, Dhoni ~33, Warner ~30, etc.

# ── OVR METHODOLOGY ─────────────────────────────────────────────────────────
# Career IPL batting score = weighted combo of: runs/match, SR, total runs
# Career IPL bowling score = weighted combo of: wickets/match, economy, total wickets
# Scale: 95-99 all-time elite (top 5-10 in their discipline IPL-wide)
#        88-94 franchise star (sustained excellence multiple seasons)
#        80-87 quality regular (solid contributor 3+ seasons)
#        70-79 useful contributor
#        60-69 fringe/squad player

# Batting OVR benchmarks (from career stats):
# 98+: Kohli (8899r/133SR/33rpm), Warner (6567/139/35), Gayle (4997/149/35)
# 95-97: ABD (5181/151/30), Dhoni (5439/137/22), Buttler (4297/149/34)
# 93-94: Rahul (5346/136/38), Suryakumar (4417/148/28), Sehwag (2728/155/26)
# 91-92: Raina (5536/136/27), Russell (2655/174/23), Gambhir (4217/123/27)
# etc.

# Bowling OVR benchmarks (from career stats):
# 98: Malinga (170w/1.39wpm/7.14econ), Bumrah (186w/1.24wpm/7.30econ)
# 96: Chahal (224w/1.27wpm/8.0econ), Steyn (97w/1.02wpm/6.94econ)
# 95: Narine (195w/1.02wpm/6.80econ), Rashid (163w/1.16wpm/7.08econ)
# etc.

rows = []

def p(name, role, base, bat, bowl, overseas, prime_age, bh, bowlh, arch, phase, btype, strength, weakness):
    rows.append([name, role, str(base), str(bat), str(bowl), str(overseas),
                 str(prime_age), bh, bowlh, arch, phase, btype, strength, weakness])

# ═══════════════════════════════════════════════════════════════════════════
# BATTERS / KEEPER-BATTERS
# ═══════════════════════════════════════════════════════════════════════════

# 98-99 OVR: Unambiguous all-time elite
p("Virat Kohli","Batsman",98,98,20,False,30,"Right","Right","Anchor","Part-time","None",
  "IPL all-time leading run scorer 8899 at 133 SR with four Orange Caps — the benchmark of T20 consistency across 264 matches",
  "Occasionally conservative strike rate in powerplay compared to modern power-hitters")
p("David Warner","Batsman",97,97,10,True,30,"Left","Right","Aggressive Opener","Part-time","None",
  "6567 IPL runs at 139 SR with three Orange Caps and SRH title — one of the most destructive openers the format has seen",
  "Vulnerability to quality short-pitch pace in the channel when not fully set in the first few deliveries")
p("Chris Gayle","Batsman",97,97,45,True,33,"Left","Right","Aggressive Opener","Part-time","Right-arm Offbreak",
  "4997 runs at 149 SR across 141 matches including the record 175* — the most destructive power-hitter in IPL history",
  "Slow to get going and needed time to settle but almost impossible to dislodge once past 20 balls")
p("AB de Villiers","Wicketkeeper",97,97,20,True,32,"Right","None","Finisher","Part-time","None",
  "5181 runs at a staggering 151 SR across 170 matches — the 360-degree genius who reinvented middle-order T20 batting",
  "Retired 2021 and even his genius occasionally struggled against elite yorkers at his stumps in death overs")

# 95-96: Clear franchise superstar level
p("MS Dhoni","Wicketkeeper",96,91,15,False,33,"Right","None","Finisher","Part-time","None",
  "5439 IPL runs at 137 SR and four CSK titles as the greatest captain in franchise cricket history",
  "Batting strike rate dropped significantly in later career but finishing instinct and captaincy remained unmatched")
p("Jos Buttler","Wicketkeeper",95,95,10,True,32,"Right","None","Aggressive Opener","Part-time","None",
  "4297 runs at 149 SR including the greatest individual IPL season of 863 runs with four centuries in 2022 for RR",
  "High-risk approach creates streaky form with sequences of poor scores alongside brilliant match-winning campaigns")
p("Rohit Sharma","Batsman",95,95,10,False,30,"Right","Right","Aggressive Opener","Part-time","None",
  "7185 IPL runs at 132 SR across 270 matches with five titles as MI captain — the most decorated franchise player",
  "Can be streaky and when dismissed cheaply the MI innings often collapses without his foundation")
p("KL Rahul","Wicketkeeper",94,94,10,False,28,"Right","None","Aggressive Opener","Part-time","None",
  "5346 IPL runs at 136 SR across 139 matches with two Orange Caps as one of the most elegant opening batters",
  "Questions about his ability to accelerate in final overs and inconsistency at the very top level")

# 93-94
p("Suryakumar Yadav","Batsman",93,93,10,False,29,"Right","Right","Middle-over Rotator","Part-time","None",
  "4417 IPL runs at 148 SR with extraordinary 360-degree strokeplay that elevated middle-order T20 batting to an art form",
  "All-or-nothing style brings inherent inconsistency but the match-winning ceiling is completely unique")
p("Virender Sehwag","Batsman",93,93,20,False,30,"Right","Right","Aggressive Opener","Part-time","Right-arm Offbreak",
  "2728 IPL runs at an exceptional 155 SR across 104 matches — brought his explosive Test-format aggression directly to T20",
  "Boom-or-bust approach meant cheap early wickets when bowlers found the channel outside off-stump")
p("Shikhar Dhawan","Batsman",91,91,10,False,30,"Left","Right","Aggressive Opener","Part-time","None",
  "6769 IPL runs at 127 SR across 221 matches — the most consistent left-hand opener across a decade of IPL cricket",
  "Lower ceiling for boundary-hitting compared to peers meaning teams around him needed power-hitters")
p("Sanju Samson","Wicketkeeper",91,91,10,False,27,"Right","None","Aggressive Opener","Part-time","None",
  "4889 IPL runs at 140 SR as RR captain with extraordinary match-winning innings when fully in form",
  "Well-documented inconsistency and rash dismissals when pressure builds after a poor start")
p("Yashasvi Jaiswal","Batsman",91,91,10,False,21,"Left","Right","Aggressive Opener","Part-time","None",
  "2350 IPL runs at 153 SR with extraordinary consistency since his 2023 breakthrough — RR's next superstar",
  "Still building T20 consistency and can occasionally be cautious before shifting into destructive gear")
p("Andre Russell","All-Rounder",91,88,87,True,30,"Right","Right","Finisher","Death Overs","Right-arm Fast",
  "2655 IPL runs at a staggering 174 SR and 123 wickets — the most destructive T20 all-rounder in the world",
  "Injury management has been an ongoing challenge limiting availability across full franchise campaigns")
p("Suresh Raina","Batsman",90,89,72,False,29,"Left","Right","Middle-over Rotator","Middle Overs","Left-arm Orthodox",
  "5536 IPL runs at 136 SR and 36 wickets across 200 matches — Mr IPL whose consistency across a decade was unrivalled",
  "Vulnerability against short-pitched pace was a known weakness opponents targeted ruthlessly in knockout games")
p("Brendon McCullum","Batsman",89,89,10,True,30,"Right","Right","Aggressive Opener","Part-time","None",
  "2882 IPL runs at 131 SR including the inaugural century in IPL's very first match — set the aggressive template for franchise cricket",
  "Later career inconsistency as teams decoded his approach and short-pitched pace exposed technical limitations")
p("Gautam Gambhir","Batsman",89,89,10,False,31,"Left","Right","Anchor","Part-time","None",
  "4217 IPL runs at 123 SR as the defining captain of KKR's back-to-back title wins in 2012 and 2014",
  "Conservative T20 approach by modern standards but exceptional match management and innings-building intelligence")
p("Shane Watson","All-Rounder",89,86,82,True,32,"Right","Right","Aggressive Opener","New-ball Bowler","Right-arm Fast",
  "3880 IPL runs at 137 SR and 92 wickets as a genuine pace-bowling all-rounder — CSK 2018 final century was iconic",
  "Injury-prone throughout career limiting bowling workload and availability across full franchise campaigns")
p("Yusuf Pathan","All-Rounder",87,84,76,False,29,"Right","Right","Finisher","Middle Overs","Right-arm Offbreak",
  "3222 IPL runs at 143 SR and 42 wickets as the most destructive middle-order all-rounder of the first KKR era",
  "Inconsistency and vulnerability to quality pace in the channel outside off-stump when not in prime form")
p("Adam Gilchrist","Wicketkeeper",88,88,10,True,30,"Left","Right","Aggressive Opener","Part-time","None",
  "2069 IPL runs at 138 SR across 80 matches including a stunning Deccan Chargers final performance to win the 2009 title",
  "IPL career was the final phase of his playing days and the form was less consistent than his absolute peak years")
p("Ricky Ponting","Batsman",84,84,10,True,30,"Right","Right","Anchor","Part-time","None",
  "Two-time World Cup winner who captained Mumbai Indians and contributed 1444 runs of quality batting across 73 matches",
  "Conservative T20 SR of 119 — the classical Australian technique was the most suited to other formats")
p("Matthew Hayden","Batsman",86,86,10,True,30,"Left","Right","Aggressive Opener","Part-time","None",
  "1107 IPL runs at 137 SR across just 32 matches — brought Ashes-level aggression to CSK's first IPL seasons",
  "Short IPL career at an age past his true prime but impact in Chennai's early seasons was genuinely match-winning")
p("Sachin Tendulkar","Batsman",89,89,15,False,29,"Right","Right","Anchor","Part-time","None",
  "2334 IPL runs at 119 SR across 78 matches — the God of Cricket's presence and MI's legendary franchise cornerstone",
  "SR of 119 reflects that T20 was the least suited format for his classical technique despite the unmatched class")
p("Yuvraj Singh","All-Rounder",88,84,78,False,28,"Left","Left","Middle-over Rotator","Middle Overs","Left-arm Orthodox",
  "2754 IPL runs at 129 SR and 36 wickets — was especially destructive in early IPL seasons and two World Cup wins show pedigree",
  "Career curtailed by health issues and later form became inconsistent though the ability was never fully gone")
p("Robin Uthappa","Wicketkeeper",87,87,10,False,29,"Right","None","Aggressive Opener","Part-time","None",
  "4954 IPL runs at 130 SR across 197 matches — Orange Cap 2014 and pivotal to KKR's back-to-back title campaigns",
  "Batting position and franchise role varied greatly preventing sustained runs of high-impact output")
p("Dinesh Karthik","Wicketkeeper",85,83,10,False,31,"Right","None","Finisher","Part-time","None",
  "4843 IPL runs at 135 SR across 233 matches including a remarkable RCB renaissance as IPL's premier finisher in 2022",
  "Inconsistent through the middle period of his career before the famous 2022 reinvention at RCB")
p("Faf du Plessis","Batsman",87,87,10,True,31,"Right","Right","Aggressive Opener","Part-time","None",
  "4773 IPL runs at 135 SR across 147 matches as one of the most technically excellent and composed franchise openers",
  "Power-hitting ceiling was slightly lower than the most destructive peers but consistency was exceptional")
p("Kieron Pollard","All-Rounder",88,85,82,True,29,"Right","Right","Finisher","Death Overs","Right-arm Medium",
  "3437 IPL runs at 147 SR and 69 wickets across 168 matches — MI's ultimate match-winning weapon for a decade",
  "Vulnerability against wrist-spin was a tactical opposition target and bowling effectiveness declined late career")
p("KA Pollard","All-Rounder",88,85,82,True,29,"Right","Right","Finisher","Death Overs","Right-arm Medium",
  "3437 IPL runs at 147 SR and 69 wickets across 168 matches — MI's ultimate match-winning weapon for a decade",
  "Vulnerability against wrist-spin was a tactical opposition target and bowling effectiveness declined late career")
p("Ambati Rayudu","Batsman",82,82,10,False,31,"Right","Right","Middle-over Rotator","Part-time","None",
  "4348 IPL runs at 127 SR across 185 matches as CSK's dependable middle-order anchor in multiple title campaigns",
  "Below-average boundary rate and conservative approach made him a stabiliser rather than match-winner")
p("Ajinkya Rahane","Batsman",83,83,10,False,28,"Right","Right","Anchor","Part-time","None",
  "5184 IPL runs at 125 SR across 188 matches — technically excellent opener whose consistency across franchises was remarkable",
  "Conservative T20 approach and below-average power-hitting ceiling by modern standards")
p("Wriddhiman Saha","Wicketkeeper",79,78,10,False,31,"Right","None","Middle-over Rotator","Part-time","None",
  "2934 IPL runs at 127 SR across 143 matches as a technically reliable keeper-batter for SRH and other franchises",
  "Never the power-hitter the modern format demands and batting in the lower middle order limited statistical impact")
p("Parthiv Patel","Wicketkeeper",79,78,10,False,26,"Left","Right","Aggressive Opener","Part-time","None",
  "2848 IPL runs at 120 SR across 136 matches as a combative left-hand keeper-batter who opened with genuine aggression",
  "SR modest by opener standards and the aggressive approach occasionally produced reckless early dismissals")
p("Manish Pandey","Batsman",81,81,10,False,27,"Right","Right","Middle-over Rotator","Part-time","None",
  "3951 IPL runs at 121 SR across 161 matches as a technically sound middle-order batter across multiple franchises",
  "Conservative 121 SR by modern T20 standards often too carefully set up the finish rather than accelerating himself")
p("Naman Ojha","Wicketkeeper",77,75,10,False,31,"Right","None","Middle-over Rotator","Part-time","None",
  "1554 IPL runs at 118 SR across 94 matches as a dependable keeper-batter providing solid SRH middle-order contributions",
  "Conservative approach and batting was solid without being spectacular limiting him to a squad role")
p("Murali Vijay","Batsman",80,80,10,False,28,"Right","Right","Anchor","Part-time","None",
  "2619 IPL runs at 121 SR across 105 matches as CSK's technically correct and composed anchor opener",
  "Limited explosive power-hitting meant opponents could set defensive fields and restrict his boundary options")
p("Manoj Tiwary","Batsman",79,79,10,False,28,"Right","Right","Middle-over Rotator","Part-time","None",
  "1695 IPL runs at 117 SR across 83 matches as a dependable middle-order contributor despite being widely underutilised",
  "Conservative strike rate and irregular franchise opportunities limited consistent high-impact contributions")
p("Graeme Smith","Batsman",80,80,10,True,27,"Left","Right","Anchor","Part-time","None",
  "739 IPL runs at 110 SR bringing South Africa captaincy class as KXIP opener — leadership quality exceeded batting output",
  "Frequent unavailability due to South Africa captaincy commitments made him a frustrating squad player")
p("Jacques Kallis","All-Rounder",86,83,80,True,34,"Right","Right","Anchor","New-ball Bowler","Right-arm Fast",
  "2427 IPL runs at 109 SR and 36 wickets as a true world-class all-rounder bringing Test-match quality to franchise cricket",
  "Conservative batting SR and moderate pace bowling were limitations but the all-round consistency was unmatched")
p("Mahela Jayawardene","Batsman",79,79,10,True,33,"Right","Right","Anchor","Part-time","None",
  "1808 IPL runs at 123 SR for MI and KKR bringing Sri Lankan master's elegant batting intelligence to franchise cricket",
  "Conservative T20 SR by modern standards though the tactical cricket intelligence was invaluable to those franchises")
p("Kumar Sangakkara","Wicketkeeper",81,81,10,True,32,"Left","Right","Anchor","Part-time","None",
  "1687 IPL runs at 121 SR across 68 matches for multiple franchises as an elegant and classy left-hand keeper-batter",
  "T20 approach was not always perfectly calibrated to the format's increasing aggression demands")
p("Tillakaratne Dilshan","Batsman",81,81,10,True,32,"Right","Right","Aggressive Opener","Part-time","None",
  "1153 IPL runs at 114 SR and pioneered the dilscoop as one of T20 cricket's early innovators of unorthodox batting",
  "SR of 114 is low by modern opener standards but his revolutionary strokeplay influenced the entire format")
p("Kevin Pietersen","Batsman",84,84,10,True,30,"Right","Right","Middle-over Rotator","Part-time","None",
  "1001 IPL runs at 134 SR across 36 matches for RCB and DD — flamboyant 360-degree strokeplay in limited franchise cricket",
  "ECB restrictions severely limited his IPL career and he never played enough seasons to build a proper franchise legacy")
p("Lendl Simmons","Batsman",80,80,10,True,29,"Right","Right","Aggressive Opener","Part-time","None",
  "1079 IPL runs at 126 SR including an outstanding 540-run season for TKR — powerful West Indian opener with genuine quality",
  "Limited IPL appearances restricted his ability to establish himself as a long-term franchise cornerstone")
p("Brendon McCullum","Batsman",89,89,10,True,30,"Right","Right","Aggressive Opener","Part-time","None",
  "2882 IPL runs at 131 SR — scored the IPL's inaugural century in the first ever match and defined KKR's aggressive brand",
  "Later career inconsistency as opponents decoded his approach and targeted short-pitched pace")
p("S Badrinath","Batsman",78,78,10,False,29,"Right","Right","Middle-over Rotator","Part-time","None",
  "1441 IPL runs at 118 SR across 65 matches as CSK's dependable glue player in their early title-winning campaigns",
  "Below-average T20 SR by modern standards limited his ceiling as a match-winner")
p("Brad Hodge","Batsman",78,78,10,True,30,"Right","Right","Middle-over Rotator","Part-time","None",
  "1400 IPL runs at 125 SR for KKR and RR as a composed and dependable Australian middle-order contributor",
  "Limited explosive T20 power-hitting by modern standards and career ended before the modern slog era evolved")
p("Shaun Marsh","Batsman",82,82,10,True,26,"Left","Right","Anchor","Part-time","None",
  "2489 IPL runs at 133 SR for KXIP across 69 matches including multiple Orange Cap seasons as one of the best early openers",
  "Injuries restricted IPL availability despite consistently high form whenever available")
p("Jesse Ryder","Batsman",80,80,10,True,27,"Left","Right","Aggressive Opener","Part-time","None",
  "604 IPL runs at 131 SR across 29 matches — a destructive left-hand big-hitter who could dominate any attack when set",
  "Off-field issues curtailed a career that never played enough seasons to show full devastating potential")
p("Michael Hussey","Batsman",83,83,10,True,30,"Left","Right","Anchor","Part-time","None",
  "1977 IPL runs at 122 SR across 58 matches for CSK bringing exceptional game sense and innings-building composure",
  "Conservative left-hand approach without explosive power-hitting ceiling — dependent on others to provide hitting")
p("Rahul Dravid","Batsman",79,79,10,False,28,"Right","Right","Anchor","Part-time","None",
  "2174 IPL runs at 115 SR for RR and DD — the Wall's batting intelligence was evident even in an unsuitable format",
  "T20 was the least suited of all formats for his classical technique and the SR of 115 reflected that honestly")
p("Sourav Ganguly","Batsman",80,80,10,False,29,"Left","Right","Anchor","Part-time","None",
  "1349 IPL runs at 106 SR as KKR's inaugural captain — brought enormous cricketing authority and experience",
  "SR of 106 was very conservative even for early IPL and the format's power game never fully suited him")
p("VVS Laxman","Batsman",78,78,10,False,28,"Right","Right","Anchor","Part-time","None",
  "1477 IPL runs at 116 SR across 71 matches for Deccan Chargers bringing world-class batting intelligence",
  "T20 was genuinely the weakest format for his classical technique and the numbers reflected the limitation")
p("Dwayne Smith","All-Rounder",81,81,66,True,28,"Right","Right","Aggressive Opener","Flexible","Right-arm Fast",
  "2385 IPL runs at 135 SR and 26 wickets as CSK's destructive opening all-rounder across title-winning campaigns",
  "Consistency was the limitation and franchise impact varied season to season depending on conditions")
p("Eoin Morgan","Batsman",80,80,10,True,28,"Left","Right","Middle-over Rotator","Part-time","None",
  "1406 IPL runs at 122 SR for KKR and DC bringing excellent tactical batting and the captaincy that won the 2019 World Cup",
  "Conservative T20 SR by modern power-hitting standards and peak franchise performances were infrequent")
p("Ross Taylor","Batsman",78,78,10,True,29,"Right","Right","Middle-over Rotator","Part-time","None",
  "1017 IPL runs at 123 SR across 54 matches as a technically sound and composed New Zealand middle-order batter",
  "Conservative approach and not a big six-hitter by modern standards limiting his T20 ceiling")
p("JP Duminy","All-Rounder",79,79,63,True,26,"Left","Right","Middle-over Rotator","Middle Overs","Right-arm Offbreak",
  "2029 IPL runs at 124 SR and 36 wickets as a technically solid South African middle-order all-rounder",
  "Below-average T20 SR by modern standards and off-spin was flat rather than a genuine wicket-taking threat")
p("Andrew Symonds","All-Rounder",83,80,75,True,28,"Right","Right","Finisher","Middle Overs","Right-arm Medium",
  "974 IPL runs at 129 SR with genuine middle-order hitting and tactical bowling cleverness for Deccan Chargers",
  "Career was winding down during IPL years and the full expression of his extraordinary talent was never seen")
p("Paul Collingwood","All-Rounder",75,74,72,True,32,"Right","Right","Middle-over Rotator","Middle Overs","Right-arm Medium",
  "Solid CSK and KXIP all-rounder who brought tactical intelligence and dependable middle-order batting",
  "Never the most explosive in any discipline — the glue-player archetype rather than a match-winning influence")
p("Manan Vohra","Batsman",71,71,8,False,23,"Right","Right","Aggressive Opener","Part-time","None",
  "1083 IPL runs at 130 SR with glimpses of explosive hitting for KXIP including a notable 95 off 50 balls",
  "Never able to cement a franchise cornerstone role and inconsistency prevented sustained high output")
p("DJ Hussey","All-Rounder",78,78,68,True,34,"Right","Right","Middle-over Rotator","Middle Overs","Right-arm Medium",
  "1322 IPL runs at 123 SR and 38 wickets as a useful Australian T20 all-rounder across multiple franchise seasons",
  "Limited explosive ceiling in both disciplines and more of a utility player than a match-winning influence")

# ═══════════════════════════════════════════════════════════════════════════
# BOWLERS
# ═══════════════════════════════════════════════════════════════════════════
p("Jasprit Bumrah","Bowler (Fast)",98,18,98,False,24,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "186 IPL wickets at 7.30 economy and 1.24 wpm — the greatest T20 bowler ever with unmatched yorker accuracy",
  "Economy can rise against aggressive left-handers targeting wide channels in the powerplay phase")
p("Lasith Malinga","Bowler (Fast)",97,15,97,True,29,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "170 IPL wickets at 7.14 economy and 1.39 wpm — the greatest death-over bowler in IPL history with unplayable yorkers",
  "Slingy action put enormous strain on his body and batting was a genuine liability at the lower order")
p("Yuzvendra Chahal","Bowler (Spin)",92,20,92,False,27,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "224 IPL wickets — the all-time record — at 8.00 economy and 1.27 wpm across 176 matches for RCB and RR",
  "Economy is the most expensive of the top wicket-takers and can be punished badly on flat batting surfaces")
p("Dale Steyn","Bowler (Fast)",93,15,93,True,29,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "97 IPL wickets at an exceptional 6.94 economy — the most economical pace bowler of his era with natural reverse swing",
  "Injuries plagued his IPL career limiting appearances and batting contributes minimal franchise value")
p("Sunil Narine","All-Rounder",93,86,93,True,28,"Left","Right","Aggressive Opener","Middle Overs","Mystery Spin",
  "195 IPL wickets at 6.80 economy and 1816 batting runs at 166 SR — the unique two-way match-winner who defines KKR",
  "Mystery action was reviewed under ICC scrutiny and remodelled action reduced peak bowling effectiveness")
p("Rashid Khan","Bowler (Spin)",96,74,96,True,22,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin",
  "163 IPL wickets at 7.08 economy and 1.16 wpm with lower-order hitting — the most complete spinner in T20 franchise cricket",
  "Premeditated slog-sweeps from experienced left-handers can occasionally disrupt rhythm in limited overs")
p("Bhuvneshwar Kumar","Bowler (Fast)",88,35,88,False,27,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Swing",
  "205 IPL wickets at 7.72 economy — second all-time with exceptional powerplay swing and masterful variations",
  "Recurring injury concerns and death-over effectiveness notably weaker than in powerplay phase")
p("Harbhajan Singh","Bowler (Spin)",89,78,89,False,30,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak",
  "150 IPL wickets at 7.08 economy across 160 matches — the best Indian spinner of the first decade with golden economy",
  "Off-spin became predictable at high level in later seasons and all-round consistency faded")
p("Piyush Chawla","Bowler (Spin)",83,60,83,False,26,"Right","Right","Lower-order Hitter","Middle Overs","Leg-spin",
  "192 IPL wickets across 191 matches — prolific but expensive at 7.96 economy as a wicket-taking leg-spinner",
  "Economy is costly and on good batting surfaces his flat-track bowling can be targeted and punished")
p("Amit Mishra","Bowler (Spin)",83,55,83,False,28,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "174 IPL wickets at 7.38 economy and 1.07 wpm across 162 matches as one of the finest Indian leg-spinners",
  "Batting is a genuine liability and slower pace can be targeted by flat-footed sloggers in favourable conditions")
p("Shane Warne","Bowler (Spin)",86,25,86,True,32,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "57 IPL wickets at 7.27 economy while captaining Rajasthan Royals to the 2008 inaugural IPL title in a legendary season",
  "Age was always a factor and leg-spin variations became familiar to opponents who had studied him extensively")
p("Muttiah Muralitharan","Bowler (Spin)",84,30,84,True,30,"Right","Right","Defensive Tailender","Middle Overs","Right-arm Offbreak",
  "64 IPL wickets at 6.70 economy — the most economical bowler in IPL history and arguably the greatest spinner ever",
  "Retired 2014 and the mystery of his action was increasingly decoded by elite T20 batters as the format matured")
p("Anil Kumble","Bowler (Spin)",80,20,80,False,31,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "45 IPL wickets at 6.58 economy — the most economical leg-spinner in IPL history with masterful flight and control",
  "Age and reduced turn limited impact but economy remained exceptional even in the later stages of his career")
p("Pragyan Ojha","Bowler (Spin)",82,20,82,False,26,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox",
  "89 IPL wickets at 7.37 economy across 90 matches as one of the best left-arm orthodox spinners in IPL history",
  "Bowling became predictable at the highest level in later years and batting minimal limiting franchise contribution")
p("Irfan Pathan","All-Rounder",83,72,83,False,25,"Left","Left","Lower-order Hitter","New-ball Bowler","Left-arm Fast",
  "80 IPL wickets and 1150 runs at 121 SR — a genuine left-arm pace all-rounder who could match-win in both disciplines",
  "Career declined sharply after 2012 as pace dropped and both disciplines faded simultaneously")
p("Dwayne Bravo","All-Rounder",87,74,87,True,30,"Right","Right","Lower-order Hitter","Death Overs","Right-arm Medium",
  "183 IPL wickets at 8.38 economy and 1560 runs — CSK's greatest death-over maestro with an unmatched slower-ball arsenal",
  "Economy in non-death phases is poor and batting at lower middle order was boom-or-bust throughout his career")
p("Zaheer Khan","Bowler (Fast)",83,18,83,False,30,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "102 IPL wickets at 7.59 economy as India's premier left-arm swing bowler creating exceptional powerplay threat",
  "Age and injuries reduced effectiveness in later seasons and batting provides minimal franchise value")
p("Praveen Kumar","Bowler (Fast)",81,18,81,False,26,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Swing",
  "90 IPL wickets at 7.73 economy as India's swing pioneer creating exceptional powerplay movement for RCB and SRH",
  "Not effective in death overs and batting minimal — a pure powerplay specialist throughout his IPL career")
p("RP Singh","Bowler (Fast)",81,18,81,False,24,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "90 IPL wickets at 7.90 economy as a reliable left-arm pace option for multiple franchises across many seasons",
  "Injury issues curtailed career early and slower pace in later years significantly reduced his effectiveness")
p("Mitchell Johnson","Bowler (Fast)",82,18,82,True,27,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "62 IPL wickets at 8.30 economy with exceptional left-arm pace creating genuine powerplay threat for MI and others",
  "Inconsistency was a career hallmark and expensive when line and length was off under T20 pressure")
p("Brett Lee","Bowler (Fast)",82,15,82,True,31,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "25 IPL wickets with extreme 150+ km/h pace as one of the fastest bowlers ever to grace early IPL seasons",
  "Short IPL career and the extreme pace occasionally created expensive economy when length was marginally off")
p("Sohail Tanvir","Bowler (Fast)",80,18,80,True,26,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "Purple Cap winner in the inaugural 2008 IPL season for RR — devastating in-swinging left-arm pace that surprised everyone",
  "Declined significantly after the first season as batters decoded his action and the mystery was removed")
p("Andrew Flintoff","All-Rounder",80,72,78,True,30,"Right","Right","Lower-order Hitter","New-ball Bowler","Right-arm Fast",
  "CSK all-rounder who brought genuine English fast bowling and destructive lower-order hitting to early IPL seasons",
  "Injury-ravaged career limited IPL appearances and he never played enough seasons to show his true potential")
p("James Faulkner","All-Rounder",82,74,82,True,23,"Left","Right","Lower-order Hitter","Death Overs","Right-arm Fast",
  "61 IPL wickets at 8.72 economy and 527 runs — a match-winning death-over all-rounder before injuries struck",
  "Later career was inconsistent compared to his early franchise peak and fell out of international favour")
p("Imran Tahir","Bowler (Spin)",83,15,83,True,30,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "82 IPL wickets at 7.76 economy and 1.39 wpm — among the best wpm ratios of any spinner in IPL history",
  "Age and diminishing fizz reduced effectiveness but economy remained competitive into his 40s")
p("Morne Morkel","Bowler (Fast)",83,15,83,True,28,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "77 IPL wickets at 7.69 economy — a tall South African quick generating exceptional bounce creating serious powerplay threat",
  "Economy was expensive on flat tracks but the genuine bounce from height made him a genuine wicket-taking threat")
p("Munaf Patel","Bowler (Fast)",78,15,78,False,26,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "74 IPL wickets with deceptive cutters and variations — reliable wicket-taker in favourable swing conditions",
  "Lack of genuine pace meant readable variations on flat tracks and economy suffered under pressure")
p("Shakib Al Hasan","All-Rounder",83,75,82,True,25,"Left","Left","Middle-over Rotator","Middle Overs","Left-arm Orthodox",
  "795 IPL runs at 124 SR and 63 wickets at 7.44 economy as a world-class Bangladesh all-rounder",
  "IPL career interrupted by bans and international commitments and never established as a franchise cornerstone")
p("Lakshmipathy Balaji","Bowler (Fast)",76,15,76,False,27,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "76 IPL wickets at 8.05 economy as a reliable domestic pacer who was a consistent contributor across many seasons",
  "Modest international pedigree and not a genuine wicket-taker on good batting surfaces")
p("Daniel Vettori","Bowler (Spin)",78,25,78,True,29,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Orthodox",
  "28 IPL wickets at 6.79 economy as one of the most economical spinners in IPL history with exceptional control for RCB",
  "Low wicket count reflects defensive role and batting was minimal contribution for the franchise")
p("Shaun Pollock","Bowler (Fast)",79,15,79,True,34,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "South African legend who brought outstanding new-ball accuracy and control to early IPL franchise cricket",
  "Career was winding down and genuine pace had declined making him a line-and-length specialist")
p("Dirk Nannes","Bowler (Fast)",76,12,76,True,34,"Right","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "28 IPL wickets at 7.29 economy as a dual-passport left-arm quick who was one of the fastest in early IPL seasons",
  "Short IPL career and batting minimal making him a pure specialist with limited all-round value")
p("Chris Morris","Bowler (Fast)",83,64,83,True,26,"Right","Right","Lower-order Hitter","Death Overs","Right-arm Fast",
  "96 IPL wickets at 8.03 economy and 618 runs at 155 SR — a match-winning all-rounder before the record RR auction",
  "The record auction purchase created unrealistic expectations at RR despite the genuine franchise talent")
p("Alfonso Thomas","Bowler (Fast)",76,15,76,True,31,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "Experienced South African seamer who contributed reliable economy and death-over wickets for multiple franchises",
  "Limited pace by international standards but dependable economy and death-over discipline were consistently good")
p("Ben Cutting","All-Rounder",78,72,75,True,28,"Right","Right","Lower-order Hitter","Death Overs","Right-arm Fast",
  "SRH and PBKS all-rounder who brought destructive lower-order hitting and right-arm variations to franchise cricket",
  "Limited first-class pedigree and occasional franchise player who never became a consistent cornerstone pick")
p("Doug Bollinger","Bowler (Fast)",77,15,77,True,30,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "37 IPL wickets at 7.22 economy as an accurate left-arm swing bowler who was highly economical for CSK in early seasons",
  "Career was in decline and accuracy was the primary weapon as pace had reduced significantly")
p("Nathan Coulter-Nile","Bowler (Fast)",78,55,78,True,28,"Right","Right","Lower-order Hitter","Death Overs","Right-arm Fast",
  "48 IPL wickets at 7.70 economy as an Australian seamer with good death-over variations for multiple franchises",
  "Fitness issues curtailed career potential and batting was limited to occasional lower-order cameos")
p("Ryan McLaren","All-Rounder",77,68,76,True,29,"Right","Right","Lower-order Hitter","Flexible","Right-arm Fast",
  "Solid KKR and CSK all-rounder contributing reliable seam bowling and useful lower-order batting across several seasons",
  "Consistency was adequate but never the match-winning impact player to guarantee a first-choice IPL spot")
p("Thisara Perera","All-Rounder",78,72,77,True,25,"Right","Right","Lower-order Hitter","Death Overs","Right-arm Fast",
  "Sri Lankan all-rounder with 31 wickets who contributed reliable death-over bowling and lower-order hitting",
  "Inconsistency meant he was never a franchise cornerstone despite genuine match-winning ability")
p("Paul Collingwood","All-Rounder",75,74,72,True,32,"Right","Right","Middle-over Rotator","Middle Overs","Right-arm Medium",
  "Solid CSK and KXIP all-rounder who brought tactical intelligence and dependable middle-order batting",
  "Never the most explosive in either discipline and more of a glue player than a match-winning influence")
p("Mitchell McClenaghan","Bowler (Fast)",78,12,78,True,28,"Left","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "71 IPL wickets at 8.49 economy as MI's reliable left-arm swing option contributing to their title-winning squads",
  "Economy of 8.49 and limited batting means a pure powerplay specialist with single-dimension franchise value")
p("R Bhatia","All-Rounder",76,68,73,False,29,"Right","Right","Middle-over Rotator","Middle Overs","Right-arm Medium",
  "71 IPL wickets at 7.41 economy and solid batting contributions — a dependable domestic all-rounder across many seasons",
  "Never a franchise cornerstone and more of a steady contributor without match-winning ceiling")
p("Agarkar","Bowler (Fast)",76,30,76,False,27,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "29 IPL wickets for MI bringing experienced new-ball threat in the early seasons using his domestic knowledge",
  "Career was in decline and the genuine swing of his peak years was not consistently available")

# ═══════════════════════════════════════════════════════════════════════════
# CURRENT ERA PLAYERS (2020s generation)
# ═══════════════════════════════════════════════════════════════════════════
p("Heinrich Klaasen","Wicketkeeper",94,94,10,True,31,"Right","None","Finisher","Part-time","None",
  "1704 IPL runs at 165 SR in just 50 matches including an extraordinary 2024 season — the most destructive modern finisher",
  "Can be vulnerable to quality wrist-spin early before settling but once set is virtually unstoppable")
p("Nicholas Pooran","Wicketkeeper",93,93,15,True,28,"Left","None","Finisher","Part-time","None",
  "2335 IPL runs at 165 SR across 91 matches — the most explosive left-hand finisher-keeper in the modern franchise era",
  "Rash early dismissals when not set and accurate tight bowling creates consistent dismissal patterns")
p("Travis Head","Batsman",93,93,55,True,28,"Left","Right","Aggressive Opener","Part-time","None",
  "1266 IPL runs at 168 SR in just 42 matches as SRH's extraordinary opener — the most destructive powerplay batter alive",
  "Vulnerable early against quality short-pitched movement before the eye is fully in")
p("Shreyas Iyer","Batsman",93,93,15,False,27,"Right","Right","Middle-over Rotator","Part-time","None",
  "3938 IPL runs at 135 SR as KKR captain who led team to the 2024 IPL title with prolific individual batting",
  "Well-documented vulnerability to short-pitched fast bowling is a persistent technical weakness")
p("Pat Cummins","All-Rounder",93,76,92,True,26,"Right","Right","Lower-order Hitter","Flexible","Right-arm Fast",
  "79 IPL wickets at 8.81 economy and 612 runs at 152 SR as KKR's 2024 championship-winning captain",
  "Availability limited to shorter stints due to Australia commitments and injury management")
p("Hardik Pandya","All-Rounder",93,89,86,False,26,"Right","Right","Finisher","Death Overs","Right-arm Fast",
  "Led GT to back-to-back IPL titles and won five total as the IPL's finest current franchise all-rounder",
  "Fitness concerns and bowling workload limits his consistency across full franchise campaigns")
p("Kagiso Rabada","Bowler (Fast)",91,18,91,True,24,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "126 IPL wickets at 8.70 economy and 1.43 wpm — among the best wpm of any fast bowler in the competition",
  "Economy of 8.70 is expensive but the wicket-taking rate is extraordinary for a pace bowler of his type")
p("Kuldeep Yadav","Bowler (Spin)",92,22,92,False,25,"Left","Left","Defensive Tailender","Middle Overs","Left-arm Wrist Spin",
  "105 IPL wickets making him India's most dangerous left-arm wrist-spinner with match-winning franchise quality",
  "Batting is a genuine liability and the wrist-spin can be expensive when length is marginally off")
p("Trent Boult","Bowler (Fast)",88,22,88,True,29,"Right","Left","Defensive Tailender","New-ball Bowler","Left-arm Fast",
  "144 IPL wickets at 8.48 economy as the premier left-arm swing bowler who drove RR's 2022 powerplay threat",
  "Opted out of central contract for IPL availability and economy can be expensive on flat subcontinental tracks")
p("Ravindra Jadeja","All-Rounder",91,80,89,False,29,"Left","Left","Middle-over Rotator","Middle Overs","Left-arm Orthodox",
  "173 IPL wickets at 7.68 economy and 3336 runs at 130 SR — the most complete all-rounder in IPL history",
  "Batting position varies causing output inconsistency and left-arm spin becomes predictable in some conditions")
p("Ravichandran Ashwin","Bowler (Spin)",87,55,87,False,29,"Right","Right","Lower-order Hitter","Middle Overs","Right-arm Offbreak",
  "187 IPL wickets at 7.20 economy across 217 matches as the most experienced T20 spinner in competition history",
  "Economy is moderate and effectiveness varies significantly depending on surface and opposition batters")
p("Axar Patel","All-Rounder",91,82,89,False,26,"Left","Left","Middle-over Rotator","Middle Overs","Left-arm Orthodox",
  "131 IPL wickets at 7.38 economy and 1919 runs at 133 SR as DC's outstanding two-way franchise player",
  "Left-arm spin can be targeted by aggressive right-handers who read his natural angle")
p("Mohammed Shami","Bowler (Fast)",88,16,88,False,29,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "137 IPL wickets at 8.55 economy — India's finest swing bowler with exceptional powerplay and variation quality",
  "Economy above 8.5 and recovery from ankle injury required extended rehabilitation limiting recent availability")
p("Arshdeep Singh","Bowler (Fast)",86,15,86,False,23,"Left","Left","Defensive Tailender","Death Overs","Left-arm Fast",
  "102 IPL wickets at 9.03 economy as PBKS's left-arm death-over specialist with excellent yorker execution",
  "Economy of 9.03 is expensive and consistency across full campaigns still developing")
p("Andre Russell","All-Rounder",91,88,87,True,30,"Right","Right","Finisher","Death Overs","Right-arm Fast",
  "2655 IPL runs at 174 SR and 123 wickets — the most dominant T20 all-rounder of the modern era for KKR",
  "Injury management challenges limiting availability and fitness across full franchise campaigns")
p("Glenn Maxwell","All-Rounder",89,86,83,True,29,"Right","Right","Aggressive Opener","Middle Overs","Right-arm Offbreak",
  "2820 IPL runs at 155 SR and 41 wickets as RCB's match-turning all-rounder with unique 360-degree ability",
  "Mental health battles led to mid-IPL breaks and the all-or-nothing style creates inherent inconsistency")
p("David Miller","Batsman",86,86,10,True,27,"Left","Right","Finisher","Part-time","None",
  "3156 IPL runs at 138 SR as GT's supreme left-hand finisher who excels in run chases under pressure",
  "Can struggle for timing in the first few balls creating vulnerability before reaching full flow")
p("Quinton de Kock","Wicketkeeper",87,87,10,True,27,"Left","Right","Aggressive Opener","Part-time","None",
  "3424 IPL runs at 135 SR across 116 matches as a technically outstanding left-hand opener-keeper for MI and LSG",
  "Can be reckless outside off-stump early in innings and the keeping is adequate without being elite")
p("Rishabh Pant","Wicketkeeper",86,86,12,False,24,"Left","None","Aggressive Opener","Part-time","None",
  "3670 IPL runs at 146 SR with extraordinary attacking intent — the most exciting young keeper-batter in Indian cricket",
  "Post-injury return means fitness needs monitoring and the reckless approach creates periodic cheap dismissals")
p("Ishan Kishan","Wicketkeeper",84,84,10,False,23,"Left","Right","Aggressive Opener","Part-time","None",
  "3211 IPL runs at 140 SR including 602 at 182 SR in 2026 — one of the most explosive left-hand openers in franchise cricket",
  "Inconsistency with periods of extended poor form and franchise loyalty questions affecting peak focus")
p("Shubman Gill","Batsman",91,91,10,False,22,"Right","Right","Anchor","Part-time","None",
  "4031 IPL runs at 139 SR across 117 matches as GT captain — technically gifted opener whose best seasons lie ahead",
  "Powerplay SR can be conservative when anchoring and the peak career production is still to come")
p("Ruturaj Gaikwad","Batsman",91,91,10,False,24,"Right","Right","Anchor","Part-time","None",
  "2565 IPL runs at 136 SR across 75 matches as CSK captain with prolific Orange Cap-level individual seasons",
  "Powerplay SR can be conservative and the full statistical peak of his career is still ahead")
p("Liam Livingstone","All-Rounder",87,83,78,True,26,"Right","Right","Aggressive Opener","Middle Overs","Leg-spin",
  "1065 IPL runs at 156 SR and leg-spin variations making him one of the most dangerous modern overseas T20 players",
  "Can be vulnerable early before finding rhythm and the big-hitting style creates inherent boom-or-bust inconsistency")
p("Sam Curran","All-Rounder",82,70,82,True,23,"Left","Left","Lower-order Hitter","Death Overs","Left-arm Fast",
  "59 IPL wickets and 997 runs at 136 SR — won the 2023 Purple Cap and is a match-winning left-arm death-over specialist",
  "The record auction purchase created enormous pressure and left-arm swing is less effective on flat subcontinental tracks")
p("Mitchell Starc","Bowler (Fast)",88,15,88,True,29,"Left","Left","Defensive Tailender","Death Overs","Left-arm Fast",
  "Returned to IPL 2024 as KKR's marquee signing contributing left-arm pace and swing to their title win",
  "High price tag created scrutiny and economy above 9 makes him expensive though wicket-taking is elite")
p("Anrich Nortje","Bowler (Fast)",87,12,87,True,27,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "61 IPL wickets with extreme 150+ km/h pace — one of the fastest bowlers in world cricket and a genuine death-over threat",
  "Economy can be expensive when line is marginally off and injuries are a persistent concern for availability")
p("Jofra Archer","Bowler (Fast)",88,20,88,True,26,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "66 IPL wickets at 7.94 economy for MI with extraordinary pace and skill — among the best IPL fast bowlers when fit",
  "Major injuries have severely limited IPL availability with multiple significant setbacks disrupting franchise career")
p("Phil Salt","Batsman",85,85,10,True,24,"Right","Right","Aggressive Opener","Part-time","None",
  "1195 IPL runs at 175 SR in 39 matches — one of the most explosive T20 openers in the world with extraordinary boundary rate",
  "High-risk style creates frequent early wickets and extreme SR will bring inconsistency over long campaigns")
p("Tim David","All-Rounder",87,86,50,True,25,"Right","Right","Finisher","Flexible","Right-arm Medium",
  "993 IPL runs at 178 SR in 49 matches — the most lethal finishing batter in the modern franchise era per ball faced",
  "Pure finisher role with primary batting value and can be vulnerable before finding his extraordinary hitting rhythm")
p("Marco Jansen","Bowler (Fast)",83,55,83,True,22,"Left","Left","Lower-order Hitter","Death Overs","Left-arm Fast",
  "39 IPL wickets with left-arm height and genuine pace plus useful lower-order hitting for SRH",
  "Economy of 9.28 is expensive and still developing consistency across longer franchise campaigns")
p("Matheesha Pathirana","Bowler (Fast)",84,15,84,True,20,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "47 IPL wickets with extraordinary slingy yorker action making him the most exciting young fast bowler in world cricket",
  "Young career and the sling action can occasionally be slightly inconsistent despite the incredible yorker accuracy")
p("Varun Chakravarthy","Bowler (Spin)",85,30,85,False,29,"Right","Right","Defensive Tailender","Middle Overs","Mystery Spin",
  "100 IPL wickets at 7.69 economy as KKR's mystery spinner who troubled the best T20 batters with unreadable variations",
  "Mystery action was reviewed under ICC scrutiny and batters who have faced him extensively have decoded him better")
p("Washington Sundar","All-Rounder",85,68,84,False,22,"Right","Right","Middle-over Rotator","New-ball Bowler","Right-arm Offbreak",
  "40 IPL wickets at 7.73 economy and 609 runs at 130 SR as a smart two-way player with excellent powerplay control",
  "Still developing and not yet establishing himself as a franchise cornerstone in sustained T20 campaigns")
p("Ravi Bishnoi","Bowler (Spin)",83,20,83,False,22,"Right","Right","Defensive Tailender","Middle Overs","Leg-spin",
  "81 IPL wickets at 8.28 economy as LSG's aggressive young leg-spinner developing into a key franchise asset",
  "Expensive economy and the wrist-spin is still developing consistency though wicket-taking ability is established")
p("Prasidh Krishna","Bowler (Fast)",83,11,83,False,25,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "85 IPL wickets at 8.82 economy and 1.21 wpm — one of the best wpm ratios of any Indian fast bowler in recent IPL",
  "Economy is expensive and needs to develop better control across different phases to become truly elite")
p("Avesh Khan","Bowler (Fast)",83,15,83,False,25,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "93 IPL wickets at 9.12 economy with raw pace and good yorker ability making him a key franchise pacer",
  "Very expensive economy at 9.12 and consistency across longer franchise campaigns remains a concern")
p("Mohammed Siraj","Bowler (Fast)",85,15,85,False,27,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "112 IPL wickets at 8.77 economy with exceptional quality and variety making him a top powerplay bowler",
  "Economy above 8.7 and death-over reliability is weaker than his powerplay effectiveness")
p("Lockie Ferguson","Bowler (Fast)",83,15,83,True,27,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "54 IPL wickets at 8.96 economy with exceptional 150+ km/h pace as GT and KKR's marquee overseas pacer",
  "Economy at 8.96 is expensive but the extreme pace generates genuine quality wicket-taking ability")
p("Deepak Chahar","Bowler (Fast)",82,55,82,False,27,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Swing",
  "89 IPL wickets with exceptional new-ball swing and hat-tricks making him CSK's most reliable powerplay bowler",
  "Batting provides occasional cameos but primary value is exclusively in the powerplay bowling phase")
p("Umesh Yadav","Bowler (Fast)",82,14,82,False,28,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "144 IPL wickets at 8.51 economy with genuine pace and occasional reverse swing across multiple franchises",
  "Economy above 8.5 and effectiveness declined in later career compared to his peak franchise seasons")
p("Mohit Sharma","Bowler (Fast)",82,15,82,False,28,"Right","Right","Defensive Tailender","Death Overs","Right-arm Variations",
  "134 IPL wickets as a death-over specialist winning the 2022 Purple Cap with excellent slower-ball execution",
  "Modest pace means the slower-ball variations become readable to batters who have faced him extensively")
p("Sandeep Sharma","Bowler (Fast)",81,12,81,False,23,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Swing",
  "151 IPL wickets at 8.13 economy with reliable powerplay swing as an experienced contributor across many franchises",
  "Not effective in death overs and batting minimal limiting him to a specialist powerplay-only role")
p("Dhawal Kulkarni","Bowler (Fast)",78,15,78,False,26,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Swing",
  "86 IPL wickets as a reliable domestic swing bowler contributing solid powerplay overs for multiple franchises",
  "Limited international pedigree and not penetrating at death making him a squad rather than marquee option")
p("Vinay Kumar","Bowler (Fast)",78,18,78,False,28,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "105 IPL wickets across 104 matches as a reliable domestic pacer who contributed consistently across many IPL seasons",
  "Modest pace and limited death-over impact made him a competent squad player rather than frontline bowler")
p("Manpreet Gony","Bowler (Fast)",74,15,74,False,30,"Right","Right","Defensive Tailender","Death Overs","Right-arm Fast",
  "37 IPL wickets for CSK in early seasons bringing pace and occasional reverse swing to death-over bowling",
  "Career faded after promising early seasons and sustained franchise quality never matched initial potential")
p("Abalaji","Bowler (Fast)",74,15,74,False,25,"Right","Right","Defensive Tailender","New-ball Bowler","Right-arm Fast",
  "76 IPL wickets at 8.05 economy as a reliable domestic pacer who contributed across multiple IPL seasons",
  "Lacked elite pace and limited death-over impact making him a competent rather than outstanding franchise bowler")

# ═══════════════════════════════════════════════════════════════════════════
# IMPORT ALL 336 CURRENT PLAYERS (from players.csv) - APPEND
# ═══════════════════════════════════════════════════════════════════════════

import csv, io, os

header = ["name","role","base_ovr","batting_ovr","bowling_ovr","is_overseas","age",
          "batting_hand","bowling_hand","batting_archetype","bowling_phase","bowling_type",
          "strengths","weaknesses"]

# Deduplicate: only keep first occurrence of each name
seen = set()
unique_rows = []
for row in rows:
    name = row[0]
    if name not in seen:
        seen.add(name)
        unique_rows.append(row)

print(f"Historical/all-time entries: {len(unique_rows)}")

# Load current players from players.csv and add if not already present
current_rows = []
with open('players.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        name = r['name'].strip()
        if name not in seen:
            seen.add(name)
            current_rows.append([
                name, r['role'], r['base_ovr'], r['batting_ovr'], r['bowling_ovr'],
                r['is_overseas'], r['age'], r['batting_hand'], r['bowling_hand'],
                r['batting_archetype'], r['bowling_phase'], r['bowling_type'],
                r['strengths'], r['weaknesses']
            ])

print(f"Current players added: {len(current_rows)}")
all_rows = unique_rows + current_rows
print(f"Total before sort: {len(all_rows)}")

# Sort by base_ovr descending (then batting_ovr, then bowling_ovr as tiebreakers)
all_rows.sort(key=lambda r: (-int(r[2]), -int(r[3]), -int(r[4])))

# Write CSV, quoting strengths/weaknesses
def write_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)

write_csv(all_rows, 'players_alltime.csv')
print(f"Written {len(all_rows)} players to players_alltime.csv")

# Verify OVR distribution
from collections import Counter
dist = Counter()
for r in all_rows:
    b = int(r[2])
    if b >= 95: dist['95-99'] += 1
    elif b >= 88: dist['88-94'] += 1
    elif b >= 80: dist['80-87'] += 1
    elif b >= 70: dist['70-79'] += 1
    else: dist['<70'] += 1
print("OVR distribution:", dict(dist))

# Check key comparisons
checks = [("Virat Kohli","Batsman"),("David Warner","Batsman"),("Jasprit Bumrah","Bowler (Fast)"),
          ("Lasith Malinga","Bowler (Fast)"),("Shubman Gill","Batsman"),("Chris Gayle","Batsman"),
          ("MS Dhoni","Wicketkeeper"),("Matthew Hayden","Batsman"),("Sachin Tendulkar","Batsman")]
name_map = {r[0]: r for r in all_rows}
for n, _ in checks:
    if n in name_map:
        r = name_map[n]
        print(f"{n}: base={r[2]} bat={r[3]} bowl={r[4]} age={r[6]}")
