# One-prompt install

Copy the block below and paste it into **Claude Code, Codex, Cursor or Antigravity**. It works
out which tool it is running in, installs the right way for that one, proves each step by
running it rather than by checking that a file exists, and stops if anything fails.

Nothing else is needed — no flags to fill in, no paths to edit.

```text
Set up the benchmark-task-authoring skill for me, end to end, and verify it actually works.

CONTEXT
I write Terminal-Bench 2 / Harbor benchmark tasks. The hard part is the difficulty gate —
tasks come back "too easy" and every CI run costs hours. This skill is a field manual of
measured laws from ~30 completed slots, a kill-list of task shapes already known dead, a
map of all 17 review stages, and one brief per category.

Repo: https://github.com/Xclaw-bot/benchmark-task-authoring
Requires: git, python 3.11+

DO THIS, IN ORDER

1. Say which coding tool you are running in before you start, then install for THAT tool
   only — not all four:
     Claude Code   git clone <repo> ~/.claude/skills/benchmark-task-authoring
                   (Windows: %USERPROFILE%\.claude\skills\benchmark-task-authoring)
     Codex         clone into my project — AGENTS.md at the repo root is read automatically
     Cursor        clone into my project — .cursor/rules/*.mdc auto-attach by glob
     Antigravity   clone into my workspace — .agents/rules/*.md are the workspace rules
   If you genuinely cannot tell which tool you are, ask me once, then continue.

2. Verify the clone rather than assuming it. All of these must exist:
   SKILL.md, AGENTS.md, references/hardness-laws.md, references/ci-stages.md,
   assets/, scripts/, .cursor/rules/, .agents/rules/
   Then count the category briefs — `references/category-*.md` must return exactly 13
   files. Print the count. If anything is missing or the count is wrong, stop and tell me.

3. Set up local retrieval so neither of us re-reads a 35k-token manual to answer one
   question:
     python scripts/dr.py index --no-embed
   Then PROVE it works by running a real query and pasting the output:
     python scripts/dr.py ask "what makes a benchmark task too easy"
   If python is missing, the index fails, or the query returns nothing, tell me exactly
   what failed. Do not silently work around it.

4. These environment variables are optional. Ask me before setting anything permanent:
     BENCH_WORK  my working dir (proposals, design records) — retrieval will index it too
     BENCH_MEM   my own notes dir — same
     BENCH_ORG   my task-repo GitHub org, so `python scripts/taskdesk.py` needs no flag

5. Now read SKILL.md yourself — "The one law" and the kill-list — and tell me, in under
   200 words total:
     - the one law, in a single sentence
     - the three kill-list shapes most likely to bite a first task
     - which category brief I should read first (ask me my category if you need it)
   I will read the manual myself. This step is so I know you actually loaded it.

6. From references/ci-stages.md, tell me the single highest-value thing to do before my
   first push, and what it costs. Name the command if there is one.

RULES
- Verify by running. A file existing is not proof a step worked — run the thing and show
  me the output.
- Do not touch any of my files outside the clone target without asking first.
- Do not create a task, a proposal, a task.toml or a verifier. This is setup only.
- If a step fails, name the step and stop. A half-installed skill that reports success is
  worse than no skill.

ONE THING TO CONFIRM AT THE END
I never invoke this skill by name. It is supposed to fire on its own when I say things
like "agents keep solving my task", "my PR checks are failing", "pass@5 came back 3/5",
"how do I make this harder", or "ava_review failed". Confirm you have it loaded and will
recognise those, then stop.
```

---

## What it will do

| step | what you should see |
|---|---|
| 1 | It names your tool and clones to one place — not four |
| 2 | A file check plus **`13`** category briefs. A wrong count means a bad clone; it stops |
| 3 | `indexed … cards / 28 files`, then a real answer to a real query, pasted back |
| 4 | It asks before setting anything permanent |
| 5–6 | A short summary proving it read the manual, not just downloaded it |

## Afterwards

You never invoke the skill by name. It fires on its own when you say something it recognises —
*"agents keep solving my task"*, *"my PR checks are failing"*, *"pass@5 came back 3/5"*,
*"ava_review failed"*, *"how do I make this harder"*.

First thing worth reading yourself: the brief for your category, `references/category-*.md`.
All 16 categories are covered across 13 files. It is about six minutes and it is the step most
likely to save you a redesign.

## Updating later

```bash
git pull && python scripts/dr.py index --no-embed
```

Re-run the index after every pull — new reference files are not in your old index.
