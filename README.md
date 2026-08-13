# dynamo-task-authoring

A Claude Code skill for writing Terminal-Bench 2 / Harbor benchmark tasks that survive the
difficulty gate — and for getting them through review in **one** CI run instead of three.

Built from about thirty task slots: the ones that cleared the gate, and the considerably
larger number that died first. Every claim carries an evidence class, so you can tell what the
platform's own measurement confirmed from what is still a hypothesis.

---

## Install

Download **[`dynamo-task-authoring.skill`](dynamo-task-authoring.skill)** and click
**Save skill** when the file card appears in Claude.

Or clone straight into your skills directory:

```bash
git clone https://github.com/<owner>/dynamo-task-authoring.git ~/.claude/skills/dynamo-task-authoring
```

After that it triggers on its own. You do not need to invoke it by name — saying things like
*"agents keep solving my task"*, *"my PR checks are failing"*, or *"how do I make this harder"*
is enough.

## The two things worth having on day one

**The kill-list.** Thirteen task shapes that are measurably dead, each with the tell that
identifies it, and — for the four that are salvageable — the repair that actually worked. Most
of them look clever right up until agents solve your task 2/2 in twenty minutes.

**The CI map.** A full review run takes about three hours, and **a block at any early stage
skips every stage downstream, including `trials`.** So a prose field you could have fixed in
five minutes does not cost you a checkbox — it costs the entire difficulty measurement, and
you find out three hours later. One slot here needed three CI runs where *neither* of the first
two failures was about difficulty at all.

## What's inside

| Path | What it is |
|---|---|
| `SKILL.md` | The one law, the 13-shape kill-list, the workflow, and routing to everything else |
| `references/hardness-laws.md` | The field manual — every law with its numbers and evidence class |
| `references/ci-stages.md` | All 17 review stages, the four blockers preflight misses, the ordered local pipeline |
| `references/retrieval.md` | How to stop re-reading long docs — index once, query for ~1k tokens |
| `references/claiming.md` | How claiming actually works (route-based, not an API mutation) |
| `references/rules/` | Eight phase-scoped rule files: mission, retrieval, hardness gate, design doctrine, Harbor format, authoring, verifier, pipeline |
| `assets/` | The 4-section proposal house format, the one-slot-one-session prompt, the batch brief |
| `scripts/dynamo-preflight.py` | Local gate check before you push (Python 3.11+) |
| `scripts/dr.py` | Local retrieval over this skill and your own notes |
| `scripts/session_desk.py` | Dashboard over your Claude Code sessions |

## Quick wins

**Free rubric self-grade.** All 31 review criteria ship in *your own task repo* at
`references/dynamo-rubric.toml`, with full guidance text. No API key, no `harbor check`. Grade
yourself as an explicit PASS/FAIL/NA table before every push — `review` gates everything
downstream, and every rubric failure in this corpus landed in one of four graded prose fields.

**Cut your token spend.** `references/hardness-laws.md` is ~35k tokens and does not fit in one
read call. Index it once and query instead:

```bash
python scripts/dr.py index --no-embed
python scripts/dr.py ask "what trips ava_review verifier_coverage" --fast
```

Roughly 220 cards in under a second, lexical-only — no model download, no API key. Needs
`numpy`. Point it at your own notes later with `DYNAMO_MEM` and `DYNAMO_WORK`.

## Scope and honesty

This is **method only** — no task content, no repo identifiers, no spec text from any
submitted task. Tasks appear only as anonymised labels (`GPU-2`, `ETL-1`).

It is also one author's corpus. The evidence classes exist for that reason: **measured-gate**
claims survived the platform's own pass@ measurement; **design-kill** and **prospective** ones
did not. Your sub-category distribution will differ, so the category-specific notes may not
transfer even where the cross-cutting laws do.

**If a law turns out wrong in your categories, that is a more valuable result than one that
holds.** Open an issue — negative results are most of what this is built from.

## Requirements

- **Python 3.11+** for `dynamo-preflight.py` (uses `tomllib`). On Windows where `python` is
  older, run it as `py -3.12`.
- **`numpy`** for `dr.py index`. `--fast` / `--no-embed` need nothing else.
- **`gh` CLI**, authenticated, for the fork → PR flow.

## License

MIT — see [LICENSE](LICENSE).
