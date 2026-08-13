# The review pipeline: clearing every stage on the first roll

A full review run takes **~3 hours** (measured: 3h 02m 55s, 17 jobs, 15 artifacts). That number
is the whole reason this file exists.

## The fact that changes how you work

**A block at any early stage SKIPS every stage downstream — including `trials`.** So a failure
in a five-minute-fixable prose field does not cost you a checkbox; it costs you *the entire
difficulty measurement*, and you find out three hours later.

The measured case: one slot needed **three CI runs, and neither of the first two failures was
about difficulty at all.** Run 1 died on `ava_review` → `verifier_coverage`. Run 2 died on a
rubric re-roll of `difficulty_explanation_quality`. Both were checkable locally in minutes.
Each one also skipped `tier1`, `qc_*` and `trials`, so two full difficulty measurements were
thrown away by problems that had nothing to do with the task being hard.

Three consequences worth internalising before your first push:

1. **CI is the confirmation step, never the test loop.** Everything with a local equivalent
   must be green locally first.
2. **Re-rolling costs you passes you already earned.** The LLM stages (`review`,
   `similarity`, `deep_review`, `ava_review`) are non-deterministic — identical text passed
   `review` on run 1 and failed it on run 2 of the same slot. Once a run is green, do not push
   again.
3. **Never push while a run is in flight** — per-PR concurrency cancels the run in progress.
   Wait for quiet, then push once.

## You are waiting on a run right now

The three hours are already spent, so spend them well. **Do not push** — per-PR concurrency
would cancel the run you are waiting on. Everything below is free, needs no API key, and is
work you would otherwise do after the result lands:

1. **Self-grade the 31 criteria** against your repo's rubric (below). If `review` is what you
   are waiting on, this tells you the answer before CI does.
2. **Run the three static greps** and the four blockers in the next section. If one of them is
   going to fail, you want to know now, not in two hours.
3. **Measure difficulty locally** — you do not need `trials` for this. The wrong-belief
   battery in `rules/10-hardness-gate.md` (steps 5–9) runs entirely on your own reference
   solver and one-line mutations of it: every wrong-belief variant must pass the public case
   but fail several sealed ones, survive restart pressure, and stay silent rather than
   crashing. That is the same question `trials` asks, at zero cost.
4. **Run the shape test** — install the obvious off-the-shelf solver for your domain and three
   one-line greedy policies against your sealed set at the disclosed cap. If the solver hits
   the target or a one-liner wins more than ~20%, no CI result was going to save you.

If the run comes back green, you have lost nothing. If it comes back blocked, you already know
what to fix.

## The stages, in order

Names as they appear in the Actions sidebar. Local-checkability is the column that matters:
anything marked ✅ should never fail in CI, because you can prove it beforehand.

| # | Stage | What it gates | Locally checkable? |
|---|---|---|---|
| 1 | `changes` | Which paths changed; routes the rest of the graph | n/a |
| 2 | `cosine_similarity` | **Your task vs already-DELIVERED Dynamo tasks.** Threshold **0.9** — blocks if *any* artifact scores ≥ 0.9. Reports per-artifact scores for **Instruction** and **Verifier** | ⚠️ Partly — you can diff your own drafts, but the delivered corpus is not visible to you |
| 3 | `review` | **The 31-criterion rubric**, plus static stage 1. The gate that blocks everything else | ✅ **Fully** — the rubric ships in your repo |
| 4 | `similarity` | Your task vs the **TB2/TB3 benchmark** sets ("Duplicate check") | ✅ In practice never an issue — measured top lexical ~0.12 |
| 5 | `validation` | Task structure and schema validity | ✅ `dynamo-preflight.py` |
| 6 | `ratelimit` | Your remaining pass@2 quota | n/a — but see the economics below |
| 7 | `pass2` | Two live agent trials at your disclosed timeout | ⚠️ Approximated by a local probe; only the platform is authoritative |
| 8 | `pass2_suggestion` | Advisory; skips when not applicable | n/a |
| 9 | `deep_review` | LLM review of task quality | ❌ Non-deterministic, confirm-only |
| 10 | `ava_review` | Automated verifier audit — **`verifier_coverage` lives here** | ✅ **Yes, and this one bites** (below) |
| 11 | `tier1` | Tier-1 quality bar | ❌ Confirm-only |
| 12 | `qc_eval` · 13 `qc_exec` · 14 `qc_gate` | Quality-control evaluation, execution and gate | ⚠️ Largely downstream of things you *can* check: oracle 1.0 / nop 0.0, anti-cheat, budget |
| 15 | `trials` | **pass@5 — the difficulty gate itself** | ⚠️ Probe only; the platform decides |
| 16 | `gate` | Final aggregation of every stage | n/a |
| 17 | `claude-cost-report` | Cost accounting for the run | n/a |

