# App Store Connect — Listing Draft (CricSim)

Everything you need to paste into App Store Connect when creating the app
record. Edit anything that doesn't sound like you. Character limits noted.

---

## App Information

| Field | Value |
|---|---|
| **App Name** (30 char max) | `CricSim` |
| **Subtitle** (30 char max) | `Build your cricket dynasty` |
| **Bundle ID** | `com.akshraj.cric` (already registered) |
| **Primary Category** | Games |
| **Secondary Category** (optional) | Sports |
| **Primary Subcategory** | Sports (under Games) |
| **Secondary Subcategory** | Simulation |
| **Support URL** | https://akshayraj18.github.io/cricket_sim/legal/privacy-policy.html *(or a simple support page — see note below)* |
| **Marketing URL** (optional) | leave blank or your GitHub Pages root |
| **Privacy Policy URL** | https://akshayraj18.github.io/cricket_sim/legal/privacy-policy.html |

> **Support URL note:** Apple requires a working support URL where users can
> reach you. The privacy policy page works in a pinch, but ideally a tiny page
> with your contact email (cricketfranchisesim@gmail.com). We can add a
> `support.html` next to the legal docs if you want — quick to do.

---

## Promotional Text (170 char max — editable anytime without review)

```
Draft your squad, manage your XI, and chase the title across a full season. Your cricket franchise, your strategy.
```

---

## Description (4000 char max)

```
CricSim puts you in charge of your own cricket franchise. Draft a squad, set
your strategy, and battle through a full season toward the championship.

BUILD YOUR SQUAD
Run a live draft to assemble your 25-player roster. Balance batting depth,
bowling firepower, and your overseas slots within the squad cap. Pick your
captain, vice-captain, and wicketkeeper.

SET YOUR STRATEGY
Choose your starting XI, batting order, and bowling plans before every match.
Use a smart lineup that adapts to your roster, or fine-tune every detail
yourself. Make the impact-sub call at the right moment.

PLAY THE SEASON
Take on every rival across a full fixtures list, climb the standings, and
push into the playoffs. Manage retentions between seasons and build a dynasty
that lasts.

SIMULATE OR PLAY LIVE
Quick-sim a match to jump ahead, or drop into the live match hub and call the
shots over by over.

LEARN AS YOU GO
A built-in How to Play tour walks you through drafting, your squad, and match
day so you're never lost.

No ads. No pay-to-win. Just cricket management.
```

---

## Keywords (100 char max, comma-separated, no spaces after commas)

```
cricket,franchise,manager,simulation,sports,t20,league,squad,draft,season,strategy,team,coach
```

---

## What's New in This Version (for v1.0)

```
Welcome to CricSim! Draft your squad, manage your XI, and chase the
championship across a full season.
```

---

## Age Rating Questionnaire — answers

Answer the questionnaire to land at **4+** (or 9+ if any sim violence flagged —
cricket has none, so aim for 4+). Key answers:

- Cartoon or Fantasy Violence: **None**
- Realistic Violence: **None**
- Sexual Content / Nudity: **None**
- Profanity / Crude Humor: **None**
- Alcohol, Tobacco, Drug Use or References: **None**
- Gambling: **None** *(this is a management sim, not real or simulated
  gambling — no betting mechanics)*
- Horror/Fear, Mature/Suggestive: **None**
- Unrestricted Web Access: **No**
- → Expected rating: **4+**

---

## Privacy — "App Privacy" Nutrition Labels

This MUST match the privacy policy. Based on your policy, here is exactly what
to declare in App Store Connect → App Privacy.

### Data the app collects

**1. Contact Info → Email Address**
- Collected: **Yes** (only when user signs in with Apple/Google AND chooses to
  share email; guests share none)
- Linked to user's identity: **Yes**
- Used for tracking: **No**
- Purposes: **App Functionality** (account / restore progress across devices)

**2. Identifiers → User ID**
- Collected: **Yes** (account identifier from Apple/Google; or anonymous
  generated ID for guests)
- Linked to identity: **Yes**
- Used for tracking: **No**
- Purposes: **App Functionality**

**3. Usage Data → Product Interaction**
- Collected: **Yes** (PostHog analytics: app opened, career created, match
  played, etc.)
- Linked to identity: **No** (you describe these as anonymous/aggregated)
- Used for tracking: **No**
- Purposes: **Analytics**

**4. Diagnostics → Crash Data**
- Collected: **Yes** (Sentry crash reports, configured to exclude personal
  data / IP)
- Linked to identity: **No**
- Used for tracking: **No**
- Purposes: **App Functionality** (and/or Analytics)

**5. Diagnostics → Other Diagnostic Data**
- Collected: **Yes** (Sentry technical error logs)
- Linked to identity: **No**
- Used for tracking: **No**
- Purposes: **App Functionality**

### Data NOT collected (do not check these)
Location, Contacts, Photos, Browsing History, Search History, Financial Info,
Health, Sensitive Info, Purchases, Audio, etc. — your policy explicitly says
none of these.

### Tracking
- "Do you or your partners use data for tracking?" → **No**
  (You don't track across apps/sites; analytics are first-party and you state
  you don't sell data.)

---

## Screenshots — what to capture

**Required:** at least 1 for **6.9" iPhone (1290 x 2796)**. Up to 10.
Capture from your phone (the device you installed the preview on) or the iOS
Simulator. Suggested set (pick 4-6):

1. Home / main screen (career list or new-career)
2. Live draft board
3. Starting XI / squad screen
4. Live match hub (or an in-progress match)
5. Season standings / fixtures
6. (optional) The How to Play tour

Plain device screenshots are accepted — no captions required to pass review.

---

## Review Notes (App Review Information)

```
CricSim is a single-player cricket franchise management simulation. No real
money, no real gambling, no user-generated content shared between users.

To test the full app, tap "Continue as Guest" on the sign-in screen — this
creates an anonymous account and gives full access with no credentials needed.
Sign in with Apple and Google sign-in are also available but optional.
```

> The "Continue as Guest" note is important — it lets Apple's reviewer test
> without needing a demo Apple/Google account. Saves a rejection.

---

## Export Compliance

Already handled in app.json: `ITSAppUsesNonExemptEncryption: false`. The app
uses only standard HTTPS/TLS, which is exempt. You won't be prompted each
submission.

---

## Pricing & Availability

- **Price:** Free
- **Availability:** All territories (or restrict if you prefer)
