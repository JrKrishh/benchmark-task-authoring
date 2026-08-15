# Category brief — Model Training & ML Infrastructure

Read this when a slot lands in this category. Evidence for anything cited lives in
`hardness-laws.md` at the section given.

Two slots have been assigned here and **both cleared, both green in a single CI run** — the
only category with that record. Both were **Distributed training**.

| | sub-category | final | notable |
|---|---|---|---|
| **MLInfra-1** | Distributed training | 0/5 solved · 5 good-valid · avg 0.000 · **0 timeouts** | fully green first roll; similarity **UNIQUE**; failures stratified with "no single root cause dominating" |
| **MLInfra-2** | Distributed training | 1/5 solved · 3 good-valid · 1 in-progress-timeout · avg 0.200 | fully green first roll, zero fixes; cleared `cosine_similarity` as the **2nd task in the same sub-category** |

That both cleared first-roll is the useful signal: this category rewards the printed-optimum
skeleton (§3.2) more cleanly than most, because infrastructure planning naturally produces a
closed-form floor and a legality question that is genuinely separate from it.

---

## The category's own hazard: your shape vocabulary burns fast

Both cleared slots are **resource-planning shapes**, and they consumed a lot of mechanics
between them. MLInfra-2 chose its scarcity device by explicit elimination, and the reasoning is
the reusable part:

> Scarcity device: **TIME** (retention clocks + a per-tick completion rate) — deliberately NOT
> any burned mechanic: no residency slots, no staging, no byte ranges, no registers, no span
> algebra, no capacity buffers.

Every item on that "burned" list was load-bearing in an earlier task by the same author. In a
category where the natural domain is *scheduling a constrained resource*, the resource itself
is the thing similarity notices. **Pick the scarce thing first, and pick one nobody has
used.** Time, ordering deadlines, retention/expiry, and membership-over-time are the ones with
mileage left here.

Similarity is passable even on a repeat sub-category: MLInfra-2 was the **8th same-author task
and the 2nd in that exact sub-category**, and still passed — but only because the surface was
differentiated loudly (different domain vocabulary, different state objects, no shared
mechanics). See §6 on the vocabulary partition.

---

## Four shapes red-teamed dead before building — do not resurrect

These were killed on paper during MLInfra-2's design phase. Each is a shape a reasonable author
reaches for in this category.

