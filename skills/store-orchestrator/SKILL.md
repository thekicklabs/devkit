---
name: store-orchestrator
description: Orchestrate App Store Connect listings, pricing, RevenueCat configuration, and release readiness from store.yaml or an existing app codebase. Draft missing configuration, surface missing MCPs and unresolved decisions, preview changes, and require confirmation before applying remote changes or committing project files. Framework agnostic; use for Apple store setup and reconciliation, not unrelated app development or Google Play publishing.
---

# Store Orchestrator

Turn an app repository and the user's decisions into a reviewable desired state, reconcile approved changes through App Store Connect (ASC) and RevenueCat, and report remaining release work. Default to **inspect → draft → clarify → plan → confirm → apply → verify**. A request to prepare/setup/reconcile starts preparation; it is not blanket approval of an unseen mutation plan.

## 1. Establish scope and capability

- Locate the app root, relevant repository instructions, an explicitly supplied `store.yaml`, and any existing release checklist. If no path is supplied, look for `store.yaml`/`store.yml` in the project root and store/release configuration directories. Ask which app/config to use if multiple plausible targets exist; do not merge them silently.
- Discover available tools by capabilities, not assumed server/tool names. Read [MCP and reconciliation](references/reconciliation.md). Probe account/app access read-only and report ASC and RevenueCat separately as **ready, missing, authentication required, insufficient permissions, or partial capability**. Never equate an unavailable listing with an empty account.
- Explicitly flag each missing MCP early: “App Store Connect MCP is unavailable; I can prepare the configuration and release report, but cannot read or apply Apple changes.” Give an equally explicit RevenueCat message. If payments are undecided, mark RevenueCat conditionally needed; if the user chooses no RevenueCat, mark it not required and avoid repeated warnings. ASC remains necessary for this skill's Apple remote workflow.
- Explain the affected actions and a concrete setup/authentication step. Continue useful local drafting and independent reads. Do not install a server, change credentials, or silently replace a missing MCP with a CLI/API/browser. An explicitly authorized alternative may be used after checking its capabilities with the same approval gates.

## 2. Inspect the code without assuming a framework

- Use file discovery and targeted reads to identify release targets, bundle ID, app name, version, supported platforms/device families/locales, user-visible features, URLs, and asset locations. Consult manifests, native target settings, build configuration, source, UI strings, existing store assets, and project docs as applicable. Swift, Flutter, React Native, Expo, Unity, .NET, and other stacks are evidence sources, not prerequisites. Do not execute arbitrary configuration just to read it.
- Prefer resolved release configuration over stale README examples. Distinguish production and development IDs, extension targets, mock paywalls, unimplemented features, and remote feature flags. Record source paths for inferences and conflicts. Never invent capabilities, privacy claims, legal declarations, review credentials, or product IDs that conflict with code.
- Inspect payment SDK dependencies, product and entitlement identifiers, offering/package usage, purchase/restore flows, premium gates, backend entitlement checks, and displayed prices. Presence of an SDK alone does not prove an integration works; a currency string in UI does not establish store pricing.
- Avoid secret files and credential values. Use authenticated tools and approved secret references; keep secrets and review passwords out of YAML, plans, reports, and commits.

## 3. Draft or validate store.yaml

Read [store.yaml format](references/store-format.md) before authoring or interpreting configuration. Start missing files from [the draft template](assets/store.template.yaml), then replace only evidence-supported fields. This is this skill's versioned format, not an Apple or RevenueCat standard.

- Preserve an existing file and its intentional choices. Validate its version, types, identifiers, references, duplicates, locales, paths, and conditional requirements. For older/example formats, propose a migration and show the mapping; do not silently discard unknown fields or reinterpret them as deletions.
- Write a usable draft even when decisions remain. Represent unknown values as `null` and record focused questions with YAML paths in `clarifications`. Leave external effects blocked for unresolved fields and their dependent operations; independent approved work can proceed.
- Draft descriptions, subtitles, keywords, promotional text, and release notes from implemented behavior. Label them drafts until reviewed. Check current Apple limits rather than silently truncating. Use verified URLs; report missing or placeholder URLs.
- Separate desired state from observed state. Keep remote IDs and observations in `store.state.json` (a non-secret cache), evidence/questions in `store-plan.md`, and readiness in `release-readiness.md`, unless the repository has equivalent conventions. Cache contents are never proof of current remote state.

