---
description: Submission pipeline — fork/PR flow, the automated check stages, pass@2 and pass@5 economics, reading feedback, and revision limits. Load when opening a PR, interpreting check results, or planning a fix.
alwaysApply: false
---

# Pipeline and iteration

## Flow

Proposal (gated **before** you build) → fork → build on `submission` → local
oracle/nop → PR → validity check → **pass@2 at your timeout** → Automated Review
(all Blocking Issues fixed) → **pass@5**.

```bash
gh pr create --repo <program-org>/<task-repo> --fill
```

Iterate by pushing to the **same branch** — checks re-run and sticky comments update
in place. Use the house PR description shape: one-sentence problem, numbered
success criteria mirroring `instruction.md`, calibration results (oracle 1.0 /
nop <1.0), how to run, notes on anything you had to interpret.

## The difficulty gate

**Acceptance bar: pass@5 ≤ 2/5.**

| pass@5 | Meaning | Outcome |
|---|---|---|
| 0/5 valid failures | Fully stumped, oracle still solves | ✅ strongest |
| 0/5 **invalid** failures | Timeout / agent / verifier error / unfair prompt | ❌ fix the cause |
| 1–2/5 | Solvable and genuinely hard | ✅ |
| 3–5/5 | Too easy | ❌ |

A **valid failure** is the model finishing and being wrong on a fair problem.
Timeouts and agent/verifier errors never count. Gate formula:
`(good valid fails) + (soft-timeout fails) >= 3` **and** `good valid >= 1` —
soft timeouts count, infra/in-progress timeouts do not.

**Never game the score.** Lowering the timeout or padding busywork makes the task
harder to *finish*, not harder to *get right*; reviewers send it back.

## Economics — treat runs as scarce

- **Pass@2 is 6 runs per day, per fellow, per task.** Never spend one before the
  oracle is green locally.
- A push cancels queued runs for the same PR (per-PR concurrency), so superseded
  runs auto-cancel — no quota wasted.
- Fork contributors **cannot** cancel upstream runs (`actions:write` → HTTP 404).
- Pass@5 auto-starts only if pass@2 was valid and Automated Review passed.
- Review pipeline: **max 2 revisions**, then Holding-Rejection. Official guidance is
  to revise sent-back tasks before claiming new ones — they are closest to the bonus.

## Reading a bad result

| Symptom | Fix |
|---|---|
| Timeout | Move difficulty into reasoning, not computation. Trim expensive steps. Raise timeout only if justified (≤3600s). Still timing out → redesign. |
| Ambiguous prompt | Tighten to exactly one reasonable interpretation. |
| Brittle verifier | Make it test the real requirement and accept any sound correct answer. |
| Not solvable | Run `solve.sh` in a clean container; it must reach reward 1.0. |
| 3–5/5 too easy | Add interacting layers and edge cases; strengthen the verifier so sloppy-but-close fails. Re-run the pre-build check in `10-hardness-gate.md` — a design that fails it will keep coming back too easy. |

Always read the pass@ **Job Analysis**, not just the score: it explains *why* the
model failed, and that diagnosis should feed back into the task before submission.

## When checks fail on infrastructure

A check that fails in seconds with an auth error (HTTP 401/403) against a central
the platform service is **not** a task defect and cannot be fixed by editing the task.
Retriggering re-runs the same broken call. Close/reopen the PR fires a fresh run
(`pull_request_target: reopened`); if the failure persists identically, escalate in
Slack `#project-the program` with the check name, the endpoint, the run IDs and the
number of reproductions. Do not keep retriggering — it adds noise to a graded PR
without changing the outcome.

## Support

Slack `#project-the program` / `the program-tasking` for task questions —
*"ask before you start guessing."* `the program announcements channel` for project notices.
Support Desk in the the platform dashboard for access, pay and admin.
