#!/usr/bin/env python3
"""taskdesk.py — a board dashboard for your benchmark task slots.

Sweeps every repo in your task org, reads each PR's label and its per-stage check
results, and writes taskdesk.html: what needs your attention, and — the part that
saves real time — exactly which review stage each PR is sitting at.

A full review run is ~3 hours and a block at an early stage skips everything
downstream, so knowing you failed at `review` rather than at `trials` is the
difference between a five-minute prose fix and a redesign.

Usage
    python taskdesk.py --org <your-task-org>        # or set BENCH_ORG
    python taskdesk.py --org <org> --out board.html

Requires the `gh` CLI, authenticated. Read-only: it never pushes.
"""
import argparse, html, json, os, subprocess, sys, time
from datetime import datetime

# Canonical stage order. Unknown stages are appended in the order gh returns them,
# so this keeps working if the pipeline gains a job.
STAGE_ORDER = ["changes", "cosine_similarity", "review", "similarity", "validation",
               "ratelimit", "pass2", "pass2_suggestion", "deep_review", "ava_review",
               "tier1", "qc_eval", "qc_exec", "qc_gate", "trials", "gate"]

# Which stages you can prove locally before pushing — see references/ci-stages.md.
LOCAL = {"review", "validation", "ava_review", "changes", "similarity"}


def gh(args, default=None):
    try:
        out = subprocess.run(["gh"] + args, capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=120)
        if out.returncode != 0:
            return default
        return json.loads(out.stdout) if out.stdout.strip() else default
    except Exception:
        return default


def sweep(org):
    repos = gh(["repo", "list", org, "--limit", "200", "--json", "name"], [])
    if repos is None:
        sys.exit("error: could not list repos for org %r — is `gh` authenticated?" % org)
    rows = []
    for i, r in enumerate(repos):
        name = r["name"]
        print("  [%d/%d] %s" % (i + 1, len(repos), name), file=sys.stderr)
        prs = gh(["pr", "list", "-R", "%s/%s" % (org, name), "--state", "all",
                  "--json", "number,state,labels,updatedAt"], []) or []
        if not prs:
            rows.append(dict(repo=name, pr=None, labels=[], state=None,
                             stages=[], updated=None))
            continue
        top = sorted(prs, key=lambda p: p["number"])[-1]
        checks = gh(["pr", "checks", str(top["number"]), "-R", "%s/%s" % (org, name),
                     "--json", "name,state,bucket"], []) or []
        stages = []
        for c in checks:
            # gh reports "review / stage_name"; keep the leaf
            leaf = c["name"].split("/")[-1].strip()
            stages.append((leaf, c.get("bucket", "").lower()))
        rows.append(dict(repo=name, pr=top["number"], state=top["state"],
                         labels=[l["name"] for l in top.get("labels", [])],
                         stages=stages, updated=top.get("updatedAt")))
    return rows


def order_stages(stages):
    known = {n: b for n, b in stages}
    out = [(n, known[n]) for n in STAGE_ORDER if n in known]
    out += [(n, b) for n, b in stages if n not in STAGE_ORDER]
    return out


def classify(row):
    """What does this slot need from you?"""
    if row["pr"] is None:
        return ("noPR", "No PR yet — design and build, then push once")
    lab = [l.lower() for l in row["labels"]]
    buckets = [b for _, b in row["stages"]]
    if "accepted" in lab and "needs-revision" not in lab:
        return ("accepted", "Accepted — only the platform Submit click remains. Do not push.")
    if "fail" in buckets:
        failed = [n for n, b in order_stages(row["stages"]) if b == "fail"]
        first = failed[0] if failed else "?"
        hint = ("checkable locally — see references/ci-stages.md before re-pushing"
                if first in LOCAL else "confirm-only stage; read the PR comment")
        return ("failing", "Blocked at <b>%s</b> — %s" % (html.escape(first), hint))
    if "pending" in buckets:
        pend = [n for n, b in order_stages(row["stages"]) if b == "pending"]
        return ("running", "Running <b>%s</b> — do not push, it cancels the run"
                % html.escape(pend[0] if pend else "?"))
    if "needs-revision" in lab:
        return ("failing", "Labeled needs-revision — read the newest PR comment")
    return ("ok", "All reported checks green")


