# `proposal-<hash>.md` — the platform artifact, and nothing else

Copy this file, fill it in, delete these instruction blocks. **The finished file contains no
instructions, no tables, no headings beyond the title, and no internal vocabulary.**

## Why the format is this strict

`difficulty_explanation_quality` is a graded rubric field and it FAILS on results-based
framing. Every sentence in section 1 is read by a grader asking "does this explain why the
work is intrinsically hard, or does it brag about outcomes?" So the proposal carries **zero**
project lore: no `pass@` numbers, no slot hashes, no "the corpus", no "archetype", no
"kill-list", no "we measured". Those belong in a **separate design record** —
`design-<hash>-<slug>.md` — which nobody grades and which is where your real reasoning lives.

Write dense prose. No bullet lists, no Part A/B/C scaffolding, no tables.

---

Category: <Category>  Sub-Category: <Sub-Category>

**1. Why this task is genuinely difficult**

<Two or three lead paragraphs. Describe the scenario and the artifact the agent must produce.
State what makes constructing it hard — the interacting constraints, the fold the agent has to
perform, the reason a locally reasonable choice becomes globally illegal. Difficulty must live
in what a wrong belief makes ILLEGAL, never in what it merely misnames.>

*The professional and why it is valuable.* <Name the actual job title that does this work and
the setting they do it in. This sentence is graded — an audience-first framing passes, a
"this is a hard benchmark task" framing fails.>

*The data.* <Synthetic or real; provenance; scale; why it is realistically challenging rather
than artificially large.>

*The pitfalls.* <The concrete traps. Each one should be a reasoning trap — a rule whose
cheapest natural implementation is the wrong one — not tedium. Name what the agent will
plausibly believe and what that belief makes impossible.>

**2. Intended solution approach**

<Key insight first, in one sentence — the thing a solver must realise. Then numbered steps
describing the intended construction. Close with an honest expert-effort estimate in hours.>

**3. How the solution will be verified**

<What the verifier checks, field by field. Calibrate EVERY tolerance — or state that the
task is exact-integer and that exactness IS the calibration. Describe the anti-cheat measures.
Say explicitly what discriminates a correct answer from a plausible-but-wrong one. Describe
cross-validation against an independent implementation written from the spec prose alone.>

**4. Category and sub-category**

<Justify the assigned category and sub-category. Then give `task_objective` and
`artifact_type` from the closed sets in `references/diversity-taxonomy.toml`, and justify each
by what the agent PHYSICALLY EMITS — never by subject matter. A task about database history
whose agent emits one script is `single_script_or_program`, not
`repository_history_or_version_control_state`.>

---

## Pre-handover check (run these, don't eyeball)

1. `grep -icE "pass@|archetype|kill-list|corpus|probe|measured bet|good-valid" proposal.md` → must be 0
2. No task hashes anywhere in the file.
3. Exactly four bold-numbered sections; the three italic-led paragraphs present and in order.
4. No tables, no bullet lists, no sub-headings.
5. Both closed-set labels present and justified by emitted artifact.
