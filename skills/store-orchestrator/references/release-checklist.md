# Release-readiness baseline

Use this baseline alongside the project's release checklist. Preserve project-specific gates and compare overlaps; do not silently replace a stricter requirement. Verify current Apple requirements for the app's platforms, regions, business model, and release type. This baseline is a working checklist, not a claim of exhaustive or permanent Apple policy.

## Status and evidence

For each row record: `item | applicability | status | evidence/date/build | owner | next action`.

Statuses: **verified**, **pending**, **blocked**, **not applicable**. Explain not-applicable decisions. Use pending for unperformed checks and missing evidence; blocked for a known unmet prerequisite/failure. A dependency manifest, filename, or user's old checkmark is not proof of a tested current build. Record user attestations explicitly as such and check whether the evidence still applies.

Group the report by setup readiness, submission readiness, and actual release state. Highlight blockers and distinguish optional improvements. Readiness requires all applicable submission gates verified; “awaiting approval” remains separate. App acceptance/release must be confirmed from remote state, not inferred from a submission response.

## Baseline comparison

| Area | What to check and evidence needed |
|---|---|
| Account/access | Correct Apple team/app and RevenueCat project/app; effective permissions; relevant developer membership and paid agreements, banking/tax setup verified by account owner or provider state |
| App identity | Release bundle ID, version/build, signing/capabilities, selected platform and supported devices match the intended app and uploaded build; the ASC version string is three-part `X.X.X` and equal to the app config's version (rule in [release-docs](release-docs.md)) |
| Store copy | Name/subtitle/description/keywords/promotional text/What's New reflect shipped features; requested locales covered; current lengths and editability verified; copyright/categories set |
| URLs | Support and privacy URLs resolve to substantive correct public pages; marketing URL if supplied; EULA/terms applicable to paid features available |
| Screenshots | Required locale/device display sets determined from current Apple rules; technical and visual inspection; user content approval; upload/order/processing checked separately |
| Previews/icon | App icon present in the correct build/store location; previews checked if supplied or required; optional previews are not invented blockers |
| App privacy | Data collection/sharing and third-party SDK behavior assessed; privacy labels, permission explanations, tracking/consent and privacy manifests/required-reason APIs checked where applicable; owner confirms declarations |
| Compliance | Age rating, content rights, export/encryption, regional/trader and other applicable declarations confirmed with appropriate evidence; do not guess answers from library names. When the app's own terms set a minimum age above the computed rating, an age-rating override to that age is required (Apple's age-rating help page, cited in the readiness doc) |
| Review access | Notes, contact details, secure demo account/access instructions, working backend and reviewer-accessible premium features where needed; no secrets committed |
| Build quality | Correct processed build selected; relevant automated checks plus current device/TestFlight smoke evidence; crashes, auth/account flows, connectivity and core feature behavior checked. Before calling a processed build "correct", compare its commit to head for the app directory: `eas build:list --json` (or the CI equivalent) gives the commit, `git log <commit>..HEAD -- <app dir>` lists what the build lacks. A VALID, attached build that predates user-visible fixes is not the release build. When the app ships OTA updates, roll the production channel back to embedded before the TestFlight smoke so the tested binary runs its own bundle; verify with a manifest read-back and record which bundle the smoke exercised |
| Account features | Account deletion and relevant login requirements checked against actual app behavior and current applicable rules |
| Apple monetization | Intended products/groups/localizations, benefits/durations, price points, availability, trials, subscriber treatment and review materials verified; submission eligibility/state checked, including first-IAP requirements where applicable. The app's own price (including free) is verified from the schedule's price rows, not the schedule record; see the resource traps in [reconciliation](reconciliation.md). Keep test-store twin products attached to the entitlement so dev builds render the full paywall, and record both provider app ids in state |
| RevenueCat | Correct Apple mapping and credentials/notifications status as applicable; product imports, entitlements, offerings/packages and paywall match code and approved plan; SDK/backend environment appropriate |
| Subscription lifecycle events | Every RevenueCat webhook event type the app can receive is consumed and acted on by the backend: INITIAL_PURCHASE, RENEWAL, CANCELLATION, UNCANCELLATION, EXPIRATION, BILLING_ISSUE, PRODUCT_CHANGE, TRANSFER (carries `transferred_from/to`, not `app_user_id`), SUBSCRIBER_ALIAS, TEST. Evidence is a test per type or a dashboard "Send test event" whose worker log shows the resolved user and resulting status. Also verify the cancelled-but-still-entitled state (auto-renew off) is visible to the user and the backend. A missing type is a **blocker** to flag to the owner, not a note: a dropped TRANSFER leaves a paying user on 402 and the previous account entitled |
| Purchase behavior | On an identified current build: products load with localized prices; successful purchase, cancellation/error handling, entitlement unlock, restore (where applicable), expiry/renewal/revocation handling; consumable fulfilment and idempotency tested if applicable |
| Release control | Intended release method/schedule/timezone verified; approved submission scope names app version/build and any IAPs; release/publication has explicit authorization. Set the release type to manual before the first submission so acceptance cannot auto-publish. After sending, verify the version state, the attached build and each subscription's state from the API, not from the submission response |
| After release | Provider state confirms availability/release; planned smoke check and purchase/entitlement monitoring ownership recorded; do not mark complete before execution |

