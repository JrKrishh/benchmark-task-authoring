# Local retrieval — answer design questions in ~1k tokens instead of ~35k

`scripts/dr.py` is a local hybrid search index over this skill's references plus, later, your
own notes. It exists because of a specific, expensive habit: re-reading a long document to
re-extract one law you already knew was in there.

`references/hardness-laws.md` alone is ~35k tokens and does not fit in a single read call.
Loading it to answer *"what trips `ava_review`?"* costs about thirty times what the answer is
worth, and you will pay that cost again on the next slot, and the one after.

## Set it up (about a minute, works with no notes of your own)

```bash
cd <skill directory>
python scripts/dr.py index --no-embed
```

That indexes the skill's own bundled references — the field manual, the eight rule files, the
CI-stage map, the templates. On a fresh install that is roughly **220 cards over 14 files
(~54k tokens of source) in well under a second.** Nothing to download, no API key, no model.

Then ask it things:

```bash
python scripts/dr.py ask "what trips ava_review verifier_coverage" --fast
```

Every answer arrives with `file:line` citations, so when you *do* want the surrounding
context you open one section instead of paging the whole document.

**Requirements.** `numpy` for indexing. `--fast` and `--no-embed` run lexical-only and need
nothing else. For semantic search — better recall on questions that do not share vocabulary
with the text — run `python scripts/export_model.py` once to build a small ONNX embedding
model, then drop the flags. Semantic mode is a genuine improvement but it is optional; the
lexical path answers most questions well and starts instantly.

## Point it at your own notes as they accumulate

Two environment variables extend the corpus beyond the skill:

```bash
export DYNAMO_MEM=/path/to/your/notes        # measured results, laws, war-chests
export DYNAMO_WORK=/path/to/your/workspace   # proposals, design records
python scripts/dr.py index                   # re-run after any write; incremental, ~1s
```

`DYNAMO_MEM` picks up your `.md` notes, ranking any file named `*-law.md` above the rest — the
assumption being that a distilled law outranks the narrative that produced it. `DYNAMO_WORK`
picks up `dynamo-proposal-*.md` and `design-*.md` in your working directory.

## Useful flags

| Flag | What it does |
|---|---|
| `--budget N` | Token ceiling on the answer. Default 2500; drop to 700–900 for a quick fact |
| `--fast` | Lexical only, no encoder — instant, and usually enough |
| `--klass law\|rule\|warchest\|proposal\|reference\|case` | Restrict to one document class. `--klass law` is the one you want when hunting a design law |
| `--task <hash>` | Restrict to one task's notes, once you have several |
| `--why` | Show the fusion scores, when a result looks wrong |
| `check <file>` | Fire the laws a draft proposal is most likely breaking |

## When a query comes back thin, route it

The ranking is tuned to stop one large document dominating every result, but on a query whose
wording does not overlap the text you want, lexical search can still hand you the most
*prominent* passage rather than the most *relevant* one. Two cheap corrections:

- **`--klass rule`** when you want process or pipeline material, **`--klass law`** when you
  want a design law. This is the single most effective flag and it resolves most thin results.
- **Use the vocabulary of the source, not of your problem.** "measure difficulty locally"
  finds less than "wrong-belief battery restart N-silence", because the second phrasing shares
  rare terms with the passage you are actually after.

If two attempts come back thin, open the section directly — the table of contents in
`hardness-laws.md` is there for exactly that.

## Why it is worth the minute

Measured on the **original** corpus where this technique was developed — roughly 540k tokens
across 120+ files of notes, war-chests and proposals. Your numbers on a fresh install will
differ: the skill's own references are a much smaller and more uniform corpus, so retrieval is
faster but has less to disambiguate between. Treat the accuracy figures as evidence the
approach works at scale, not as a promise about day one.

| | before | after |
|---|---|---|
| Session start | ~18k tokens | **~3k** |
| One design question | 20–40k tokens | **1.2–2.5k** |
| Retrieval accuracy | — | **top-1 71%, top-3 93%** (14 ground-truth cases) |
| Citations resolving to the real source line | — | **40/40** |
| Latency | — | 1.2 s hybrid · 0.38 s cached · 0.10 s `--fast` |

Three findings from building it, in case you build something similar:

**Import cost dominates a CLI.** `sentence_transformers` costs ~17 s of imports per process —
fatal for a tool you call ten times a task. Exporting BGE-small to ONNX runs the query path in
0.66 s cold and 8 ms warm at cosine 1.000000 parity with the original, verified rather than
assumed.

**Rank fusion alone was not enough on a corpus with one dominant document.** The largest,
most-cross-referenced file won slot 1 for nearly every query and buried the note that actually
measured the thing — **top-1 was 29%**. Three corrections fixed it to 71%: a *coverage* term
(what share of the query's rare terms a card really contains), a verbatim-phrase bonus, and
per-file saturation so one source cannot occupy every slot.

**Chunking must carry true line offsets.** Reconstructing them after reassembly drifted 14
lines and made every citation untrustworthy. Tracking offsets through the split fixed it to
40/40 exact — and a citation you cannot trust is worse than no citation, because you stop
checking.

## The discipline that makes it pay

Query the index *before* opening any long document. Open a file only to read **around** a card
retrieval already handed you — that targeted read is fine and often necessary. What costs you
is opening the file to *search* it.

Re-run `dr.py index` after writing notes. It is incremental and takes about a second; a stale
index quietly returns yesterday's answer, which is the one failure mode that erodes trust in
the tool.