`pass@5` auto-starts only if `pass2` was valid **and** Automated Review passed. So everything
above `trials` is a gate on getting measured at all.

## The four blockers that preflight does NOT catch

These cost real cycles. Preflight's checks are laxer than the platform's, so check each
explicitly.

**`ava_review` → `verifier_coverage`: your reference solution must never exit nonzero.**
A bounded search that `raise`s on budget or deadline exhaustion leaves a ragged acceptance
boundary between *crashed* and *answered wrongly* — and AVA blocks on it **even though the
failing path never fires on the shipped set**. Two measured instances; one cost a full cycle,
the other returned a FAILURE with no comment and no check output.
*Fix:* give the search a deadline **inside** the recursion plus a trivially-valid non-minimal
fallback. Then write a fail-paths tool that forces the reference down every damaged-input path
— unachievable floor, tiny deadline, malformed input — and asserts **exit 0, a well-formed
artifact, and graded as a wrong answer, never a crash.** Reasoning about this is not enough;
AVA checks it mechanically, so you must too.

**`review` → `difficulty_explanation_quality`: name a real-world audience, in the graded
field.** Two failure modes, both measured. First, the field never names *who in the real world
would need to solve this and why* — the rubric's own guidance says exactly that, and it must
be **inside** the graded field, not implied by the surrounding task framing. Second,
results-based framing: reciting measured rates or selection outcomes reads as *results*, not
as intrinsic difficulty. Move every hard number to `verification_explanation` and the PR body.

