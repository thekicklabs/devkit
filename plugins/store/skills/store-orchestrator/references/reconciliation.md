# MCP discovery, reconciliation, and recovery

## Capability check

Discover currently callable tools and read their actual schemas. An App Store Connect server may expose named tools or an API operation search/execute interface. With generic execution, discover method/path/input and side effects before calling; a generic execute tool is not evidence that every Apple operation exists. Do not hardcode a community implementation or a tool count.

Build a small capability table for the operations this run needs:

| Service | Read/resolve | Potential writes, only after approval |
|---|---|---|
| ASC | Account/app identity, editable version, locales, products/groups, price points/schedules, availability, assets, build/review state | Metadata, supported resource creation, prices, availability, asset upload/order, review submission/release |
| RevenueCat | Project/app identity, store mappings, products, entitlements, offerings/packages, current offering, paywalls | Product import/create, entitlement attachment, offering/package configuration, approved current offering/paywall changes |

Distinguish missing server from authentication failure, insufficient role/scope, wrong account, unsupported operation, or transient outage. Never treat any of these as “resource does not exist.” Authentication setup is a user action through supported auth flows; never ask users to paste Apple `.p8` contents or secret RevenueCat keys into chat/YAML.

For missing RevenueCat, provide its official setup link and hosted MCP endpoint `https://mcp.revenuecat.ai/mcp`. As a documented Codex CLI option (recheck current docs when giving commands):

```bash
codex mcp add RevenueCat --url https://mcp.revenuecat.ai/mcp
codex mcp login RevenueCat
```

Use the same configured server name when logging in. For ASC, ask the user to connect their chosen trusted implementation with access to the correct Apple team/app and the needed operations. Do not invent an Apple-hosted MCP URL or automatically install a community package. If the chosen MCP cannot create the initial app record, mark app creation as a manual prerequisite and continue preparing its fields.