| shape | why it dies |
|---|---|
| **Topology-aware rank placement** | Graph partitioning is named *and* library territory (§3.1 #5), and optimization-margin difficulty is dead. The TP/PP/DP group math is also already burned |
| **Data-shard prefetch / locality assignment** | Reduces to a fetch-minimum under residency + eviction + budget — which is precisely an earlier slot's graded quantity. Worse, it **decomposes per worker** without those devices (§3.1 #2) |
| **Communicator-rebuild deadlock ordering** | All the difficulty sits in one ordering layer whose feasibility is cheap to simulate; global-total-order is the textbook fix; the constructive N is weak |
| **Pipeline / rematerialization schedule refit** | 1F1B and Checkmate are literature — knowledge, not difficulty. The stash slots are also a burned mechanic |

The common thread: this domain is **exceptionally well-documented**, so almost any named
scheduling problem in it has a textbook answer the model already holds. Ask of every candidate:
*does this problem have a name?* If yes, it is knowledge.

---

## The CP-SAT hole — the specific trap of this category

Infrastructure planning naturally produces a **dispatch layer**: precedence constraints,
deadlines, a per-tick completion rate. That shape is RCPSP, and `allow_internet = true` is
mandated, so an attacker armed with a constraint solver will crack most instances of it.

MLInfra-2's position, and it worked: **put the difficulty in deriving the constraint set, not
in searching over it.** Its identity layer — which records are missing, which watermark applies,
whether a sum is over step-membership or current-membership — is what the agents got wrong. The
dispatch itself was allowed to be tractable.

Two things follow, and both are mandatory here:

1. **The build battery must include a CP-armed attacker** as a measured red flag, not an
   afterthought.
2. **Do not rely on tightness.** Random restart over dispatch orders is cheap to test; select
   sealed instances against restart, unpruned DFS and EDF-best-first *under the disclosed cap*
   (§3.1 #12 — feasible fraction between 1e-4 and 1e-1 is worth zero).

If the probe cracks it, remember the counter-law: **probe-dead ≠ gate-dead** (§9.1). The probe
proves a shortcut *exists*; the gate measures whether the agent *finds* it. The cheap middle
path is a disclosed-flaw measurement push — static-stage failures cost no quota.

---

## What made both slots clear on the first roll

**A dependency structure that is genuinely 2-D.** MLInfra-2's accumulator chains form a
lattice over the rank × step grid — *not decomposable per cell*. That is the direct answer to
the factorising-predicate law (§5.2): if your constraint decomposes per worker, per shard or
per step, the agent measures it one coordinate at a time.

**Deep doom that propagates backwards.** A chain's final cell needs a sibling that expires
early, so the true latest-start of every upstream cell silently advances. Per-cell greedy
dispatch strands chains many ticks later, and expiry is permanent. This is the
unrecoverable-and-not-locally-visible pattern (§3.1 #11) in its cleanest infrastructure form.

**A battery of wrong-planner archetypes as the verification step.** MLInfra-1 shipped six
(bulk-prefetch, bulk-stage, optimizer-replicated, coord-freeness, ceil-stage, no-zero): all
pass the public case for blindness, each dies on at least one sealed case. Alongside it, a
five-way tie-check battery of *valid alternate* schedules passed 45/45, guarding
over-constraint. **Trial failures landed exactly on the predicted classes.**

> Worth noting against the general rule: MLInfra-1's sealed cases were **hand-designed and it
> worked**, because the load-bearing step was the adversarial battery rather than the instance
> search. Randomized generation (§6.3) is the safer default; it is not the only viable one when
> the battery is strong.

And the shape of the kills on MLInfra-2's pass@2: **both agents wrote greedy schedulers — "no
backtracking, no deadline propagation."** The same class that dominated pass@5. When your
pass@2 failures name the archetype you designed for, the pass@5 will usually agree.

---

## The timeout arithmetic — a latent miss worth copying the fix from

MLInfra-1 shipped with **9 program invocations × 60 s cap = 540 s worst case against a 300 s
verifier budget.** It did not bite — all five trial agents crashed fast, giving 5 good-valid
fails — but an agent hanging on five or more cases would have killed the verifier and turned
genuine analytical failures into infra classifications.

The rule (§7): **`n_items × per_item_cap < verifier timeout_sec`, with margin.** Compute it
before shipping. The bundled fix, for reference: raise the verifier budget to ≥ 900 s or drop
the per-case cap to ~25 s, convert `TimeoutExpired` into a clean `pytest.fail`, and disclose
the cap in `instruction.md` and `verification_explanation`.

MLInfra-2 lost one trial to an **in-progress timeout** on an agent that had diagnosed correctly
mid-fix. That is the other end of the same problem (§7) and it costs a countable fail.

---

## If your sub-category is Reinforcement learning

⚠️ **No RL slot has ever been built, so everything in this section is `prospective`** —
reasoning from the category's measured laws, not from a measured RL outcome. Weight it
accordingly and re-measure.

**The similarity position is good.** RL is a fresh sub-category here; both prior slots were
Distributed training. You have margin at the sub-category level that MLInfra-2 did not.

**The naming hazard is severe, and worse than elsewhere.** RL is one of the most thoroughly
documented areas in the field. PPO, DQN, A2C, GAE, TD(λ), prioritised replay, advantage
normalisation — every one is a named crux with a reference implementation the model holds
(§3.1 #5). A task whose core is "implement the algorithm correctly" is transcription.

**Two more traps specific to this sub-category:**

- **Stochasticity fights exact grading.** Anything that samples needs a seed contract, and even
  then floats in the graded path are a rejection risk. Prefer a design where the agent emits a
  *plan or a reconstruction* over integers, not a trained artifact or a reward curve.
- **"Reward hacking" is a graded rubric criterion.** A task whose domain vocabulary is rewards
  and returns invites a collision in the prose fields — reviewers reading `reward_hacking`
  against a task literally about rewards. Choose vocabulary that keeps the two separable.

**Where the difficulty plausibly lives — RL *infrastructure*, not RL *algorithms*.** The
category's own record says the winning shape is a constrained planning or reconstruction
problem over a well-specified runtime, with a printed floor and a 2-D dependency structure.
Candidate framings that keep that shape while inheriting RL's realism:

- **Replay-buffer eviction and sampling-eligibility reconstruction** under retention and
  staleness rules — membership over time, which is a device with mileage left.
- **Rollout-worker scheduling with expiring trajectories** — but beware, this is closest to
  MLInfra-2's time-scarcity shape and would need loud differentiation.
- **Checkpoint/resume reconciliation of an interrupted training run** — recovering which
  updates were durably applied when workers, optimizer state and buffer state have different
  durability rules. This inherits the identity-layer difficulty that cleared MLInfra-2 while
  changing every noun.

Whichever you pick, run the category checks below before committing, and the CP-armed attacker
before believing any of it.

---

## Pre-build checklist for this category

1. **Does the problem have a name in the literature?** This domain is unusually well-covered.
   If yes, it is knowledge, not difficulty.
2. **Does a library return the load-bearing object?** Search for it explicitly.
3. **Have you picked a scarce resource nobody has used?** List the burned ones first.
4. **Does your constraint decompose per worker, per shard or per step?** If yes it factorises
   (§5.2) and the agent measures it one coordinate at a time.
5. **Is there a dispatch layer?** Then assume a constraint solver reaches it. Put the
   difficulty in deriving the constraint set instead, and battery it with a CP-armed attacker.
6. **Is a wrong move unrecoverable AND not locally visible?** Backward-propagating expiry is
   the shape that worked.
7. **Does `n_items × per_item_cap < verifier timeout_sec` hold with margin?** MLInfra-1 shipped
   at 540 s against 300 s and got lucky.
8. **Do your wrong-planner archetypes all pass the public case** and each die on a sealed one?
9. **Does a tie-check battery of valid alternates pass 100%?** Guards over-constraint.
10. **Is every graded number an exact integer?** Especially if the domain is stochastic.

---

## Honest limits

**n = 2, both cleared, both the same sub-category.** No abandoned slot to learn from here, and
no measurement at all outside Distributed training — so the Reinforcement learning section
above is reasoning, not evidence, and is labelled as such.

Both slots also predate several later laws. Their numbers stand; some of their framing has been
superseded by the wider manual.