CSS = """
:root{--bg:#151920;--surface:#1c222b;--surface2:#212936;--line:#2b3340;--line2:#39424f;
--ink:#e9e6dd;--muted:#98a0ad;--faint:#6b7480;--accent:#e2a75c;--accent-ink:#151920;
--good:#66b98a;--warn:#d9a441;--crit:#d97a6c;--info:#7aa5d8;--neut:#8b93a1;
--good-bg:rgba(102,185,138,.13);--warn-bg:rgba(217,164,65,.13);--crit-bg:rgba(217,122,108,.13);
--info-bg:rgba(122,165,216,.13);--neut-bg:rgba(139,147,161,.12);
--mono:"Cascadia Code","Consolas",ui-monospace,SFMono-Regular,Menlo,monospace;
--sans:"Segoe UI",system-ui,-apple-system,sans-serif;}
@media (prefers-color-scheme:light){:root:not([data-theme="dark"]){
--bg:#f1efe9;--surface:#fbfaf7;--surface2:#eeebe2;--line:#dcd7cb;--line2:#c9c3b4;
--ink:#262a31;--muted:#676e79;--faint:#8d93a0;--accent:#a06f24;--accent-ink:#fbfaf7;
--good:#2e7d4f;--warn:#95680f;--crit:#b0492f;--info:#33648f;--neut:#6c7480;
--good-bg:rgba(46,125,79,.10);--warn-bg:rgba(149,104,15,.10);--crit-bg:rgba(176,73,47,.10);
--info-bg:rgba(51,100,143,.10);--neut-bg:rgba(108,116,128,.10);}}
:root[data-theme="dark"]{--bg:#151920;--surface:#1c222b;--surface2:#212936;--line:#2b3340;
--ink:#e9e6dd;--muted:#98a0ad;--accent:#e2a75c;}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);margin:0;font-size:14.5px;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px 64px}
header{border-bottom:1px solid var(--line);background:var(--surface)}
.hd{max-width:1180px;margin:0 auto;padding:18px 20px 14px;display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 24px}
.hd h1{font:600 17px/1.2 var(--mono);letter-spacing:.14em;margin:0;text-transform:uppercase}
.hd h1 .dot{color:var(--accent)}
.stamp{font:400 12px var(--mono);color:var(--muted)}
.desklink{font:600 11px var(--mono);letter-spacing:.1em;color:var(--accent);text-decoration:none;
border:1px solid var(--line);border-radius:5px;padding:4px 10px;white-space:nowrap;margin-left:auto}
.desklink+.desklink{margin-left:0}
.desklink:hover{border-color:var(--accent)}
.desklink:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h2{font:600 12px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted);
margin:34px 0 12px;display:flex;align-items:center;gap:10px}
h2::after{content:"";flex:1;height:1px;background:var(--line)}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:10px;margin-top:22px}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px 10px}
.tile b{display:block;font:600 26px/1.1 var(--mono);font-variant-numeric:tabular-nums}
.tile span{font-size:11.5px;color:var(--muted)}
.tile.g b{color:var(--good)}.tile.c b{color:var(--crit)}.tile.w b{color:var(--warn)}.tile.acc b{color:var(--accent)}
.act{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;background:var(--surface);
border:1px solid var(--line);border-left:3px solid var(--neut);border-radius:6px;padding:10px 14px;margin-bottom:8px}
.act.g{border-left-color:var(--good)}.act.c{border-left-color:var(--crit)}
.act.w{border-left-color:var(--warn)}.act.i{border-left-color:var(--info)}
.act .verb{font:600 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;min-width:104px}
.act.g .verb{color:var(--good)}.act.c .verb{color:var(--crit)}
.act.w .verb{color:var(--warn)}.act.i .verb{color:var(--info)}
.act .what{flex:1;min-width:260px}
.hash{font:600 12.5px var(--mono);background:var(--surface2);border:1px solid var(--line);
border-radius:4px;padding:1px 6px;white-space:nowrap}
.slot{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:13px 15px;margin-bottom:10px}
.slot .top{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px 12px}
.slot .nm{font:600 13.5px var(--mono);overflow-wrap:anywhere;min-width:0}
.slot .meta{font:400 11.5px var(--mono);color:var(--muted);margin-left:auto}
.slot .why{font-size:12.5px;color:var(--muted);margin-top:4px}
.chip{display:inline-block;font:600 10.5px var(--mono);letter-spacing:.05em;border-radius:4px;padding:1.5px 7px}
.chip.g{color:var(--good);background:var(--good-bg)}.chip.c{color:var(--crit);background:var(--crit-bg)}
.chip.w{color:var(--warn);background:var(--warn-bg)}.chip.n{color:var(--neut);background:var(--neut-bg)}
.chip.i{color:var(--info);background:var(--info-bg)}
.stages{display:flex;flex-wrap:wrap;gap:3px;margin-top:9px}
.st{font:600 9.5px var(--mono);letter-spacing:.03em;padding:2.5px 6px;border-radius:3px;
background:var(--surface2);color:var(--faint);border:1px solid transparent;white-space:nowrap}
.st.pass{color:var(--good);background:var(--good-bg)}
.st.fail{color:var(--crit);background:var(--crit-bg);border-color:var(--crit)}
.st.pending{color:var(--warn);background:var(--warn-bg)}
.st.skipping,.st.skipped{color:var(--faint)}
.legend{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:11.5px;color:var(--muted)}
.note{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:14px 16px;font-size:12.5px;color:var(--muted)}
.note b{color:var(--ink)} .note code{font-family:var(--mono);font-size:11.5px}
a{color:var(--info)}
"""


