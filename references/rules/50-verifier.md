---
description: Verifier design — ground-truth protection, tolerance justification, anti-cheat, AVA, and the 11-item pre-submission self-check. Auto-attaches to test files; load when writing or auditing a verifier.
globs: <task-repo>/task/tests/**
alwaysApply: false
---

# Verifier craft

The verifier runs in the **same image** as the agent, after the agent stops.
Harbor overlays `tests/` at `/tests` only at verify time. Everything it needs must
be baked into `environment/Dockerfile` (pinned) — `test.sh` installs and downloads
nothing.

## Ground truth must be unreachable

```
❌ truth read from a path the submission can also open
✅ truth lives where the submission cannot reach it — tests/, overlaid at verify time
```

Expected values belong in `tests/`, never in `environment/`, never in the image.
Prefer values **derived** in the solution over hardcoded constants, so a
non-specialist reviewer can follow the derivation.

## Assertions

- Every assertion traces to a requirement stated in `instruction.md`; every stated
  requirement has coverage. Grading on unstated criteria is an unfair stump.
- One requirement per test function, each with a docstring naming the behaviour it
  checks in the instruction's terms.
- Verify **behaviour by execution**, never by scanning source for keywords,
  imports or regexes — an agent can insert a keyword without implementing anything.
- Existence and formatting checks should rarely fail for a competent solver. If
  they are what fails, the defect is in the instruction.

## Tolerances

Exact comparison is preferred and needs no defence when the pipeline is
integer-deterministic and the format is normatively pinned. Any inequality-based
check — ranges, thresholds, percentile bounds, fuzzy matching — must have its
calibration justified in `verification_explanation`: what the band brackets, which
legitimate variation it absorbs (float precision, alternative valid algorithms,
quadrature, rounding), and whether it was validated against an alternative correct
method rather than only the reference. **A band only the reference can hit is too
tight; a band that admits obviously wrong answers is too loose.** Bare statements
like "accepted range [29, 31]" are insufficient.

## Anti-cheat

Resist the shortcuts agents actually attempt: fabricated tool wrappers,
monkey-patched libraries, cached or hardcoded precomputed answers, edits to the
test framework, reading files that contain the solution. Specifically:

- **Symlink guard** the output path so it cannot be aliased to an answer key.
- **Integrity-pin inputs** by SHA-256 where tampering could manufacture a pass.
- Pin the exact key set and value types, so a partial or degenerate answer fails
  rather than slipping through.
- Never run the agent's own code as part of grading.
- Open internet is on — confirm the answer is not retrievable online.

## Pre-submission self-check (11 items)

1. Every output field's format and naming fully specified — IDs, enums, exact
   string literals — so the agent never guesses.
2. The verifier checks only what the instruction (or a doc it points at) states —
   no hidden literals, no undocumented fields.
3. Where a value can be computed more than one valid way, the instruction names the
   **single canonical rule** (single assignment, priority/tie-break, sort order).
4. Duplicate, redelivery and other edge cases described explicitly.
5. **A reasonable alternative implementation still passes** — the verifier is not
   silently enforcing the oracle's arbitrary choice. If only one approach is valid,
   the instruction says so.
6. No file the agent can read discloses the bug, the fix or the expected output.
7. No undisclosed detail steers the agent wrong — **the task fails on the agent's
   own wrong call, not because the environment misled it.** Every file the agent
   should use is named in the instruction.
8. No malicious code, no prompt injection in fixtures/READMEs/comments, no
   obfuscated payloads.
9. Every rule traced against the **real shipped fixtures** — no two rules
   contradict on the actual data.
10. `solve.sh` output re-read line by line against `instruction.md`, and vice versa.
11. For each assertion: *"could someone fake this and still pass?"* → **no**.

## Two separate defects, do not conflate

A **coherent contract** (the instruction fully and consistently describes what to
produce) and a **sound verifier** (it grades that contract without leaks or
bypasses) fail independently. The accepted-corpus rejections included one for
coverage and one for underdetermination — neither was about difficulty.
