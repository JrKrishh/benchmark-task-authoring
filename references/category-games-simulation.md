# Category brief — Games, Puzzles & Interactive Simulation

Two slots with opposite outcomes, and the contrast is the whole lesson.

| | sub-category | outcome |
|---|---|---|
| **Games-1** | Game AI & strategy | **died** — seven designs, slot ultimately released |
| **Games-2** | Interactive text games | **0/5 · 5 good-valid · avg 0.000 · all 14 stages green on ONE push, zero revisions** |

Games-2 is the maximum possible gate result. Games-1 is the corpus's most expensive failure.
Same category, and the difference is structural.

---

## Why Games-1 died: correct rules + a searchable move space

Games hand you fully-stated rules and a move space. That combination is the
**correct-rules + naive-search family**, and it is dead (§3.1 #13 and the naive-search bar).

The decisive measurement: Games-1's trap caught the *one* agent who used recursive minimax with
a position-keyed transposition table (22/32 wrong) — and **four of five agents sidestepped it
entirely** by using BFS with 0-initialised value iteration, a textbook technique on a loopy game
graph. pass@5 came back **4/5 solved**.

> **A trap aimed at one algorithm fails if a different, standard algorithm solves the problem
> correctly. Check what the textbook approach is before building the trap.**

Two further failures from the same slot:

- **Hardening by scale does not work.** The design was hardened to ~67k states (11× the
  original) and still went 2/2 solved — **both agents wrote two independent solvers and
  reconciled them** (§3.1 #8).
- The redesign direction that was identified but never shipped: make the third-repetition
  outcome the **material difference at that moment** instead of zero, which makes "cycles are
  worth 0" false and renders value iteration *unsound* rather than merely unlucky.

---

## Why Games-2 cleared: an archetype is a whole planner

Games-2 cleared on one push and contributed the **archetype-faithfulness law**, which is now
the standard for battery construction everywhere:

> **A wrong belief must be threaded through EVERY site that reads it** — the engine, the derived
> deadlines, the candidate ORDER, and the self-replay. An archetype is a whole planner, not a
> patched predicate.

Measured twice on that slot: once where a **stable-sort tie** silently restored correct
behaviour, and once where an **inherited deadline** did. In both cases the archetype looked
wrong but behaved right, because one site still held the correct belief.

**Tie-break order is part of an archetype's semantics.** If your wrong-belief planner and your
reference differ only in a comparator that never fires, you have measured nothing.

Games-2 also carries the **asserted-tractable-leg-first** discipline: build and measure the leg
you claim is tractable before the leg you claim is hard.

---

## The harness constraint that shapes every design here

Harbor tasks are **non-interactive**. There is no stdin dialogue with a running game. The agent
must emit a physical artifact the verifier executes or checks — an engine, a policy, a
walkthrough, a replay, a solver.

Decide early what the agent physically emits, because that choice fixes your closed-set
`artifact_type` label, and the wall-clock law applies to whatever search that artifact implies.

---

## The shape that works here

**Product-vs-state-graph favours this category** (§3.1 #3) — games are the natural home of
destructive moves. The tell: *what does a move destroy?* If pieces merely occupy positions, you
have a product of ranges and a solver eats it. If a move consumes and regenerates the resource,
you have a state graph.

Games-2's shape — recertifying a walkthrough against a changed world — is constructive by
construction: the agent must build a valid traversal, and a wrong belief about the engine makes
traversals **illegal** rather than merely suboptimal.

---

## Pre-build checklist

1. **Are the rules fully stated and the move space searchable?** That is the dead family. What
   does a move *destroy*?
2. **What is the textbook approach to your game?** Build the trap against *that*, not against
   the algorithm you imagined.
3. **Is your trap unsound for the standard technique, or merely unlucky for it?** Unsound is
   what works.
4. **Are you hardening by scale?** Two correct solvers agree at any size.
5. **Is every archetype a whole planner** — belief threaded through engine, deadlines, candidate
   order and self-replay?
6. **Does a tie-break or an inherited value silently restore correctness** in your archetype?
7. **What does the agent physically emit?** The harness is non-interactive.
8. **Is the naive-search family barred in wall clock at the disclosed cap, un-contended?**
9. **Have you measured the leg you claim is tractable**, first?
10. **Exact integers; blind public sample.**

---

## Honest limits

One clear and one loss, so the sample is genuinely two-sided here — rarer and more useful than
the all-clear categories, but still n = 2.

Games-1's slot was released after seven designs; a locally-built task from it was never pushed
and has no repo to land in. Treat that shape as a design donor, not a template.

Four sub-categories are untouched: board and card games, puzzle solving, world simulation, and
rendering and graphics. **Board/card games and puzzle solving are the highest-risk of these** —
both are exactly the correct-rules + searchable-moves shape that killed Games-1, and both are
saturated with named algorithms.
