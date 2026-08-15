# Update message — short version (chat / Slack / Discord)

> Update to `benchmark-task-authoring` — the biggest one since I shared it.
>
> **Every category now has a brief.** All 16, across 13 files in `references/`. Each one is
> that category's measured record: what cleared, what died, the shapes already killed there,
> the category-specific hazard, and a pre-build checklist. Each states its own `n`, so a
> claim resting on one slot reads as one slot. Read yours before you design anything — it's
> ~6 minutes and it's the step most likely to save you a redesign.
>
> **Three new laws in the field manual**, all from slots that cleared in the last week:
> • **§8.8 — a non-blocking advisory is a block that hasn't fired yet.** One task took seven
>   CI runs and only the *first* block was about difficulty; three of the four later blockers
>   were advisories an earlier run had already printed and graded PASS. The LLM stages
>   re-roll, so an advisory is the grader telling you where its next roll may land. Includes
>   the AVA loose/strict oscillation and the only thing that stops it.
> • **§9.6 — the pass@2 difficulty suggestion is a diagnostic instrument, not a consolation
>   prize.** Four semantic cores on one slot, two of them 2/2. What finally cleared it was the
>   platform's own free suggestion finding a single mis-calibrated percentile. Spend it early;
>   it's capped at 2/day and it diagnosed in one shot what four redesigns missed.
> • **§5.6 — an archetype is a whole planner, not a patched predicate.** If the wrong belief
>   doesn't reach every site that reads it — including the tie-break order — your battery is
>   measuring a planner that exists nowhere, and its kill rates aren't evidence.
>
> **One-prompt setup**, if you'd rather not do it by hand — paste this into your agent and
> it detects which tool you're in, installs the right way for Claude Code / Codex / Cursor /
> Antigravity, and verifies by actually running things rather than checking a file exists:
> https://github.com/Xclaw-bot/benchmark-task-authoring/blob/main/SETUP-PROMPT.md
>
> **Bug fix worth knowing about if you already installed it:** local retrieval wasn't indexing
> `ci-stages.md` or the category briefs — i.e. the two things the skill tells you to read
> first were the two it could never return. Fixed.
>
> Update: `git pull && python scripts/dr.py index --no-embed`
> (or re-download the `.skill` if that's how you installed it)
>
> https://github.com/Xclaw-bot/benchmark-task-authoring

---

# Update message — one-liner version

> `benchmark-task-authoring` update: all 16 categories now have a measured brief, three new
> laws in the manual (advisories are latent blocks · the pass@2 suggestion is a diagnostic ·
> an archetype must be a whole planner), and a retrieval fix.
> Update: `git pull && python scripts/dr.py index --no-embed` ·
> New here? One prompt does the whole install:
> https://github.com/Xclaw-bot/benchmark-task-authoring/blob/main/SETUP-PROMPT.md

---

# Update message — email version

**Subject:** benchmark-task-authoring update — category briefs + three new laws

Hi,

Pushed a sizeable update to the task-authoring skill I shared earlier.

**Every category now has a brief** — all 16, across 13 files under `references/`. Each carries
that category's measured record: what cleared, what died, the shapes already killed there, the
hazard specific to it, and a pre-build checklist. Every brief states its own sample size, so a
claim resting on a single slot reads as a single slot rather than as a rule. If you read one
thing before designing, read the brief for your category.

**Three laws were promoted into the field manual**, each from a slot that cleared in the last
week. They had been filed only under the category that discovered them, which meant most people
would never have met them:

- **§8.8 — advisories are blocks that haven't fired yet.** One slot took seven CI runs, and only
  the first block was about difficulty. Three of the four later blockers were advisories an
  earlier run had already printed and graded PASS. The LLM-graded stages are non-deterministic,
  so identical text can pass today and fail tomorrow — an advisory tells you where the next roll
  may land. The section also covers the AVA loose/strict oscillation (`sound_verifier` vs
  `no_false_rejection`) and the fixed point that ends it.
- **§9.6 — the pass@2 difficulty suggestion is a diagnostic instrument.** On one slot, four
  semantic cores were built and two came back 2/2. What cleared it was not a fifth core but the
  platform's own free suggestion, which located a single mis-calibrated percentile. It's capped
  at 2/day; spending it early is the cheapest diagnostic in the pipeline.
- **§5.6 — an archetype is a whole planner.** A wrong belief must be threaded through every site
  that reads it, tie-break order included. Patch only the engine and you're measuring a planner
  that half-holds the belief — neither the wrong reading nor the right one — and its kill rates
  aren't evidence of anything.

**Setup is now a single prompt**, for anyone installing fresh. Paste it into your agent and it
works out which tool it's running in, installs the right way for Claude Code, Codex, Cursor or
Antigravity, and verifies each step by running it rather than by checking that a file exists:

https://github.com/Xclaw-bot/benchmark-task-authoring/blob/main/SETUP-PROMPT.md

**One fix worth flagging if you installed earlier:** local retrieval wasn't indexing
`ci-stages.md` or the category briefs, so the two files the skill most insists you read first
were the two it could never return. Corrected.

To update an existing clone:

    git pull && python scripts/dr.py index --no-embed

Or re-download the `.skill` file if that's how you installed it.

https://github.com/Xclaw-bot/benchmark-task-authoring

Still method only — no task content, no repo identifiers, and every claim carries its evidence
class so you can tell a measured result from a hypothesis.
