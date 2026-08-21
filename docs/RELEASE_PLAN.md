# Release Plan — v1.1 (first update since launch)

Target: ship within 1–2 days of 2026-08-17.

Every user in production is still on **1.0.0**; no update has ever shipped. That
makes this release unusually valuable regardless of what is in it — it is the
first time we get a second data point on anything.

---

## Why this scope

From the usage data in `ideas.txt` (PostHog project 469107 + Railway Postgres,
pulled 2026-08-17):

- 74 people, 49 installs, 48 careers, 10,648 matches simulated
- growth accelerating: 8 / 11 / 12 new careers in the last three full weeks
- **64% of people use the app on exactly one day and never return**
- but 27 of 48 careers have played 71+ matches; the deepest has finished 20 seasons

The core loop demonstrably works for people who reach it. The leak is the first
session. That is what v1.1 should attack — but note we currently **cannot
measure** whether any fix worked, because there are no gameplay analytics events.
So instrumentation ships first, in this release, even though users won't see it.

---

## Scope — in

1. ~~**Phase 8 content** (PR #32): T20/ODI/Test formats, international
   tournaments and bilateral series, all-time ODI/Test draft pools, world
   franchises.~~ **Merged 2026-08-18.**
2. ~~**IP-safe player names** (PR #44).~~ **Merged 2026-08-18.** Phase 8 had
   shipped 465 real names; all renamed. This was a hard blocker.
3. ~~**Security dependencies** (PR #43).~~ **Merged 2026-08-18.** Dependabot
   alerts 18 → 3; the remaining three are build-time only and two have no patch
   in existence. See "Known risks".
4. ~~**Gameplay analytics events**~~ — draft started/completed/abandoned, match
   started/completed, season completed, screen views, `$device_model`.
   **Merged 2026-08-19** (`f155662`); see `src/observability/`.
5. ~~**Account data bleed on sign-out/sign-in**~~ **Merged 2026-08-19.**
6. ~~**Tutorial "career not found" on first run**~~ **Merged 2026-08-19.**
7. ~~**Test-match result and scoring calibration**~~ — "won by 0 wickets"
   affected 32% of Test matches. **Merged 2026-08-19.**
8. ~~**Team-colour legibility**~~ — contrast helpers, 92 assertions over 30
   teams in both themes. **Merged 2026-08-20** (#51, #52).
9. ~~**Player names via CSV**~~ — export/import in Settings.
   **Merged 2026-08-21** (#53); migration `12baff3d6136` applied in production.

### Remaining before submit

10. **iPhone display issues** (`KNOWN_ISSUES.md`) — the last user-visible
    blocker. Segmented-control truncation and scorecard column collisions are
    fixed; the initial-screen overlap still needs a reproduction on device.
11. **Google sign-in fails in the App Store build.** Works in dev, so it is
    almost certainly an EAS production-profile client-ID mismatch rather than
    code — but it is a broken sign-in path in a release about first-run
    retention, so it should not ship unresolved.

## Scope — out (deliberately)

- **Expo SDK 57 / RN 0.86.** SDK 57 is out; upgrading days before a release
  trades a known-good build for an unknown one. Do it right after v1.1 ships.
- **Fictionalising names further.** Already settled: franchises and players are
  fictionalised, country/city names are not protected. See LAUNCH_ROADMAP §0.1.
- **Monetisation / auction mode (8D).** Still deferred until the user base grows.
- **The retention redesign itself** (draft escape hatch, defaulting new careers
  to the no-draft roster). Ship the instrumentation first so the next release
  can be judged against real numbers rather than a hunch.

---

## Release blockers found 2026-08-21

- [x] **Version bumped 1.0.0 -> 1.1.0.** `app.json` still said `1.0.0`, which is
      the version already on the App Store — Connect rejects an upload whose
      version matches a released one. Build number is handled by
      `autoIncrement: true` in the production profile.
- [ ] **App Store privacy labels must be re-answered in App Store Connect.**
      The privacy policy now discloses device model/manufacturer/type,
      autocaptured screen views, and analytics linked to an account identifier.
      The Connect questionnaire is a separate declaration and is what Apple
      checks the app against; leaving it describing 1.0 is a rejection risk and
      a compliance one. Likely additions: Identifiers > User ID, Usage Data >
      Product Interaction, Diagnostics, and User Content for custom names.
- [ ] **"What's New" text** for the listing (custom names, rating prompt,
      display fixes, Test-match scoring corrections).
- [ ] **Governing jurisdiction still unset in the Terms.** Section 12 has
      shipped since June carrying a visible `> Note: Set your specific
      governing jurisdiction before publishing.` It is published at
      /legal/terms.html right now.

### Google sign-in: the documented hypothesis is wrong

The plan assumed a production client-ID mismatch. Checked 2026-08-21 — it is
not that:

- `app.json`'s `iosUrlScheme` matches `GOOGLE_IOS_CLIENT_ID` in `config.ts`.
- The production EAS profile sets no `EXPO_PUBLIC_GOOGLE_*`, so it uses those
  same inline IDs, which are real.
- The backend accepts **both** the web and iOS client IDs as `aud`, and
  `GOOGLE_CLIENT_IDS` is not overridden on Railway, so production runs those
  defaults.

Diagnosing further needs the actual native error from a production build —
which we cannot read, because there is still no Sentry auth token. That makes
the Sentry token a blocker for this bug, not just a nice-to-have.

## Pre-flight checklist

- [ ] `make test-all` green locally (~97s)
- [ ] `make lint` clean
- [ ] `make mobile-typecheck` and `make mobile-lint` clean (0 errors)
- [ ] CI green on the PR — **check this explicitly**: CI had never once run on
      the phase-8 branch, so a PR showing only CodeQL checks is not "passing"
- [ ] Smoke test on simulator: create career → draft → play a match → finish a
      season, for T20 *and* one of ODI/Test
- [ ] Smoke test on an iPad simulator — 12% of users are on iPadOS
- [ ] Bump version + build number; confirm EAS `production` profile env vars
- [ ] Tag the release commit so crash reports can be tied to a build

## Known risks

- **CI pins Node 20, which reached EOL in April 2026.** `make mobile` already
  uses Node 22 locally (Makefile auto-selects the newest v2x), so CI and local
  differ. `actions/setup-node` is now v7 (#38) but `node-version:` is still 20.
  Worth aligning, but *after* this release.
- **3 Dependabot alerts remain and are accepted for v1.1.** All are build-time
  tooling that never enters the App Store binary: two `image-size` (high, via
  `metro`) for which **no patched version exists**, and one `uuid` (medium, via
  `@expo/ngrok`/`xcode`, dev-only). The exposure is a developer machine at
  bundle time, not an end user.
- **Deferred to the post-v1.1 SDK upgrade:** Expo SDK 57 / RN 0.86, which is the
  only thing that clears the remaining toolchain advisories, and the
  `@sentry/react-native` 7 → 8 major bump that rides with it. Do not take these
  in a release window — Sentry is what tells us whether the release is healthy.
- We ship blind on crash rates: the Sentry credentials in `secrets/ids.txt` are
  ingest-only DSNs. Generate a Sentry **auth token** so crash-free-session rate
  can go in this checklist.
- **`expo-web-browser` gained a config plugin in #43** — a native change. The
  dev client must be rebuilt (`make mobile-ios`); a JS reload will not pick it
  up, and neither will a stale simulator build.

---

## After shipping

1. Watch crash-free session rate and the new funnel events for ~a week.
2. Then use that baseline to judge the retention work (draft escape hatch,
   no-draft default for a first career, shorter tutorial).
3. ~~Only then revisit the in-app rating prompt~~ — **shipped in v1.1
   instead.** The concern was collecting reviews for a build already replaced;
   that resolves itself by shipping the prompt *in* v1.1, since anyone who can
   see it is already running v1.1. See `docs/APP_RATING_PROMPT.md`.
   **Still needs `EXPO_PUBLIC_APP_STORE_ID`** in the EAS production profile
   before the Settings link appears.