def render(rows, org, skill_url, sessiondesk):
    now = datetime.now().astimezone()
    for r in rows:
        r["cls"], r["why"] = classify(r)
    n_accept = sum(r["cls"] == "accepted" for r in rows)
    n_fail = sum(r["cls"] == "failing" for r in rows)
    n_run = sum(r["cls"] == "running" for r in rows)
    n_nopr = sum(r["cls"] == "noPR" for r in rows)

    e = html.escape
    acts = []
    if n_accept:
        hs = " ".join('<span class="hash">%s</span>' % e(r["repo"]) for r in rows if r["cls"] == "accepted")
        acts.append('<div class="act g"><span class="verb">Submit</span><span class="what">%s — accepted. '
                    'Only the platform Submit click remains, and a push would re-roll the '
                    'non-deterministic stages you already passed.</span></div>' % hs)
    for r in rows:
        if r["cls"] == "failing":
            acts.append('<div class="act c"><span class="verb">Fix</span><span class="what">'
                        '<span class="hash">%s</span> #%s — %s</span></div>' % (e(r["repo"]), r["pr"], r["why"]))
    for r in rows:
        if r["cls"] == "running":
            acts.append('<div class="act w"><span class="verb">Wait</span><span class="what">'
                        '<span class="hash">%s</span> #%s — %s. Use the time: self-grade the rubric '
                        'and run the local battery.</span></div>' % (e(r["repo"]), r["pr"], r["why"]))
    if n_nopr:
        hs = " ".join('<span class="hash">%s</span>' % e(r["repo"]) for r in rows if r["cls"] == "noPR")
        acts.append('<div class="act i"><span class="verb">Build</span><span class="what">%s — no PR yet. '
                    'Red-team against the kill-list before building, and get the full local pipeline '
                    'green before the one push.</span></div>' % hs)
    if not acts:
        acts.append('<div class="act g"><span class="verb">Clear</span>'
                    '<span class="what">Nothing needs you right now.</span></div>')

    slots = []
    for r in sorted(rows, key=lambda x: ({"failing": 0, "running": 1, "noPR": 2,
                                          "accepted": 3, "ok": 4}[x["cls"]], x["repo"])):
        chip = {"accepted": ("g", "ACCEPTED"), "failing": ("c", "BLOCKED"),
                "running": ("w", "RUNNING"), "noPR": ("i", "NO PR"), "ok": ("n", "GREEN")}[r["cls"]]
        st = "".join('<span class="st %s" title="%s">%s</span>' % (e(b or "queued"), e(b or "queued"), e(n))
                     for n, b in order_stages(r["stages"])) or \
             '<span class="st">no checks reported</span>'
        pr = ("#%s" % r["pr"]) if r["pr"] else "—"
        labels = " ".join('<span class="chip n">%s</span>' % e(l) for l in r["labels"])
        slots.append(
            '<div class="slot"><div class="top"><span class="nm">%s</span>'
            '<span class="chip %s">%s</span>%s<span class="meta">%s</span></div>'
            '<div class="why">%s</div><div class="stages">%s</div></div>'
            % (e(r["repo"]), chip[0], chip[1], labels, pr, r["why"], st))

    return """<meta charset="utf-8">
<title>Task Desk</title>
<meta http-equiv="refresh" content="600">
<style>%s</style>
<header><div class="hd">
  <h1>Task Desk<span class="dot">_</span></h1>
  <span class="stamp">%s · org %s · %d repos · read-only sweep</span>
  <a class="desklink" href="%s" title="Your Claude Code session desk">SESSION DESK &#8599;</a>
  <a class="desklink" href="%s" target="_blank" rel="noopener" title="The authoring skill: hardness laws and the CI-stage map">SKILL &#8599;</a>
</div></header>
<div class="wrap">
  <div class="tiles">
    <div class="tile"><b>%d</b><span>slots</span></div>
    <div class="tile g"><b>%d</b><span>accepted</span></div>
    <div class="tile c"><b>%d</b><span>blocked</span></div>
    <div class="tile w"><b>%d</b><span>running</span></div>
    <div class="tile acc"><b>%d</b><span>no PR yet</span></div>
  </div>
  <h2>Action required</h2>
  %s
  <h2>Slots &middot; stage by stage</h2>
  %s
  <div class="legend">
    <span><span class="st pass">passed</span></span>
    <span><span class="st fail">failed</span></span>
    <span><span class="st pending">running</span></span>
    <span><span class="st">queued / skipped</span></span>
  </div>
  <h2>Reading this board</h2>
  <div class="note">
    <p><b>A block at any early stage skips every stage downstream, including <code>trials</code>.</b>
    So a failure in a five-minute prose field does not cost you a checkbox — it costs the whole
    difficulty measurement, and you learn that about three hours later. The stage strip above
    shows exactly where each PR stopped.</p>
    <p><b>Stages you can prove locally before pushing:</b> <code>review</code> (the 31-criterion
    rubric ships in your own repo), <code>validation</code> (preflight), <code>ava_review</code>
    (force every failure path and assert exit 0). Those should never fail in CI. See
    <code>references/ci-stages.md</code> in the skill for each one's fix.</p>
    <p><b>Never push while a run is in flight</b> — per-PR concurrency cancels it. And once a run
    is green, stop pushing: the LLM stages are non-deterministic and you can lose a pass you
    already earned.</p>
  </div>
</div>
""" % (CSS, now.strftime("%Y-%m-%d %H:%M"), e(org), len(rows), e(sessiondesk), e(skill_url),
       len(rows), n_accept, n_fail, n_run, n_nopr, "\n  ".join(acts), "\n  ".join(slots))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--org", default=os.environ.get("BENCH_ORG"),
                    help="GitHub org holding your task repos (or set BENCH_ORG)")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "taskdesk.html"))
    ap.add_argument("--skill-url", default="https://github.com/JrKrishh/benchmark-task-authoring")
    ap.add_argument("--session-desk", default="session-desk.html")
    a = ap.parse_args()
    if not a.org:
        sys.exit("error: pass --org <your-task-org> or set BENCH_ORG")
    t0 = time.time()
    print("sweeping %s ..." % a.org, file=sys.stderr)
    rows = sweep(a.org)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(render(rows, a.org, a.skill_url, a.session_desk))
    print("taskdesk.html: %d slots in %.1fs -> %s" % (len(rows), time.time() - t0, a.out))


if __name__ == "__main__":
    main()
