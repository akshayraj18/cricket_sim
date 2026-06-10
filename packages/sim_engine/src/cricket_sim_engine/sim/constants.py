"""Shared constants for the league simulation: persistence, sizing, and seed data.

`TEAM_META` and the name-component lists are presentation/generation data used
across `LiveMatch` and `LeagueState`; the numeric constants govern save-file
location, squad sizing, and the retention-window cycle.
"""

SAVE_FILE = "ui_save_state.pkl"
SAVES_DIR = "saves"
SQUAD_SIZE = 21
RETAIN_NORMAL = 11
RETAIN_RESET = 5

INDIAN_FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Ishan", "Kabir", "Reyansh", "Rohan",
    "Sai", "Vihaan", "Ayaan", "Dev", "Kiaan", "Krish", "Neel", "Pranav",
    "Rahul", "Rudra", "Shivam", "Yash", "Arnav", "Dhruv", "Harsh", "Manav",
]
INDIAN_LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Yadav", "Reddy", "Iyer", "Nair", "Verma",
    "Rana", "Gill", "Khan", "Choudhary", "Deshmukh", "Pawar", "Saxena", "Shetty",
    "Tripathi", "Mishra", "Bishnoi", "Thakur", "Gaikwad", "Sundar", "Varma", "Jaiswal",
]
OVERSEAS_FIRST_NAMES = [
    "Liam", "Noah", "Oliver", "Jack", "Harry", "Mason", "Ethan", "Lucas",
    "James", "Logan", "Theo", "Oscar", "Finn", "Dylan", "Archie", "Cooper",
    "Caleb", "Riley", "Max", "Jude", "Leo", "Sam", "Ben", "Tom",
]
OVERSEAS_LAST_NAMES = [
    "Smith", "Brown", "Wilson", "Taylor", "Anderson", "Johnson", "Williams", "Miller",
    "Thompson", "Walker", "Clark", "Robinson", "Campbell", "Bennett", "Carter", "Morgan",
    "Phillips", "Turner", "Hughes", "Edwards", "Fletcher", "Marsh", "Allen", "Wright",
]


TEAM_META = {
    "Chennai Super Kings": {"abbr": "CSK", "home": "MA Chidambaram Stadium", "primary": "#f7c948", "accent": "#22409a"},
    "Mumbai Indians": {"abbr": "MI", "home": "Wankhede Stadium", "primary": "#045093", "accent": "#d1ab3e"},
    "Royal Challengers Bengaluru": {"abbr": "RCB", "home": "M. Chinnaswamy Stadium", "primary": "#da1818", "accent": "#111111"},
    "Kolkata Knight Riders": {"abbr": "KKR", "home": "Eden Gardens", "primary": "#3a225d", "accent": "#c6a76f"},
    "Sunrisers Hyderabad": {"abbr": "SRH", "home": "Rajiv Gandhi Intl. Stadium", "primary": "#f26522", "accent": "#1f1f1f"},
    "Rajasthan Royals": {"abbr": "RR", "home": "Sawai Mansingh Stadium", "primary": "#e91e8f", "accent": "#254aa5"},
    "Delhi Capitals": {"abbr": "DC", "home": "Arun Jaitley Stadium", "primary": "#17479e", "accent": "#ef1b23"},
    "Gujarat Titans": {"abbr": "GT", "home": "Narendra Modi Stadium", "primary": "#1b2133", "accent": "#b69249"},
    "Lucknow Super Giants": {"abbr": "LSG", "home": "Ekana Cricket Stadium", "primary": "#00a3e0", "accent": "#f28c28"},
    "Punjab Kings": {"abbr": "PBKS", "home": "New PCA Stadium", "primary": "#d71920", "accent": "#b7b7b7"},
}
