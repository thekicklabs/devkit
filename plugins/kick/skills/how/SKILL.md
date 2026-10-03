---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

On Codex, read the [platform mapping](../kick-mode/references/codex-tools.md) before following this skill.

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

## Step 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no subagents. Read the code and explain it yourself in one pass. Go to Step 3.
- **Complex** (a subsystem spanning several files or services, a cross-cutting feature, a full architectural overview): spawn explorers first. Go to Step 2.

When in doubt, take the simple path.

## Step 2. Explore (complex questions only)

Split the question into at most two exploration angles, each a distinct slice of the subsystem. Spawn both explorers in one message on the `fast` role from [models](../kick-mode/references/models.md). On Claude Code use the read-only `subagent_type: "Explore"`; on Codex, apply the read-only guard from kick-mode's Subagents section.

Each explorer gets the prompt in `references/explorer-prompt.md` with its angle filled in.

## Step 3. Explain

Write the explanation yourself, following `references/explainer-prompt.md`. For a complex question, build it from every explorer's findings and spot-check the claims you lean on against the code.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
