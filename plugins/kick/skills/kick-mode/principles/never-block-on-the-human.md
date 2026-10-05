# Never Block on the Human

The human supervises asynchronously. Within the user's ask/decide rules, make the call, proceed, and let the human course-correct after the fact.

**Why:** Every permission pause stalls the work and makes the human the bottleneck. Code changes are reversible and reviewable, so a wrong decision the rules let you make usually costs less than blocking.

**Pattern:**
- **Decide what the rules say is yours.** Naming, placement inside an established structure, which helper to reuse, obvious edge cases, test selection. Do it, then say what you chose and why.
- **Ask what the rules reserve for the human.** The ask list kick-mode's [Precedence](../SKILL.md#precedence) points to, and any two readings that produce materially different work. Ask once, with options and your recommendation first.
- **Make the system self-healing.** When you notice a problem, log it and fix it in the next round.

**Boundaries:**
- **Irreversible actions** (push, merge, force-push, deleting data, sending external messages) always need confirmation.
- **Inside an [Autonomous run](../playbooks/autonomous-run.md)**, log an ask-list decision and take it if it is reversible; stop before anything irreversible.
- **Product direction** comes from the human. Execution should not block.
