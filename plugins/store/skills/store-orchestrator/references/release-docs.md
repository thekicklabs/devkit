# Project artefact conventions

The shape of the files this skill writes into a project, learned on real runs. Use it
when the repository has no equivalent convention; when it has one, keep the project's
and note the differences. Nothing here stores a secret, a password or a contact value.

## Repo layout

```
store/
├── ios/<locale>/           name, subtitle, keywords, promotional_text, description,
│                           release_notes as .txt, mirroring fastlane `deliver`
├── ios/review/             subscription review screenshots
├── screenshots/            listing screenshots (see the store-screenshots skill)
├── store.yaml              desired state (this skill's format)
├── store.state.json        observed remote state, non-secret cache
├── store-plan.md           batches: evidence, operations, approvals
├── release-readiness.md    gate-by-gate report
├── privacy-and-age-rating.md  declaration answers with reasons
└── README.md               layout, limits, rules, fixed fields not stored here
```

- The `deliver` layout costs nothing now and lets metadata upload be automated later
  without moving files.
- Note each field's Apple limit beside its file in the README; the check is
  `wc -m ios/<locale>/{name,subtitle,keywords,promotional_text}.txt` before every write.
- Keywords never repeat a word already in the name or subtitle.
- The marketing version is always three-part `X.X.X` (`1.0.0`, never `1.0`), the same
  string the app config declares (Expo `version`, `CFBundleShortVersionString`,
  `versionName`). Create the ASC version with that string; a two-part version created
  earlier is renamed with `PATCH versionString` (see the traps in
  [reconciliation](reconciliation.md)). Build numbers increment independently on every
  upload and are never part of the marketing version.
- Release notes are bumped in the same commit as the version bump.
- The README ends with a "fixed ASC fields not stored here" list (categories, URLs,
  primary locale, bundle id) so nobody hunts for them in the txt files.

## store-plan.md

One heading per batch (`batch A`, `batch B`, …), appended in order, never rewritten.
Each batch has:

- plan id (`batch-d-<date>`), targets with ids and their states, observation time, and
  the desired-state sources (`store.yaml`, txt files, declaration doc);
- a negative scope line: "no submission, no release, no pricing" (or whatever this batch
  does not do), and the approval line with who approved and when;
- an operation table `# | Operation | Target | Before | After | Status` with op ids
  (`D5`, `B8`) that other documents cite as evidence; name the endpoint in the Operation
  column when it was non-obvious;
- a "Not written by this batch" list for the owner UI tasks (agreements, banking, tax,
  App Privacy, new-territories flag);
- "Still open", numbered, updated as items close.

Gotchas go in the row where they were hit, not in a separate notes section. An audit
mistake is corrected in writing in the row that fixes it ("the earlier audit misread this
as free"), never silently.

## release-readiness.md

- First line: "Updated <date> after <event>", then per-provider last-read times and a
  pointer to `store.state.json` for ids.
- The four-status vocabulary (verified, pending, blocked, not applicable) and one bold
  state line: version, build, what is submitted, what is not released.
- Three tables, setup / submission / release, each
  `Item | Applicability | Status | Evidence/date/build | Owner | Next action`.
  Owner is `agent`, `user` or `user + agent`. Next action is `none` or an imperative
  with a date. Evidence names a build number, an op id, or a live re-read date.
- Then the TestFlight smoke script, then a dated Apple references list with one line on
  what each page decided.

Starting row inventory (drop what does not apply, explain why):

- Setup: team and app access, RevenueCat access, app identity, version/build policy,
  agreements and banking, EU trader status, tax category, app availability, subscription
  availability, store copy and URLs, terms and privacy policy live, app icon, categories
  and primary locale, RevenueCat integration, subscription lifecycle events.
- Submission: listing screenshots, subscription review screenshots, subscription review
  notes, first subscription submission, App Privacy answers, age rating, content rights,
  UGC classification, export compliance, SDK minimum, privacy manifests, required-reason
  APIs, each extension target, each permission purpose string, analytics GeoIP,
  authenticated legal/support links, account deletion disclosure, account deletion
  cleanup, review access, reviewer notes, correct processed build, TestFlight smoke,
  purchase behavior.
- Release: remote mutation approval, review submission, manual release, post-release
  checks.

## store.state.json

- Top level: `observed_at`, a `source` slug naming the event that produced it
  (`review-submitted-<date>`), then `asc` and `revenuecat` trees.
- Secrets and contacts are pointers, never values: `"credentials_ref": "backend env
  REVIEW_ACCOUNT_*"`, `"contact_set": true`.
- Every ASC build is joined to its CI build id and git commit, and the CI build counter
  sits beside the ASC build number so a mismatch is visible.
- Cancelled or failed attempts are first-class objects (`cancelled_review_submission`
  with items and a note), not deleted.
- A field that only records an API limitation says so: `"api_readable": false`.
- Never bump a number by hand after a new build; re-read and rewrite the object.

## TestFlight smoke skeleton

Run on the exact build to be submitted. Each step names the readiness row it closes.

1. Both sign-in paths: production auth and the reviewer credentials.
2. Primary create path plus every permission surface (microphone, camera, photo library,
   notifications).
3. Each ingestion path (share extension, email forwarding, import).
4. External content and one outbound link where the app shows third-party results.
5. Public-share lifecycle: publish, open the link signed out, unpublish, confirm 404.
6. Push end to end: enable, trigger, receive.
7. Paywall with localized prices and renewal disclosure, sandbox purchase, restore,
   subscription management surface.
8. Account deletion on a disposable account: the subscription warning, the management
   link, cancel once, then delete and confirm asynchronous cleanup (public links, stored
   files) after the documented window.

## Reviewer account

- A seeded demo account with a fixed OTP code read from the backend environment, so the
  reviewer needs no mailbox. Kept on the free tier so the reviewer can sandbox-purchase.
- App review notes template: how to sign in (fixed code, no email is sent), what is
  pre-populated, a pre-emptive explanation of anything a reviewer might flag (unlisted
  sharing, web results with citations), and why the account is on the free tier.
- Separate per-subscription review notes with the navigation path to the paywall and what
  the subscription unlocks.

## Declaration reasoning

`privacy-and-age-rating.md` holds one row per questionnaire field including the
`NONE`/`false` ones, each with a one-line reason drawn from the code. Patterns that held
up:

- Chat with an AI is not messaging.
- Cited search results shown inside the app are not unrestricted web access.
- No feed and no discovery means no social media.
- Unlisted, owner-shared direct links are argued as UGC No, with the escalation plan
  written down (reporting, blocking, moderation and contact controls) in case App Review
  objects.
- Content rights is Yes whenever third-party results or snippets are shown.

## Commits

`docs(store): <what is now true>`, one per applied batch or state transition
("record the 1.0.0 review submission", "record the cancelled submission"), so the git
log of the store directory is the release timeline.
