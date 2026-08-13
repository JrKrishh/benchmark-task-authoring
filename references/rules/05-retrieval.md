---
description: Retrieve from the local index instead of re-reading the corpus
alwaysApply: true
---

# Retrieve, do not re-read

The Dynamo corpus is ~193k tokens across 49 files. Re-reading a war-chest to
re-extract a law is the single largest avoidable token cost in this workspace,
and it scales with every slot shipped.

**Before opening any of `../hardness-laws.md`, a `dynamo-*.md` memory
file, `../hardness-laws.md`, or a past `dynamo-proposal-*.md` — query the index.**

```bash
python scripts/dr.py boot                    # session start (~3k tok, replaces ~18k)
python scripts/dr.py ask "<question>"        # ~1-2k tok, <1s, cited
python scripts/dr.py ask "<q>" --task <hash> --klass law --budget 1200
python scripts/dr.py check <proposal.md>     # laws a draft is likely breaking
python scripts/dr.py laws --write            # regenerate the distilled deck
```

Every returned card cites a real `file:line` (verified 40/40). Opening that file
to read *around* a card you were given is a targeted read and is fine. Opening a
file to *search* it is the thing to stop doing.

Run `dr.py index` after any memory write — incremental, ~1s.

## Cache measurements, never re-derive or re-run them

Standing rule: *never fabricate a measurement*. The cache is how you keep that
rule cheaply — a stored result is fingerprinted against the tree that produced
it, and `get` fails with exit 4 if that tree has changed since.

```bash
# store: pipe the command's output straight in
python dynamo-preflight.py <task-dir> 2>&1 | \
  python scripts/dr.py cache put preflight-<hash> --stdin --watch <task-dir>

# reuse, or re-run if missing (3) or stale (4)
python scripts/dr.py cache get preflight-<hash> --watch <task-dir> \
  || python dynamo-preflight.py <task-dir>

python scripts/dr.py cache list
```

Cache preflight output, probe solve rates, timeout-probe wall clocks, oracle/nop
rewards. A `STALE` result is a signal to re-run, never to quote the old number.
Always pass `--watch`: without it nothing is verified, and the tool will say so.
