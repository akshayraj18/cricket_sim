#!/usr/bin/env python3
"""One-time IP-safe rename: real IPL franchises + players -> fictional.

Single source of truth + audit record for the rename so every surface (engine
constants, players_data rosters, the two player CSVs, mobile theme, webapp,
tests) stays consistent.

- TEAM_MAP / ABBR_MAP: applied to all text files by `apply_team_renames`.
- PLAYER_MAP: the real->fictional player names. The CSV transform (names +
  generic IP-free bios) was produced externally and validated (ratings, ages,
  slots, and roles are byte-identical to the originals; no real player/team/
  nationality references remain). `apply_player_roster_renames` re-applies the
  same names to the 2026 roster lists in players_data.py.

Player names follow an initial-preserving convention (keep the first letters of
the first and last names; alter interior letters), so abbreviated scorecard
forms like "V. Kohli" stay familiar as "V. Kuhli" while the full name is
legally distinct. Users can rename anyone via the in-app roster editor.

Usage:
    python scripts/ip_safe_rename.py --check    # print mappings, change nothing
    python scripts/ip_safe_rename.py --apply    # re-apply team + roster renames
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "packages" / "sim_engine" / "src" / "cricket_sim_engine"

# --- Team mapping (real -> fictional). Keep the city; invent the rest. --------
TEAM_MAP = {
    "Chennai Super Kings": "Chennai Cholas",
    "Mumbai Indians": "Mumbai Mavericks",
    "Royal Challengers Bengaluru": "Bengaluru Bulls",
    "Kolkata Knight Riders": "Kolkata Knights",
    "Sunrisers Hyderabad": "Hyderabad Hawks",
    "Rajasthan Royals": "Rajasthan Raptors",
    "Delhi Capitals": "Delhi Dynamos",
    "Gujarat Titans": "Gujarat Gladiators",
    "Lucknow Super Giants": "Lucknow Lions",
    "Punjab Kings": "Punjab Panthers",
}

ABBR_MAP = {
    "CSK": "CHE", "MI": "MUM", "RCB": "BLR", "KKR": "KOL", "SRH": "HYD",
    "RR": "RAJ", "DC": "DEL", "GT": "GUJ", "LSG": "LKO", "PBKS": "PUN",
}

# Player name mapping actually applied to players.csv / players_alltime.csv
# (real -> fictional, IP-safe). Kept for audit; the CSV transform was done
# externally and validated (ratings/slots byte-identical, no real-name leaks).
PLAYER_MAP = {
    "AB de Villiers": "AB de Vylliers",
    "AM Ghazanfar": "AM Ghezanfar",
    "Aaron Finch": "Aeron Fynch",
    "Aarya Desai": "Aerya Disai",
    "Abdul Samad": "Abdol Semad",
    "Abhinandan Singh": "Abhynandan Syngh",
    "Abhinav Manohar": "Abhynav Menohar",
    "Abhinav Tejrana": "Abhynav Tijrana",
    "Abhishek Sharma": "Abhyshek Sherma",
    "Abishek Porel": "Abyshek Purel",
    "Adam Gilchrist": "Adem Gylchrist",
    "Adam Milne": "Adem Mylne",
    "Agit Agarkar": "Agyt Agerkar",
    "Aiden Markram": "Ayden Merkram",
    "Ajay Mandal": "Ajey Mendal",
    "Ajinkya Rahane": "Ajynkya Rehane",
    "Akash Deep": "Akesh Diep",
    "Akash Madhwal": "Akesh Medhwal",
    "Akash Singh": "Akesh Syngh",
    "Akeal Hosein": "Akial Husein",
    "Akshat Raghuwanshi": "Akshet Reghuwanshi",
    "Albie Morkel": "Albye Murkel",
    "Alfonso Thomas": "Alfunso Thumas",
    "Alzarri Joseph": "Alzerri Juseph",
    "Aman Khan": "Amen Khen",
    "Aman Rao": "Amen Reo",
    "Ambati Rayudu": "Ambeti Reyudu",
    "Amit Kumar": "Amyt Komar",
    "Amit Mishra": "Amyt Myshra",
    "Andre Russell": "Andri Rossell",
    "Andrew Flintoff": "Andriw Flyntoff",
    "Andrew Symonds": "Andriw Symunds",
    "Angkrish Raghuvanshi": "Angkrysh Reghuvanshi",
    "Aniket Verma": "Anyket Virma",
    "Anil Kumble": "Anyl Komble",
    "Anmolpreet Singh": "Anmulpreet Syngh",
    "Anrich Nortje": "Anrych Nurtje",
    "Anshul Kamboj": "Anshol Kemboj",
    "Anuj Rawat": "Anoj Rewat",
    "Anukul Roy": "Anokul Ruy",
    "Arjun Tendulkar": "Arjon Tindulkar",
    "Arshad Khan": "Arshed Khen",
    "Arshdeep Singh": "Arshdiep Syngh",
    "Arshin Kulkarni": "Arshyn Kolkarni",
    "Ashish Nehra": "Ashysh Nihra",
    "Ashok Sharma": "Ashuk Sherma",
    "Ashutosh Sharma": "Ashotosh Sherma",
    "Ashwani Kumar": "Ashweni Komar",
    "Atharva Ankolekar": "Atherva Ankulekar",
    "Atharva Taide": "Atherva Teide",
    "Auqib Dar": "Aoqib Der",
    "Auqib Nabi": "Aoqib Nebi",
    "Avesh Khan": "Avish Khen",
    "Axar Patel": "Axer Petel",
    "Ayush Badoni": "Ayosh Bedoni",
    "Ayush Mhatre": "Ayosh Mhetre",
    "Ayush Vartak": "Ayosh Vertak",
    "Azmatullah Omarzai": "Azmetullah Omerzai",
    "Ben Cutting": "Bin Cotting",
    "Ben Duckett": "Bin Dockett",
    "Ben Dwarshuis": "Bin Dwershuis",
    "Ben Stokes": "Bin Stukes",
    "Bhuvneshwar Kumar": "Bhovneshwar Komar",
    "Brad Hodge": "Bred Hudge",
    "Brendon McCullum": "Brindon McCollum",
    "Brett Lee": "Britt Lie",
    "Brijesh Sharma": "Bryjesh Sherma",
    "Brydon Carse": "Brydun Cerse",
    "Cameron Green": "Cemeron Grien",
    "Chama Milind": "Chema Mylind",
    "Chetan Sakariya": "Chitan Sekariya",
    "Chintal Gandhi": "Chyntal Gendhi",
    "Chris Gayle": "Chrys Geyle",
    "Chris Lynn": "Chrys Lyno",
    "Chris Morris": "Chrys Murris",
    "Connor Esterhuizen": "Cunnor Estirhuizen",
    "Cooper Connolly": "Cuoper Cunnolly",
    "Corbin Bosch": "Curbin Busch",
    "DJ Hussey": "DJ Hossey",
    "Daksh Kamra": "Deksh Kemra",
    "Dale Steyn": "Dele Stiyn",
    "Dan Lawrence": "Den Lewrence",
    "Daniel Lategan": "Deniel Letegan",
    "Daniel Vettori": "Deniel Vittori",
    "Danish Malewar": "Denish Melewar",
    "Daryl Mitchell": "Deryl Mytchell",
    "Dasun Shanaka": "Desun Shenaka",
    "David Miller": "Devid Myller",
    "David Warner": "Devid Werner",
    "Deepak Chahar": "Diepak Chehar",
    "Deepak Hooda": "Diepak Huoda",
    "Devdutt Padikkal": "Divdutt Pedikkal",
    "Devon Conway": "Divon Cunway",
    "Dewald Brevis": "Diwald Brivis",
    "Dhawal Kulkarni": "Dhewal Kolkarni",
    "Dhawan Rishi": "Dhewan Ryshi",
    "Dheeraj Kumar": "Dhieraj Komar",
    "Dhruv Jurel": "Dhrov Jorel",
    "Digvesh Rathi": "Dygvesh Rethi",
    "Dinesh Karthik": "Dynesh Kerthik",
    "Dirk Nannes": "Dyrk Nennes",
    "Donovan Ferreira": "Dunovan Firreira",
    "Doug Bollinger": "Duug Bullinger",
    "Dushmantha Chameera": "Doshmantha Chemeera",
    "Dwayne Bravo": "Dweyne Brevo",
    "Dwayne Smith": "Dweyne Smyth",
    "Eden Apple Tom": "Edin Appli Tum",
    "Eoin Morgan": "Euin Murgan",
    "Eshan Malinga": "Eshen Melinga",
    "Faf du Plessis": "Fef du Plissis",
    "Fazalhaq Farooqi": "Fezalhaq Ferooqi",
    "Finn Allen": "Fynn Allin",
    "Gautam Gambhir": "Geutam Gembhir",
    "Gerald Coetzee": "Girald Cuetzee",
    "Glenn Maxwell": "Glinn Mexwell",
    "Glenn Phillips": "Glinn Phyllips",
    "Graeme Smith": "Greeme Smyth",
    "Gurjapneet Singh": "Gorjapneet Syngh",
    "Gurnoor Brar": "Gornoor Brer",
    "Gus Atkinson": "Gos Atkynson",
    "Harbhajan Singh": "Herbhajan Syngh",
    "Hardik Pandya": "Herdik Pendya",
    "Harnoor Singh": "Hernoor Syngh",
    "Harpreet Brar": "Herpreet Brer",
    "Harsh Dubey": "Hersh Dobey",
    "Harshal Patel": "Hershal Petel",
    "Harshit Rana": "Hershit Rena",
    "Heinrich Klaasen": "Hiinrich Kleasen",
    "Himmat Singh": "Hymmat Syngh",
    "Imran Tahir": "Imren Tehir",
    "Irfan Pathan": "Irfen Pethan",
    "Irfan Umair": "Irfen Umeir",
    "Ishan Kishan": "Ishen Kyshan",
    "Ishant Sharma": "Ishent Sherma",
    "Izaz Sawariya": "Izez Sewariya",
    "JP Duminy": "JP Dominy",
    "Jack Edwards": "Jeck Edwerds",
    "Jacob Bethell": "Jecob Bithell",
    "Jacob Duffy": "Jecob Doffy",
    "Jacques Kallis": "Jecques Kellis",
    "Jake Fraser-McGurk": "Jeke Freser-McGork",
    "James Faulkner": "Jemes Feulkner",
    "Jamie Overton": "Jemie Ovirton",
    "Jamie Smith": "Jemie Smyth",
    "Jason Holder": "Jeson Hulder",
    "Jasprit Bumrah": "Jesprit Bomrah",
    "Jayant Yadav": "Jeyant Yedav",
    "Jaydev Unadkat": "Jeydev Unedkat",
    "Jesse Ryder": "Jisse Rydir",
    "Jhye Richardson": "Jhyi Rychardson",
    "Jikku Bright": "Jykku Bryght",
    "Jitesh Sharma": "Jytesh Sherma",
    "Jofra Archer": "Jufra Archir",
    "Jonny Bairstow": "Junny Beirstow",
    "Jordan Cox": "Jurdan Cux",
    "Jos Buttler": "Jus Bottler",
    "Josh Hazlewood": "Jush Hezlewood",
    "Josh Inglis": "Jush Inglys",
    "KC Cariappa": "KC Ceriappa",
    "KL Rahul": "KL Rehul",
    "KM Asif": "KM Asyf",
    "Kagiso Rabada": "Kegiso Rebada",
    "Kamindu Mendis": "Kemindu Mindis",
    "Kamlesh Nagarkoti": "Kemlesh Negarkoti",
    "Kane Williamson": "Kene Wylliamson",
    "Kanishk Chouhan": "Kenishk Chuuhan",
    "Karan Lal": "Keran Lel",
    "Karn Sharma": "Kern Sherma",
    "Kartik Sharma": "Kertik Sherma",
    "Kartik Tyagi": "Kertik Tyegi",
    "Karun Nair": "Kerun Neir",
    "Kevin Pietersen": "Kivin Pyetersen",
    "Khaleel Ahmed": "Kheleel Ahmid",
    "Kieron Pollard": "Kyeron Pullard",
    "Krains Fuletra": "Kreins Foletra",
    "Krunal Pandya": "Kronal Pendya",
    "Kuldeep Sen": "Koldeep Sin",
    "Kuldeep Yadav": "Koldeep Yedav",
    "Kumar Kartikeya": "Komar Kertikeya",
    "Kumar Kushagra": "Komar Koshagra",
    "Kumar Sangakkara": "Komar Sengakkara",
    "Kwena Maphaka": "Kwina Mephaka",
    "Kyle Jamieson": "Kyli Jemieson",
    "Lakshmipathy Balaji": "Lekshmipathy Belaji",
    "Lasith Malinga": "Lesith Melinga",
    "Lendl Simmons": "Lindl Symmons",
    "Lhuan-dre Pretorius": "Lhoan-dri Pritorius",
    "Liam Livingstone": "Lyam Lyvingstone",
    "Lockie Ferguson": "Luckie Firguson",
    "Luke Wood": "Loke Wuod",
    "Lungi Ngidi": "Longi Ngydi",
    "M Shahrukh Khan": "M Shehrukh Khen",
    "MS Dhoni": "MS Dhuni",
    "Macneil Noronha": "Mecneil Nuronha",
    "Madhav Tiwari": "Medhav Tywari",
    "Maheesh Theekshana": "Meheesh Thiekshana",
    "Mahela Jayawardene": "Mehela Jeyawardene",
    "Mahipal Lomror": "Mehipal Lumror",
    "Manan Vohra": "Menan Vuhra",
    "Manav Suthar": "Menav Sothar",
    "Mandeep Singh": "Mendeep Syngh",
    "Mangesh Yadav": "Mengesh Yedav",
    "Manimaran Siddharth": "Menimaran Syddharth",
    "Manisankar Murasingh": "Menisankar Morasingh",
    "Manish Pandey": "Menish Pendey",
    "Manoj Tiwary": "Menoj Tywary",
    "Marco Jansen": "Merco Jensen",
    "Marcus Stoinis": "Mercus Stuinis",
    "Matheesha Pathirana": "Metheesha Pethirana",
    "Matt Henry": "Mett Hinry",
    "Matthew Breetzke": "Metthew Brietzke",
    "Matthew Hayden": "Metthew Heyden",
    "Matthew Short": "Metthew Shurt",
    "Mayank Dagar": "Meyank Degar",
    "Mayank Markande": "Meyank Merkande",
    "Mayank Rawat": "Meyank Rewat",
    "Mayank Yadav": "Meyank Yedav",
    "Michael Bracewell": "Mychael Brecewell",
    "Michael Hussey": "Mychael Hossey",
    "Mitchell Johnson": "Mytchell Juhnson",
    "Mitchell Marsh": "Mytchell Mersh",
    "Mitchell McClenaghan": "Mytchell McClinaghan",
    "Mitchell Owen": "Mytchell Owin",
    "Mitchell Santner": "Mytchell Sentner",
    "Mitchell Starc": "Mytchell Sterc",
    "Moeen Ali": "Mueen Aly",
    "Mohammad Nabi": "Muhammad Nebi",
    "Mohammed Shami": "Muhammed Shemi",
    "Mohammed Siraj": "Muhammed Syraj",
    "Mohd Izhar": "Muhd Izher",
    "Mohit Rathee": "Muhit Rethee",
    "Mohit Sharma": "Muhit Sherma",
    "Mohsin Khan": "Muhsin Khen",
    "Money Grewal": "Muney Griwal",
    "Morne Morkel": "Murne Murkel",
    "Mujeeb Ur Rahman": "Mojeeb Ur Rehman",
    "Mukesh Choudhary": "Mokesh Chuudhary",
    "Mukesh Kumar": "Mokesh Komar",
    "Mukul Choudhary": "Mokul Chuudhary",
    "Munaf Patel": "Monaf Petel",
    "Murali Vijay": "Morali Vyjay",
    "Murugan Ashwin": "Morugan Ashwyn",
    "Musheer Khan": "Mosheer Khen",
    "Mustafizur Rahman": "Mostafizur Rehman",
    "Muttiah Muralitharan": "Mottiah Moralitharan",
    "Naman Dhir": "Neman Dhyr",
    "Naman Ojha": "Neman Ojhe",
    "Naman Tiwari": "Neman Tywari",
    "Nandre Burger": "Nendre Borger",
    "Nathan Coulter-Nile": "Nethan Cuulter-Nyle",
    "Nathan Ellis": "Nethan Ellys",
    "Nathan Smith": "Nethan Smyth",
    "Nehal Wadhera": "Nihal Wedhera",
    "Nicholas Pooran": "Nycholas Puoran",
    "Nishant Sindhu": "Nyshant Syndhu",
    "Nitish Kumar Reddy": "Nytish Komar Riddy",
    "Nitish Rana": "Nytish Rena",
    "Noor Ahmad": "Nuor Ahmed",
    "Nuwan Thushara": "Nowan Thoshara",
    "Onkar Tarmale": "Onker Termale",
    "Parthiv Patel": "Perthiv Petel",
    "Pat Cummins": "Pet Commins",
    "Pathum Nissanka": "Pethum Nyssanka",
    "Paul Collingwood": "Peul Cullingwood",
    "Phil Salt": "Phyl Selt",
    "Piyush Chawla": "Pyyush Chewla",
    "Prabhsimran Singh": "Prebhsimran Syngh",
    "Praful Hinge": "Preful Hynge",
    "Pragyan Ojha": "Pregyan Ojhe",
    "Prashant Solanki": "Preshant Sulanki",
    "Prashant Veer": "Preshant Vier",
    "Prasidh Krishna": "Presidh Kryshna",
    "Praveen Dubey": "Preveen Dobey",
    "Praveen Kumar": "Preveen Komar",
    "Prince Yadav": "Prynce Yedav",
    "Prithvi Raj": "Prythvi Rej",
    "Prithvi Shaw": "Prythvi Shew",
    "Priyansh Arya": "Pryyansh Arye",
    "Pyla Avinash": "Pyle Avynash",
    "Quinton de Kock": "Qointon de Kuck",
    "R Bhatia": "R Bhetia",
    "RP Singh": "RP Syngh",
    "RS Ambrish": "RS Ambrysh",
    "Rachin Ravindra": "Rechin Revindra",
    "Raghu Sharma": "Reghu Sherma",
    "Rahmanullah Gurbaz": "Rehmanullah Gorbaz",
    "Rahul Chahar": "Rehul Chehar",
    "Rahul Dravid": "Rehul Drevid",
    "Rahul Tewatia": "Rehul Tiwatia",
    "Rahul Tripathi": "Rehul Trypathi",
    "Raj Bawa": "Rej Bewa",
    "Raj Limbani": "Rej Lymbani",
    "Rajat Patidar": "Rejat Petidar",
    "Rajvardhan Hangargekar": "Rejvardhan Hengargekar",
    "Ramakrishna Ghosh": "Remakrishna Ghush",
    "Ramandeep Singh": "Remandeep Syngh",
    "Rashid Khan": "Reshid Khen",
    "Rasikh Salam": "Resikh Selam",
    "Ravi Bishnoi": "Revi Byshnoi",
    "Ravi Singh": "Revi Syngh",
    "Ravichandran Ashwin": "Revichandran Ashwyn",
    "Ravichandran Smaran": "Revichandran Smeran",
    "Ravindra Jadeja": "Revindra Jedeja",
    "Richard Gleeson": "Rychard Glieson",
    "Ricky Ponting": "Rycky Punting",
    "Riley Meredith": "Ryley Miredith",
    "Rinku Singh": "Rynku Syngh",
    "Rishabh Pant": "Ryshabh Pent",
    "Ritik Tada": "Rytik Teda",
    "Riyan Parag": "Ryyan Perag",
    "Robin Minz": "Rubin Mynz",
    "Robin Uthappa": "Rubin Utheppa",
    "Rohit Sharma": "Ruhit Sherma",
    "Romario Shepherd": "Rumario Shipherd",
    "Ross Taylor": "Russ Teylor",
    "Rovman Powell": "Ruvman Puwell",
    "Ruchit Ahir": "Rochit Ahyr",
    "Ruturaj Gaikwad": "Roturaj Geikwad",
    "Ryan McLaren": "Ryen McLeren",
    "Ryan Rickelton": "Ryen Ryckelton",
    "S Badrinath": "S Bedrinath",
    "Sachin Tendulkar": "Sechin Tindulkar",
    "Sahil Parakh": "Sehil Perakh",
    "Sai Kishore": "Sei Kyshore",
    "Sai Sudharsan": "Sei Sodharsan",
    "Sakib Hussain": "Sekib Hossain",
    "Salil Arora": "Selil Arura",
    "Salman Nizar": "Selman Nyzar",
    "Sam Curran": "Sem Corran",
    "Sameer Rizvi": "Semeer Ryzvi",
    "Sandeep Sharma": "Sendeep Sherma",
    "Sanju Samson": "Senju Semson",
    "Sanvir Singh": "Senvir Syngh",
    "Sarfaraz Khan": "Serfaraz Khen",
    "Sarthak Ranjan": "Serthak Renjan",
    "Satvik Deswal": "Setvik Diswal",
    "Sean Abbott": "Sian Abbutt",
    "Sediqullah Atal": "Sidiqullah Atel",
    "Shahbaz Ahmed": "Shehbaz Ahmid",
    "Shahbaz Nadeem": "Shehbaz Nedeem",
    "Shakib Al Hasan": "Shekib Al Hesan",
    "Shane Warne": "Shene Werne",
    "Shane Watson": "Shene Wetson",
    "Shardul Thakur": "Sherdul Thekur",
    "Shashank Singh": "Sheshank Syngh",
    "Shaun Marsh": "Sheun Mersh",
    "Shaun Pollock": "Sheun Pullock",
    "Sherfane Rutherford": "Shirfane Rotherford",
    "Shikhar Dhawan": "Shykhar Dhewan",
    "Shimron Hetmyer": "Shymron Hitmyer",
    "Shivam Dube": "Shyvam Dobe",
    "Shivam Mavi": "Shyvam Mevi",
    "Shivam Shukla": "Shyvam Shokla",
    "Shivang Kumar": "Shyvang Komar",
    "Shreyas Gopal": "Shriyas Gupal",
    "Shreyas Iyer": "Shriyas Iyir",
    "Shubham Dubey": "Shobham Dobey",
    "Shubman Gill": "Shobman Gyll",
    "Siddarth Yadav": "Syddarth Yedav",
    "Siddharth Kaul": "Syddharth Keul",
    "Simarjeet Singh": "Symarjeet Syngh",
    "Sohail Tanvir": "Suhail Tenvir",
    "Sourav Ganguly": "Suurav Genguly",
    "Spencer Johnson": "Spincer Juhnson",
    "Srikar Bharat": "Srykar Bherat",
    "Steve Smith": "Stive Smyth",
    "Sunil Narine": "Sonil Nerine",
    "Suresh Raina": "Soresh Reina",
    "Suryakumar Yadav": "Soryakumar Yedav",
    "Suryansh Shedge": "Soryansh Shidge",
    "Sushant Mishra": "Soshant Myshra",
    "Suyash Sharma": "Soyash Sherma",
    "Swapnil Singh": "Swepnil Syngh",
    "Swastik Chikara": "Swestik Chykara",
    "T Natarajan": "T Netarajan",
    "Tanay Thyagarajan": "Tenay Thyegarajan",
    "Tanush Kotian": "Tenush Kutian",
    "Taskin Ahmed": "Teskin Ahmid",
    "Tejas Baroka": "Tijas Beroka",
    "Tejasvi Dahiya": "Tijasvi Dehiya",
    "Thisara Perera": "Thysara Pirera",
    "Tilak Varma": "Tylak Verma",
    "Tillakaratne Dilshan": "Tyllakaratne Dylshan",
    "Tim David": "Tym Devid",
    "Tim Seifert": "Tym Siifert",
    "Tom Banton": "Tum Benton",
    "Travis Head": "Trevis Hiad",
    "Trent Boult": "Trint Buult",
    "Tripurana Vijay": "Trypurana Vyjay",
    "Tristan Stubbs": "Trystan Stobbs",
    "Tushar Deshpande": "Toshar Dishpande",
    "Tushar Raheja": "Toshar Reheja",
    "Umesh Yadav": "Umish Yedav",
    "Umran Malik": "Umren Melik",
    "Urvil Patel": "Urvyl Petel",
    "Utkarsh Singh": "Utkersh Syngh",
    "VVS Laxman": "VVS Lexman",
    "Vaibhav Arora": "Veibhav Arura",
    "Vaibhav Sooryavanshi": "Veibhav Suoryavanshi",
    "Vansh Bedi": "Vensh Bidi",
    "Varun Aaron": "Verun Aeron",
    "Varun Chakravarthy": "Verun Chekravarthy",
    "Venkatesh Iyer": "Vinkatesh Iyir",
    "Vicky Ostwal": "Vycky Ostwel",
    "Vignesh Puthur": "Vygnesh Pothur",
    "Vihaan Malhotra": "Vyhaan Melhotra",
    "Vijay Shankar": "Vyjay Shenkar",
    "Vijaykumar Vyshak": "Vyjaykumar Vyshek",
    "Vinay Kumar": "Vynay Komar",
    "Vipraj Nigam": "Vypraj Nygam",
    "Virat Kohli": "Vyrat Kuhli",
    "Virender Sehwag": "Vyrender Sihwag",
    "Vishal Nishad": "Vyshal Nyshad",
    "Vishnu Vinod": "Vyshnu Vynod",
    "Wahidullah Zadran": "Wehidullah Zedran",
    "Wanindu Hasaranga": "Wenindu Hesaranga",
    "Waqar Salamkheil": "Weqar Selamkheil",
    "Washington Sundar": "Weshington Sondar",
    "Wiaan Mulder": "Wyaan Molder",
    "Will Jacks": "Wyll Jecks",
    "Will Sutherland": "Wyll Sotherland",
    "Wriddhiman Saha": "Wryddhiman Seha",
    "Xavier Bartlett": "Xevier Bertlett",
    "Yash Dayal": "Yesh Deyal",
    "Yash Dhull": "Yesh Dholl",
    "Yash Raj Punja": "Yesh Rej Ponja",
    "Yash Thakur": "Yesh Thekur",
    "Yashasvi Jaiswal": "Yeshasvi Jeiswal",
    "Yudhvir Singh": "Yodhvir Syngh",
    "Yusuf Pathan": "Yosuf Pethan",
    "Yuvraj Singh": "Yovraj Syngh",
    "Yuzvendra Chahal": "Yozvendra Chehal",
    "Zaheer Khan": "Zeheer Khen",
    "Zak Foulkes": "Zek Fuulkes",
    "Zeeshan Ansari": "Zieshan Anseri",
    # --- Phase 8 additions: the all-time ODI/Test/T20I pools and the current
    # national squads, which shipped with real names. Derived via
    # derive_ip_safe_name() and recorded here so the mapping is auditable
    # and stable across runs.
    "Aamer Jamal": "Aemer Jemal",
    "Aaron Hardie": "Aeron Herdie",
    "Abdul Qadir": "Abdol Qedir",
    "Abdullah Shafique": "Abdollah Shefique",
    "Abrar Ahmed": "Abrer Ahmid",
    "Adam Zampa": "Adem Zempa",
    "Adil Rashid": "Adyl Reshid",
    "Afif Hossain": "Afyf Hussain",
    "Ahmad Raza": "Ahmed Reza",
    "Ahmed Daniyal": "Ahmid Deniyal",
    "Ahmed Shahzad": "Ahmid Shehzad",
    "Ajantha Mendis": "Ajentha Mindis",
    "Ajay Jadeja": "Ajey Jedeja",
    "Alastair Cook": "Alestair Cuok",
    "Alec Bedser": "Alic Bidser",
    "Alec Stewart": "Alic Stiwart",
    "Alex Carey": "Alix Cerey",
    "Alex Hales": "Alix Heles",
    "Alick Athanaze": "Alyck Athenaze",
    "Allan Border": "Allen Burder",
    "Allan Donald": "Allen Dunald",
    "Alvin Kallicharran": "Alvyn Kellicharran",
    "Amir Hamza": "Amyr Hemza",
    "Amir Jangoo": "Amyr Jengoo",
    "Andre Botha": "Andri Butha",
    "Andre Fletcher": "Andri Flitcher",
    "Andrew Balbirnie": "Andriw Belbirnie",
    "Andrew Strauss": "Andriw Streuss",
    "Andy Bichel": "Andy Bychel",
    "Andy Flower": "Andy Fluwer",
    "Andy Roberts": "Andy Ruberts",
    "Angelo Mathews": "Angilo Methews",
    "Angelo Perera": "Angilo Pirera",
    "Arafat Minhas": "Arefat Mynhas",
    "Aravinda de Silva": "Arevinda de Sylva",
    "Arjuna Ranatunga": "Arjona Renatunga",
    "Arthur Morris": "Arthor Murris",
    "Aryan Dutt": "Aryen Dott",
    "Asad Shafiq": "Ased Shefiq",
    "Asanka Gurusinha": "Asenka Gorusinha",
    "Asif Iqbal": "Asyf Iqbel",
    "Asitha Fernando": "Asytha Firnando",
    "Babar Azam": "Bebar Azem",
    "Bahir Shah": "Behir Sheh",
    "Barry Richards": "Berry Rychards",
    "Bas de Leede": "Bes de Liede",
    "Beau Webster": "Biau Wibster",
    "Ben McDermott": "Bin McDirmott",
    "Ben Sears": "Bin Siars",
    "Bert Sutcliffe": "Birt Sotcliffe",
    "Bhagwath Chandrasekhar": "Bhegwath Chendrasekhar",
    "Bill Lawry": "Byll Lewry",
    "Bill O'Reilly": "Byll O'Riilly",
    "Bill Ponsford": "Byll Punsford",
    "Bishan Bedi": "Byshan Bidi",
    "Blessing Muzarabani": "Blissing Mozarabani",
    "Bob Simpson": "Bub Sympson",
    "Bob Willis": "Bub Wyllis",
    "Brad Haddin": "Bred Heddin",
    "Brad Hogg": "Bred Hugg",
    "Brandon King": "Brendon Kyng",
    "Brendan Doggett": "Brindan Duggett",
    "Brendon Taylor": "Brindon Teylor",
    "Brian Lara": "Bryan Lera",
    "Brian McMillan": "Bryan McMyllan",
    "Brian Statham": "Bryan Stetham",
    "Campbell Cowan": "Cempbell Cuwan",
    "Carl Hooper": "Cerl Huoper",
    "Chamika Karunaratne": "Chemika Kerunaratne",
    "Chaminda Vaas": "Cheminda Veas",
    "Charith Asalanka": "Cherith Aselanka",
    "Charlie Griffith": "Cherlie Gryffith",
    "Chris Cairns": "Chrys Ceirns",
    "Chris Harris": "Chrys Herris",
    "Chris Jordan": "Chrys Jurdan",
    "Chris Lewis": "Chrys Liwis",
    "Chris Woakes": "Chrys Wuakes",
    "Clarrie Grimmett": "Clerrie Grymmett",
    "Clive Lloyd": "Clyve Lluyd",
    "Clive Rice": "Clyve Ryce",
    "Clyde Walcott": "Clydi Welcott",
    "Colin Cowdrey": "Culin Cuwdrey",
    "Colin Croft": "Culin Cruft",
    "Colin McDonald": "Culin McDunald",
    "Colin Munro": "Culin Monro",
    "Collis King": "Cullis Kyng",
    "Conrad Hunte": "Cunrad Honte",
    "Courtney Walsh": "Cuurtney Welsh",
    "Craig Ervine": "Creig Ervyne",
    "Curtly Ambrose": "Cortly Ambruse",
    "Damien Fleming": "Demien Fliming",
    "Damien Martyn": "Demien Mertyn",
    "Dan Christian": "Den Chrystian",
    "Danish Kaneria": "Denish Keneria",
    "Darren Gough": "Derren Guugh",
    "Darwish Rasooli": "Derwish Resooli",
    "Daryll Cullinan": "Deryll Collinan",
    "David Bedingham": "Devid Bidingham",
    "David Boon": "Devid Buon",
    "David Gower": "Devid Guwer",
    "David Wiese": "Devid Wyese",
    "David Willey": "Devid Wylley",
    "Dawid Malan": "Dewid Melan",
    "Dawlat Zadran": "Dewlat Zedran",
    "Dean Elgar": "Dian Elger",
    "Denis Compton": "Dinis Cumpton",
    "Dennis Lillee": "Dinnis Lyllee",
    "Derek Underwood": "Direk Undirwood",
    "Dermot Reeve": "Dirmot Rieve",
    "Desmond Haynes": "Dismond Heynes",
    "Devon Thomas": "Divon Thumas",
    "Dhananjaya de Silva": "Dhenanjaya de Sylva",
    "Dilhara Fernando": "Dylhara Firnando",
    "Dilip Vengsarkar": "Dylip Vingsarkar",
    "Dilruwan Perera": "Dylruwan Pirera",
    "Dinesh Chandimal": "Dynesh Chendimal",
    "Don Bradman": "Dun Bredman",
    "Doug Walters": "Duug Welters",
    "Dunith Wellalage": "Donith Willalage",
    "Dushan Hemantha": "Doshan Himantha",
    "Elton Chigumbura": "Eltun Chygumbura",
    "Everton Weekes": "Evirton Wiekes",
    "Evin Lewis": "Evyn Liwis",
    "Fabian Allen": "Febian Allin",
    "Faheem Ashraf": "Feheem Ashref",
    "Fakhar Zaman": "Fekhar Zeman",
    "Farokh Engineer": "Ferokh Engyneer",
    "Fidel Edwards": "Fydel Edwerds",
    "Frank Worrell": "Frenk Wurrell",
    "Franklyn Rose": "Frenklyn Ruse",
    "Fred Trueman": "Frid Troeman",
    "Garfield Sobers": "Gerfield Subers",
    "Gary Kirsten": "Gery Kyrsten",
    "Gary Wilson": "Gery Wylson",
    "Geoff Boycott": "Gioff Buycott",
    "Geoff Howarth": "Gioff Huwarth",
    "George Dockrell": "Giorge Duckrell",
    "George Headley": "Giorge Hiadley",
    "George Linde": "Giorge Lynde",
    "Gerhard Erasmus": "Girhard Eresmus",
    "Glenn McGrath": "Glinn McGreth",
    "Glenn Turner": "Glinn Torner",
    "Gordon Greenidge": "Gurdon Grienidge",
    "Graeme Cremer": "Greeme Crimer",
    "Graeme Hick": "Greeme Hyck",
    "Graeme Pollock": "Greeme Pullock",
    "Graeme Swann": "Greeme Swenn",
    "Graham Gooch": "Greham Guoch",
    "Graham Thorpe": "Greham Thurpe",
    "Greg Chappell": "Grig Cheppell",
    "Gudakesh Motie": "Godakesh Mutie",
    "Gulbadin Naib": "Golbadin Neib",
    "Gundappa Viswanath": "Gondappa Vyswanath",
    "Hanif Mohammad": "Henif Muhammad",
    "Hansie Cronje": "Hensie Crunje",
    "Haris Rauf": "Heris Reuf",
    "Harold Larwood": "Herold Lerwood",
    "Harry Brook": "Herry Bruok",
    "Harry Tector": "Herry Tictor",
    "Hasan Ali": "Hesan Aly",
    "Hasan Mahmud": "Hesan Mehmud",
    "Hashan Tillakaratne": "Heshan Tyllakaratne",
    "Hashim Amla": "Heshim Amle",
    "Hashmatullah Shahidi": "Heshmatullah Shehidi",
    "Hazratullah Zazai": "Hezratullah Zezai",
    "Heath Streak": "Hiath Striak",
    "Henry Nicholls": "Hinry Nycholls",
    "Herschelle Gibbs": "Hirschelle Gybbs",
    "Ian Botham": "Ien Butham",
    "Ian Chappell": "Ien Cheppell",
    "Ian Harvey": "Ien Hervey",
    "Ian Healy": "Ien Hialy",
    "Ian Smith": "Ien Smyth",
    "Ibrahim Zadran": "Ibrehim Zedran",
    "Iftikhar Ahmed": "Iftykhar Ahmid",
    "Ikram Ali Khil": "Ikrem Aly Khyl",
    "Imad Wasim": "Imed Wesim",
    "Imam-ul-Haq": "Imem-ul-Heq",
    "Imran Khan": "Imren Khen",
    "Innocent Kaia": "Innucent Keia",
    "Inzamam-ul-Haq": "Inzemam-ul-Heq",
    "Irfan Khan Niazi": "Irfen Khen Nyazi",
    "Ish Sodhi": "Ish Sudhi",
    "Isitha Wijesundara": "Isytha Wyjesundara",
    "Jacob Oram": "Jecob Orem",
    "Jake Weatherald": "Jeke Wiatherald",
    "Jaker Ali": "Jeker Aly",
    "James Anderson": "Jemes Andirson",
    "James Rew": "Jemes Riw",
    "Jan Nicol Loftie-Eaton": "Jen Nycol Luftie-Eeton",
    "Janith Liyanage": "Jenith Lyyanage",
    "Jason Gillespie": "Jeson Gyllespie",
    "Jason Roy": "Jeson Ruy",
    "Jatinder Singh": "Jetinder Syngh",
    "Javagal Srinath": "Jevagal Srynath",
    "Javed Miandad": "Jeved Myandad",
    "Jayden Seales": "Jeyden Siales",
    "Jeff Thomson": "Jiff Thumson",
    "Jeffrey Dujon": "Jiffrey Dojon",
    "Jeffrey Vandersay": "Jiffrey Vendersay",
    "Jeremy Coney": "Jiremy Cuney",
    "Jerome Taylor": "Jirome Teylor",
    "Jim Laker": "Jym Leker",
    "Jimmy Adams": "Jymmy Adems",
    "Joe Root": "Jue Ruot",
    "Joel Garner": "Juel Gerner",
    "John Campbell": "Juhn Cempbell",
    "John Reid": "Juhn Riid",
    "John Wright": "Juhn Wryght",
    "Johnson Charles": "Juhnson Cherles",
    "Jonathan Trott": "Junathan Trutt",
    "Jonty Rhodes": "Junty Rhudes",
    "Jordan Hermann": "Jurdan Hirmann",
    "Josh Tongue": "Jush Tungue",
    "Justin Greaves": "Jostin Griaves",
    "Justin Kemp": "Jostin Kimp",
    "Justin Langer": "Jostin Lenger",
    "Kamil Mishara": "Kemil Myshara",
    "Kamran Ghulam": "Kemran Gholam",
    "Kapil Dev": "Kepil Div",
    "Karim Janat": "Kerim Jenat",
    "Keacy Carty": "Kiacy Certy",
    "Keith Miller": "Kiith Myller",
    "Ken Barrington": "Kin Berrington",
    "Keshav Maharaj": "Kishav Meharaj",
    "Kevin O'Brien": "Kivin O'Bryen",
    "Kevin Sinclair": "Kivin Synclair",
    "Khaled Ahmed": "Kheled Ahmid",
    "Khawaja Mohammad Nafay": "Khewaja Muhammad Nefay",
    "Khurram Shahzad": "Khorram Shehzad",
    "Khushdil Shah": "Khoshdil Sheh",
    "Kim Hughes": "Kym Hoghes",
    "Kraigg Brathwaite": "Kreigg Brethwaite",
    "Kusal Mendis": "Kosal Mindis",
    "Kusal Perera": "Kosal Pirera",
    "Kyle Verreynne": "Kyli Virreynne",
    "Lahiru Kumara": "Lehiru Komara",
    "Lahiru Udara": "Lehiru Udera",
    "Lance Gibbs": "Lence Gybbs",
    "Lance Klusener": "Lence Klosener",
    "Lawrence Rowe": "Lewrence Ruwe",
    "Len Hutton": "Lin Hotton",
    "Liam Dawson": "Lyam Dewson",
    "Liton Das": "Lyton Des",
    "Litton Das": "Lytton Des",
    "Lokesh Rahul": "Lukesh Rehul",
    "Lorcan Tucker": "Lurcan Tocker",
    "Luke Wright": "Loke Wryght",
    "Mahmudullah": "Mehmudullah",
    "Majid Khan": "Mejid Khen",
    "Makhaya Ntini": "Mekhaya Ntyni",
    "Malcolm Marshall": "Melcolm Mershall",
    "Marcus Harris": "Mercus Herris",
    "Marcus Trescothick": "Mercus Triscothick",
    "Mark Adair": "Merk Adeir",
    "Mark Chapman": "Merk Chepman",
    "Mark Ramprakash": "Merk Remprakash",
    "Mark Taylor": "Merk Teylor",
    "Mark Wood": "Merk Wuod",
    "Marlon Samuels": "Merlon Semuels",
    "Marnus Labuschagne": "Mernus Lebuschagne",
    "Marquino Mindley": "Merquino Myndley",
    "Martin Crowe": "Mertin Cruwe",
    "Martin Donnelly": "Mertin Dunnelly",
    "Martin Guptill": "Mertin Goptill",
    "Matt Short": "Mett Shurt",
    "Matthew Forde": "Metthew Furde",
    "Matthew Kuhnemann": "Metthew Kohnemann",
    "Matthew Potts": "Metthew Putts",
    "Matthew Renshaw": "Metthew Rinshaw",
    "Max O'Dowd": "Mex O'Duwd",
    "Mehidy Hasan Miraz": "Mihidy Hesan Myraz",
    "Michael Bevan": "Mychael Bivan",
    "Michael Holding": "Mychael Hulding",
    "Michael Klinger": "Mychael Klynger",
    "Mick Lewis": "Myck Liwis",
    "Mike Atherton": "Myke Athirton",
    "Mike Hussey": "Myke Hossey",
    "Mikyle Louis": "Mykyle Luuis",
    "Milan Rathnayake": "Mylan Rethnayake",
    "Milind Kumar": "Mylind Komar",
    "Misbah-ul-Haq": "Mysbah-ul-Heq",
    "Mohamed Ayyub": "Muhamed Ayyob",
    "Mohammad Azharuddin": "Muhammad Azheruddin",
    "Mohammad Hafeez": "Muhammad Hefeez",
    "Mohammad Nawaz": "Muhammad Newaz",
    "Mohammad Rizwan": "Muhammad Ryzwan",
    "Mohammad Saleem Safi": "Muhammad Seleem Sefi",
    "Mohammad Wasim Jr": "Muhammad Wesim Jr",
    "Mohammad Yousuf": "Muhammad Yuusuf",
    "Mohammed Asif": "Muhammed Asyf",
    "Mominul Haque": "Muminul Heque",
    "Muhammad Waseem": "Mohammad Weseem",
    "Mushfiqur Rahim": "Moshfiqur Rehim",
    "Mushtaq Ahmed": "Moshtaq Ahmid",
    "Mushtaq Mohammad": "Moshtaq Muhammad",
    "Najibullah Zadran": "Nejibullah Zedran",
    "Najmul Hossain Shanto": "Nejmul Hussain Shento",
    "Nantie Hayward": "Nentie Heyward",
    "Naseem Shah": "Neseem Sheh",
    "Nasser Hussain": "Nesser Hossain",
    "Nasum Ahmed": "Nesum Ahmid",
    "Nathan Lyon": "Nethan Lyun",
    "Naveen-ul-Haq": "Neveen-ul-Heq",
    "Nayeem Hasan": "Neyeem Hesan",
    "Neil Harvey": "Niil Hervey",
    "Neil McKenzie": "Niil McKinzie",
    "Nick Knight": "Nyck Knyght",
    "Nishan Madushka": "Nyshan Medushka",
    "Nkrumah Bonner": "Nkromah Bunner",
    "Noman Ali": "Numan Aly",
    "Nour El Islam Guessoum": "Nuur El Islem Goessoum",
    "Nuwan Pradeep": "Nowan Predeep",
    "Obaid Shah": "Obeid Sheh",
    "Obed McCoy": "Obid McCuy",
    "Oliver Peake": "Olyver Piake",
    "Ollie Pope": "Ollye Pupe",
    "Ollie Robinson": "Ollye Rubinson",
    "Oman Bilal Khan": "Omen Bylal Khen",
    "Ottneil Baartman": "Ottniil Beartman",
    "Parvez Hossain Emon": "Pervez Hussain Emun",
    "Pasindu Sooriyabandara": "Pesindu Suoriyabandara",
    "Paul Stirling": "Peul Styrling",
    "Pavan Rathnayake": "Pevan Rethnayake",
    "Peter Kirsten": "Piter Kyrsten",
    "Peter Loader": "Piter Luader",
    "Peter May": "Piter Mey",
    "Phil Tufnell": "Phyl Tofnell",
    "Pieter Seelaar": "Pyeter Sielaar",
    "Polly Umrigar": "Pully Umrygar",
    "Prabath Jayasuriya": "Prebath Jeyasuriya",
    "Pramod Madushan": "Premod Medushan",
    "Prasanna": "Presanna",
    "Prenelan Subrayen": "Prinelan Sobrayen",
    "Quentin Sampson": "Qoentin Sempson",
    "R Ashwin": "R Ashwyn",
    "Rahmat Shah": "Rehmat Sheh",
    "Ramesh Mendis": "Remesh Mindis",
    "Rashidul Hasan": "Reshidul Hesan",
    "Rassie van der Dussen": "Ressie van der Dossen",
    "Ravi Rampaul": "Revi Rempaul",
    "Ray Lindwall": "Rey Lyndwall",
    "Reeza Hendricks": "Rieza Hindricks",
    "Regis Chakabva": "Rigis Chekabva",
    "Rehan Ahmed": "Rihan Ahmid",
    "Riaz Hassan": "Ryaz Hessan",
    "Richard Hadlee": "Rychard Hedlee",
    "Richie Richardson": "Rychie Rychardson",
    "Rishad Hossain": "Ryshad Hussain",
    "Robert Croft": "Rubert Cruft",
    "Robin Singh": "Rubin Syngh",
    "Rodney Marsh": "Rudney Mersh",
    "Roelof van der Merwe": "Ruelof van der Mirwe",
    "Rohail Nazir": "Ruhail Nezir",
    "Rohan Kanhai": "Ruhan Kenhai",
    "Roston Chase": "Ruston Chese",
    "Roy Fredericks": "Ruy Fridericks",
    "Ruben Trumpelmann": "Roben Trompelmann",
    "Rubin Hermann": "Robin Hirmann",
    "Ryan Burl": "Ryen Borl",
    "Ryan Campbell": "Ryen Cempbell",
    "Ryan Sidebottom": "Ryen Sydebottom",
    "Sachith Pathirana": "Sechith Pethirana",
    "Sachithra Senanayake": "Sechithra Sinanayake",
    "Sadeera Samarawickrama": "Sedeera Semarawickrama",
    "Sahibzada Farhan": "Sehibzada Ferhan",
    "Saim Ayub": "Seim Ayob",
    "Sajid Khan": "Sejid Khen",
    "Salman Ali Agha": "Selman Aly Aghe",
    "Samit Patel": "Semit Petel",
    "Samuel Badree": "Semuel Bedree",
    "Sanath Jayasuriya": "Senath Jeyasuriya",
    "Saqib Mahmood": "Seqib Mehmood",
    "Saqlain Mushtaq": "Seqlain Moshtaq",
    "Sarfraz Nawaz": "Serfraz Newaz",
    "Saud Shakil": "Seud Shekil",
    "Sayed Shirzad": "Seyed Shyrzad",
    "Scott Boland": "Scutt Buland",
    "Scott Edwards": "Scutt Edwerds",
    "Sean Williams": "Sian Wylliams",
    "Shadab Khan": "Shedab Khen",
    "Shadman Islam": "Shedman Islem",
    "Shaheen Shah Afridi": "Sheheen Sheh Afrydi",
    "Shahid Afridi": "Shehid Afrydi",
    "Shahzad Mawali": "Shehzad Mewali",
    "Shai Hope": "Shei Hupe",
    "Shamar Joseph": "Shemar Juseph",
    "Shan Masood": "Shen Mesood",
    "Shane Bond": "Shene Bund",
    "Shaun Tait": "Sheun Teit",
    "Shoaib Akhtar": "Shuaib Akhter",
    "Shoaib Bashir": "Shuaib Beshir",
    "Shoaib Malik": "Shuaib Melik",
    "Shoriful Islam": "Shuriful Islem",
    "Sikandar Raza": "Sykandar Reza",
    "Simi Singh": "Symi Syngh",
    "Simon Harmer": "Symon Hermer",
    "Sonal Dinusha": "Sunal Dynusha",
    "Soumya Sarkar": "Suumya Serkar",
    "Srinivas Venkataraghavan": "Srynivas Vinkataraghavan",
    "Stephan Baard": "Stiphan Beard",
    "Steve Harmison": "Stive Hermison",
    "Steve Waugh": "Stive Weugh",
    "Steven Smith": "Stiven Smyth",
    "Stuart Broad": "Stoart Bruad",
    "Stuart Law": "Stoart Lew",
    "Stuart MacGill": "Stoart MecGill",
    "Subhash Gupte": "Sobhash Gopte",
    "Sufyan Moqim": "Sofyan Muqim",
    "Sulieman Benn": "Solieman Binn",
    "Sunil Gavaskar": "Sonil Gevaskar",
    "Suranga Lakmal": "Soranga Lekmal",
    "Sydney Barnes": "Sydniy Bernes",
    "Tabraiz Shamsi": "Tebraiz Shemsi",
    "Taijul Islam": "Teijul Islem",
    "Tamim Iqbal": "Temim Iqbel",
    "Tanveer Sangha": "Tenveer Sengha",
    "Tanzid Hasan Tamim": "Tenzid Hesan Temim",
    "Tanzim Hasan Sakib": "Tenzim Hesan Sekib",
    "Tayyab Tahir": "Teyyab Tehir",
    "Ted Dexter": "Tid Dixter",
    "Temba Bavuma": "Timba Bevuma",
    "Tendai Chatara": "Tindai Chetara",
    "Tevin Imlach": "Tivin Imlech",
    "Tharindu Rathnayake": "Therindu Rethnayake",
    "Tim Southee": "Tym Suuthee",
    "Tino Best": "Tyno Bist",
    "Todd Murphy": "Tudd Morphy",
    "Tom Graveney": "Tum Greveney",
    "Tom Latham": "Tum Letham",
    "Tom Moody": "Tum Muody",
    "Tony Lock": "Tuny Luck",
    "Tony de Zorzi": "Tuny de Zurzi",
    "Towhid Hridoy": "Tuwhid Hrydoy",
    "Tymal Mills": "Tymel Mylls",
    "Umar Akmal": "Umer Akmel",
    "Upul Tharanga": "Upol Theranga",
    "Usman Khan": "Usmen Khen",
    "Usman Khawaja": "Usmen Khewaja",
    "Usman Tariq": "Usmen Teriq",
    "Venkatesh Prasad": "Vinkatesh Presad",
    "Victor Trumper": "Vyctor Tromper",
    "Vijay Hazare": "Vyjay Hezare",
    "Vijay Merchant": "Vyjay Mirchant",
    "Vikramjit Singh": "Vykramjit Syngh",
    "Vinoo Mankad": "Vynoo Menkad",
    "Virendra Sehwag": "Vyrendra Sihwag",
    "Vishwa Fernando": "Vyshwa Firnando",
    "Viv Richards": "Vyv Rychards",
    "Wahab Riaz": "Wehab Ryaz",
    "Wahidullah Shafaq": "Wehidullah Shefaq",
    "Wally Hammond": "Welly Hemmond",
    "Waqar Younis": "Weqar Yuunis",
    "Wasim Akram": "Wesim Akrem",
    "Wayne Daniel": "Weyne Deniel",
    "Wes Hall": "Wis Hell",
    "Will O'Rourke": "Wyll O'Ruurke",
    "Will Young": "Wyll Yuung",
    "William O'Rourke": "Wylliam O'Ruurke",
    "Yamin Ahmadzai": "Yemin Ahmedzai",
    "Younis Khan": "Yuunis Khen",
    "Zaheer Abbas": "Zeheer Abbes",
    "Zahir Khan": "Zehir Khen",
    "Zak Crawley": "Zek Crewley",
    "Zakir Hasan": "Zekir Hesan",
}

# Files that reference team names as plain strings (the player CSVs are
# transformed separately and already contain the fictional names).
TEAM_TEXT_FILES = [
    ENGINE / "players_data.py",
    ENGINE / "sim" / "live_match.py",
    ROOT / "mobile" / "src" / "constants" / "theme.ts",
    ROOT / "webapp" / "index.html",
    ROOT / "docs" / "mockups" / "phase1-mockups.html",
    ROOT / "legacy" / "ui_server.py",
    ROOT / "tests" / "conftest.py",
    ROOT / "tests" / "test_league_state_extra.py",
    ROOT / "tests" / "test_serialization.py",
    ROOT / "tests" / "test_draft.py",
    ROOT / "backend" / "tests" / "careers" / "test_match_history.py",
    ROOT / "backend" / "tests" / "careers" / "test_career_routes.py",
    ROOT / "backend" / "tests" / "season" / "test_season_routes.py",
    ROOT / "backend" / "tests" / "live_match" / "test_live_match_routes.py",
    ROOT / "backend" / "tests" / "auth" / "test_auth_routes.py",
]


# --- deriving new names -------------------------------------------------------
#
# PLAYER_MAP above was authored by hand for the original IPL pool. Phase 8 added
# three all-time pools and current international squads containing several
# hundred further real names, which is far too many to hand-write while keeping
# the convention consistent. The convention itself is mechanical, so we derive
# from it instead and keep every result in PLAYER_MAP as the audit record.
#
# The rule (reverse-engineered from the hand-authored entries, which it
# reproduces for 434 of 435 of them): shift the first vowel that follows a
# word's opening letter, so initials survive and abbreviated scorecard forms
# stay familiar — "V. Kohli" -> "V. Kuhli". Hyphenated surnames shift each
# segment independently ("Coulter-Nile" -> "Cuulter-Nyle"). Initialisms ("AB")
# and name particles ("de", "van") are left alone.
#
# The one hand-authored entry this does not reproduce is "Lynn" -> "Lyno": a
# surname with no shiftable vowel. Such names have no derivable form, so they
# are reported for a hand-written PLAYER_MAP entry rather than guessed at.

VOWEL_SHIFT = {"a": "e", "e": "i", "i": "y", "o": "u", "u": "o"}
NAME_PARTICLES = {"de", "van", "der", "du", "da", "di", "le", "la", "bin", "al"}


def _shift_word(word: str) -> str:
    if len(word) < 3 or word.lower() in NAME_PARTICLES or word.isupper():
        return word
    for i, ch in enumerate(word):
        if i == 0:
            continue
        shifted = VOWEL_SHIFT.get(ch.lower())
        if shifted:
            return word[:i] + (shifted.upper() if ch.isupper() else shifted) + word[i + 1:]
    return word  # no shiftable vowel — caller reports it for a manual mapping


def derive_ip_safe_name(name: str) -> str:
    """Apply the rename convention to a real player name."""
    return " ".join(
        "-".join(_shift_word(part) for part in token.split("-"))
        for token in name.split(" ")
    )


def is_derivable(name: str) -> bool:
    """Whether the convention actually changes this name (vowel-less names do not)."""
    return derive_ip_safe_name(name) != name


def _replace_teams(text: str) -> str:
    for old, new in TEAM_MAP.items():
        text = text.replace(old, new)
    for old, new in ABBR_MAP.items():
        for q in ("'", '"'):
            text = text.replace(f"{q}{old}{q}", f"{q}{new}{q}")
    return text


def apply_team_renames(write: bool) -> None:
    for path in TEAM_TEXT_FILES:
        if not path.exists():
            print(f"  (skip, missing) {path}")
            continue
        original = path.read_text()
        updated = _replace_teams(original)
        if updated != original:
            print(f"  team-renamed {path.relative_to(ROOT)}")
            if write:
                path.write_text(updated)


def apply_player_roster_renames(write: bool) -> None:
    """Re-apply PLAYER_MAP to the quoted roster names in players_data.py."""
    path = ENGINE / "players_data.py"
    text = path.read_text()
    # Longest names first so a short name isn't a substring of a longer one.
    for real in sorted(PLAYER_MAP, key=len, reverse=True):
        fict = PLAYER_MAP[real]
        for q in ("'", '"'):
            text = text.replace(f"{q}{real}{q}", f"{q}{fict}{q}")
    print(f"  roster-renamed players_data.py")
    if write:
        path.write_text(text)


# Phase 8 data: the all-time ODI/Test/T20I pools and the current national
# squads. These shipped with real names and are what `--apply` now also covers.
ALLTIME_CSVS = [
    ENGINE / "players_alltime_odi.csv",
    ENGINE / "players_alltime_t20_intl.csv",
    ENGINE / "players_alltime_test.csv",
]
INTERNATIONAL_DATA = ENGINE / "international_data.py"


def csv_player_names() -> set[str]:
    """Every name in the all-time pool CSVs (the name is always the first column)."""
    names: set[str] = set()
    for path in ALLTIME_CSVS:
        if not path.exists():
            continue
        lines = path.read_text().splitlines()
        for line in lines[1:]:
            if line.strip():
                names.add(line.split(",", 1)[0].strip())
    return names


# Every squad member is declared as `_p("Name", "Role", ...)`, so the player
# name is always the first argument. Match on that structure rather than on
# "looks like a name": country names ("South Africa") and batting archetypes
# ("Middle-order Rotator") are quoted identically and a shape-based regex
# happily renames them, which silently decouples the rosters from
# INTERNATIONAL_TEAMS_LIST and corrupts archetype values.
_PLAYER_CALL = re.compile(r'_p\(\s*"([^"]+)"')


def international_player_names() -> set[str]:
    """Player names declared in international_data.py, and nothing else."""
    if not INTERNATIONAL_DATA.exists():
        return set()
    return set(_PLAYER_CALL.findall(INTERNATIONAL_DATA.read_text()))


def unmapped_names() -> set[str]:
    """Real names in the Phase 8 data that PLAYER_MAP does not yet cover."""
    return (csv_player_names() | international_player_names()) - set(PLAYER_MAP)


def audit_derived_names() -> tuple[dict[str, str], list[str], list[str]]:
    """Derive names for everything unmapped, and report what needs a human.

    Returns (derived, undecidable, collisions):
      - undecidable: no shiftable vowel, so the convention yields the real name
      - collisions:  two real names deriving to the same fictional name, or a
                     derived name colliding with a real name still in the data
    """
    real_names = csv_player_names() | international_player_names() | set(PLAYER_MAP)
    derived: dict[str, str] = {}
    undecidable: list[str] = []
    seen: dict[str, str] = {v: k for k, v in PLAYER_MAP.items()}
    collisions: list[str] = []

    for real in sorted(unmapped_names()):
        if not is_derivable(real):
            undecidable.append(real)
            continue
        fake = derive_ip_safe_name(real)
        if fake in real_names:
            collisions.append(f"{real} -> {fake} (collides with a real name)")
            continue
        if fake in seen:
            collisions.append(f"{real} -> {fake} (already used by {seen[fake]})")
            continue
        seen[fake] = real
        derived[real] = fake
    return derived, undecidable, collisions


def _rename_csv_names(path: Path, mapping: dict[str, str], write: bool) -> int:
    """Rewrite only the first CSV column, leaving every other byte untouched.

    These files use CRLF endings, and Path.read_text() applies universal-newline
    translation — which would silently rewrite every line to LF and bury the
    real change in an all-lines diff. newline="" round-trips them verbatim.
    """
    with open(path, "r", encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)
    changed = 0
    for idx, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        name, sep, rest = line.partition(",")
        new = mapping.get(name.strip())
        if new:
            lines[idx] = f"{new}{sep}{rest}"
            changed += 1
    if changed and write:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write("".join(lines))
    return changed


def apply_alltime_csv_renames(mapping: dict[str, str], write: bool) -> None:
    for path in ALLTIME_CSVS:
        if not path.exists():
            print(f"  (skip, missing) {path}")
            continue
        n = _rename_csv_names(path, mapping, write)
        print(f"  renamed {n:>3} names in {path.name}")


def apply_international_renames(mapping: dict[str, str], write: bool) -> None:
    if not INTERNATIONAL_DATA.exists():
        print("  (skip, missing) international_data.py")
        return
    text = INTERNATIONAL_DATA.read_text()
    original = text
    changed = 0

    # Rewrite only the first argument of each _p(...) call, so nothing outside a
    # player-name position can be touched no matter what the mapping contains.
    def _sub(match: re.Match) -> str:
        nonlocal changed
        real = match.group(1)
        new = mapping.get(real)
        if not new:
            return match.group(0)
        changed += 1
        return match.group(0).replace(f'"{real}"', f'"{new}"', 1)

    text = _PLAYER_CALL.sub(_sub, text)
    print(f"  renamed {changed:>3} player names in international_data.py")
    if write and text != original:
        INTERNATIONAL_DATA.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rewrite files in place")
    parser.add_argument("--check", action="store_true", help="print mappings only")
    args = parser.parse_args()

    print(f"Teams: {len(TEAM_MAP)}  Players: {len(PLAYER_MAP)}")

    derived, undecidable, collisions = audit_derived_names()
    print(f"\nPhase 8 data needing mappings: {len(unmapped_names())}")
    print(f"  derived by convention: {len(derived)}")
    if undecidable:
        print(f"  NO SHIFTABLE VOWEL ({len(undecidable)}) — add these to PLAYER_MAP by hand:")
        for n in undecidable:
            print(f"    {n}")
    if collisions:
        print(f"  COLLISIONS ({len(collisions)}) — resolve by hand:")
        for c in collisions:
            print(f"    {c}")

    full_map = {**PLAYER_MAP, **derived}

    print("\nApplying team renames:")
    apply_team_renames(write=args.apply)
    print("Applying player roster renames:")
    apply_player_roster_renames(write=args.apply)
    print("Applying all-time pool CSV renames:")
    apply_alltime_csv_renames(full_map, write=args.apply)
    print("Applying international squad renames:")
    apply_international_renames(full_map, write=args.apply)

    if not args.apply:
        print("\n(dry run — pass --apply to write)")


if __name__ == "__main__":
    main()
