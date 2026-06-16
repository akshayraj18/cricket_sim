# Known Issues — post-launch follow-ups

Tracked from the first on-device preview build (iOS, against live Railway API).
These are non-blocking for the initial App Store submission; address in a
follow-up pass.

**Status (v1.0 submission):**
- ✅ #3 in-app branding → "CricSim" — FIXED
- ✅ #4 "won won" result text — FIXED
- ⏳ #1 tutorial career-not-found — DEFERRED to v1.1 (first-run-only edge case;
  needs on-device retest)
- ⏳ #2 team-color fallbacks (match hub + fixtures) — DEFERRED to v1.1
- ℹ️ #5 parody player names — kept for v1.0, IP risk noted

## 1. "How to Play" tutorial errors before a career exists

**Symptom:** Launching the guided "How to Play" tutorial *before* creating a
career throws "career not found" errors. (Works once a career exists.)

**Likely cause:** The tutorial's demo-career lifecycle (throwaway career it
creates/tears down) assumes a career context that isn't present on a fresh
install / first run. The tour fetches/league state before its demo career is
provisioned.

**Where to look:**
- `mobile/src/components/tutorial/guided-tour.tsx` (demo-career create/teardown,
  `draftConsumed` ref)
- `mobile/src/components/tutorial/guided-tour-host.tsx`
- `mobile/src/context/LeagueContext.tsx` (refresh suppression while `tourActive`)
- Backend "career not found" path — confirm the demo career is created before
  any league-state fetch fires.

**Fix idea:** Gate tutorial start on the demo career being fully created, or
make the league fetch tolerant of a not-yet-created career during the tour.

## 2. Team colors fall back to default green

**Symptom:** Mumbai Mavericks (and presumably other teams) show the default
green instead of their team colors in:
- the **Enter Match Hub** screen
- the **Fixtures** list on the Season tab

(Team colors *do* render correctly in the game hub, per earlier work — so the
color data exists; these two surfaces aren't reading it.)

**Where to look:**
- `mobile/src/components/live-match-hub.tsx` (Enter Match Hub)
- `mobile/src/app/(tabs)/season.tsx` (Fixtures list)
- Compare with the game hub component that *does* apply team colors correctly,
  and the team-color source (theme / team metadata).

**Fix idea:** Wire the same team-color lookup the game hub uses into the match
hub and fixtures rows; verify the team object carries color fields in those
code paths.

## 3. In-app branding still says "Franchise Sim" / "Cricket Franchise Universe"

**Symptom:** App Store name + icon are "CricSim", but in-app the home header
reads "🏏 Franchise Sim" and the sign-in hero title reads "Cricket Franchise
Universe."

**Why it matters:** Apple guideline 2.3.8 expects the store name to match the
in-app name. Generally passes, but it's an inconsistency and a minor rejection
risk. Align in-app text to "CricSim" before/soon after first submission.

**Where to look:** home screen header component, sign-in screen hero title.

## 4. Duplicated word in match-result banner: "won won"

**Symptom:** Match result reads e.g. "BLR won won by 8 runs" (duplicate
"won"). Visible on the Match Centre result banner (IMG_0822).

**Fix idea:** The result string likely concatenates a "{TEAM} won" prefix with
a result phrase that already starts with "won". De-dupe in the result-text
builder (live match / match-centre result formatting).

## 5. Parody player names (IP consideration — not a bug)

Player names are deliberate misspellings of real cricketers ("Vyrat Kuhli",
"Jesprit Bomrah", "Qointon de Kuck", etc.). Tolerated as parody but a possible
publicity-rights / IP flag in App Review and a future takedown risk. Decide
whether to keep, further fictionalize, or license. Noted for awareness; not
blocking initial submission.