## Release-mode test builds

A local release-configuration build (for screenshots, smoke tests, or a TestFlight
rehearsal) behaves differently from a dev build in two ways that look like app bugs:

- **RevenueCat refuses Test Store keys in release binaries.** The SDK aborts launch with a
  message about protecting the security of test purchases when `Purchases.configure` receives
  a `test_` key and the bundle is not in dev mode. Either supply the production platform key
  (`appl_` / `goog_`) or, when the build only needs to run and the backend grants
  entitlement another way, blank the key at build time so configure is skipped (this only
  works if the app already guards against a missing key). Note in the readiness report
  which was done; a build without the key cannot exercise the paywall.
- **Build-time public env is baked in.** `EXPO_PUBLIC_*` values are read when the JS bundle
  is built, so a release build without the production env falls back to whatever default the
  config declares (often a localhost API URL). Confirm the values the production build will
  see, e.g. the EAS environment or the CI env, before treating any release-mode test as
  representative.

## Screenshot procedure

1. Inventory actual files by locale, platform, device/display type, and order. Check whether they correspond to the selected version/build. Find gaps relative to supported device families; do not assume phone-only or demand every device size without checking Apple's supported reuse rules.
2. Inspect file type, pixel dimensions, orientation, count, and other current provider constraints. Check screenshots and video previews separately. A dimension match proves technical eligibility only.
3. Open and inspect every asset intended for upload, or clearly enumerate uninspected assets. Check readability/cropping, localized text, stale branding/prices, accidental personal data, debug UI, unsupported feature claims, sequence, and faithful depiction of actual app use. If rendering/view tools are unavailable, report visual inspection pending; do not claim it happened.
4. Obtain user approval of the actual set and ordering in the mutation plan. Image generation cannot prove shipped UI; never silently fabricate app screenshots from code. If actual screenshots cannot be captured here, provide a precise capture list and leave capture pending. Generating marketing treatment around real captures is separate requested work.
5. After approved upload, verify server processing and assigned set/order. Report these stages independently: **found → technical checks → visual checks → user approval → upload → processing verified**. Product review screenshots are distinct assets with their own status.

## Current primary references

Consult these when their rules determine a decision, and include the relevant checked date/source in the report:
- [Apple screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/)
- [Apple App Store Connect Help](https://developer.apple.com/help/app-store-connect/)
- [Apple App Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [Submit an app](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-app/)
- [Set an app price](https://developer.apple.com/help/app-store-connect/manage-app-pricing/set-a-price/)
- [RevenueCat testing](https://www.revenuecat.com/docs/test-and-launch/overview)

If current documentation or remote state cannot be accessed, mark the affected requirement unverified and explain how to verify it. Do not label compliance or readiness verified from this static checklist alone.
