# One slot, one session — the handoff prompt template

The single highest-leverage workflow habit in this kit: **never work two slots in one
conversation.** Each claimed slot gets its own Claude Code session, spawned with a
self-contained prompt. A session that owns one hash cannot accidentally push another slot's
repo, cannot blur two designs together, and can be killed without losing anything else.

Copy the block below, fill the `<>` fields, paste as the opening message of a fresh session.

---

```
Draft the Dynamo task proposal for slot `<HASH>`.

- Repo: https://github.com/<ORG>/dynamo-<HASH>-<category-slug> (<N> PRs, claimed <DATE>)
- Category: <Category> · Sub-category: **<Sub-category>**

FIRST: read `<PATH>/batch-brief.md` — it carries the batch-wide rules, the standing laws,
and the similarity denominator. Then run the retrieval index for laws rather than opening
long war-chest notes:  python tools/dr.py boot

SLOT-SPECIFIC RISK — <the single hazard that will kill THIS slot. Pick one, be concrete:
  · exact sub-category collision with an already-submitted task (name it, say what must differ:
    counted quantity, emitted artifact, semantic core — all three, not just the story skin)
  · a category hazard (floats in scientific/geometry work; everything-is-named in low-level
    work; optimization-margin framing; naive-search escape)
  · a family this category has already died to>

DESIGN LAWS THAT KILL THIS SHAPE — <name 2–3 from HARDNESS-LAWS.md that this specific
sub-category is magnetically attracted to violating, with the one-line test for each>

STOP AT THE PROPOSAL. No fork, no clone, no build, no push, no PR.

Deliver TWO files:
1. `dynamo-proposal-<HASH>.md` — platform artifact only, four-section house format,
   dense prose, zero internal lore. Grep for banned tokens before handing over.
2. `design-<HASH>-<slug>.md` — the design record: red-team table (3+ candidates with
   one-line post-mortems), kill-list clearance, disclosure ban list, pre-registered
   numeric bars, and the similarity argument.

Red-team 3+ designs against the kill-list BEFORE presenting. Kill for tokens, not
build-hours. Then report back and wait.
```

---

## Why "stop at the proposal" is the default

Running past the proposal into a build, in the same session, is legal and sometimes right —
but price it first. Every push re-rolls the non-deterministic rubric and the pass@ trials, so
a one-line fix costs the same wall-clock as a redesign. Measured on one slot in this corpus:
running proposal→green PR in a single session took **four CI cycles**, two of them spent on
self-inflicted spec/data inconsistencies that a fresh-eyes gate would have caught.

Decide deliberately per slot. Default to stopping.
