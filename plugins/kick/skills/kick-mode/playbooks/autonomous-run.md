### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping for reversible calls.** The user starts this mode explicitly ("run until done", "go hands-off", "/loop until X"); nothing else enters it.

1. **Open the log.** Start a decision trail with the **show-me-your-work** skill before the first change. Every row below lands there.
2. **State the exit condition** as a checkable predicate before the first iteration: tests green, repro fixed, a metric past its target.
3. **Decide by the ask list, not by asking.** An item the user's ask/decide rules reserve for the human (kick-mode's [Precedence](../SKILL.md#precedence)) gets a log row with the options, your pick, and why, then you take it when it is reversible. Stop and ask before anything irreversible: a push, a merge, a persisted-schema change, deleting the user's work, and anything touching auth, payments, or personal data. A product call no experiment can settle also waits for the user; log it and keep working on the rest.
4. **Work in verifiable units.** Each iteration makes the smallest change the evidence justifies, runs the suite, and commits only when the suite is green and the predicate moved. Revert a change that did not help; a change that "might help" does not ride along. Sequence per the [sequence-verifiable-units](../principles/sequence-verifiable-units.md) principle.
5. **Wake on events, not timers.** Pace waits with Claude Code's `loop` skill: a watcher for an event (CI, a ref advancing) with a long heartbeat as fallback, or a fixed heartbeat sized to when the result is worth re-checking. Codex has no `loop`; re-check on a cadence yourself.
6. **Own mid-run discoveries.** Fix broken skills, flaky checks, and related bugs you hit, each as its own unit with its own log row, then return to the predicate.
7. **Interrogate before done.** When the predicate is met, run `interrogate` on the whole diff. Fix the Act-on findings, rerun the suite, and interrogate again, for at most two rounds. Log what remains with the reason it stays.
8. **Stop** when the predicate holds and the last review is clean or its remainder is logged. A plateau is not a stop: pivot the approach. A real dead end is: surface it rather than spin. Never relax the predicate to declare victory.

**Reply:** the log path, the exit condition and its final state, the suite output pasted, the interrogate report, what landed and what was reverted, and every ask-list decision you took with its log row.
