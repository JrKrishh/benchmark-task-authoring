# Batch brief template — the file every slot session reads first

When you hold more than two slots at once, the per-slot sessions need one shared document so
they stay consistent without talking to each other. This is that document. Write it once per
batch, before spawning any session.

Copy below, fill the `<>` fields.

---

# Dynamo batch — <N> slots claimed <DATE>

Shared brief. Every session in this batch reads this file first, then works ONLY its own slot.

Platform project id: `<PROJ>`  ·  Board: <board URL>

## The slots

| # | repo hash | Category | **Sub-category** | similarity margin |
|---|---|---|---|---|
| 1 | `<hash>` | <Category> | **<Sub-category>** | <clear / ⚠️ COLLIDES with `<hash>`> |

Repo URL pattern: `https://github.com/<ORG>/dynamo-<hash>-<category-slug>`

### The similarity denominator

List every sub-category you have ALREADY submitted. The similarity check grades same-author,
same-sub-category, so this list is what "clear" is measured against. Read it off the platform
(`pastTasks`), never off memory.

<`hash` Sub-category · `hash` Sub-category · …>

### Internal collisions (two live slots sharing one sub-category)

If two slots in THIS batch share a sub-category, whichever opens a PR first becomes the
other's denominator. Assign disjoint territories HERE, before either session starts, and make
them binding:

- **`<hash>` → <family A>.** <One line: what its constructed object is about.>
- **`<hash>` → <family B>.** <Same.>

A session whose best design drifts across the line reports back instead of building it.

## Standing rules for this batch

1. **Boot from the index, not the long notes.** `python tools/dr.py boot`, then
   `dr.py ask "<question>"`. Never open a war-chest to *search* it — only to read around a
   card the index already cited.
2. **Stop at the proposal** unless explicitly told otherwise for a given slot. No fork, no
   build, no push, no PR. (See `slot-session-prompt.md` for why.)
3. **Deliver `artifact_type` + `task_objective` with the proposal.** Closed sets; copy exact
   snake_case values from `references/diversity-taxonomy.toml` in any assigned repo. Graded on
   what the agent PHYSICALLY EMITS, never on subject matter.
4. **Red-team 3+ designs before presenting.** Kill for tokens, not build-hours.
5. **One session owns one hash.** Never start, edit or push another slot's repo.

## The laws most likely to kill a draft in this batch

Pull the full text from `HARDNESS-LAWS.md` — do not reconstruct from these one-liners.

- **Checked-vs-constructed** — a CHECKED predicate cannot carry difficulty; only a
  CONSTRUCTED object can. Ask: *what must the agent build that the verifier could not hand it?*
- **Factorising-predicate** — if legality decomposes over independent fields, the agent
  measures it one coordinate at a time. Dead. Repair: make the admissible set a union of boxes.
- **Legality-not-naming** — difficulty lives in what a wrong belief makes ILLEGAL, never in
  what it misnames.
- **De-disclosure** — state PREMISES, never INFERENCES. Performing the derivation in prose is
  worth about −3/5 at the gate.
- **Product-vs-state-graph** — a product of per-item ranges is solver bait; difficulty needs a
  state graph reached by DESTRUCTIVE moves. The tell: *what does a move destroy?*
- **The agent clock** — implementation volume is a design constraint, not a dial. A task whose
  crux is "code a lot before you can test anything" loses trials to timeouts that count for
  neither side of the gate arithmetic.

## Category hazards

<Per-category notes for the categories in this batch. Scientific/geometry → exact integers
only, floats are a rejection risk. Low-level/GPU → everything is named, so lexical difficulty
is dead and no real accelerator is available. Games → the correct-rules + naive-search family.
etc.>