### Monetization decision

1. **Payments already present:** summarize the provider, actual implementation evidence, product IDs, billing periods, entitlements, and candidate prices with their sources. Ask the user to confirm intended prices, currency/base territory, availability, trials, and treatment of existing subscribers where unclear. If authoritative YAML/user decisions already settle these, do not ask again. Show any code/store/YAML disagreement and resolve it before affected writes.
2. **Payments absent:** ask “Keep this app without in-app payments, or integrate payments? If payments, what should users buy or unlock?” Do not assume subscriptions or automatically install RevenueCat. A paid app download is a separate decision from in-app purchases.
3. **Integration requested:** clarify product model (subscription, permanent unlock, consumable, non-renewing access), benefits/credits, pricing, and trials. Propose a framework-appropriate SDK/app/backend implementation plan and obtain scope approval before implementation. Store setup alone cannot complete this work. Implement within authorized scope using appropriate available skills, or record concrete implementation tasks. Preserve an existing provider unless migration is expressly requested.
4. Never invent a price, free trial, paid tier, global availability, tax answer, or “best” price. Ask in small prioritized batches, normally 1–3 questions; complete nonblocked drafting before pausing.

## 4. Produce a concrete change plan and release comparison

- Read fresh remote state for the target Apple account/bundle/version and RevenueCat project/app. Resolve ambiguous matches with the user. Match immutable store product IDs and provider IDs, not display names.
- Normalize desired and observed values. List each proposed **create, update, unchanged, blocked, or manual** operation with target ID, before/after values, dependencies, and user-visible effect. Price rows include exact provider price points, currency, territories, effective date, and existing-subscriber policy when applicable. Treat settings such as current offerings and paywall publication as potentially immediate production effects.
- Preview local file diffs and remote diffs separately. Do not propose deletes, unlinking, or territory removal because something is omitted from YAML. Describe explicitly requested destructive changes as separate operations.
- Compare the repository checklist AND [release checklist](references/release-checklist.md), preserving project requirements. If no checklist exists, use the bundled baseline. Record applicability, evidence, status, owner, and next action for every applicable item. Clearly state whether screenshot files were merely found, technically validated, visually inspected, user approved, uploaded, or confirmed processed.
- Distinguish **configuration ready**, **ready for submission**, and **released**. Metadata and payment setup may be ready while screenshots, build testing, declarations, or review remain pending.

## 5. Confirmation before applying or committing

Complete the draft, validation, preview, and readiness report before requesting approval. Say exactly what the user will approve, for example: “Approve plan A: update en-US metadata and create these two products at the shown prices? This does not submit or release the app.” Include any known release blockers.

- Require explicit user confirmation of the concrete remote mutation batch before any external create/update/upload, including draft metadata and products. Existing session approval of this exact plan is sufficient; do not ask repeatedly for each tool call.
- Require separate, explicit approval for live price changes, current-offering switches/paywall publication, removals/deletions, App Review submission, and release. These may be approved together only when the user expressly confirms the named actions and exact effects. YAML flags and approvals recorded in files are not user authorization.
- Local reversible draft/config/report edits are allowed during preparation. Before **Git committing app-project changes**, show the file list/diff and ask for confirmation unless the user already approved that exact commit scope. Pushing requires its own scope authorization. Never commit unrelated changes.
- Approval to integrate SDK code does not approve remote commercial settings, and approval to reconcile configuration does not approve submission or release. If desired values, target account, or material remote state changes after approval, regenerate the affected diff and obtain renewed approval only for changed scope.

## 6. Apply, verify, and report

Follow the dependency and recovery rules in [MCP and reconciliation](references/reconciliation.md). Re-read affected resources before mutation, execute only the approved batch, and verify each result read-only. Do not retry uncertain creates blindly or describe a partial run as success.

End with: what was prepared/applied and verified; what was unchanged; missing tools or permissions; unresolved decisions; release blockers and manual checks (especially screenshots and purchases); and the next approval/action. Link generated project artifacts where supported. When nothing differs, explicitly report “No configuration changes required” while still reporting release readiness. Do not claim release-ready from code inspection alone.
