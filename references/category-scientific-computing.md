# Category brief — Scientific Computing & Domain Science

Two slots, both cleared at **0/5 solved**. Both used the same skeleton, and one of them is the
corpus's clearest evidence that your own pre-build verdict can be wrong.

| | sub-category | final | notable |
|---|---|---|---|
| **SciComp-1** | Numerical methods | 0/5 · **0 timeouts** | extreme feasible density (5.97e-12) as the difficulty mechanism |
| **SciComp-2** | Signal processing | 0/5 · `accepted` in ONE run | **the author's own pre-build NO_GO was wrong** |

---

## The category's one non-negotiable: exact integers

**Tolerance is the category hazard.** A float in the graded path is simultaneously a rejection
risk *and* slack an agent can be wrong inside. Both clears used exact integers throughout, and
this is the single most transferable rule here.

This bites hardest precisely where it is least convenient — signal processing, numerical
methods, differential equations and statistical modelling are all float-native domains. If your
design needs a float anywhere the verifier looks, redesign in exact integer, rational or
fixed-point arithmetic before proceeding.

---

## The finding SciComp-2 owns: your NO_GO can be wrong

SciComp-2's author ran a pre-build gate and it returned **NO_GO**. The slot was built anyway
and went **0/5, accepted, green in a single run.**

What actually happened at the gate is the instructive part: **agents solved the fold the author
feared was disclosed, and died on a rule the author had discounted as trivial.**

> Your model of which part is hard is a hypothesis, not a measurement. It is wrong often enough
> that a pre-build NO_GO should slow you down, not stop you.

Pair this with §9.1's asymmetry: *"too hard / dead" signals are weak; "too easy" is
authoritative.* A local probe that solves your task is a warning. A local probe that says the
task is impossible is barely evidence at all.

---

## The Bezout law — an axis that looks available here and is not

Scientific domains invite existential legality: *"does there exist n, m such that some linear
relation holds?"* over periodic streams. **That predicate is provably shallow.**

For `∃ n,m : linear relation`, the reachable differences are multiples of `g = gcd(A_i, A_j)`,
and Bezout puts a witness within about `A_j/g`. The two knobs fight and cannot both be won:

| | consequence |
|---|---|
| `g` large | witness depth `A_j/g` is small — the first witness is early |
| `g` small | collision density `(c_i+c_j)/g` is high — sample 0 already collides |

Depth is `~min(A_j/g, g/(c_i+c_j))`. Measured: horizons of 10⁷–10⁸ samples per recorder,
**deepest first witness = sample 22, median ~4.** Reaching the 10⁷ samples needed to burn a
wall-clock cap requires `A ~ 10¹⁴`, where per-pair collision probability is ~10⁻⁷ and the floor
is zero.

> **There is no parameter regime where the predicate is both common and expensive to witness.**

If a cost leg needs an expensive per-candidate test, the legality condition must be **universal
over the horizon**, or an optimisation with no witness — and the correct route must never
evaluate the predicate at all.

---

## The shape both clears used

**Printed optimum + constructive scheduling.** The spec prints the closed-form floor and
guarantees achievability; difficulty is in constructing a legal object that attains it. Both
slots used it; the category has never been tried with anything else, so nothing here says
another shape fails — only that this one works twice.

SciComp-1's difficulty mechanism was **extreme feasible density (5.97e-12)** — one of only
three ways any corpus task has reached 0/5. Note the bar: §3.1 #12 says feasible fractions
between 1e-4 and 1e-1 are worth exactly zero; only below ~1e-7 counts, and only if
`expected_draws × cost_per_draw > 10 × cap`.

---

## Battery warning specific to this category

**A weak archetype battery passes 34% of kernels** — measured here. In a domain where the
natural archetypes are numerical variants that mostly agree, a battery can look healthy while
selecting instances that punish nothing. Whatever battery you propose, say explicitly why it is
strong, and re-run it on the selected set after any core change.

Related and load-bearing: the battery overrules your judgment, in one direction only. It can
tell you a design is too easy; it cannot tell you a design is hard.

---

## Pre-build checklist

1. **Is every graded number an exact integer?** No floats in the graded path — this is the
   category rule.
2. **Is your legality predicate existential over periodic structure?** Then Bezout makes it
   shallow. Make it universal over the horizon instead.
3. **Did your pre-build gate say NO_GO?** Weak evidence. Measure before abandoning.
4. **Is your difficulty announced but not crossable** — a narrowing belief, an undiscovered
   construction, or density below ~1e-7?
5. **Is your feasible fraction in the worthless band** (1e-4 to 1e-1)?
6. **Is your battery strong, or does it just agree with itself?**
7. **Have you re-run the battery on the selected set** after the last core change?
8. **Does `n_items × per_item_cap < verifier timeout_sec` hold?** Both clears kept caps at
   25–30 s.
9. **Blind public sample.**
10. **Sharing a sub-category with an earlier slot?** Differentiate on all four axes.

---

## Honest limits

**n = 2**, and both used the same skeleton. The exact-integer rule, the
battery-overrules-judgment rule and the Bezout law are the parts that generalise; the specific
floors and the 25–30 s caps are two data points.

The local difficulty probe **agreed** on SciComp-1 (0/2 solved) and **disagreed** on SciComp-2,
where the author's own gate returned NO_GO and the platform cleared it. One agreement, one
disagreement — treat the probe accordingly.

Six sub-categories are untouched: differential equations and simulation, physics and mechanics,
chemistry and materials workflows, biology and bioinformatics, statistical modeling, and
optimization/operations research. **Optimization and OR carries an obvious hazard** — margin
difficulty is dead everywhere, and that sub-category is named for it.
