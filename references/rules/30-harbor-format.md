---
description: Harbor/TB2 mechanical format — file layout, task.toml schema, Dockerfile rules, base images, artifacts, timeouts, preflight and the leak check. Auto-attaches to task files; load when building or fixing task structure.
globs: dynamo-*/task/**
alwaysApply: false
---

# Harbor format — the mechanical gate

Per-repo `references/` files (rubric, `diversity-taxonomy.toml`,
`check-base-image.sh`) are authoritative and override anything here.

## Layout

```
task/
  instruction.md          # the only thing the agent sees at runtime (HUMAN-WRITTEN)
  task.toml               # manifest
  environment/
    Dockerfile            # ONE image, for both the agent run and the verifier
    data/                 # inputs copied in; NEVER ground truth
  solution/
    solve.sh              # mounted at /solution, runs the reference (HUMAN-WRITTEN)
  tests/
    test.sh               # verifier entry point; installs NOTHING
    test_outputs.py       # pytest assertions
    expected/             # ground truth — overlaid at /tests only at verify time
```

Canonical TB2 uses a **single image**. There is no `tests/Dockerfile` and
`[verifier] environment_mode` stays unset.

## task.toml

- `artifacts = [...]` at **top level**, above the first `[section]`. Every
  agent-produced path the tests read must be declared.
- `[task] name = "dynamo/<kebab-name>"` — inside the `[task]` table, `org/name`
  format, name part ≤3 words. A root-level `task = "..."` string makes Harbor
  resolve zero tasks and abort.
- `[metadata]`: `category`/`subcategory` are pre-seeded, do not edit.
  `task_objective[]` and `artifact_type[]` are **closed sets** from
  `diversity-taxonomy.toml`. `expert_time_estimate_hours` non-zero and plausible.
  The three explanation fields must be congruent with the actual files, and
  `verification_explanation` must justify the calibration of **every** tolerance.
- Timeouts: agent `timeout_sec` ≤ **3600** (project-wide hard ceiling). Long enough
  that the model can finish — *the challenge is correctness, not finishing in time*.
  All five trials timing out means the timeout is too low, not the task too hard.
- No invented fields; extras are silently ignored and create false impressions.

## Dockerfile

- `FROM` one of the ten pre-approved digest-pinned bases (exact digests in
  `references/check-base-image.sh`). Using an approved family with the wrong digest
  is a hard fail; a non-approved base is a non-blocking warning.
- Bake **verifier deps pinned** here (`pytest`, `pytest-json-ctrf`) so `test.sh`
  installs nothing at verify time.
- Never `COPY solution/` or `tests/`.
- Inputs go in `environment/data/`, copied in (`COPY data /app/data`).
- `RUN mkdir -p` the parent dir of every declared artifact, or artifact upload fails.
- apt: don't pin versions; `apt-get update` before install; `rm -rf
  /var/lib/apt/lists/*` in the **same** layer. No `apt-get upgrade`, no `--platform`,
  no `nproc`-derived parallelism, no `chmod` of secrets.

## Before every push

```bash
py -3 dynamo-preflight.py <task-dir> --refs <task-repo>/references
```

Use `py -3` on this machine: the script needs `tomllib` (Python 3.11+) and the
bare `python` on PATH here is 3.8, which fails with `ModuleNotFoundError`.

It replicates the pipeline's static checks (metadata completeness, placeholders,
taxonomy membership, slug shape, timeouts, absolute paths, instruction token
budget, artifact declaration, base image, Dockerfile hygiene, pinning, reward
write, verify-time installs, stray files, line endings). Passing it does not
guarantee the pipeline passes, but every failure it catches would otherwise cost a
CI round-trip.

## Leak check — run after every build

Confirm nothing in the agent-visible image discloses the answer: no ground truth
under `environment/`, no expected values in comments, docstrings, filenames or
fixtures, and no later git commit in a shipped repo revealing it. If a value the
verifier grades on can be read from inside the container, the task is void.

## Local validation

```bash
harbor run -p . --agent oracle
```

Expect reward **1.0**; `--agent nop` must be **< 1.0**. Write job output outside the
repo (`harbor run -o <dir>`) — Harbor writes into `task/jobs/`, which trips
`no_extraneous_files`.

## Windows

`core.autocrlf=true` plus Python text-mode writes produce CRLF. Normalise
explicitly to LF and re-verify that sealed copies stay byte-identical.
