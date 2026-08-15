# Intro message — short version (chat / Slack / Discord)

> Sharing something that took me ~30 slots to learn the hard way.
>
> `benchmark-task-authoring` is a Claude Code skill that packages the measured laws for what
> actually makes agents fail a Terminal-Bench task — plus the part I wish I'd had on day one:
> how to clear all 17 review stages on **one** push instead of three.
>
> The thing that changed how I work: a full review run is ~3 hours, and a block at any early
> stage skips everything downstream *including* `trials`. So a five-minute prose fix in
> `difficulty_explanation_quality` doesn't cost you a checkbox — it costs you the entire
> difficulty measurement, and you find out three hours later. I burned three runs on one slot
> where neither of the first two failures was about difficulty at all.
>
> What's in it:
> • The kill-list — 13 task shapes measured dead, with the tell for each and which four have
>   a real repair
> • All 17 CI stages: what each gates, which are checkable locally, and the four blockers
>   preflight misses
> • The free 31-criterion rubric self-grade (no API key — the rubric ships in your own repo)
> • A local retrieval tool so you stop re-reading the same long docs: index once, then answer
>   a design question in ~1k tokens instead of ~35k
>
> Repo: https://github.com/Xclaw-bot/benchmark-task-authoring
>
> Install: grab the `.skill` file and click **Save skill**, or clone it straight into
> `~/.claude/skills/`. It then fires on its own when you say things like "agents keep solving
> it" or "my PR checks are failing".
>
> Or let your agent do the whole thing — one prompt, works in Claude Code, Codex, Cursor and
> Antigravity, and verifies the install rather than assuming it:
> https://github.com/Xclaw-bot/benchmark-task-authoring/blob/main/SETUP-PROMPT.md
>
> It's method only — no task content, no repo ids. Everything carries an evidence class so you
> can see what was measured at the gate vs. what's still a hypothesis. If a law turns out wrong
> in your categories, that's more useful than one that holds — tell me and I'll fix it.

---

# Intro message — email version

**Subject:** A skill for getting benchmark tasks through the difficulty gate faster

Hi —

Sharing a Claude Code skill I put together from about thirty task slots: the ones that cleared
the difficulty gate, and the considerably larger number that died first.

Two things in it I'd have paid for on day one.

The first is the kill-list: thirteen task shapes that are measurably dead, each with the tell
that identifies it and — for the four that are salvageable — the repair that actually worked.
Most of them are shapes that look clever right up until agents solve your task 2/2 in twenty
minutes.

The second is the part nobody warned me about. A full review run takes about three hours, and
a block at any early stage skips every stage downstream, including the difficulty trial. So a
prose field you could have fixed in five minutes doesn't cost you a checkbox — it costs the
whole difficulty measurement. I spent three CI runs on one slot where neither of the first two
failures had anything to do with difficulty. The skill documents all seventeen stages, which
ones you can prove locally beforehand, and the four blockers that preflight doesn't catch.

There's also a free 31-criterion rubric self-grade (no API key needed — the rubric already
ships in your task repo), and a local retrieval tool so you can stop re-reading long documents:
index once and a design question costs ~1k tokens instead of ~35k.

It's here: https://github.com/Xclaw-bot/benchmark-task-authoring

If you'd rather not install it by hand, there's a single prompt you can paste into your agent —
it detects whether it's in Claude Code, Codex, Cursor or Antigravity, installs the right way for
that one, and verifies each step by running it instead of assuming it worked:
https://github.com/Xclaw-bot/benchmark-task-authoring/blob/main/SETUP-PROMPT.md

To install, download the `.skill` file from the repo and click **Save skill**, or clone the
repo straight into `~/.claude/skills/`. After that it triggers on its own when you say things
like "agents keep solving it" or "my PR checks keep failing".

It's method only — no task content and no repo identifiers. Every claim carries an evidence
class, so you can see which survived the platform's own measurement and which are still
hypotheses. If one of the laws turns out to be wrong in your categories, that's a more
valuable result than one that holds — please tell me.

— <your name>