Sources to refresh at execution time:
- [RevenueCat setup](https://www.revenuecat.com/docs/tools/mcp/setup)
- [RevenueCat tool reference](https://www.revenuecat.com/docs/tools/mcp/tools-reference)
- [Apple API reference](https://developer.apple.com/documentation/appstoreconnectapi)

RevenueCat may expose operations that create store products. Treat those as Apple mutations too. Select one supported write route per resource and verify the resulting store object; do not create the same product through both MCPs. Apple is authoritative for Apple catalog/prices/availability; RevenueCat is authoritative for entitlement/offering configuration. Both can affect production even when the next app version is a draft.

## Plan and apply

1. Resolve target identities and list existing objects with pagination. Match Apple bundle/product IDs and RevenueCat project/app/store mapping. Bind the plan to these exact identities and observation time. Report code/config/remote drift; proposed YAML values win only within an explicitly approved diff.
2. Resolve constraints read-only: editable version/state, immutable fields, locale support, real price points and schedules, asset requirements, capabilities/roles, existing offering effects. Unsupported operations become manual tasks. Never delete/recreate a product to “fix” an immutable mismatch.
3. Create `store-plan.md` with a plan identifier, desired-config digest, target identities, rows `{operation, target, before, after, dependencies, impact, status}`, concrete local diff, questions, and the bounded approval request. Include full text changes and price/territory details, using an attached file when long. Display no secrets.
4. After approval, re-read the affected fields. A material change invalidates that operation's plan; unchanged independent approved operations remain authorized. Skip exact matches. Preserve unrelated fields and unmanaged objects.
5. Execute dependencies in order where supported: app/version prerequisites → subscription groups → Apple products/localizations → resolved price schedules/availability/review assets → RevenueCat store products → entitlement mappings → offerings/packages → separately approved current offering/paywall changes. Metadata and listing media may proceed independently when their prerequisites are met. Build upload, submission, and release are separate scopes.
6. For screenshots/previews, validate and inspect first, then use actual supported reservation/upload/finalization steps, checksums, ordering, and bounded processing-status polling. A created upload record or successful byte transfer is not processed media. Report pending processing accurately.
7. Re-read results and record exact IDs, normalized observations, timestamps, source config digest, and outcomes in `store.state.json`. This file is a cache/audit aid, not a provider database, approval token, or substitute for read-before-write. Keep it secret-free.

Never use test-mode purchase data as evidence that Apple catalog writes are sandbox-only. Explain scheduled versus immediate changes and any subscriber-consent implications using current provider behavior. Never accept contracts, supply tax/banking data, or certify declarations on the user's behalf as incidental setup.

## App Store Connect resource traps

Learned on real runs; each one either hid a blocker behind a green read or turned an
approved write into a 4xx. Check them before planning the affected operation.

- **App price: read the rows, not the schedule.** `GET /v1/apps/{id}/appPriceSchedule`
  returns a record with a base territory even when the app has no price at all. Only
  `appPriceSchedules/{id}/manualPrices` (and `automaticPrices`) prove a price exists; an
  empty list means the app cannot be submitted and the ASC page shows "Add Pricing". Free
  is a real price point (customerPrice `0.0`) that must be set like any other, via
  `POST /v1/appPriceSchedules` with the app, base territory and an inline `appPrices` row.
- **Subscription prices do not equalize themselves through the API.** A price created with
  one territory leaves the other territories empty; RevenueCat reports "only 1 territory
  price provided" and the product stays MISSING_METADATA. Read
  `subscriptionPricePoints/{usaPoint}/equalizations`, show the full table, then
  `POST /v1/subscriptionPrices` once per territory with `preserveCurrentPrice: true`.
- **The initial subscription price also needs `preserveCurrentPrice: true`.** Without it
  the first `POST /v1/subscriptionPrices` returns a bare 409 with no attribute named.
- **App availability (v2) is create-once.** A second `POST /v2/appAvailabilities` returns
  409. Change a single territory with `PATCH /v1/territoryAvailabilities/{id}` (ids come
  back only with `include=territory`). `availableInNewTerritories` has no write route after
  creation: it is an owner action in Pricing and Availability → App Availability → Manage,
  readable afterwards to verify.
- **Subscription availability is replace-on-POST**, so it can be re-posted with the full
  territory list and the flag together.
- **Age rating declaration types.** `ageAssurance` is a boolean, not an enum; the write
  is rejected with a 409 naming the attribute if sent as a string. Other content fields
  take `NONE`/`INFREQUENT_OR_MILD`/`FREQUENT_OR_INTENSE`. The computed store rating and the
  override are both visible on the appInfo/declaration after the write.
  `socialMediaAgeRestricted` must stay null unless `socialMedia` is true.
- **First-version metadata limits.** `whatsNew` is rejected on an app's first version;
  set it from the second version on. An extra locale left incomplete (name only, every
  other field empty) blocks submission; deleting it is a destructive operation under its
  own approval. A primary-locale change is applied with a lag; re-read before treating it
  as failed.
- **`PATCH versionString` is non-destructive.** Renaming a version (e.g. `1.0` → `1.0.0`)
  keeps localizations, screenshots, review detail and release type on the same record;
  no re-upload is needed.
- **Subscription review screenshots need an exact device size.** 923×2000 fails with
  `IMAGE_INCORRECT_DIMENSIONS`; a native iPhone capture (e.g. 1179×2556) passes. Images
  relayed through chat are often downscaled, so check dimensions before reserving the
  upload, and flatten alpha. A failed record must be deleted before a new reservation.
- **The MCP sandbox cannot send bytes.** Reserve via the API, `curl -X PUT --data-binary`
  to the returned URL with its `requestHeaders`, then PATCH `uploaded: true` with the MD5.
  The sandbox also has no `setTimeout`; poll with separate calls.
- **The API cannot read App Privacy, EU trader status or the tax category** (the last two
  live on the Agreements page and Pricing and Availability). These are owner attestations
  recorded from screenshots or the owner's word, never "verified by API".
- **Build bundles come through `include`, not the relationship route.**
  `GET /v1/builds/{id}/buildBundles` is denied, but `GET /v1/builds/{id}?include=buildBundles`
  returns them. `sdkBuild`/`platformBuild` (e.g. `23A339` = iOS 26.0 SDK) verify the SDK
  minimum, `entitlements` lists every bundle including extensions and their app groups, and
  `minOsVersion` sits on the build itself.
- **Swapping the build on a version.** `PATCH /v1/appStoreVersions/{id}/relationships/build`
  replaces it; verify with `GET /v1/appStoreVersions/{id}/build`. Export compliance is per
  build (`usesNonExemptEncryption`), so re-check it after every swap.
- **Reviewer credentials are readable.** `GET /v1/appStoreReviewDetails/{id}` returns the
  demo account, contact and notes; read it live to answer "are the reviewer credentials in"
  before submitting rather than trusting the plan.
- **Subscriptions are not accepted as `reviewSubmissionItems`.** Posting an item with a
  `subscription` relationship returns 409. The owner adds each subscription from its own
  product page in ASC ("Submit for Review" there only adds it to the open draft). The
  `appStoreVersion` item can be added via the API to the same draft, and the draft is sent
  with `PATCH /v1/reviewSubmissions/{id}` `submitted: true`. Decode the draft's warnings:
  "new subscription groups must be submitted with an auto-renewable subscription from
  within that group" = add a subscription item; "add an app version for the selected
  platform" = add the version item.
- **Proof the subscriptions went with the version** is their state flipping
  `READY_TO_SUBMIT` → `WAITING_FOR_REVIEW`. A version waiting while its subscriptions stay
  ready means they were left out. First subscriptions must ship with a new app version, so
  cancel and resubmit rather than let the version be approved alone.
- **Cancelling a submission.** `PATCH /v1/reviewSubmissions/{id}` `canceled: true`; the
  state goes `CANCELING` → `COMPLETE`, the version becomes `DEVELOPER_REJECTED` (normal,
  still editable) and the attached build survives. Re-read with a separate call.
- **ITMS warnings arrive only by email** to the account holder after a build processes;
  ask for a yes/no rather than claiming none exist.
- **Internal TestFlight testers are not invited by adding them.** A tester added to an
  internal group before the group holds a build sits at `state: NOT_INVITED` with no email.
  `POST /v1/betaTesterInvitations` sends it; the build appears in TestFlight only after the
  invite is accepted on the same Apple ID the device uses.
- **EAS stores no ASC submit key by default.** `eas submit --non-interactive` fails with
  "App Store Connect API Keys cannot be set up in --non-interactive mode"; the owner runs
  the first submit interactively. The EAS Xcode build log downloads as an opaque blob, so
  the toolchain version cannot be confirmed from it.

## Failure and rerun behavior

- Stop dependent writes on failure. Continue independent operations only if already approved and unaffected. Report succeeded/failed/blocked/unknown operations, with IDs and recovery steps.
- After a timeout on a create/write, query by exact identity and inspect outcome before retrying. If the outcome cannot be established, stop that operation. Use idempotency features only when actually supported.
- Allow at most three bounded retries for clearly transient read failures or confirmed safe retryable operations, respecting provider limits. Do not loop on authentication, permission, validation, or unknown-result errors.
- Do not automatically roll back by deleting products, reversing prices, or changing a current offering; compensating mutations may be irreversible and need a concrete approval.
- On rerun, read current state, normalize comparisons (including keyword serialization, decimal values, ordering semantics, effective schedules), skip matches, and propose only remaining differences. No duplicate creation and no unrequested pruning.
