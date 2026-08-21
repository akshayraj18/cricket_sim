# Asking for an App Store rating

**Shipped 2026-08-21.** Two separate paths, because Apple treats them
differently:

| | Trigger | Mechanism |
|---|---|---|
| **Automatic** | Finishing a 2nd season | System rating prompt (`expo-store-review`) |
| **Manual** | Settings → "Rate CricSim" | Link to our App Store page |

---

## The constraint that shaped this

The obvious design — *"Having a good time? Rate us! [Yes] [Not now]"* — is
**not allowed**. App Store Review Guideline 1.1.7 requires the system API and
disallows custom review prompts, and Expo's own SDK docs say the same in
shorter form: *"No pre-review questions."* A custom dialog that gates or
imitates the system prompt is a rejection risk, not a style preference.

So there is no pre-prompt. The system prompt is requested directly at a good
moment, and the user's answer is between them and iOS.

The reason the pattern is so common in other apps is that it used to be
allowed, and plenty of apps still carrying it predate the rule. It is not a
signal that it is safe.

## Why "finishing a season"

Expo's guidance is to ask "after the user has finished some signature
interaction". Season completion is the clearest one the game has:

- It is a genuine accomplishment, not a routine action.
- It is rare. A match win happens constantly and would make the request feel
  arbitrary.
- The usage data supports it: 27 of 48 careers have played 71+ matches, so
  people who reach a season end are the engaged ones worth asking.

It is wired into `useFunnelTracking`'s `season_completed` transition rather
than to a screen, because that hook already guarantees the three properties the
prompt needs, each of which had to be got right for analytics anyway:

- fires **once per real transition**, not once per refetch;
- **never on first observation** of a career, so a cold start cannot trigger it;
- **silent during the guided tour**, which races a demo career through a season.

Reimplementing that detection elsewhere would mean reimplementing those bugs.

## The local guards

iOS shows roughly **three prompts per year** and silently ignores the rest.
`requestReview()` resolves either way, so **a wasted request is invisible** —
there is no error, no signal, nothing. That is precisely why the gating is
local and tested (`services/__tests__/store-review.test.ts`):

- **At least two completed seasons.** Per the plan in `ideas.txt`: the prompts
  should go to people who kept playing, not to everyone who reaches a first
  season end. This is the gate that keeps the 64% one-and-done cohort from ever
  seeing it. One constant (`MIN_COMPLETED_SEASONS`) if it proves too strict.
- **Once per app version.** Stops a player finishing several seasons in one
  sitting from burning every slot.
- **120-day cooldown.** Longer than a season takes.
- **Three asks, ever.** Someone who has ignored it three times has answered.
- **A corrupt or future-dated timestamp counts as "too soon"**, so a clock
  change cannot unlock an extra prompt.

The state is written **before** the request, not after: if the write failed
afterwards we would ask again next season, which is the failure mode worth
avoiding.

`isAvailableAsync()` / `hasAction()` are checked **after** the local guards, so
a TestFlight build (where the API reports unavailable) neither burns an ask nor
moves the cooldown.

## Failure is silent by design

`maybeRequestReview()` never throws and never surfaces anything. Failing to ask
for a review is not a problem the user can act on, and an error toast about it
would be worse than the missing prompt. `expo-store-review` is loaded with a
guarded `require()` for the same reason the CSV feature does it — see
`CSV_ROSTER_IO.md`.

## Configuration

The App Store ID is **`6779728013`**, committed as the default in
`api/config.ts`. It is public information — it is in our own store URL — and
hard-coding it means the Rate row works in a local dev build, not only in EAS
builds. `EXPO_PUBLIC_APP_STORE_ID` still overrides it.

To find it again: App Store Connect > your app > App Information > **Apple ID**,
or the digits in `apps.apple.com/.../id<digits>`. It can also be looked up from
the bundle ID with no login:

```
curl -s "https://itunes.apple.com/lookup?bundleId=com.akshraj.cric" | jq .results[0].trackId
```

If the ID is ever cleared, `RATE_APP_URL` becomes null and the Settings row
hides rather than opening a broken page.

The automatic prompt needs no configuration.

## Testing it

The system prompt **cannot be triggered on demand**, and does not appear at all
in TestFlight builds. On a development build it appears at most three times per
year per device. To re-test, delete and reinstall the app, or clear the
`cricket_sim.review_*` keys.

The gate logic is unit-tested and does not require any of that.

The **Settings > Rate CricSim** row, by contrast, is testable immediately: it
opens the store listing every time, with no quota and no gating. That is the
only part of this feature a person can verify by tapping it.

## Timing note

An earlier plan deferred this on the grounds that asking for ratings while
everyone is on 1.0.0 would collect reviews for a build already replaced. That
concern resolves itself here: the prompt ships *in* v1.1, so anyone who can see
it is already running v1.1.
