"""Source text for the hosted Terms of Service and Privacy Policy.

Kept as plain constants so the legal copy lives in one place and the router
stays a thin presentation layer. These pages back the in-app "Terms of Service"
and "Privacy Policy" links and serve as the public policy URLs required by the
Apple App Store and Google Play.

`APP_NAME`/`CONTACT_EMAIL`/`GOVERNING_LAW` are the only app-specific values;
update them here (e.g. swap APP_NAME for a registered company/LLC name once one
exists) and both pages pick the change up.
"""

APP_NAME = "Cricket Franchise Sim"
CONTACT_EMAIL = "cricketfranchisesim@gmail.com"
GOVERNING_LAW = "State of Georgia, United States"

# Last substantive update to either policy. Shown on both pages.
LAST_UPDATED = "June 16, 2026"

# --- Terms of Service ---------------------------------------------------------
# Each entry is (section heading, list of paragraph strings).
TERMS_SECTIONS: list[tuple[str, list[str]]] = [
    (
        "1. Acceptance of Terms",
        [
            f"Welcome to {APP_NAME} (the \"App\"). By creating an account, signing in, "
            "or otherwise using the App, you agree to be bound by these Terms of "
            "Service (the \"Terms\"). If you do not agree, do not use the App.",
            "You must be at least 13 years old (or the minimum age of digital "
            "consent in your country) to use the App.",
        ],
    ),
    (
        "2. The Service",
        [
            f"{APP_NAME} is a single-player cricket franchise management simulation "
            "game. It lets you draft a squad, manage a team, and simulate matches "
            "and seasons. All teams, players, and leagues in the App are fictional "
            "and are not affiliated with, endorsed by, or sponsored by any real-world "
            "cricket league, team, player, or governing body.",
            "We may add, change, or remove features at any time, and we may suspend "
            "or discontinue the App in whole or in part without notice.",
        ],
    ),
    (
        "3. Your Account",
        [
            "You may play as a guest, or sign in with Apple or Google to back up your "
            "progress. You are responsible for activity that occurs under your "
            "account and for keeping your sign-in credentials secure.",
            "You may delete your account at any time from within the App. Deleting "
            "your account permanently removes your careers, statistics, and match "
            "history, and this cannot be undone.",
        ],
    ),
    (
        "4. Acceptable Use",
        [
            "You agree not to: (a) reverse engineer, decompile, or attempt to extract "
            "the source code of the App except as permitted by law; (b) use the App "
            "to violate any law or the rights of others; (c) interfere with or "
            "disrupt the App's servers or networks; or (d) attempt to gain "
            "unauthorized access to any part of the service or other users' data.",
        ],
    ),
    (
        "5. Intellectual Property",
        [
            f"The App, including its software, design, text, and graphics, is owned by "
            f"{APP_NAME} and is protected by intellectual property laws. We grant you "
            "a personal, non-exclusive, non-transferable, revocable license to use "
            "the App for your own non-commercial entertainment.",
        ],
    ),
    (
        "6. Disclaimers",
        [
            "THE APP IS PROVIDED \"AS IS\" AND \"AS AVAILABLE\" WITHOUT WARRANTIES OF "
            "ANY KIND, WHETHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO "
            "WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND "
            "NON-INFRINGEMENT. We do not warrant that the App will be uninterrupted, "
            "error-free, or that your progress will never be lost.",
        ],
    ),
    (
        "7. Limitation of Liability",
        [
            f"TO THE MAXIMUM EXTENT PERMITTED BY LAW, {APP_NAME.upper()} WILL NOT BE "
            "LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE "
            "DAMAGES, OR ANY LOSS OF DATA OR PROGRESS, ARISING OUT OF OR RELATING TO "
            "YOUR USE OF THE APP.",
        ],
    ),
    (
        "8. Changes to These Terms",
        [
            "We may update these Terms from time to time. When we do, we will revise "
            "the \"Last updated\" date above. Your continued use of the App after "
            "changes take effect constitutes acceptance of the revised Terms.",
        ],
    ),
    (
        "9. Governing Law",
        [
            f"These Terms are governed by the laws of the {GOVERNING_LAW}, without "
            "regard to its conflict-of-laws principles.",
        ],
    ),
    (
        "10. Contact",
        [
            f"Questions about these Terms? Contact us at {CONTACT_EMAIL}.",
        ],
    ),
]

# --- Privacy Policy -----------------------------------------------------------
PRIVACY_SECTIONS: list[tuple[str, list[str]]] = [
    (
        "1. Overview",
        [
            f"This Privacy Policy explains what information {APP_NAME} (the \"App\") "
            "collects, how it is used, and the choices you have. We aim to collect "
            "as little personal information as possible.",
        ],
    ),
    (
        "2. Information We Collect",
        [
            "Account information: If you sign in with Apple or Google, we receive a "
            "unique account identifier and, depending on your choices, your name and "
            "email address. If you play as a guest, no personal identity information "
            "is collected.",
            "Game data: We store your in-game progress — careers, squads, "
            "statistics, and match history — so it can be restored across sessions "
            "and devices.",
            "Diagnostic and usage data: We collect anonymized crash reports and "
            "aggregate usage analytics to help us find bugs and improve the App. "
            "This data is not used to identify you personally.",
        ],
    ),
    (
        "3. How We Use Information",
        [
            "We use the information we collect to operate and maintain the App, save "
            "and sync your game progress, diagnose and fix problems, and improve "
            "features. We do not sell your personal information.",
        ],
    ),
    (
        "4. Third-Party Services",
        [
            "The App relies on a small number of third-party services to function: "
            "Apple and Google for optional sign-in; Sentry for crash reporting; and "
            "PostHog for anonymized product analytics. Each processes data under its "
            "own privacy policy.",
        ],
    ),
    (
        "5. Data Retention and Deletion",
        [
            "We retain your game data for as long as your account exists. You can "
            "permanently delete your account and all associated data at any time from "
            "the account menu inside the App. Once deleted, this data cannot be "
            "recovered.",
        ],
    ),
    (
        "6. Children's Privacy",
        [
            "The App is not directed to children under 13, and we do not knowingly "
            "collect personal information from children under 13. If you believe a "
            "child has provided us personal information, contact us and we will "
            "delete it.",
        ],
    ),
    (
        "7. Your Rights",
        [
            "Depending on where you live, you may have the right to access, correct, "
            "or delete your personal information. You can exercise deletion directly "
            f"in the App, or contact us at {CONTACT_EMAIL} for other requests.",
        ],
    ),
    (
        "8. Changes to This Policy",
        [
            "We may update this Privacy Policy from time to time. When we do, we will "
            "revise the \"Last updated\" date above.",
        ],
    ),
    (
        "9. Contact",
        [
            f"Questions about your privacy? Contact us at {CONTACT_EMAIL}.",
        ],
    ),
]