**`review` → static stage 1: three greps.** Bare `name.ext` tokens anywhere in
`instruction.md`; the strings `solution/`, `tests/` or `test.sh` in the Dockerfile **even
inside comments** (the stock Dockerfile's own comments contain them — rewrite them); and CRLF
line endings in `tests/test.sh`. Verify the *committed blob*, not your working copy:
`git cat-file blob $(git rev-parse HEAD:<file>)`, and set `core.autocrlf false` in the repo.

**`trials` → classification: fails that land as `infra` or `in-progress-timeout` count for
NEITHER side.** A run can be 0/5 solved and still blocked. Keep a merely-valid answer trivial
to produce so agents always submit *something*, and run the timeout-law probe below.

## Two more shipped-file hazards

**Delete the "You have N seconds to complete this task…" line.** It used to be mandatory and
statically enforced. It is now an explicit fail condition under `instruction_concision` — the
agent's time budget belongs in `[agent].timeout_sec`, not in prose. Preflight misses this.
Do not over-apply it: a **per-request cap** is a property of your *verifier* and must still be
disclosed in `instruction.md` and `verification_explanation`. Two different sentences — delete
the boilerplate, keep the cap.

**`ctrf.json` counts, not just the reward.** `pytest-json-ctrf` collapses parametrized tests
into one entry (15 collected reported as "3 tests"), and the platform reads ctrf. Ship one
explicit test function per graded case — loop-generated with per-case docstrings passes.

Also: `instruction.md` is a **prompt, not a document** — no title, no headers. Add
`environment/.dockerignore` once your build context has subdirectories. Keep the oracle at
roughly ≤0.25 s per instance so the disclosed per-item cap is ~100× and
`n_items × cap < verifier timeout_sec` holds with margin.

## The ordered local pipeline — every step green before one push

1. **Preflight.** `python dynamo-preflight.py <task>` (Python 3.11+). Then the three greps
   above by hand — preflight's versions are laxer than the platform's.
2. **Oracle and nop.** `harbor run -p . -a oracle -o <dir outside the repo>` → reward 1.0,
   then `-a nop` → 0.0. Output outside the repo, or job artifacts trip `no_extraneous_files`.
   On Windows set `PYTHONIOENCODING=utf-8 PYTHONUTF8=1` or harbor's spinner kills captured runs.
3. **Timeout-law probe.** A `solve.sh` variant that writes a valid public artifact then hangs
   forever: every sealed test must fail **scored** (`pytest.fail`), `ctrf.json` written,
   reward 0 — never an unscored verifier timeout. Read the ctrf counts.
4. **Forced-failure probe** on the reference — the `ava_review` fix above. No input may make
   it exit nonzero or produce no artifact.
5. **Hostile-planner probe, executed against the real grader.** Rewrite graded inputs on disk
   mid-run; answer from a memorised plan; symlink the graded artifact. Each must score 0, each
   caught by a *different* guard (import-time snapshot, SHA pin, realpath).
6. **Batteries.** Wrong-solver battery (all pass public, all die sealed); valid-variant
   tie-check; held-out-order robustness; and the **correct-rules + naive-search family** —
   random restart, unpruned DFS, best-first — barred in **wall clock at the disclosed cap,
   measured un-contended.** That family killed three slots on one day after every other gate
   was green.
7. **Differential fuzz** over degenerate shapes your generator never emits, plus the floor
   implemented a **third** time from the SPEC prose alone.
8. **Re-verify from the SHIPPED files**, not from your selection records.
9. **The full 31-criterion rubric self-grade** — see below. This is the highest-value step.
10. **A real-agent difficulty probe** if you have API keys — expect 0/2 with failures *scored*,
    and read the authoritative reward file rather than the console summary. Treat empty or
    cancelled jobs as inconclusive, never as a pass. **If you have no keys, skip this step
    rather than skipping the pipeline** — steps 5–9 are the API-free substitute and they are
    what actually predicts the gate. A probe result is a warning, never a verdict: it measures
    an upper bound on what a solver *could* do given the rules, not what the trial model
    actually writes.
11. **Push once**, and let CI confirm.

## The rubric self-grade — free, and the single highest-value pre-push step

`harbor check` needs an API key. **You do not need one.** The full rubric ships in every task
repo at `<your-task-repo>/references/dynamo-rubric.toml` (not in this skill) — roughly 41 KB, every criterion with a complete
`description` *and* `guidance` block. Reading it and grading yourself costs nothing.

Do it as an explicit **per-criterion table: PASS / FAIL / NA plus a one-line reason** — not a
vibe check — so it is auditable and a FAIL cannot be glossed over. Fix every FAIL before
pushing. `review` gates everything downstream, so this one step protects the whole run.

Proof it works: the criterion that cost one slot its second CI run states verbatim *"explain
who in the real world would need to solve this and why."* A five-minute read of that
criterion against the field would have caught it.

Pay special attention to the four graded prose fields — `difficulty_explanation`,
`solution_explanation`, `verification_explanation`, and the taxonomy labels. **Every rubric
failure in this corpus landed in one of them.**

## Economics — treat runs as scarce

- **pass@2 is 6 runs per day**, per fellow, per task. Never spend one before the oracle is
  green locally.
- A push cancels queued runs for the same PR, so superseded runs auto-cancel and no quota is
  wasted — but a push mid-flight kills a run you were waiting on.
- Fork contributors **cannot** cancel upstream runs (`actions:write` → 404).
- **Max 2 revisions**, then Holding-Rejection. Official guidance is to revise sent-back tasks
  before claiming new ones — they are closest to the bonus.

## The harness is not the task

When your measurement harness and your shipped tree are separate code, **every local bar
measures the harness.** Three separate instances of this in a single build, each of which
looked exactly like a finding about the task — including one where the mechanism the whole
design rested on was implemented in the harness core *only*, so the reported kill rates
described a reduction the shipped solver and grader never ran.

The fix is cheap: **make the differential fuzz compare the harness core as an extra route**
alongside the shipped solver and grader. Routes that agree with each other prove nothing if
they share an omission — and adding the harness as a third route found a second unknown drift
within minutes.

Corollary for reporting: before quoting any difficulty number, check which module produced it.
If it is not the file that ships, the number is about your harness.

## What local cannot replicate

`cosine_similarity`, `deep_review`, `ava_review`'s LLM judgement, and the true pass@5 with the
pinned trial model. Those stages are **confirm-only** — never iterate against them, because
each iteration re-rolls everything that already passed.
