# The Hardness Laws: A Field Manual for Terminal-Bench 2 Task Authors

Distilled from 15 cleared slots, at least four of them fully green in a single CI run, plus every measured failure it took to get there. Tasks are cited by anonymised slot labels (category + ordinal, e.g. GPU-2, ETL-1); each label is one real task and stays stable across the document. Every claim below carries its evidence and its evidence class: **measured-gate** (the platform's own pass@2/pass@5 measured it), **design-kill** (killed by local measurement or argument, never gate-measured), or **prospective** (untested hypothesis). Where the corpus contradicts itself, both readings are given.

---

## Contents

This file is ~35k tokens and **does not fit in a single read call** — plan on two passes, or
jump straight to the section you need.

**If you are holding a result that came back too easy, go to §9.2 first, then §3.1.** Reading
this file front-to-back is the right approach when designing, and the wrong one when
diagnosing: the diagnosis lives near the end.

| § | Section | Load it when |
|---|---|---|
| 1 | [The One Law](#1-the-one-law) | Always — the three consequences everything else hangs off |
| 2 | [Gate Arithmetic and the Failure Taxonomy](#2-gate-arithmetic-and-the-failure-taxonomy) | Before designing; and whenever a result needs interpreting |
| 3 | [Design: The Kill-List and the Proven Floor Shapes](#3-design-the-kill-list-and-the-proven-floor-shapes) | Choosing or red-teaming a task shape — **§3.1 is the 13-shape kill-list, §3.2 the proven floor shapes** |
| 4 | [The Disclosure Calculus](#4-the-disclosure-calculus) | Writing the spec — what to state and what to withhold |
| 5 | [Beliefs: What Can Actually Carry Gate Load](#5-beliefs-what-can-actually-carry-gate-load) | Designing the wrong belief your task punishes |
| 6 | [Instance Selection](#6-instance-selection) | Choosing which instances ship in the sealed set |
| 7 | [Time: Caps, Clocks, and Classification](#7-time-caps-clocks-and-classification) | Setting timeouts; diagnosing timeout-blocked results |
| 8 | [Verifier and QC](#8-verifier-and-qc) | Writing or auditing the verifier — and **§8.8 before every push after the first**, because an advisory you left is the next run's blocker |
| 9 | [Measurement Epistemics: What Evidence Is Worth](#9-measurement-epistemics-what-evidence-is-worth) | **Diagnosing a result — start at §9.2 "What a 2/2 block means"**, then §9.1 for the evidence asymmetry, §9.3 for the stop conditions, and **§9.6 before you build another core** — one measured 2/2 was a mis-calibrated percentile, not a dead shape. Also: deciding whether any measurement justifies a decision |
| 10 | [The Pre-Push Checklist](#10-the-pre-push-checklist) | Immediately before the one push |

---

## 1. The One Law

**Difficulty is not engineering effort, and the gate does not measure how hard your task was to build. It measures one thing: whether strong agents, handed every rule in fair prose, still fail to CONSTRUCT a correct artifact.**

Three consequences hang off this, and every other law in this manual is downstream of one of them:

1. **A property the agent CHECKS cannot carry difficulty; only an object the agent must CONSTRUCT can.** Pre-build test: *what must the agent build that the verifier could not hand it by simulating?* If the honest answer is "nothing — it just decides a predicate correctly," the design is dead however subtle the predicate looks to a human. (Four independent confirmations; see Part 5.)

2. **Knowing N is not achieving N.** Every cleared math/ML slot in the corpus *prints its closed-form optimum in the spec* and still wins, because constructing a legal object attaining N is the hard part. Seven slots cleared on this skeleton (Math-1, SciComp-1, ML-1, ML-3, ML-2, MLInfra-1, MLInfra-2 — measured-gate, six of seven at 0/5 solved).

3. **Fairness forces every graded rule into agent-visible text — so the only thing you may withhold is the *consequence* of the rules taken together.** State premises, never inferences. Performing the derivation in prose is worth about −3/5 at the gate (measured; Part 4).

The failure mode this manual exists to kill: you spend a week building an exotic semantics, agents solve it 2/2 in under an hour, and the platform tells you `difficulty_crux = NA` — they never even reached the decision point you designed. That is not bad luck. It is one of a small number of measurably dead shapes, catalogued below.

---

## 2. Gate Arithmetic and the Failure Taxonomy

Design against the arithmetic first. A task can be genuinely hard and still fail the gate on classification alone.

### What the gate needs

| Quantity | Requirement |
|---|---|
| pass@5 solved | ≤ 2/5 to be accepted (agents must fail ≥ 3 of 5) |
| Countable fails | good-valid-fail + soft-timeout ≥ 3, AND ≥ 1 good-valid-fail |
| Partial credit | None. An avg@5 of 4 (4/5 solved) is a FAIL (confirmed in platform comms) |

### What counts and what doesn't

| Trial outcome | Counts toward the fail bar? |
|---|---|
| good-valid-fail | Yes |
| soft-timeout-fail | Yes |
| solved | Against you |
| in-progress-timeout | **Neither side** |
| infra / setup-timeout | **Neither side** |
| task/verifier-issue | **Neither side** |

> [!danger] A run can be 0/5 solved and STILL BLOCKED.
> Measured twice. Math-1's first pass@5: 0/5 solved · 1 good-valid-fail · 4 infra/setup-timeouts — blocked; the fix was a per-item cap change from 120 s to 25 s. Math-2 run 2: 0 solved · 2 good-valid-fail · 3 in-progress-timeouts — blocked, needed 3 countable, got 2. Failure *taxonomy* matters more than solve rate.

**Budget for losing ~1 trial in 5** to an in-progress-timeout or a harness wedge (terminus-2 sometimes fails to deliver a heredoc EOF and wedges the shell for the whole run — classified infra). Measured: MLInfra-2 lost one, ML-1 lost one, SciComp-2 lost one (an agent had a working solution at step 7, rewrote it at step 9 with the floor unimported, and ran out of clock). Aim for ≥ 4 countable fails, not exactly 3.

### The measurement stack (fixed platform numbers)

- Difficulty is measured with the Terminus-2 agent; the repo's `task.toml` pins `model_tested = "Opus-4.8"` — **the docs site's "GPT-5.4" is stale; the repo file is authoritative.** 128k max completion tokens, reasoning on, effort xhigh.
- Agent timeout ceiling: 3600 s, project-wide. Raising it makes the task easier; lowering it games the score and reviewers send it back. Do not touch it.
- pass@2 is limited to 6 runs/day per fellow per task, quota resets 00:00 UTC; difficulty-suggestion comments are capped at 2/day and can arrive stale.
- 31 named rubric criteria; a single FAIL on any of them can block. The QC gate runs 30 Major checks (A1–A6, B1–B6, C1–C6, D1–D5, E1–E7) and defaults to FAIL.
- instruction.md is capped at 1,500 tokens and is a *prompt*, not a document: no title, no headers, zero bare `name.ext` tokens (a hit fails static review and skips every downstream stage).
- A stage-1 static FAIL or an AVA block **skips tier1, qc, pass2 and trials entirely** — one trivial non-difficulty failure costs the whole difficulty measurement (measured on ML-1, GPU-1, GPU-2).

### Two review-stage traps that fail whole tasks

**The instruction-suffix reversal (measured-gate, standing as of Aug 2026).** The line "You have N seconds to complete this task. Do not cheat by using online solutions or hints specific to this task." is now an automatic rubric FAIL under `instruction_concision`, which names that boilerplate as an explicit fail condition. Measured on GPU-2: 30/31 criteria PASS, the single FAIL was this line, and the block skipped everything downstream. The agent's time budget belongs in `task.toml` (`[agent].timeout_sec`), not in prose. A per-item cap disclosed in prose where the task's legality depends on it ("each invocation gets 60 seconds") is *not* the banned boilerplate.

> [!warning] Contradiction on record.
> The platform's instructions site (snapshot 2026-07-25) states the opposite — "The final line is enforced. Must end with exactly: … A static check fails the PR otherwise" — and every earlier slot shipped that line. A submit-checklist page has also *required* the line while the rubric fails it. Resolution: the rubric TOML ships in the repo and wins; omit the line. Local preflight tooling passes both with and without it — this violation is caught only at review.

**Taxonomy labels (measured-gate).** `artifact_type` is judged strictly on what the agent *physically produces or modifies*, never on what the task is conceptually about. An input the agent merely reads earns no label; the category name earns no label. Two measured fails: ML-1 added `model_or_checkpoint` because the subject was a neural network the agent only ever read inside an input JSON — FAIL, cost a full review cycle; DataSci-1 added `dataset_or_tabular_file` for its input roster JSON — FAIL, and dropping to the two-label pair passed. Default for the printed-optimum shape (agent writes one planner, emits one JSON plan): `artifact_type = ["single_script_or_program", "generated_output_artifact"]`, `task_objective = ["implement", "optimize"]`. Verify exact snake_case spellings against `references/diversity-taxonomy.toml` in the task repo, not the docs page. A plan *describing* an archive is not an archive; a determined layout means the agent optimizes nothing, so drop "optimize" in that case.

---

## 3. Design: The Kill-List and the Proven Floor Shapes

### 3.1 The kill-list — shapes measured dead

| # | Dead shape | Evidence | Class |
|---|---|---|---|
| 1 | **Checked predicate** as the core (uniformity/divergence analysis, alias analysis, address-space inference, escape analysis, effect systems, type inference, "does a legal X exist?") | GPU-2 design #1 killed pre-build; ETL-2 v1 2/2 solved; Media-2 blocked 2/2 twice until a constructive leg was added; positive control GPU-2 design #2 (same author/slot/week, only checked→constructed changed) cleared at 1/5 | measured-gate + design-kill |
| 2 | **Factorising legality predicate** (conjunction of independent per-field conditions) | ETL-2 v1: 2/2 solved, `difficulty_crux = NA`; third kill on paper DataQuery-1 (F1 ∧ F2 ∧ F3) | measured-gate |
| 3 | **Product of per-item ranges** (assign items positions under a cumulative resource) — CP-SAT/OR-Tools bait; `allow_internet = true` is mandated, the agent installs the solver | Two same-day paper kills on LowLevel-1 designs #1 and #2; one-line policies won 85–95% of instances | design-kill; see the density escape below |
| 4 | **Optimization margin in clean math** | min-degree optimal 399/400 on min-fill; textbook Paar within ±1 op of strong search on min-XOR SLP | design-kill |
| 5 | **Named crux / library-returned object** — a crux with a name in the literature is knowledge, not difficulty; any load-bearing object a library returns kills the design | commutator identity killed one design; `sympy.smith_normal_decomp` returning the saturated integer kernel killed 2 | design-kill (each entry cost a billed run) |
| 6 | **Fully-specified custom-semantics interpreter** ("the API is the spec itself") | kill-list entry; Build-2 probes measured a fully-stated byte-layout calculus at 4/4 solved (100%) on the probe rig — a local pass@k re-run of the task against a strong agent on your own API keys; build one, and read every “probe” number in this manual as coming from one | design-kill / probe |
| 7 | **Breadth of independent one-line rules** | 9 fields × 39 scenarios ≈ 300 clean sub-results still solved 2/2; SysInfra-1 v1's core was eight independent one-line rules | measured-gate + design-kill |
| 8 | **Scale / brute-force thesis** — growing state spaces cannot open a validation gap; two correct solvers agree at any size, so the agent cross-checks with a second solver | Games-1 Cascade hardened to ~67k states (11× v1): pass@2 2/2 solved; both agents wrote TWO independent solvers and reconciled them | measured-gate |
| 9 | **Blindness engineering** — a spec complete enough to be fair is self-verifiable; the agent writes its own second implementation | six designs failed on it; one design’s third version went 2/2 (Opus matched all 32 sealed values with exact rationals to ~1700 digits). PARTLY SUPERSEDED: the gap opens when the spec is fully sufficient AND the answer is a constructed artifact meeting a printed optimum | measured-gate |
| 10 | **Rare deciding rules** — a clause invisible in the evidence is invisible in the result | design #4: hypotheses fitting 90%+ of logs changed 0–7% of answers, and vice versa; design #5: 6 of 8 rule-omission variants diverged on 0% of games | design-kill |
| 11 | **Order-independent end state** — if every correct plan reaches the same end state, a fatal move strands something immediately and backtracking is free | corollary from DataSci-1; the working contrast is a wrong move that is unrecoverable AND not locally visible | design-kill |
| 12 | **Tightness as the sole defense** — feasible fraction in 1e-4..1e-1 is worth exactly zero | measured on three withdrawn designs; only below ~1e-7 counts, and only if expected_draws × cost_per_draw > 10 × cap | design-kill |
| 13 | **Trap aimed at one algorithm** — a different standard algorithm sidesteps it | Cascade v1: 4/5 solved; 4 of 5 agents used BFS + value iteration, sidestepping the graph-history trap that caught only the one minimax agent (22/32 wrong) | measured-gate |

> [!note] The density escape on kill #3.
> SciComp-1 is a partial counterexample: a register file plus eviction is closer to an allocation product than a state graph, and it cleared 0/5 — but on extreme feasible density (5.97e-12), not on structure. The law reads: a product of ranges is dead **unless** feasible density is below ~1e-7. And note the internal tension: the product-law file treats its paper kills as final while the early-signal evidence (Part 9) says a pre-build NO_GO has been measured wrong. Use the law to choose between designs; be slower to abandon a slot on it.

**The cheap tell for kill #3:** *what does a move destroy?* If nothing — items just occupy positions — the space is a product and a solver eats it. Difficulty needs a **state graph reached by destructive moves**, where the resource is consumed and regenerated by the moves themselves. Gate-cleared state-graph examples: move order over depot slots with one empty slot (0/5); relocation order under clobber (GPU-2, 1/5); append-only write order under a staging cap (Media-1 v7, 0/5).

**The matching shape is dead too — a cumulative placement resource on top of rule-derived eligibility reduces the search to a small bipartite matching with a fixed charge: polynomial, and maximum expressible tightness does not save it** (design-kill, Build-1 gate-first probe): at N=16, slack=1, exhaustive DFS solved 12/12 in 0.000–0.001 s, max 209 nodes (the measured greedy agent still solved 9/12); at slack=0 (Σslots = N, the maximum tightness the design can express) DFS solved 12/12, 12/12, 8/8 at N=22/30/40 with zero timeouts — against a pre-registered kill bar of "DFS solves ≤ 4/12". Generator-only hardening fails the same way: free reversible moves dissolve per-instant quotas.

**The one-line-policy battery (pre-build, costs under an hour):** write the three most obvious one-line policies and enumerate the optimum EXACTLY on small instances. Winners should sit near 0%. LowLevel-1 design #2 measured latest 52–95%, earliest 0–55%, no-policy only 5–15% across a 12-point sweep — dead. Methodology warning, measured the hard way: it took FOUR attempts to get one right number, and each wrong one was plausible — (1) a loose resource bound produced "greedy solves 100%" for the wrong reason; (2) an ascending search order produced 97% spurious "timeouts" that looked like a hard feasible band; (3) a non-admissible B&B bound reported P_opt = P_late by construction; (4) full enumeration on small instances settled it and *reversed* conclusion 3 entirely (P_opt < P_late on 93–97%, mean gap 8–10 slots). The first probe on that design had reported a naive/reference search-cost ratio of 21,614× on a design a one-liner solves — **never infer hardness from a search-cost ratio, and never trust a pruned search you wrote yourself.**

**The coupling repair for kill #7** (design-kill, Build-2 family H): make each step CONSUME context, so selection becomes a stage-level fold — one slip shifts every later selection and every downstream key. Measured after nine independent one-line rules were diagnosed as exactly kill #7's dead shape: with each stage's additions consuming the context, the family is live on all 12 incidents and kills 12/12 while staying blind on the public example. The repair costs one SPEC sentence and makes the natural implementation wrong. The anti-pattern that silently neutralises it: a cumulative per-stage archive kills the family — the union is identical with or without consumption; use per-item streams.

**Refutation must be SHARED and LATE** (design-kill, SysInfra-1 — no Systems-Infrastructure slot has ever reached the gate, so design-kill evidence only): a wrong choice refuted locally and independently costs the agent one retry; it must be irrefutable until the LAST stage of its block, or the search space is options^blocklength only on paper. Measure refutation lag TWICE — checkpoint lag AND prune lag; both measured 3 and uniform on SysInfra-1, making backtracking cheap. The companion measurement was the decisive kill: measure the reference planner's cost against the JOINT space — removing the gradient an attacker climbs does not stop it enumerating; you must show the joint space is unreachable, not merely un-guidable (one collapsing bit per block made per-block hardness trivial jointly; the kill-gate NO_GO landed with two of its clauses mutually exclusive by construction).

### 3.2 The proven floor shapes

The winning skeleton, measured across seven cleared math/ML slots: **the spec PRINTS a closed-form optimum N and guarantees achievability** (no stored optima — the verifier recomputes N from sealed input); difficulty lives in constructing a legal plan under interacting stateful rules with nonlocal coupling; a merely-valid answer is easy, so every attempt finishes with a concrete wrong answer; grading is by independent simulation of the end state so any correct strategy passes.

Six floor formulas have cleared the gate:

| Floor formula | Shape | Slot, result |
|---|---|---|
| N = Σ_K max(0, need(K) − carry(K)) | conservation / demand−supply | ML-2, 0/5 · 5 gvf |
| N = \|D \ A\| | set difference | ML-1, 0/5 · 4 gvf · 1 ipt |
| N = \|M\| | cardinality of a derived set | MLInfra-2, 1/5 · 3 gvf |
| N = Σ_v \|{S[c] : c an add-value with v as operand} \ {S[v]}\| | non-canonical-write count | SciComp-1, 0/5 · 5 gvf |
| N = #{orbits of products not served by the archive} under cyclic shift | **equivalence-index / orbit count — the strongest** | ML-3, 0/5 · 5 gvf, accepted |
| N = \|{stages whose state-shape is not held}\| | set cardinality through a fold | SciComp-2, 0/5 · 4 gvf, one-run green |

The orbit count is strongest because both the relation and each side's membership must be computed *through the semantic core* before the count exists — not a conservation sum, not a read-off set difference. Soundness kit for any window/period design: (i) the Fine–Wilf extent floor w_r ≥ 2P−1 (measured 95.8% broken without the condition, 0% with); (ii) certify per instance no single frame serves two classes; (iii) certify achievability by executing the reference plan through the verifier's own simulator.

**The hardness law** (derived across all 7 printed-optimum tasks; measured-gate with stated honest limits): ship only if, with EVERY stated rule held correctly, a competent solver still cannot cheaply construct the optimum. Two measurable requirements: **≥ 2 load-bearing beliefs** that are misreadable, narrowing, public-blind, unrepairable by restart, and N-silent; plus **≥ 1 spec-stated resource constraint** that makes the bulk/uniform architecture illegal. Key measurement: one cleared reconciliation-planner slot went 2/5 solved → 0/5 when a stated serial staging slot was added, outlawing "stage everything, then restore." Honest limits, stated in the source: the three "killed" comparison designs were never run against the trial model; identical reconciler content measured 0/5, 2/5, 0/5 on different days — at n=5 against a 60% bar, a genuinely 70%-fail design still fails ~16% of the time, so the fitted 4/3 split is partly noise and known wrong on at least one case.

Supporting structural rules, each with measured backing:

- **Scarcity must be fragmented and consumed.** One universal resource that only has to be given up last makes the task vacuous — Sec-1's first two generators were solved 25/25 by every naive policy (measured-gate).
- **A cap without contention is not a constraint.** If old items are only retired and new only created, the populations move monotonically apart and no contention occurs (design-kill, from a real slot).
- **Feasibility over your OWN scheduler predicts nothing about agents — and a scarce resource sized off the reference's high-water mark is free by construction** (measured-gate, SciComp-2): the pool was sized at P = max single-wave cost; 87.9% of random wave orders were feasible (2110/2400) and unsorted order solved 11/12, so the author concluded the stated resource carried no load and called NO_GO — at the gate, 3 of 5 trials OVERRAN the elastic pool, because agents write greedy and perturbation schedulers, not your wave scheduler. Do not delete a resource on own-scheduler evidence, and do not count a reference-calibrated resource as difficulty: certification wins the tension — any design calibrating its scarce resource off the reference inherits a free resource.
- **The two-condition law.** Deferring an object past a destructive step needs BOTH its destination reachable AND its content producible by what survives. Designing only the first made every instance infeasible (20k random orders failed) and was also a bug in the oracle's own move ordering — fixing it there gave a 400× speedup (design-kill, Sec-1).
- **The floor must be non-zero and non-decomposable.** A wrong belief that cannot change N cannot break anything silently; and if the floor decomposes into independent per-key subproblems each is separately trivial. ML-2's keep rate under this check was 0–4 per 40 candidate instances (36/40 rejected); it then cleared 0/5 (measured-gate).
- **The generator trap: items processed early must still be constrained** (design-kill, Math-2): if constraint accumulates along the processing order, the first items see nothing, are compatible with everything, and — with transitive closure — the partition floor collapses to N = 1, making every N-silent belief inert. Decouple "constrained" from "position in the order"; one SPEC sentence suffices (early items arrive already formed from an upstream operation — realistic, and it restores the floor).
- **Legality, not naming.** Difficulty must live in what a wrong belief makes ILLEGAL, never what it misnames. Cleanest A/B in the corpus (Media-1, measured-gate): v1–v6, wrong belief produced a misnamed file, plan still legal — 2/2 solved *six times*, including the platform auditor's own suggested fix; v7, wrong belief produced an ILLEGAL plan (breaks append order / blows a stated capacity) — 0/2, then 0/5, avg@5 0.000. Stacking more silent belief traps (9 → 11 archetypes) moved nothing. The recipe: find the object the beliefs compute; add a physical rule making that object the only legal ORDER of operations; add a stated scarce resource sized to the correct schedule's high-water mark (the bulk architecture measured 1.3–2.8× over the cap on small instances, 1.6× on large — outlawed architecturally); restrict destinations to true canonical names plus the mover's own staging name, or agents launder through invented temp names; and replay each wrong-belief plan under its own believed layout, asserting it passes end-to-end while the true verifier rejects it.
- **Exact integers only — no float in the graded path.** Tolerance is simultaneously a rejection risk and slack an agent can be wrong inside. Confirmed twice in Scientific Computing (SciComp-1: value·2^s so every shift divides exactly, 0/5; SciComp-2: integer tick lattices, 0/5, one-run green, `verification_explanation` passing on "there is no tolerance to calibrate"). In any float-native subcategory, find the **exact subgroup** rather than a tolerance: quarter turns on an integer grid make placements signed permutation matrices (Math-2 — first Computational Geometry slot ever to clear); index lattices put semantics in *which-sample-of-the-source* so no sample value is ever computed. Assert zero floats mechanically by *tokenising* the shipped verifier and reference — a regex false-positives on `/` inside path strings.
- **Difficulty must live in the modeling surface, not algorithm choice.** The trial model executes any nameable textbook algorithm; its only observed analytical failure across 9 trials/2 designs in the games line was omitting a dimension from state identity (measured-gate, Games-1).
- **Successor shape, untested (prospective):** make testing a SINGLE candidate itself expensive — feasibility of one move requires solving a nested subproblem — so cost == N cannot be evaluated cheaply. Explicitly marked "nothing in the corpus has tried it," and one attempt at it died to the Bezout law (Part 5). A hardening-panel measurement also showed the CSP version is unreachable: a CSP small enough to certify achievability on is small enough for the agent to exhaust (an attacker implemented the "expensive feasibility" solver at the proposal's own dimensions in 0.03 s against a 25 s cap — design-kill).
- **The repair-task mold — "green is the trap" (prospective: zero proposals, builds, or gate measurements in the Debugging & Repair category):** one visible bait bug OFF the crux code path plus two dormant defects on DISJOINT paths, each violating a stated rule that never fires in the visible suite; grade the repaired engine in a de-privileged child process against a locked oracle shipped only under tests/. Standing risks unique to grading agent-repaired code: failures can land as task/verifier-issue or infra when the agent's repaired code is what runs — a strict downgrade against the ≥ 3-countable-fails bar — and triage signatures bind (stated narrowly = transcription, broadly = ambiguous). Adjacent measured points: Media-1 cleared by exactly one trial while two post-bait grinders scored in-progress; Sec-2's pass@2 agent tripped on signature over-specificity.

---

## 4. The Disclosure Calculus

### 4.1 State premises, never inferences

Fairness forces every graded rule into agent-visible text. What must be withheld is the **consequence of the rules taken together** — the agent has to do the joining. Performing the derivation in prose is worth about −3/5 at the gate.

**The controlled A/B (measured-gate, ETL-1):** same semantic core, same verifier, same instances, ONLY the SPEC prose cut — 4/5 solved → 1/5 solved, accepted. Two earlier versions at 4/5 had both been blocked. What was cut: one entailment sentence, one disambiguation paragraph, and three summary bullets. What survived is what keeps it fair — the raw *premises*.

**The tell that disclosure bypassed your core: `difficulty_crux = NA`** — agents never reached the decision point. A 13-agent panel read the leaky version and recommended RELEASE; it was wrong. Panels do not detect this. Only cutting the prose and re-measuring does.

### 4.2 A printed formula is the derivation already done

**Measured on Math-2 (Computational Geometry):** run 1’s SPEC §4 printed the two composition formulas that jointly answer both load-bearing beliefs — the derivation, already done. Result: pass@5 3/5 solved, avg@5 0.600, everything else green in one run (rubric 31/31, similarity unique) — BLOCKED. The auditor's tell, worth memorizing: *"All five agents independently converged on the same conceptual pipeline as the golden approach."* Five-agent convergence on one pipeline is the signature of a handed-over derivation — read it that way before accepting an "it's in the training data" explanation.

Run 2, §4 de-disclosed, identical core: 0/5 solved. **Prose alone moved 3 solved → 0 solved** — the first measurement of the law on printed formulas rather than explanatory prose.

**The near miss that bounds the law:** SciComp-2's shipped spec printed `resume(s) = max(r(s), resume(parent(s))) + Weff(s)·A'(s)` — exactly the composed-resumption inference the task was meant to require — and cleared 0/5 anyway. **A leak does not always cost the slot; it costs the slot when it happens to be the crux.** The trap is worst where transforms are the subject (geometry, numerical methods, linear algebra, signal processing) because the natural way to specify a transform is to write it down. There, treat every printed equation as guilty until checked against the belief list.

**Detection heuristic:** grep the SPEC for `=`, matrices, and recurrences; of each, ask whether it is a rule to obey or the answer to a belief the agent was supposed to derive. Hunt list for an adversarial re-read: a formula composing two stated rules; a worked example exposing an intermediate the agent should derive; a sentence performing an entailment ("order makes no difference"); printed tables, matrices, or step-lists that save the construction.

### 4.3 Worked examples and other oracles

**A worked example is a convergence oracle** (design-kill / probe-measured, Build-2): the winning agent's trajectory logged 45× "DERIVATION", 88× "diff", 97× "verify" — it converged by *diffing against the shipped example*, never reasoning the calculus out. After the derivation file was removed, a later probe still solved 1/1 because the public instance's visible index contained 3 genuinely derivable keys — the trajectory said it verbatim ("Chain keys match cache_index entries where expected", 198× "matches"). **An oracle is ANY visible value the agent's own computation can reproduce**, not just printed derivations. Repairs (design-kill class): a derivation-free public example asserted in spec_check; demanded ∩ index = ∅ on the public instance, asserted mechanically (sealed instances MUST keep true supplied keys — that is the floor); coupled shadow lineages so every anticipated wrong reading sees an isomorphic hit profile and self-validates green before dying at grading.

**A micro-example that demonstrates a trap's consequence is disclosure** (Build-2 probe #1, 1/2 solved: both trials transcribed the designed gate-carriers correctly because the spec's own micro-examples performed the derivations; the one loss was an *undesigned* slip — luck, not design). **Never hand-write a spec example:** a hand-written replacement silently dropped a token and contradicted a rule two lines above; recompute every printed claim from the reference, and after any de-disclosure edit re-run a blind implementer over the trimmed prose — cutting inference prose is exactly when consistency defects get introduced.

**Public-sample blindness:** the public sample ships with its correct answer, so it is a free discriminator. Every wrong-belief archetype must be byte-identical to the reference ON THE SAMPLE, asserted mechanically at generation (ETL-2: cost two rebuilds — the DP had to pick, among count-optimal targets, the cheapest from the current state; and sample designations had to sit at record tails, not heads). Only an always-different ARCHITECTURE archetype may fairly differ on the sample. Gate confirmation: the sample passed for the 3 of 5 wrong-archetype agents exactly as designed. Prefer **blindness by construction over blindness by luck**: on LowLevel-1 the first *structurally* blind public seed passed all five archetypes 150/150 after 600 empirically-searched seeds had failed. And if a wrong belief fails the public case, the agent gets feedback and repairs it — construct the public case so every belief archetype gives the SAME answer there (on Sec-1 that took three knobs: explicit target lists instead of wildcards, removing the structure that forces the closure, generous caps). Some archetypes structurally cannot pass the public case (a destroy-first dispatcher); disclose that in `verification_explanation` rather than forcing it.

### 4.4 How-to-work coaching is a difficulty leak

Measured in the cleanest possible ladder (Math-2, four runs each moving one variable):

| Run | Change | Result |
|---|---|---|
| 1 | matrices printed | 3/5 solved — blocked |
| 2 | §4 de-disclosed | 0/5, but 3 in-progress-timeouts — blocked (2 countable) |
| 3 | dual profile encoding + instruction opening "Get a planner that runs end to end in place early and refine it from there" | 4/5 solved — blocked |
| 4 | the one coaching sentence reverted, encoding kept | **2/5 solved · 3 good-valid-fail — CLEARED, all 16 checks green** |

The single process-strategy sentence was worth more than the *entire* de-disclosure gain (0/5 → 4/5). State what to emit and when it counts; never state the working strategy. The narrower always-emit rule ("emit your best artifact even when you cannot certify optimality") is about the deliverable and is safe — and load-bearing for classification (Part 7).

### 4.5 The limits of de-disclosure

- **It cannot rescue a design with no structural leg.** Media-2 v3 de-disclosed three inference sentences AND added a tenth silent belief family → pass@2 2/2 solved *again* (agents fought 47m14s instead of 23m5s and still won). Fairness was not the cost — `unambiguous` PASSED on the de-disclosed spec.
- **It can overshoot into uncountable timeouts.** Cutting derivations can make the task LONGER rather than subtler: Math-2 run 2 converted would-be good-valid-fails into 3 in-progress-timeouts; one trial burned the whole hour in 7 LLM calls (last four: 688 s, 530 s, 748 s, 1070 s) and never wrote plan.py. The only lever is cutting implementation *volume* while keeping the cruxes — never the 3600 s cap.
- **The QC fairness bind** (measured-gate, ETL-1): undocumented + load-bearing → QC blocks it as hidden knowledge; documented + trivial to implement → the difficulty gate blocks it (agents obey). What must still be stated or QC blocks: every graded rule, the exact output schema, and normative achievability ("inputs are constructed so that a legal X exists" — its absence gets flagged blocker-adjacent). The bind is real but not binary: the same slot cleared at 1/5 in the *middle band* between hidden rule and narrated derivation. Prefer shapes where semantics live somewhere the spec does not have to reach — a documented-container parsing task makes the format spec the only channel for semantics and produces reading-difficulty and essentially nothing else.

---

## 5. Beliefs: What Can Actually Carry Gate Load

### 5.1 Checked vs constructed (measured-gate + design-kill)

Restating the one law with its full evidence, because everything else here depends on it. Four independent confirmations:

1. **GPU-2 design #1** (scalar-promotion-map, killed pre-build): the core was "is this value uniform on the active set" — every definition collapses. Over all inputs: undecidable for the reference, or (XOR-only language) symbolic execution in O(W·ops) with bitsets → trivial. Over a shipped bundle: decided by simulation in milliseconds. By a stated calculus: transcription. The SAT/BDD escape is blocked because `allow_internet = true` is mandated.
2. **ETL-2 v1**: the factorising-predicate law arrived at the same verdict from the other side — 2/2 solved (Part 5.2).
3. **Media-2**: blocked 2/2 twice; the post-mortem verdict was "needs a constructive leg" — and per the current record it cleared 0/5 · 5 gvf once that leg was added (note: the older per-slot analysis filed the slot as "blocked, too easy, not patchable"; that verdict is stale — a second confirmation that a 2/2 block is a design problem, not a dead category).
4. **Positive control, GPU-2 design #2**: same author, same slot, same sub-category, same week; only checked→constructed changed (the agent must construct a canonical layout through a 3-rule cascade then a legal relocation) — pass@5 1/5 · 4 valid fails · approach_validity 5/5.

Measured-good constructions: inverting a forward semantics (ML-3); synthesising a layout under composed rules (Build-1, Media-1, GPU-2); recovering hidden state by replay (ETL-1). Measured-dead: the whole static-analysis family, and any existential predicate (see the Bezout law below).

> [!warning] Honest limit — the law kills designs, not slots.
> GPU-2 #1 was killed by argument, never gate-measured, and SciComp-2 is the standing warning: that slot's own pre-build NO_GO was WRONG — agents solved the fold the author feared was disclosed and died on a rule discounted as trivial; it went 0/5 accepted, green in one run. Strong evidence for choosing BETWEEN designs; weak evidence for ABANDONING a slot. The failed escape, recorded so it is not retried: reframing a checked predicate as "implementation difficulty" does not work — Build-1 v2 and ML-3 cleared 0/5 with every rule stated because their cores are CONSTRUCTIONS; stating the rules of a construction leaves the implementation hard, stating the rules of a predicate leaves nothing.

**The Bezout law (design-kill, SciComp-2 v2):** you cannot build an expensive candidate test out of "does a collision/witness exist?" over periodic structures — the first witness is provably early. Measured: horizons of 10^7–10^8 samples per recorder; deepest first witness = sample 22, median ~4; witness depth ~ min(A_j/g, g/(c_i+c_j)) for g = gcd(A_i, A_j), so it is structural, not tunable — forcing a deep witness needs A ~ 10^14 where collision probability is ~10^-7 and the floor is zero. If a cost leg needs an expensive per-candidate test, the legality condition must be UNIVERSAL over the horizon or an optimisation with no witness, and the correct route must never evaluate the predicate at all.

### 5.2 The factorising-predicate law (measured-gate — the corpus's sharpest A/B on the *requirement*)

**If the legality predicate factorises over independent fields, the agent measures it one coordinate at a time. It is CHECKABLE, not constructive, and dead no matter how exotic the semantics look.**

The A/B (ETL-2, same fiction, artifact, floor, grading, instance generator — only the requirement changed):

- **v1** — disjoint per-register banks make admission exactly a conjunction of independent per-field equalities. Cheapest route: probe one field at a time, ≤ 18 decodes per passage, 0.31 s vs the reference's 0.16 s — **a 2× ratio no cap, instance scaling, or passage-length change can separate**. A probe implementing exactly per-field probing scored 1.000. Gate: 1/2 then 2/2 solved, `difficulty_crux = NA` on every solved trial.
- **v2 — the union-of-boxes repair** — the disjoint per-field banks were replaced with one shared pool, so the admissible entry state becomes a **union of boxes**. Per-field probing is now WRONG on most passages, in both directions (accepts configurations that grade wrong, rejects valid ones); a single symbolic pass is also wrong — it derives only the archive's own box (it *was* v1's reference). The union stays exactly computable in a bounded number of cheap passes, so exactness is kept — union derivation matched brute-force enumeration on every passage tested. Gate: **0/5 solved · 5 good-valid-fails · avg@5 0.000, rubric 31/31 on all four rolls, `difficulty_crux` PASS on all five trials.** 3 of 5 agents independently converged on the exact archetype `task.toml` names, emitting complete correctly-decoded text 1–8% above the floor. Grader: "This is the failure archetype task.toml explicitly names as the primary crux."

**Pre-build test:** pick the true configuration, change ONE field, and see whether the graded property moves — if iterating that over each field reconstructs the real constraint, the difficulty is gone before the first line is written. **Sharper version:** compute every shared/derived input first, then ask whether the predicate still factorises — if it does, the interaction was in the plumbing, not the requirement. The false defence to watch for: "the rules interact because F1 and F3 both read the scope F2 resolves" — a SHARED INPUT is not an interaction; resolve the shared object once and each condition is separately decidable (killed DataQuery-1 on paper).

> [!danger] The exactness corollary — landed verbatim three times.
> **The property chosen to make a floor provably exact is often the very one that makes it cheaply measurable.** ETL-2 v1's disjoint banks were picked deliberately (and recorded as a win) to make the exactness proof easy — the proof was the leak. Same corollary killed LowLevel-1 #1 ("a forced-greedy proof and a one-line solver are the same fact stated twice") and ETL-3 #1 ("B* is provably exact because each edge is independently checkable"). When your exactness proof is easy, run the factorising test immediately.

**Object identity must be COMPUTED, not read** (measured-gate, five cleared cores): in every cleared semantic core the agent must derive *which things are the same thing* — orbits, canonical keys, multiset labels, membership classes — before any counting is possible (Math-1: synthesis legal only from unsealed co-aisle residents; SciComp-1: only rescale writes a non-canonical scale; ML-3: multiset channel labels; ML-2: canonical-key derivation; MLInfra-2: step-vs-current membership). A wrong identity rule corrupts the floor, the plan, and the agent's own self-check CONSISTENTLY — N-silence built in by construction. Corollary, the second measured repair route for a factorising predicate beside union-of-boxes: move the difficulty onto object identity — a canonical form produced by a fixpoint whose last stage feeds back into its second (the repair that fixed DataQuery-1 on paper).

### 5.3 N-silence: the belief oracle and what survives it

The printed optimum is a **free belief oracle on sealed data**: a wrong belief whose plan crashes, wedges, exhausts a resource, or over/undershoots N is an ALARM the agent notices and repairs in one retry. Only beliefs whose wrong plans self-report cost == N, end-state legal, own validator green, survive. **The conjunction with restart-proofness IS the gate:** narrowing enough that search cannot cross, silent enough that the agent never knows to search again.

**Restart repairs every over-permissive slip; it cannot cross an action-space boundary** (measured-gate, controlled experiment inside a cleared depot-relocation slot): seal-blind (over-permissive) is restarted around → 12/12 pass; freeze-blind (narrowing) → kills 9/12, unrepairable. Same task, same search, same instances. Also measured: 36,034 restarts under a wrong protected-path belief never solve the reconciliation-planner slot's hardest sealed instance, while 2 restarts under the correct belief do.

**Loud is one retry; only crossability decides** (measured-gate, Media-2 v1, 2/2 solved): both agents wrote the SAME intended bug — consuming the donor before the fit check — and both *self-caught* it (steps 5 and 7) with validation scripts they wrote themselves. That family had measured loud (silent 0/10) and was shipped as the load-bearer anyway. The reframe: Media-1 v7's kill was also loud ("Cannot free staging capacity") and cleared 0/5 — the difference is the repair lay OUTSIDE the agents' action space. Loudness itself is not fatal; CROSSABLE is. Check the silent/loud split of the battery BEFORE pushing. And two loud-only archetypes at 12/12 still came back 0/5 on ML-3 — loud kills still score as valid fails at the gate.

**Loosen the budget — a stated resource limit must never be the alarm** (design-kill, confirmed twice): tight budgets made SE-1's descendant-blind archetype SELF-DETECT ("over budget") and score as a klaxon instead of a silent kill; the shipped rule was budget = max(N+1, bulk−1) — the exact-count check does the killing, the allowance only outlaws the bulk architecture. Media-2's standing form: stock is set ABOVE the worst believed-wrong layout on purpose; "stock is fiction + a legality bound, never the kill." Related trap on the other side (design-kill, ETL-2): **derive the cap, never tune it** — measure the worst-case primitive exhaustively, then derive a cap that provably satisfies three properties: every minimum-cost solution fits; the degenerate architecture cannot fit; and the over-demanding archetype ALSO fits, so the cap never warns a wrong-belief agent its reading is wrong. A first pass with a *guessed* worst-case value silently failed the second property on 6 of 8 editions.

**Stop spending budget on scheduling order** (measured-gate): ordering is always cheap, always restart-repairable, always audited by N. Spend the difficulty budget on (i) WHAT THE OBJECTS ARE — layouts composed from stated formulas, index maps, padding on padding — and (ii) the stated scarce resource. The model case: a byte map that corrupts planner and checker *identically*, so cost == N never audits it (MLInfra-1).

**The derived-vs-stated axis is dead** (measured-gate): stating a rule costs nothing; what matters is the belief's properties (misreadable, narrowing, public-blind, unrepairable, N-silent), not whether a sentence asserts the fact. A 12-agent panel proposed the axis; all three adversarial lenses refuted it, and the counter-measurement stands: 4/5 agents held the WRONG belief about a plainly normative sentence in a cleared task, and the run still cleared 0/5.

**Conscious forks cap at a coin flip** (prospective, never gate-measured): any reading an agent consciously recognizes as a choice is capped at roughly 50%/trial by mirroring. Kill-load must sit on unconscious procedural slips.

> [!warning] N-silence is necessary, not sufficient.
> SysInfra-1's floor had "N-silence rated better than any shipped task" and the design was still killed NO_GO — the joint space stayed enumerable (design-kill; note no Systems-Infrastructure slot has ever reached the gate, so that category's evidence is design-kill only). Best-in-corpus silence coexisted with an unbuildable design.

### 5.4 Inert beliefs: prove killability before building

**A wrong-belief archetype can be symmetry-equivalent to the truth and kill 0/12 while looking like a real family. No generator tuning fixes a mathematically inert belief.** (design-kill, measured on Media-2): two selection-belief families each scored 0/12 — the set being selected from structurally never held more than one candidate, so the wrong reading and the truth always picked the same row, even after re-parameterizing the instances.

**Structural test:** for any selection belief, ask *what is the maximum size of the set being selected from?* If provably ≤ 1, the belief is inert regardless of instances. The generic two-part fix: (a) make selection order-sensitive, so consumption changes which candidate the NEXT selection gets; (b) add an eligibility gate some candidates fail, so ineligible candidates accumulate and the pool can hold ≥ 2. Both families went 0/12 → 12/12, and the gate itself became a third live family (12/12). Bonus: choose the selection rule that is the LESS natural reading, so the cheapest transcription is wrong by default. **Run the 12-instance × N-family kill/silence grid BEFORE selecting instances** — it costs seconds; run after selection, an inert family looks exactly like a badly-chosen instance set.

More inertness anatomy, all design-kill:

- **Preconditions your generator never produces:** three of eleven Math-2 archetypes scored 0/8 at first — one needed a chain four links deep, one needed dir = −1 when all instances had +1, one was filtered for free by geometry (z ≤ 0).
- **A carried-quantity fold is only an interaction if the carry survives a stage:** SciComp-2's carried-debt rule fired only above a threshold the natural instance distribution never reached — the first stage absorbed it every time; three archetypes at 0/12, the debt live on 1/12 instances. Measure P(carry > 0) before believing a propagation rule.
- **A quantiser downstream of an arithmetic trap erases it:** the record-lattice snap rounded true and wrong answers to the same boundary; the archetype read 2/12 when it was MASKED — 11/12 after rescaling. Check the graded quantity's resolution against every trap's error magnitude.
- **Off-by-one boundary beliefs are effectively unkillable by chance** unless every quantity sits on a common grid — exact boundary hits have probability ~0 otherwise. Dropping the belief was cheaper than aligning the arithmetic.
- **An inert stratum is dead weight:** "natural implementation is correct" rules carry nothing (Python `sorted()` matching the intended byte order by accident, set/dict dedup correct by accident). Certify per stratum that the *cheapest transcription is wrong* before counting it (Build-2 red-team). Corollary from the tie-check side: if the valid-variant battery shows a structural choice is freely interchangeable, that is evidence of shallowness as well as fairness — that choice is not a real decision.
- **In principle unkillable:** ML-3's forward_phase — a wrong tile is reflect ∘ shift of the right one, producing the same result. Prove each target belief is killable before building the task around it.
- **Over-permissive readings subsumed by stricter checks are inert:** SE-1's depth_blind and shallow_fp both 0/16 — a stricter check subsumes them.

### 5.5 The battery outranks your judgment — in exactly one direction

**Never discount a measured silent high-kill archetype because the rule "reads trivially."** The most expensive lesson in the corpus (measured-gate, SciComp-2): one archetype measured 12/12 kills at 100% silence; the author discounted it in the proposal as "a stated rule trivial to implement once read, worth its measured wrong-belief rate ≈ 0" and called NO_GO. At the gate, **4 of 5 kills were exactly that archetype** — a one-variable output substitution with the correct value already in scope, false-positively confirmed by the agents' own validators. Meanwhile the rule the task was *built* around was solved correctly by every agent.

The counter-face, held simultaneously: **a high kill rate proves kill-given-belief, never belief rate.** "Ten of fourteen archetypes killed ≥ 7/12 at ~90% silence and it proved nothing" (same file); "a 100% archetype kill rate is not evidence of difficulty — only the live gate decides" (Math-2). And the sharpest measurement of the gap (measured-gate, LowLevel-1): a fully green local pipeline — pooled kill-given-belief minimum 98.46% (n ≥ 235), variants 26/26, rubric 31/31 first roll — went **pass@5 5/5 SOLVED, avg@5 1.000**. Measured belief rate: 2/7 trials engaged the wrong walk, 1/7 shipped it, 1/7 self-identified and fixed it at step 30–31. "A single stated rule, however misreadable in principle, gets implemented correctly by careful strong agents ~85% of the time." Depth of composition — many interacting cases — is what converts a low belief rate into a kill.

The two directions do not cancel. Kill rate is a necessary screen (an inert archetype is dead weight), not a sufficiency proof; and the one property worth trusting over your own judgment is measured SILENCE at high kill rate. A mutation battery proves a belief is PUNISHED, not that agents HOLD it (third confirmation, ETL-1: the tick-naive mutant failed as a scored wrong answer, the generator forced it wrong in every session — the gate measured 4/5 solved with the designed crux killing zero agents; the one failure was an unrelated hallucinated 110-entry ADPCM step table where the standard has 89).

**Promote measured slips.** The kill that lands is often not the designed crux: LowLevel-1's one real kill was a rule never designed as a crux and never batteried, while its designed crux was engaged and SOLVED by every pass@5 agent ("the instruction states the walk so explicitly that re-reading repairs it"); Build-2's probe loss was an undesigned unset-ARG slip, promoted afterwards to a designed, mirrored, seeded family on all 12 incidents. When a real slip appears in a probe or pre-check, turn it into a designed family instead of leaving it to luck.

> [!note] Contradiction: is implementation-difficulty a live bet?
> One reading (from LowLevel-1/Build-1): reading-difficulty is dead, implementation-difficulty is alive — Build-1 v2 swapped only the semantic core to ABI struct layout (alignment capping, padded array stride, nested-alignment propagation, tail padding, unions, bitfield straddling — all simultaneously; one slip changes equivalence classes on 84% of random worlds and 0% on the public profile) and went 2/2 solved → **0/5 · 5 gvf**, the cleanest core-swap A/B in the corpus; the attributed mechanism is EIGHT interacting cases. The other reading (from Build-2 probes, design-kill class): "implement a fully-stated calculus exactly" is not a difficulty shape no matter how baroque — the byte-layout archive core measured 4/4 solved on the probe rig against a design estimate of 0.12/trial (wrong by ~8×), and more interacting rules did not help; a field table is mechanical and self-verifiable. A third data point cuts across both: RegOps-1's five clean date rules died 2/2 and then cleared 0/5 after a *data-only* rebuild, rules unchanged — attributing its 2/2 to instances, not rule shape. The corpus keeps all three. Operational reading: implementation-difficulty is 2–2 as a bet; the claimed discriminator is *interacting cases per rule, not rule count* (prospective — count interacting cases on real inputs as the first job after the generator exists, and spend an early pass@2 rather than a long hardening pass).

**You can force a WALK, you cannot force a MARGIN** (design-kill, LowLevel-1): move-attached divergence can be forced onto every legal path by generator construction; resource-level divergence cannot — a wrong belief about spending headroom is either avoidable or loud. Measured: the margin family died at BOTH tightness settings (slack: 17% median kill; knife-edge: 39%, ≥ 90% on only 2.6% of candidates) while the walk family reached candidates confirmed at ≥ 98% joint kill. In an open plan space, divergence sites are avoidable — kill must be forced by construction, and a belief that blocks the agent's own search (26/40 self-blocked) is worthless.

### 5.6 The archetype-faithfulness law — a wrong belief must reach every site that reads it

**A wrong-belief archetype is a WHOLE planner, not a patched predicate. The belief has to be threaded through every site that consumes it — the engine, the derived deadlines, the candidate ORDER, and the self-replay. Patch the engine alone and you measure a planner that half-holds the belief, which is neither the wrong reading nor the right one — it exists nowhere, and its kill rate describes no agent.**

Measured-gate, Games-2, which cleared 0/5 · 5 good-valid-fails · avg@5 0.000 with all 14 stages green on one push. The law came out of finding the same defect **twice in one build**, both times in the same direction — both inflated the archetype's *survival*, i.e. made the task look easier than it was. That is the safe direction, but only because they were caught:

1. **Tie-break order is part of the belief's semantics.** The candidate list appended the sheltered delivery before the exposed one, and the sort is **stable** — so when the patched instant collapsed to 0 the two estimates *tied* and the stable sort handed the archetype the safe choice. The belief could not express itself at all. Fix: emit the exposed candidate first (truth is unaffected — its estimate is strictly earlier whenever a sweep threatens). That one change took the archetype from passing to failing with two goals swept.
2. **A derived quantity inherited from truth silently repairs the belief.** A second archetype inherited *truth's* pickup deadline while believing effects land at the start of a tick — so it was **more cautious than its own belief required**, and lost an entire designed kill.

Second confirmation (measured-gate, DataQuery-1): three archetypes rewritten as full planners and run over 480 reports bit 760 times and produced **zero wrong numbers** — the belief was inert under summation (§5.4), which is a finding you simply cannot obtain from a patched predicate, because a patched predicate never gets far enough to roll up.

**The operational test, before you trust any battery number:** list every site in your archetype that reads the belief — the simulator, each derived bound, the ordering or tie-break, and the replay that checks its own work. If the belief is absent from any of them, the archetype is not the wrong reading and its rate is not evidence. This is what §5.5's "the battery outranks your judgment" depends on: an unfaithful battery outranks nothing.

---

## 6. Instance Selection

### 6.1 Select on measured rates, not pass/fail bars

**Select sealed instances on P(arbitrary order fails), measured per archetype over ~400 draws, and ship the lowest** — never on "no archetype solves in N shuffled orders." A real agent writes ONE policy with ONE deterministic tie-break. Measured (Sec-1): the exists-a-lucky-order bar at N=320 rejected 45/45 candidates while the true per-archetype rates were 0–3.5%; the slot shipped at ≤ 1.50% and cleared.

### 6.2 Disjoint seeds, twice, with margin

**A single-stage bar overfits to its own seeds.** Measured three times:

- Sec-1: 9 of 12 instances died on held-out seeds (75%).
- RegOps-1: 3 stage-1 leaders at 0% on stream A came back 18%, 10%, 5% on disjoint stream B.
- LowLevel-1: rates over < 15 believed plans gave phantom survivors (90% → 0% stream swings; enforcing n ≥ 15 collapsed 15 survivors to 1 — "never report a rate without its sample size"); sets selected at ~98% wobbled below 98% on later streams; a zero-tolerance per-stream bar at n≈50 is statistically brittle (one leaked plan reads as 97.9%); the shipped claim was rounded DOWN to the pooled minimum, and a third-stream re-confirmation dropped 2 of 8 seeds sitting exactly at the bar.

Recipe: cheap filter → disjoint-seed bar with margin above the requirement → third-stream confirmation of anything sitting on the bar. Pool kill rates across streams; bar the pooled rate.

### 6.3 The battery is the fitness function — and it has a mandatory member

Build the wrong-belief archetypes as the **instance-selection fitness function**, not as an after-the-fact test. Hand-designed trap instances failed twice on Math-1 to alternate solution paths; randomized instance search scored by the battery is what worked (measured-gate). Battery sizes that shipped: 10, 6, 11 scripted planners.

> [!danger] The mandatory member: CORRECT_RULES + NAIVE SEARCH.
> A battery of only wrong beliefs and fixed-order policies can hit a 100% kill rate and prove nothing, because a search recovers from exactly those mistakes. Measured independently on THREE slots the same day (design-kill; DataSci-1, ML-1, ML-2): each slot's full archetype battery died across thousands of runs while a correct-rules naive search solved essentially all sealed instances locally in under a second — so the naive-search bar alone is also insufficient when the whole search space is one cheap-to-test dimension. A "tight" feasible fraction (0.25%–10%) is NOT tight when the feasibility test costs 0.1 ms.
> Counterweight (Part 9): all three of those slots later measured 0/5 at the gate — the probe kill was a warning about the *design ceiling*, not a gate prediction.

**A weak wrong-solver battery poisons instance selection** (measured, SciComp-1 — the other half of the battery-outranks-judgment law): strawman archetypes let bad instances pass the fitness function. The first battery's recursive-descent and LRU strawmen passed 34% of random kernels; replacing them with strong archetypes collapsed that rate — measured before the slot cleared 0/5. Measure the battery's own strength before trusting any selection built on it.

Bar the naive-search member in **wall clock at the disclosed per-item cap, measured un-contended** (Part 7), with a planner stronger than the control. Held-out confirmation drives real numbers: MLInfra-2's selection (6 shuffle seeds, final gate on held-out seeds 100–109 + 25 s probes) moved random-restart solve density from ~1/20 to < 1/5000 per draw; SciComp-1 raised its bars twice, each time because a survivor appeared under a held-out seed.

**Battery engineering** (measured-gate, ML-3): build archetypes as ONE sem-parameterised planner with exactly one belief function swapped each, used consistently everywhere (demand reading, realisation, archive test, self-check) — the *consistency* is what makes slips silent. Re-run the battery after ANY planner-core change (a rotation dedupe sound for shift-invariant canons silently broke the one phase-sensitive archetype and corrupted a 150-seed sweep). Verify each archetype's wrong decision actually EXISTS in the shipped instances — on random instances every class had one admissible resource, so first-fit ≡ optimal everywhere; the kill needed engineered cross-realisability plus planted bait plus a budget tightened to the forced load. Record alarms per run and classify silent-vs-loud empirically.

**Achievability must be constructed, not sampled:** random instances are essentially never achievable at the floor (measured, ML-1). The reusable pattern is witness-first generation with planted traps and per-instance certification by executing the reference through the verifier's own simulator (ML-3).

**≥ 3 independent failure classes** (measured-gate): winners produce failures with no single root cause dominating — MLInfra-1 split its five fails across coordinate-mapping stubs, missing read-after-write gating, a flat-index bug, and resource bookkeeping. The gate-quality bar used on cleared slots: ≥ 3 failure classes with pairwise Jaccard < 0.5 on their failing-instance sets (measured examples: 0.10/0.22/0.33; 7 pairs below 0.5, most disjoint 0.17). One file legitimately declined Jaccard where rejection was universal and substituted mechanically-certified sample blindness — both standards are in the corpus; use Jaccard when kill sets are partial, universal-rejection + blindness when they are not.

**Corpus balancing** (design-kill, from an audit-style task): after generating any corpus, count every graded field — a field that is 90% one value grades nothing. When graded fields fight, balance the field requiring the expensive reasoning first (balancing codes first collapsed materiality to 6 true/39 false; materiality first gave 22/23 with codes still spread 22/8/8/7).

### 6.4 Rebuilding against a measured archetype, and adversarial selection

**A 2/2 block on correct, hard-to-implement rules can be an instance problem** (measured-gate, RegOps-1): reproduce the cheap archetype that actually solved your task, measure its per-instance success rate, and regenerate sealed instances that drive it toward zero — validating every candidate with the real reference AND the real verifier. Numbers: the greedy+repair archetype measured mean 77% on the shipped set (per-register 100/100/15/100/100/100/75/0/65/70/100/100 — the 0% register is the template to imitate; a register with 18 groups at 70% shows group COUNT is not the lever). Rebuild over 70 candidates → mean 6.3% (stream-B rates 0,0,0,0,2,2,5,8,10,12,18,18). Gate: 0/5 · 4 gvf, accepted, with the pass@2 suggestion having named the designed lever exactly. The lever's parameter had to be SEARCHED: a flat 6-day origin shift left 46 of 64 joint windows empty.

> [!note] Contradiction, internal to that record: the post-rebuild greedy mean is reported as both 6.3% and 7.6% (fixed-seed, 120 runs/register, max 26%) in the same file, never reconciled. Treat as ~6–8%.

**When an auditor's corrected reading must become decisive** (measured-gate, SE-1): the corrected reading's natural decisive rate was 0.6%; constructive selection found 6/16 decisive instances where random sampling found 2/195. Re-select sealed instances so the corrected reading is decisive on **a third or more**.

**Structure-blind attackers and red-team duty** (design-kill): a structure-blind attacker is a better acceptance bar than a gate-shaped memoised search — it assumes nothing about your intended structure and finds the shortcut your battery is blind to; make it a standing member. Pre-build, run two parallel adversarial agents (a floor-attacker with *brute-force verification duty* — actual code, SOUND/BROKEN verdicts with counterexamples, not opinions — and a solver-simulant with web search). On ML-3 this found two fatal soundness bugs in an already-accepted proposal (a floor that was not a floor, and a headline pitfall that was provably inert). But **verify every claimed-live archetype empirically** — the attacker's own suggested archetype was itself inert (0/33k), and the same panel ruled NO-GO on the design that then cleared the gate. Red-teaming kills bad designs; it does not bless good ones. Harvest spec ambiguities from two implementations built blind to each other (33 findings, one flat bug, ~12 coincidental agreements on one slot) — the *disagreements* are where the spec is ambiguous.

---

## 7. Time: Caps, Clocks, and Classification

### 7.1 The timeout law

**n_items × per-item cap < verifier timeout_sec, always — validated by probe, not arithmetic.** Otherwise a slow-wrong agent hangs the suite, no ctrf.json is written, and a genuine analytical failure is logged as missing infrastructure. This turned a 0/5-solved run into a BLOCK (measured-gate).

| Slot | Arithmetic | Outcome |
|---|---|---|
| Math-1 | cap 120 s → blocked (4 infra); fixed to 25 s | cleared |
| SciComp-1 | 25 s × 13 = 325 s vs 900 s budget | cleared |
| SciComp-2 | 30 s × 13 = 390 s vs 900 s budget | cleared |
| Math-2 | 40 s × 12 = 480 s vs 900 s budget, worst reference part 0.46 s | cleared |
| a fifth slot (anonymized) | 9 × 60 s = 540 s vs a **300 s** budget — latent | survived only because all five agents crashed fast |

The probe that validates it: replace the solve script wholesale with one that writes a valid public artifact then installs a sleeper; assert all sealed tests fail SCORED, ctrf written, inside the verifier budget (SciComp-2 measured 13/13 scored in 6m11s of 900 s, reward 0). Companion rules: TimeoutExpired → clean `pytest.fail`; keep a merely-valid answer trivial to produce so agents always submit *something*; disclose the per-item limit in instruction.md and verification_explanation; keep the oracle ≲ 0.25 s/instance so the disclosed cap is ~100×+ the oracle cost. **Exclude reference-hanging instances**: one slot's reference DFS was bimodal — 60 of 70 candidates solved in median 0.13 s / max 0.23 s, 4 thrashed past 20 s, *nothing in between* — and one shipped hanger would have scored every trial task/verifier-issue.

### 7.2 The wall-clock law

**Bar the naive-search archetype in WALL CLOCK at the disclosed cap, never in nodes or draws** (measured-gate, cost a full re-selection): a sealed set that passed "naive DFS fails at 600k nodes" was cracked by the same search in 7.8 seconds — 25 s of Python DFS is ~3M nodes, so the node bar was ~5× too weak. Calibration is box-specific: calibrate nodes/sec un-contended on your own machine (ours measured ~121k) and derive the node bar from that (use ~6M nodes as a deterministic load-independent bar if you must have one). Corollaries, both measured: **a wall-clock bar under CPU contention is optimistic** — two parallelised selection runs each got half a core, and a seal-time un-contended re-confirmation (one program, the cap, 1 CPU — the verifier's condition) rejected 2 instances that had passed; and **a budget-doubling probe overruns the cap** and reports WINs the real cap would never allow — put a hard deadline check *inside* the search.

### 7.3 The staged cap is a weapon

A small per-item cap plus an emit-best-so-far instruction **converts the entire "agent writes simulation-cost code" failure class into good-valid-fails the gate counts.** Measured (ML-3): 4 of 5 live agents wrote the naive materialising-cost route instead of the closed-form predicate, and the cost bug stayed invisible until the sealed inputs blew the disclosed cap — 4 of 5 kills scored as cap overruns of the naive-cost route, 0 in-progress, 0 infra. Requirements: (i) the semantics admit a closed-form route the agent must derive; (ii) sealed inputs large enough that the naive route exceeds the disclosed cap; (iii) the public case small/empty along exactly that axis so the shortcut passes it. Design the cap so the closed-form implementation finishes ~40× under it. Agents that write exponential solvers are the norm — bound them so they fail SCORED, never as hangs.

### 7.4 Wall-clock separation needs a real ratio

Measured ratio ledger:

| Wrong-route / reference ratio | Verdict |
|---|---|
| 2× (ETL-2 v1 probing) | dead — no cap separates it |
| 3.7× (Math-2 raster at ×20 scale) | dead — a prior slot needed 20× |
| 8× (ETL-2, pool of 4) | still not cappable |
| ~39× (ETL-2, pool widened twice) under a 10 s cap | **works** — one gate agent's brute-force enumerator died at 18.3 s vs 10 s as a good-valid-fail |

**Buy the ratio by widening the state space, not scaling instances.** Instance scaling runs into memory: pushing the Math-2 raster past its cap needed roughly ×50 scale, where a single bend's raster is ~6.5 GB against a 2048 MB container — the agent OOMs, "a memory limit dressed as difficulty and reads as gaming" (design-kill; the ETL-2 leg is the only gate-measured one). Media-2 measured its timeout weapon (~4× instance weight for ~2.2 s vs a 20 s cap) and dropped it rather than inflating the repo. And remember Part 5.2: a cost leg on a factorising predicate is not a cost leg at all — per-field probing collapses it.

### 7.5 The hardening trap and the grind

**Hardening toward search converts good-valid-fails into 3600 s in-progress timeouts, which count for NEITHER side — a genuinely hard task can become ungatable** (measured-gate, part of the ceiling-law evidence; one trial finished 8 seconds inside the kill, another was cut off ~20 s from fixing its own bug — more time would have converted it into a SOLVE, which is why you never raise the cap). De-disclosure can trip the same wire (Math-2 run 2, Part 4.5). Corollary: read `low_timeout` per trial — on that run the two countable fails were exactly the two trials with low_timeout PASS.

**The anti-grind pass** (measured-gate margin): Media-1 cleared by exactly one trial while two agents ground past the intended stopping point — a post-bait grinder scores in-progress and counts for neither side. Remedies (prospective for the repair-task mold, which has zero gate measurements in its category): broad visible-surface coverage so post-bait green reads as done; scope the instruction to the visible failure only; wrong repairs must complete fast and wrong, never stall.

---

## 8. Verifier and QC

### 8.1 The reference must never exit nonzero

`ava_review` blocks on a ragged acceptance boundary between "crashed" and "answered wrongly" **even if the failing path never fires on the shipped set** (measured-gate, cost a full CI cycle on GPU-1, criterion `verifier_coverage`: a bounded search that raises on budget/deadline exhaustion). Every failure path must fall back to a trivially-valid-but-non-minimal answer and exit 0, with the wall-clock deadline *inside* the recursion and pre-emit asserts replaced by an explicit self-check. Second measured instance (ETL-1): an `epoch_of()` returning None → TypeError on a damaged-input path drew an ava_review FAILURE with no comment and no check output; the battery mutant that had crashed with exactly that TypeError was the AVA failure *pre-announced* — and fixing the crash path flipped that mutant from an uncountable alarm into 1 silent kill. Standing practice: a fail-paths tool that forces the reference down each damaged-input path and asserts exit 0 + a well-formed artifact. "This is what AVA checks; reasoning about it is not enough."

### 8.2 The oracle must be right on every IN-CONTRACT input

QC builds its OWN adversarial inputs (measured-gate, SE-1): after pass2 passed, qc_gate blocked on an input with two lines pointing at the SAME commit — the reference appended one follow-up per line where one commit serves both. Both of that slot's oracle bugs shared a root cause: **every battery only tested shapes the author's own generator emits.** Fixes: hand-built edge instances as a permanent ladder stage (7 shipped), plus a fuzz that respects the contract — the first contract-ignorant fuzz reported 26 divergences that were ALL out-of-contract phantom bugs.

**Differentially fuzz over degenerate shapes the generator never emits** — agreement on shipped instances is a spot-check, not a check. Measured finds: ML-1's forward- and backward-reachability implementations agreed on all 13 shipped instances and diverged on a degenerate shape (a graded site that is itself an `off` node) where the grader would have falsely rejected a valid plan. Volumes that shipped: 8000 degenerate worlds / 0 disagreements (Build-1); 917 verdict trios + 346 after renames (MLInfra-2, three-way including a clean-room checker built from the design prose alone by a subagent); 210,000 random intervals across 7 word widths (SciComp-1); 4000 degenerate chains / 0 divergences (SciComp-2). **Implement the floor a THIRD time from the spec prose alone** and require agreement — direct evidence for the `unambiguous` criterion (13/13 on Sec-1; 12/12 on SciComp-2, first-roll pass).

**Semantic agreement is not grading soundness:** a differential between two implementations of the semantics cannot find *under-enforcement* in the grader. Run a corruption battery enumerated from the rules document — one violation per stated rule (7/7 rejected) — plus a valid-variant half so the fix does not overshoot into over-constraint (40/40 legal variants accepted). Two rules for the variant half: **cover solution CLASSES, not orderings** (SE-1's battery permuted sites and order but never tried cascading — the one class that mattered; a cascading spec-valid solution scored zero and burned a whole pass@2), and **swapping two adjacent independent ops is NOT a corruption** — independent ops commute.

### 8.3 The verifier-strictness law

**When an auditor says your verifier applies a criterion the spec does not state, that gap is a defect AND a difficulty signal: a rule your own reference got wrong is, by direct evidence, a rule that is easy to get wrong — the definition of a load-bearing belief.** Measured end-to-end (SE-1): the verifier enforced a stricter reading of a stated invariant than the spec's wording; a trial's spec-valid, cheaper answer was scored zero and the auditor graded approach_validity FAIL against the task. Two repairs were on offer: (a) state the stricter rule in the spec — the cheap patch, which would have made the task transcription; (b) implement the corrected reading in reference and floor — taken. On the next measurement **all four pass@5 failures were exactly that inference** (4 good-valid-fails, 1/5 solved, accepted): the author's own bug had become the task's kill mechanism.

Companion grading rule: **grade a counted optimum as `emitted <= floor`, never `== floor`.** The floor is certifiably ACHIEVABLE (the reference attains it), not certifiably MINIMAL; `<=` makes a residual over-estimate harmless while every over-counting archetype still dies.

That slot is also the proof that an **inference-only, search-free task can clear the fail-rate bar**: no search space, no timeout weapon, 4 good-valid-fails with ZERO timeouts, every trial finishing in 10–13 minutes under a 60-minute cap — provided there is a genuine withheld inference that all natural misreadings miss.

### 8.4 Anti-cheat mechanics (all reproduced end-to-end before shipping)

- **Snapshot at import.** If the grader re-reads a graded input from disk inside the test body, a submitted program running once per case can overwrite the sealed inputs during an early case and satisfy every remaining case from one precomputed plan. Reproduced (design-kill, Build-1): a planner with ZERO planning logic scored 17/17. Fix is ~3 lines — snapshot every graded input at import time, strictly before any submitted program runs (regression: attacker drops to 12 failed / 5 passed; reference stays 17 passed).
- **Cap the plan file size before `json.load`** (an unbounded op stream OOM-kills pytest, no ctrf is written, and a scored failure is misfiled as infra); type-check op arguments (bare TypeErrors read as grader bugs); make sure the in-suite self-check exercises the branch it claims to guard.
- **Sandbox the verifier against self-oracle reads** (prospective — verified functional, no measured exploit): when the verifier re-runs the agent's program in-process, stage inputs under /app, chmod the tests directory 0700, run the agent's program as an unprivileged user.
- **Run a hostile-planner probe against the real grader** — rewrite graded inputs mid-run, answer from a memorised plan, symlink the graded artifact — each attack caught by a *different* guard (import-time snapshot, SHA pin, realpath).
- **Verifier derives ground truth from a sealed copy inside tests/**, never hardcoded expected values (a named rubric red flag) and never reads from agent-writable /app. Ship the agent's PROGRAM as the graded artifact where possible (e.g. `artifacts = ["/app/plan.py"]`) — the verifier re-runs it on sealed instances, strictly stronger than grading one output.

### 8.5 Every graded rule must bite; everything shipped must be regenerable

- **QC mutation-tests the reference against the corpus:** a rule the data never exercises is dead code and a block. Measured (ETL-1): a predictor clamp activated on 0 of 3,768,888 samples, so deleting it still scored reward = 1; the fix drove the corpus into the rails and added a build-time assertion (`assert clamp_divergences > 50`). Floor AND ceiling every count — a stale lookup once reported "all 310 blocks lost" while every lower-bound assertion passed. And a QC-mandated fix is worth 0 as difficulty.
- **Commit the generator; re-measure every published number when data changes.** A 1.1 MB sealed set with no generator anywhere had to be reconstructed from prose; the rebuild invalidated ~8 published measurements. Swapping sealed data without re-running every number quoted in task.toml publishes fabricated measurements — re-measure and CORRECT claims, never renumber them.
- **Validate the SHIPPED artifacts, not the generator's records:** an export whitelist silently stripped new fields from shipped JSON while the oracle stayed green because both sides read missing fields as empty (measured-gate — failed rubric review).
- **Validate candidate instances against the VERIFIER, not only the reference:** a register could be reference-solvable and verifier-rejected outright (the verifier called a shape "malformed" that the reference silently truncated past). The battery must import the shipped verifier and drive its real acceptance path.
- **A differential failure confined to one structural subset is a comparison bug:** 280 divergences over 475 assets, every one a GROUPED asset — the two sides computed pre- vs post-transformation quantities; align them and it is 0.
- **The harness must carry a control and load exactly what ships:** a probe was wrong on its first two runs and invisibly so — every mutant reported a uniform 6/9 because all nine tests died on FileNotFoundError; other measured fakes include a stale module picked up by sys.path (fix: load by explicit file path and *print which file is under test*), "live" defined by internal-state diff instead of the shipped verifier's verdict (6 phantom failures), a stale generator report graded against the previous core's kill matrix, and a retired family left in the config rejecting every world. Instrument a stuck search with a rejection counter — never guess.
- **A semantic-core swap is a lockstep change across every DESCRIBING file:** task.toml's three explanation fields and the README, not just code. Measured: a re-roll failed `solution_explanation_quality` because task.toml still described the previous core in three flatly wrong ways — and the earlier same-SHA SUCCESS had been the lucky roll. **Never attribute a same-SHA SUCCESS→FAILURE flip to grader noise without fetching the verdict.** (These files are not agent-visible; fixing them changes the rubric, never the difficulty verdict.)
- **Environmental ceilings:** keep graded outputs inside runtime limits so failures stay analytical — e.g. graded denominators capped below Python's 4300-digit int→str limit after 2 cases blew past it.

### 8.6 ctrf and static-stage hazards (each measured, each cost a cycle)

- pytest-json-ctrf 0.3.5 **collapses parametrized tests into one entry** and the platform reads ctrf: 15 collected tests reported as "3 tests." Ship one explicit test function per graded case (loop-generated with per-case docstrings passes the rubric — 13 generated, ctrf reported 13). Read the ctrf COUNTS in the timeout probe, not just the reward.
- The stock Dockerfile's own COMMENTS contain `solution/`, `tests/`, `test.sh` — forbidden substrings the static gate matches even in comments. Rewrite them.
- tests/test.sh ships CRLF — rewrite LF, verify committed blobs, set core.autocrlf false. (A CRLF default in `csv.DictWriter`, undisclosed, was once a task's only pass@2 fail — flagged "not a genuine difficulty miss." Removing a spurious failure deletes a counted fail; replace it with real difficulty in the same push, and know the replacement only counts if agents actually fall into it — the compensating crux shipped there caught nobody, 4/5.)
- `environment/.dockerignore` is required once the build context has subdirectories. Never COPY solution/ or tests/ into the image. test.sh must always exit 0 and write reward 1/0 to /logs/verifier/reward.txt.
- Keep build/design scripts OUTSIDE the task repo and set `sys.dont_write_bytecode = True` — importing shipped code from a design script creates `__pycache__` inside task/ and fails `no_extraneous_files`; harness job output must also be written outside the repo.

### 8.7 The graded prose fields — where every rubric failure in the corpus landed

Self-grade all 31 criteria against `<your-task-repo>/references/*-rubric.toml` (ships in every task repo, ~41 KB, every criterion with description and guidance) as an explicit PASS/FAIL/NA table before every push. The four graded prose fields — difficulty_explanation, solution_explanation, verification_explanation, taxonomy labels — are where every rubric failure landed.

- `difficulty_explanation` must **name a real-world audience** ("explain who in the real world would need to solve this and why" — verbatim criterion text) and state data provenance; results-based framing (reciting battery numbers) is read as a NEGATIVE. Safe form: audience + intrinsic structural reasons each wrong reading fails + provenance + qualitative disclosure of the residual; put measured numbers in verification_explanation and the PR body.
- Frame the task as work someone is paid to do — `interesting_realistic` bites hardest on custom games and toy puzzles.

> [!warning] The grader is a non-deterministic re-roll, and inconsistent.
> Measured: the SAME difficulty_explanation text passed one roll and failed the next (GPU-1, 30/31, sole fail). And Sec-1 PASSED while carrying measured numbers ("worst success rate 0.00%", "750 randomized orders") that the same criterion failed elsewhere. Consequences: once a run is green, **never push again** (pushing re-rolls every LLM stage); never push mid-pipeline; never push an empty re-trigger (tier1 reads "0 files changed" as "fix not attempted").

**The proposal artifact** (prospective — format never gate-measured itself; the load-bearing claim is that `difficulty_explanation_quality` fails results-based framing): the platform proposal is a header line "Category: X  Sub-Category: Y" plus exactly four bold-numbered sections in dense prose — why genuinely difficult (three italic-led paragraphs: the professional, the data, the pitfalls); intended solution approach (key insight first, expert effort in hours); verification (calibration of every tolerance or why exactness is the calibration, anti-cheat, what discriminates correct from plausible-wrong, cross-validation); category/sub-category with task_objective + artifact_type. No tables, no checklists, no scaffolding — and zero internal shorthand: grep the draft for pass@, hashes, "probe-dead", "archetype", "kill-list" and strip them; the design record (dead alternatives, red-team tables, numeric bars) lives in a separate file. At the proposal gate, the verdict you want from the approach probe is "approach found but NOT confident of first-pass implementation."

### 8.8 A non-blocking advisory is a block that has not fired yet

**Clear every advisory before the next push, not just the blocker.** Measured-gate, Sec-2: **seven CI runs to clear one task, and only the first block was about difficulty.** Three of the four later blockers were things an earlier run had already printed as a non-blocking advisory and graded PASS.

| run | blocked at | flagged earlier? |
|---|---|---|
| 1 | `pass2` 2/2 too easy | — (a real difficulty result) |
| 2 | `qc_gate` — an emitted field was never checked | **yes** — `deep_review` advisory, *same run* |
| 3 | `review` — `difficulty_explanation` omitted data provenance | **yes** — eval advisory, on run **1** |
| 4 | `ava_review` `sound_verifier` — byte-equal citations accepted | **yes** — AVA advisory, on run **3** |
| 5 | `ava_review` `no_false_rejection` — the run-4 fix over-enforced | new; see the oscillation below |
| 6 | *(none)* | all stages green, `accepted` |

The mechanism is §8.7's re-roll seen from the other side: the LLM-graded stages are **non-deterministic**, so identical text that scores PASS-with-advisory today scores FAIL tomorrow. Run 3's `review` FAIL landed on prose that had already passed `review` twice. **An advisory is the grader telling you where its next roll may land.** And because an early-stage block skips every downstream stage, a one-sentence prose gap cost a full `pass2` + `qc_*` + `tier1` + `trials` cycle — roughly 3 hours.

**The AVA loose/strict oscillation, and its fixed point.** AVA audits the verifier against the spec in **both** directions, so a naive fix flips you straight to the opposite block:

- `sound_verifier` — the verifier ACCEPTS something the spec forbids (too loose).
- `no_false_rejection` — the verifier REJECTS something the spec permits (too strict).

On Sec-2, run 4 blocked because provenance citations were accepted on byte equality alone; the fix required the true origin; run 5 then blocked because the format document promised only re-execution, so the verifier was now enforcing more than the stated contract. Relaxing the check would have flipped straight back to run 4's block.

> **The fixed point is: enforce the strict reading AND state it in the spec.** This extends §8.3, whose standing advice ("fix the verifier and the reference") is incomplete — when the strict reading is the *correct* one, the thing to fix is the **spec**, so the stated contract matches what is enforced.

**Measure your rationale before defending it.** On run 4 the author had *argued* that loose acceptance protected legitimate alternative citations. Testing the claim took one 20-line script and reversed it: **7,740 bytes across six sealed images, zero with a second valid source** — the duplication was an aspiration from the v1 proposal that the generator never actually produced. When a reviewer's finding contradicts your design rationale, the rationale is the cheaper thing to measure.

---

## 9. Measurement Epistemics: What Evidence Is Worth

### 9.1 The asymmetry

**Every cheap early signal in the corpus has been measured wrong at least once — except one. Signals that say "too hard / dead" are weak. The one authoritative signal is the platform's own "too easy" (pass@2 = 2/2 SOLVED).**

| Signal | Measured failure | Verdict |
|---|---|---|
| Local probe says DEAD | ML-2: probe solved 8/9 in < 1 s → gate 0/5 · 5 gvf; DataSci-1: probe 13/13 in 0.1 s → 0/5 · 5 gvf; ML-1: released as shallow → pass@2 0/2 with platform conclusion "the difficulty is genuine" | **Probe-dead ≠ gate-dead** (confirmed 3×). The probe proves a shortcut EXISTS; the gate measures whether the agent FINDS it (the trial model reaches for a heuristic ordering, not 10^4 random-restart draws). |
| Pre-build NO_GO by argument | SciComp-2: the author's own NO_GO was wrong → 0/5 accepted, one-run green; Math-1: judge red-teamed the survivor at P(gate) ≈ 0.17–0.20 → cleared everything | Licenses choosing between designs, NOT abandoning a slot. |
| pass@2 PASS | RegOps-1: the PASS was carried by a task defect (failing trial scored difficulty_crux FAIL); fixing the defect gave 2/2 solved | Read pass@2 WITH its rubric rows — difficulty_crux NA/FAIL on the failing trial means the pass is spurious. |
| pass@2 timeout signals | GPU-2: 1 in-progress-timeout AND a low_timeout FAIL at pass@2; both evaporated at pass@5 (low_timeout 5/5 PASS) — any "fix" would have been damage | n=2 timeout signals are noise. Do not harden before seeing pass@5. |
| 100% archetype kill rate | DataSci-1: six archetypes died across 2,880 runs, task still trivially solvable (a search recovers from exactly those mistakes); LowLevel-1: 98.46% pooled kill → gate 5/5 solved | Kill-given-belief ≠ belief rate (Part 5.5). |
| **Platform pass@2 = 2/2 SOLVED** | Never overturned on unchanged agent-visible content | **Authoritative.** No local re-measurement overturns it. Two independent 2/2 on one skeleton is conclusive — do not revive the design. |

The mirror asymmetry, also measured: **local probes and batteries over-predict in opposite directions.** Probes over-predict *death* (the probe is an upper bound on what a solver could do given the rules); batteries over-predict *difficulty* (they measure the verifier's sensitivity, not the agent's error distribution). The wrong-solver battery — which models what agents actually write — is the better predictor of the two, and ML-1's actual pass@2 failures landed exactly on archetypes its battery already contained.

> [!warning] Contradiction: is a local probe kill mandatory before pushing?
> One record mandates it — "never push until agents die locally," validated once end-to-end (a local probe's 0/2 with "Cannot free staging capacity" predicted CI pass@2 0/2, pass@5 0/5 with the *same root cause*; one probe costs ~30–75 min vs ~2–4 h per CI cycle). Two other records document the same class of evidence over-predicting death and being wrong about release decisions ("two for two on do not release a slot on your own probe"). And a third holds both positions itself: a slot skipped the probe deliberately because "probe-dead ≠ gate-dead cuts both ways," went 5/5 solved, and the post-mortem concluded the probe rig "is the ONLY pre-push instrument that measures belief rate — skipping it traded a local measurement for a billed gate run that returned the same number." Operational resolution: run the probe; treat its KILL verdict as unreliable for release/abandon decisions, but treat its SOLVE verdict as a serious warning about belief rate — and when the design is a printed-optimum skeleton with a fully green pipeline, a probe solve is the one instrument that can still save the run.

**The kill/ship decision numbers** (prospective — derived across all 7 printed-optimum tasks, honest limits stated: the three "killed" comparison designs were never run against the trial model; identical content measured 0/5, 2/5, 0/5 on different days; ~16% false-fail at n=5 for a genuinely 70%-fail design): a strong probe solving ≥ 8/12 within 10% of the cap AND < 2 beliefs surviving the N-silence test → dead, do not build. The probe solves BUT ≥ 2 N-silent narrowing beliefs plus the stated resource constraint hold → SHIP — a dead search space is the normal state of a good design.

### 9.2 What a 2/2 block means

**A 2/2 block is a design problem, not a dead slot or category.** Confirmed repeatedly, and each repair has a mechanism section — go to it, because the one-word label below is not a recipe:

| Slot | 2/2 → 0/5 repair | Use it when | Mechanism |
|---|---|---|---|
| Media-2 | **Constructive leg added** | The core is a checked predicate — the agent decides rather than builds | **§5.1** |
| ETL-2 | **Union of boxes** | Legality factorises over independent fields | **§5.2** |
| Media-1 | **Structural change** (legality, not naming) | A wrong belief only *misnames* the artifact instead of making it illegal | **§3.2** (proven floor shapes) + §4 on what to withhold |
| RegOps-1 | **Data-only rebuild** | The rules genuinely are hard — the *instances* are the problem | **§6.4** — reproduce the archetype that solved your task, measure its per-instance rate, regenerate sealed instances driving it toward zero (mean 77% → ~6–8%; gate 0/5 · 4 gvf) |

The last row matters more than its length suggests: it is the only repair that leaves your semantics intact, so reach for it when the design survives the kill-list but the shipped instances were too kind.

Every task that reached 0/5 has one of: a narrowing belief search cannot cross, a construction agents never find, or extreme feasible density (5.97e-12). Adding more belief families or cutting more prose after a 2/2 is measured waste ("three attempts, two designs, zero movement"; "the fix was structural, not quantitative").

**The ceiling law bounds what the printed-optimum skeleton can do** (measured-gate, Build-1 v1): fairness + a closed-form floor + small instances jointly cap difficulty at "will the agent bother to backtrack" — fairness gives a transcribing agent a perfect legality oracle, attainability certification makes placement cheaply solvable, small instances make the residual search enumerable. Measured: 2/2 solved, difficulty_crux NA twice, wrong-belief rate 0/8 on rules harder than anything a 9-agent hardening panel could add; one agent validated a correct plan at step 40 and burned the rest of the hour on an unsolicited rewrite. Escapes exist where difficulty is *announced but not crossable* (a narrowing belief hiding the correct move; extreme density) — and the same skeleton's v2, with only the semantic core swapped, went 0/5, so the ceiling is about the family's easy region, not a death sentence.

### 9.3 pass@2 statistics and stop conditions

- pass@2 at n=2 is one sample: a pass2 SUCCESS is not evidence a task is hard; a 1/2 is not predictive of pass@5 (measured: 1/2 with a genuine crux kill preceded a 5/5). Identical content has measured 0/5, 2/5, 0/5 on different days; at n=5 against a 60% bar, a 70%-fail design fails ~16% of the time.
- Stop conditions that shipped: **0/2 → go to pass@5. 1/2 → one instance-tightening pass, re-run once. 2/2 → stop the same day** (two independent 2/2 on one skeleton is conclusive). Hard ceiling: 2 runs / 12 hours on one design.
- "Never overturned" applies to unchanged agent-visible content — and prose-only edits ARE content changes (that is the whole de-disclosure lever). The corpus does not fully reconcile this; treat a SOLVED verdict as binding on the design *as shipped*, and any structural or disclosure change as a new design.

### 9.4 Panels

A design panel converging on RELEASE is not evidence a slot is dead or safe — it is evidence nobody in the panel found the lever (a 13-agent panel with 8 adversarial reviews recommended RELEASE on a leaky spec that then cleared only after the prose cut; another panel's judge ruled NO-GO on the design that cleared everything). **Use panels and red-teams to kill, never to bless** — while remembering they killed three designs that had passed every static gate (all three measured 2/2 at pass@2, so the kills were right), and that pre-build red-teams with brute-force duty have found real soundness bugs. Same instrument, opposite error directions; both kept.

### 9.5 Watch-and-fix discipline

On early-signal evidence alone, fix **packaging, static stages, ava_review, rubric re-rolls — never a semantic core.** Every CI block skips the downstream difficulty stages, so a non-difficulty failure costs the whole measurement (one slot needed THREE CI runs; neither of the first two failures was about difficulty, and both were checkable locally in minutes). Local checks cannot replicate the platform's LLM stages (similarity, deep_review, AVA — non-deterministic) or the true pass@5 with the pinned model; those are confirm-only, never iterate-against.

**Similarity** (measured-gate): same-author printed-optimum tasks collide on cosine_similarity (block at ≥ 0.9 on Instruction + Verifier). What works is loud surface differentiation with the semantic core untouched — different domain vocabulary, different state objects, no shared mechanics (one task passed as the *eleventh* same-author submission; measured passing scores 0.63–0.80). Because renames touch the graded surface, **rename late, then re-run every battery** (one slot re-ran its full three-way fuzz, +346 verdict trios, after renames). Counter-case on record: one slot was blocked at cosine_similarity self-match and abandoned. The shape's real expiry is similarity, not difficulty.

### 9.6 The pass@2 suggestion is a diagnostic instrument, not a verdict — spend it early

**Measured-gate, ETL-3.** Four semantic cores were built for this slot: v1 killed on paper, **v2 pass@5 3/5**, **v3 pass@2 2/2**, **v4 pass@2 2/2**. What finally cleared it — 0/5 solved · 5 good-valid-fails · avg@5 0.000, all 17 stages green in one run — was not a fifth core. It was **the platform's own pass@2 difficulty suggestion**, which located the defect *from the task's own `task.toml` disclosure*, and the defect was **one mis-calibrated percentile**:

> Running-total thresholds sat at the 0.50–0.60 percentile of cohort totals, so most cohorts crossed only near their last reading — collapsing *release at settlement* onto *release when the last figure is finished*, which left the intended rule unable to change any cell count.

Measured: at the 0.55 percentile **26%** of cohorts settle early; at 0.08–0.18, **68%**. Moving the thresholds took the intended carrier from **1/11 to 10/11**, and a second suggestion (three template variants instead of one fixed role assignment, so the decomposition cannot be recovered once from the public sample and reapplied) closed the rest.

Two things follow, and the second is the expensive one:

1. **Spend the suggestion early.** It is free, capped at 2/day (UTC reset), and here it diagnosed in one shot what four design iterations missed. Treating it as a consolation prize attached to a failed run wastes the cheapest diagnostic in the pipeline.
2. **Read your own disclosure adversarially before building another core.** The author had written *"measured near-inert on the shipped set, failing one, none and none of the eleven"* into `task.toml` — and then spent two CI cycles on new semantics instead of fixing the inert carrier that sentence names. The platform read that sentence and found it immediately. Before you conclude a design is dead, re-read what you told the grader about it: a 2/2 is sometimes a calibration failure your own prose already confessed to, not a dead shape.

This is the calibration sibling of §9.2's four repairs — closest to the data-only rebuild, but cheaper still, because the parameter is one you already have and the instrument that finds it is free.

---

## 10. The Pre-Push Checklist

Design (before writing code):

1. Checked-vs-constructed test: what must the agent BUILD that the verifier could not hand it by simulating? "Nothing" → redesign.
2. Factorising test: flip one field of the true configuration; does iterating that reconstruct the constraint? Compute every shared input first, then re-ask. Conjunction → union of boxes or redesign.
3. Product-vs-state-graph: what does a move DESTROY? Nothing → CP-SAT bait, dead unless feasible density < ~1e-7.
4. One-line-policy battery: three obvious policies, optimum by EXACT enumeration on small instances. Any policy > 0% → not constructive yet. Trust only full enumeration.
5. Floor: non-zero on the shipped set, non-decomposable per key, printed with normative achievability, graded `<=` never `==`.
6. ≥ 2 N-silent narrowing beliefs + ≥ 1 stated resource outlawing the bulk architecture (implement the bulk architecture; confirm it fails 100% of sealed). Budgets set ABOVE the worst believed-wrong layout.
7. Kill/silence grid (12 instances × N families) BEFORE instance selection. Every archetype: kill exists in shipped instances, selection pool provably ≥ 2, carry survives a stage, no quantiser masks it, cheapest transcription per stratum is wrong.
8. Named-crux and library check: nothing load-bearing that a literature name or a pip install returns; ≥ 2 sealed-exercised departures from each nearby library, outsourcer archetype batteried.
9. No float in the graded path — tokenise verifier + reference to assert it.

Disclosure:

10. Grep the SPEC for `=`, matrices, recurrences, entailment sentences ("order makes no difference"), step-lists. Each: rule to obey, or answer to a belief? Cut the answers.
11. No how-to-work coaching in instruction.md; the always-emit rule is allowed and wanted.
12. Public example: derivation-free, no expected answer, byte-identical for every belief archetype (asserted mechanically), no visible value the agent's computation can reproduce; blindness by construction. Every printed claim recomputed from the reference; blind implementer re-run after any prose cut.
13. Delete the "You have N seconds… do not cheat" line. Time budget lives in task.toml only.

Instances:

14. Battery includes correct-rules + naive search, barred in wall clock at the disclosed cap, un-contended, deadline inside the search. Battery re-run after ANY planner-core change and after renames.
15. Selection on measured rates (~400 draws/archetype), two-stage disjoint seed streams, margin above the bar, pooled rates with sample sizes, seal-time un-contended re-confirmation. Witness-first generation, per-instance attainability certified through the verifier's own simulator. Candidates validated against the VERIFIER, not just the reference.
16. ≥ 3 failure classes, no dominant root cause.

Verifier and packaging:

17. Reference exits 0 on every damaged-input path (force each one) and never hangs — exclude bimodal thrashers.
18. n_items × cap < verifier budget, validated by the sleeper probe; ctrf counts read, one test function per graded case; a merely-valid answer trivial to produce.
19. Snapshot graded inputs at import; plan-size cap before json.load; arg type checks; hostile-planner probe (rewrite/memorise/symlink) each caught by a different guard; tests dir 0700, agent program unprivileged.
20. Differential fuzz over degenerate out-of-generator shapes (contract-respecting); third floor implementation from prose alone; corruption battery one-per-rule + valid variants covering solution CLASSES; every graded rule bites on the shipped corpus (build-time divergence assertions, floors AND ceilings).
21. Generator committed; every published number re-measured after any data change; shipped artifacts validated (not generator records); prose fields lockstep with the core; Dockerfile comments clean, LF endings, .dockerignore, no bare name.ext in instruction.md, no __pycache__/, job output outside the repo.
22. Full 31-criterion rubric self-grade; audience named in difficulty_explanation, provenance stated, measured numbers moved to verification_explanation; taxonomy labels match what the agent physically emits, spellings checked against the repo's taxonomy file.

Measurement:

23. Every archetype is a whole planner — the belief reaches the engine, each derived bound, the tie-break order and the self-replay (§5.6). An unfaithful battery's rates are not evidence.
24. Run the local probe; a probe KILL is a warning, not a verdict — a probe SOLVE is the belief-rate alarm.
25. pass@2: 0/2 → pass@5. 1/2 → one tightening pass, once. 2/2 → stop; the fix is structural — but before assuming that, spend the difficulty suggestion and re-read your own `task.toml` disclosure adversarially (§9.6). Read difficulty_crux and low_timeout per trial before concluding anything.
26. Budget ≥ 4 countable fails (one trial in five is lost to nothing). Never harden toward search after a timeout; never touch the 3600 s cap.
27. **Every advisory in the review comment is fixed — not just the blocker** — including advisories still open from earlier runs (§8.8). Diff what the verifier ENFORCES against what the spec STATES, in both directions.
28. Once green: do not push again. Ever.