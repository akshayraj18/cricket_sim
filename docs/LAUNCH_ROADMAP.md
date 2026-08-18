# Launch Roadmap — App Store + Google Play

Status legend: ☐ not started · ◐ partial · ☑ done

---

## 0. Blockers (must resolve before either store will approve)

### 0.1 ☑ IP-safe content
- Parody team names throughout (no "IPL", "Mumbai Indians", real abbreviations)
- Player names are fictional but recognizable — IP-safe convention already applied
- *(Country and city names are not protected — India, Australia, Mumbai, etc. are fine)*
- Roster editor in squad screen lets users rename teams/players (standard workaround)
- Phase 8 regression, fixed 2026-08-18: the three all-time pools
  (`players_alltime_{odi,test,t20_intl}.csv`) and the current national squads in
  `international_data.py` shipped with **real** player names — 465 of them.
  `international_data.py` even documented the rename as deliberately deferred.
  All are now renamed via `tools/ip_safe_rename.py`, whose `PLAYER_MAP` is the
  audit record. **Re-run `--check` before any release that adds player data**;
  it reports any real name that has not been mapped.

### 0.2 ☐ In-app account deletion  *(Apple Guideline 5.1.1(v) — required)*
- Backend: `DELETE /auth/me` removes user, careers, tokens
- Mobile: "Delete account" action in account sheet with confirm dialog

### 0.3 ☑ Privacy policy
- Hosted at `https://akshayraj18.github.io/cricket_sim/legal/privacy-policy.html`
- Apple privacy nutrition labels + Google Data Safety form filled to match

---

## 1. Backend (already live on Railway)

- ☑ Railway deployment: Postgres + Redis managed add-ons
- ☑ Production env vars set (ENVIRONMENT=production, JWT_SECRET, DATABASE_URL, REDIS_URL)
- ☑ Alembic migrations applied to production DB
- ☑ Health check: `https://<railway-url>/health` → `{"status":"ok"}`
- ☑ HTTPS/TLS provided by Railway automatically
- ☐ Cloudflare (or Railway WAF) in front for DDoS protection *(optional but recommended)*

---

## 2. Mobile app → production backend

- ☑ `EXPO_PUBLIC_API_URL` set to Railway backend URL in EAS production profile
- ☑ Apple bundle ID + Sign in with Apple capability provisioned on paid team
- ☐ Google sign-in production OAuth client IDs verified (see KNOWN_ISSUES.md)

---

## 3. Build + submit

- ☑ Apple Developer Program ($99/yr)
- ☑ EAS Build configured (production profile with prod API URL + Sentry/PostHog keys)
- ☑ App Store listing assets (screenshots, icon, description, keywords)
- ☑ Initial App Store submission submitted and approved
- ☑ App live on App Store (CricSim, 4 downloads as of Jul 2026)
- ☐ Google Play Console ($25 one-time) — not yet started

---

## 4. Security backstops

- ☑ Application security hardening (JWT enforcement, CORS allowlist, rate limiting)
- ☑ Sentry crash reporting (backend + mobile)
- ☑ PostHog analytics
- ☐ GitHub Dependabot alerts enabled
- ☐ GitHub secret scanning enabled

---

## 5. Post-launch follow-up

- ☐ Account deletion flow (0.2) — before wider App Store push
- ☐ Account data bleed fix (see KNOWN_ISSUES.md) — before wider rollout
- ☐ iPhone display QA pass (see KNOWN_ISSUES.md)
- ☐ Google Play listing and submission
- ☐ Monetisation (Phase 6 — see ideas.txt)
