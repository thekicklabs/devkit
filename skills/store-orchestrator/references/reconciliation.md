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

## Failure and rerun behavior

- Stop dependent writes on failure. Continue independent operations only if already approved and unaffected. Report succeeded/failed/blocked/unknown operations, with IDs and recovery steps.
- After a timeout on a create/write, query by exact identity and inspect outcome before retrying. If the outcome cannot be established, stop that operation. Use idempotency features only when actually supported.
- Allow at most three bounded retries for clearly transient read failures or confirmed safe retryable operations, respecting provider limits. Do not loop on authentication, permission, validation, or unknown-result errors.
- Do not automatically roll back by deleting products, reversing prices, or changing a current offering; compensating mutations may be irreversible and need a concrete approval.
- On rerun, read current state, normalize comparisons (including keyword serialization, decimal values, ordering semantics, effective schedules), skip matches, and propose only remaining differences. No duplicate creation and no unrequested pruning.
