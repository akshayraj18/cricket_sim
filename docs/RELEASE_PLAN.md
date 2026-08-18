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

1. **Phase 8 content** (PR #32): T20/ODI/Test formats, international tournaments
   and bilateral series, all-time ODI/Test draft pools, world franchises.
   Already built; merged once CI is green.
2. **Gameplay analytics events** — draft started/completed/abandoned, match
   started/completed, season completed, screen views, `$device_model`.
   Small, low-risk, and unblocks measuring everything else.
3. **Account data bleed on sign-out/sign-in** (`KNOWN_ISSUES.md`) — a privacy
   bug, and cheap: scope the `active_career_id` storage key per user id.
4. **Tutorial "career not found" on first run** — a first-run crash in a release
   whose whole theme is first-run retention.

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
  differ. Worth aligning, but *after* this release.
- **18 open Dependabot vulnerabilities (15 high) on main**, plus 6 open
  Dependabot PRs. Triage the high ones before the next release.
- We ship blind on crash rates: the Sentry credentials in `secrets/ids.txt` are
  ingest-only DSNs. Generate a Sentry **auth token** so crash-free-session rate
  can go in this checklist.

---

## After shipping

1. Watch crash-free session rate and the new funnel events for ~a week.
2. Then use that baseline to judge the retention work (draft escape hatch,
   no-draft default for a first career, shorter tutorial).
3. Only then revisit the in-app rating prompt — asking for reviews while every
   user is on 1.0.0 would collect ratings for a build we have already replaced.
