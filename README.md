<h1 align="center">benchmark-task-authoring</h1>

<p align="center">
  <b>Write Terminal-Bench 2 / Harbor tasks that survive the difficulty gate —<br>
  and get them through review in <i>one</i> CI run instead of three.</b>
</p>

<p align="center">
  <a href="#install"><img alt="install" src="https://img.shields.io/badge/install-one%20click-e2a75c?style=flat-square"></a>
  <img alt="skill" src="https://img.shields.io/badge/Claude%20Code-skill-7aa5d8?style=flat-square">
  <img alt="python" src="https://img.shields.io/badge/python-3.11%2B-66b98a?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-8b93a1?style=flat-square">
</p>

---

## Install

**One click.** Download **[`benchmark-task-authoring.skill`](benchmark-task-authoring.skill)**
→ open it in Claude → press **Save skill**. Done.

<details>
<summary><b>Or clone it</b> (same thing, if you prefer git)</summary>

```bash
git clone https://github.com/JrKrishh/benchmark-task-authoring.git \
  ~/.claude/skills/benchmark-task-authoring
```
</details>

**You never invoke it by name.** It fires on its own the moment you say something it
recognises:

> *"agents keep solving my task"* · *"my PR checks are failing"* ·
> *"how do I make this harder"* · *"pass@5 came back 3/5"* · *"ava_review failed"*

---

## First fifteen minutes

| | | |
|---|---|---|
| **1** | Read *The one law* + the kill-list in `SKILL.md` | 5 min |
| **2** | Set up retrieval — stop re-reading a 35k-token manual | 1 min |
| **3** | Put a board up — see which stage each slot is stuck at | 1 min |
| **4** | Read `references/ci-stages.md` before your first push | 8 min |

```bash
python scripts/dr.py index --no-embed          # 2 · index this skill
python scripts/taskdesk.py --org <your-org>    # 3 · your board, stage by stage
```

---

## Why this exists

Two things cost more than everything else combined, and both are avoidable.

> ### 🧱 You designed a shape that was already dead
> Thirteen task shapes are **measurably** dead — they look clever right up until agents
> solve your task 2/2 in twenty minutes. The kill-list gives the tell for each, and for the
> four that are salvageable, the repair that actually worked.
>
> The test that catches most of them, before you write a line:
> *what must the agent **build** that the verifier could not hand it by simulating?*

> ### ⏱️ You burned three CI runs on things that were not difficulty
> A review run takes **~3 hours**, and **a block at any early stage skips everything
> downstream — including `trials`.** So a prose field you could have fixed in five minutes
> does not cost you a checkbox, it costs the entire difficulty measurement, and you find out
> three hours later.
>
> One slot here needed three runs where *neither* of the first two failures was about
> difficulty at all. `references/ci-stages.md` maps all 17 stages, which ones you can prove
> locally beforehand, and the four blockers preflight misses.

---

## The two desks

```bash
python scripts/taskdesk.py --org <your-task-org>   # where does the work stand?
python scripts/session_desk.py                     # what is this costing?
```

**Task desk** — one card per slot with a **stage-by-stage strip**: green for passed, red for
the stage that blocked you, amber for what is running. Because an early block skips
everything downstream, the strip answers the only question that matters when a PR goes red —
*five-minute prose fix, or redesign?* Blocked slots sort first; the action band names each
fix. Read-only, never pushes.

**Session desk** — live sessions, token spend by day and project, searchable ledger. Useful
when several slots are running at once and you want to see where the budget went.

Both are plain HTML — no server, no build. They cross-link to each other and back here.

---

## What's inside

| Path | What it is |
|---|---|
| **`SKILL.md`** | The one law, the 13-shape kill-list, the workflow, routing to everything else |
| **`references/hardness-laws.md`** | The field manual — every law with its numbers and evidence class |
| **`references/ci-stages.md`** | All 17 review stages, the four blockers preflight misses, the ordered local pipeline |
| `references/retrieval.md` | Index once, query for ~1k tokens instead of ~35k |
| `references/claiming.md` | How claiming actually works (route-based, not an API mutation) |
| `references/rules/` | Eight phase-scoped rule files: mission → retrieval → hardness gate → design doctrine → Harbor format → authoring → verifier → pipeline |
| `assets/` | The 4-section proposal house format, the one-slot-one-session prompt, the batch brief |
| `scripts/preflight.py` | Local gate check before you push |
| `scripts/dr.py` | Local retrieval over this skill and your own notes |
| `scripts/taskdesk.py` | Board dashboard — per slot, which stage it is sitting at |
| `scripts/session_desk.py` | Session and token-spend dashboard |

---

## Two free wins

**The rubric self-grade costs nothing.** All 31 review criteria ship in *your own task repo*
at `references/dynamo-rubric.toml`, with full guidance text — no API key, no `harbor check`.
Grade yourself as an explicit PASS / FAIL / NA table before every push. `review` gates
everything downstream, and **every rubric failure in this corpus landed in one of four graded
prose fields.**

**Retrieval cuts your token spend by an order of magnitude.** The field manual does not fit in
one read call. Index it once — ~220 cards in under a second, lexical-only, no model download,
no API key — then ask it questions with `file:line` citations:

```bash
python scripts/dr.py ask "what trips ava_review verifier_coverage" --fast
```

---

## Requirements

| | |
|---|---|
| **Python 3.11+** | for `preflight.py` (`tomllib`). On Windows where `python` is older: `py -3.12` |
| **`numpy`** | for `dr.py index`. `--fast` / `--no-embed` need nothing else |
| **`gh` CLI**, authenticated | for `taskdesk.py` and the fork → PR flow |

---

## Scope, and how much to trust it

This is **method only** — no task content, no repo identifiers, no spec text from any
submitted task. Tasks appear as anonymised labels (`GPU-2`, `ETL-1`).

It is also one author's corpus, which is why every claim carries an evidence class:

| Class | Means |
|---|---|
| **measured-gate** | The platform's own pass@ measurement confirmed it |
| **design-kill** | Killed by local measurement or argument, never gate-measured |
| **prospective** | Untested hypothesis, flagged as such |

Weight them accordingly. Your sub-category distribution will differ from mine, so the
category-specific notes may not transfer even where the cross-cutting laws do.

**If a law turns out wrong in your categories, that is more valuable than one that holds** —
[open an issue](https://github.com/JrKrishh/benchmark-task-authoring/issues). Negative results
are most of what this is built from.

---

<p align="center"><sub>MIT — see <a href="LICENSE">LICENSE</a></sub></p>
