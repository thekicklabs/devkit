---
name: code-review
description: Review a diff as the engineer accountable for the system six months from now — find the few issues that materially affect correctness, invariants, failure modes, security, data, or design; try to disprove each against the surrounding code; report with severity and confidence, then hand off to the stack's own review checklist. Use when asked to review changes, a PR, or a branch.
---

# Code review

The job is not to find the most issues. It is to find the few that matter to whoever owns
this system in six months. Assume the author is competent and the code runs; look past
"does it work" to what it assumes, which invariants it touches, and what happens when
things go wrong. If the change is sound, say so — do not manufacture findings.

## 1. Read

Read the whole diff first. Then, before flagging anything, read around it: how the changed
code is called, what callers guarantee, what downstream expects, whether the framework or an
existing helper already handles it. An isolated diff line is not evidence.

## 2. Look for

Trace execution paths, not lines. Of the change as a whole ask: what does it assume, which
invariant could it break, what changes even though the API looks the same, what only shows
under production traffic, what gets harder next time.

| Dimension | Look for |
| --- | --- |
| Correctness | missing branch · boundary / off-by-one · null or empty · ordering assumption · stale data · unexpected mutation · type or serialisation mismatch · exception handling · happy path vs real input |
| Invariants | idempotency · uniqueness · exactly-/at-least-once · monotonic state transitions · transaction boundaries · authorisation boundaries · ownership · DB↔external consistency · retry safety. Call out any that is weakened, even implicitly |
| Failure modes | timeout · partial transaction · duplicate message · crash mid-operation · worker restart · malformed or unexpected-but-valid response · missing config · cancellation. Can it partially succeed? Does a retry then produce the right result? |
| Concurrency | race · lost update · duplicate processing · locking and isolation assumptions · cache consistency · out-of-order events · TOCTOU. Assume nothing runs exactly once or in order unless the architecture guarantees it |
| Data integrity | constraints · nullable · defaults · backfill · deletion · referential integrity · rollback · during a rolling deploy, old rows meeting new code and new rows meeting old code |
| Contracts | public and internal APIs · events · queue payloads · config · CLI · error format · ordering. Same schema with a different meaning counts |
| Security | authn/authz · privilege escalation · tenant isolation · injection · SSRF · path traversal · unsafe deserialisation · secret or personal data in code, config, logs, errors · caller-controlled input replacing trusted internal data |
| Performance | only what changes asymptotic behaviour or production resources: N+1 · unbounded loop or memory · repeated network calls · expensive work on the request path · missing batching · hot rows · retry storms. Ask what 10× and 100× look like |
| Operability | for each important new failure mode: can an operator tell what failed, for whom, whether it is safe to retry, how often it happens? |
| Design | logic in the wrong layer · duplicated policy · abstraction before its second caller · hidden dependency · global mutable state · implementation detail leaking through an interface · a simpler design that meets the same requirement |
| Tests | do they protect the behaviour that matters — transitions, boundaries, failures, retries, authorisation, malformed input — or just mirror the implementation? |

### House rules

Always BLOCKER:

- Tests not run, failing, or "passes" claimed without output.
- New behaviour without a test; a bug fix without its regression test.
- Scope larger than the request.
- A convention changed in code but not in its `AGENTS/` file.
- A new dependency nobody agreed to.
- A persisted-shape or contract change without its migration / other-side update.

MEDIUM unless the change makes them worse: swallowed errors or a broad catch hiding the real
failure · `any` / `Any` where a real type exists · leftover debug output or commented-out
code · comments that restate the code or refer to something the diff removed · duplicated
logic where a helper exists · a name that lies.

## 3. Try to disprove each finding

Before it goes in the report: is it handled elsewhere? Does the framework guarantee it? Is
it reachable? Does the caller already enforce the invariant? Could it be intentional? Is
there a test showing the intended behaviour? Would the fix be a worse trade-off? Drop what
does not survive. Never let a finding rest on library behaviour you have not checked; when
unsure, say it is a question, not a bug.

## 4. Severity and confidence

| Severity | Meaning |
| --- | --- |
| BLOCKER | must not ship as is: security hole, data corruption, major correctness failure, irreversible migration issue, outage risk, or a house rule above |
| HIGH | very likely fix before merge: realistic race, broken retry semantics, important edge case, contract regression, real scalability problem |
| MEDIUM | worth fixing, not necessarily before merge: poor failure handling, avoidable coupling, missing test on an important edge, operational blind spot |
| LOW | sparingly, only when it materially improves the codebase. Never style, naming, or formatting unless it causes genuine ambiguity |

Confidence on every finding: **HIGH** the code shows it · **MEDIUM** depends on surrounding
behaviour · **LOW** plausible, needs confirming.

## 5. Report

Per finding:

```
### [SEVERITY] Title
**Location:** file:line / function
**Problem** — what is wrong
**Why it matters** — the concrete failure or long-term cost
**Scenario** — a realistic sequence of events that produces it
**Suggested direction** — the smallest reasonable fix
**Confidence:** HIGH / MEDIUM / LOW
```

Then for the change as a whole:

- **What changed** — the behavioural change in 2–5 sentences.
- **System impact** — components, invariants, interfaces, operational characteristics affected.
- **Findings** — survivors of step 3, most severe first; confirmed bugs separate from risks
  and questions.
- **Residual risks / assumptions** — what could not be verified from the code.
- **Assessment** — exactly one of: *No material issues found* · *Material issues identified;
  see findings* · *Insufficient context to verify critical assumptions*. No score.

## Constraints

- One root cause, one finding — one precise architectural finding over five symptoms.
- Unchanged code is out of scope unless the change makes an existing issue newly relevant.
- No large refactor suggestions without a concrete problem to justify them.
- Respect project conventions unless they cause a substantive issue.
- Security, data integrity, concurrency, and irreversible operations get heightened scrutiny.

The bar for every finding: would the engineer responsible for this system six months from
now be glad it was caught? If not, leave it out.

## Then

Open `AGENTS/<stack>/review.md` for each stack the diff touches and run its checklist.
