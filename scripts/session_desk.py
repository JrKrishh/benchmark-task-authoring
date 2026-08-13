#!/usr/bin/env python3
"""Session Desk — one dashboard over your agent sessions across tools.

Sources, and why only these two:
    Claude Code  ~/.claude/projects/*/*.jsonl   full transcripts + per-message usage
    Codex        ~/.codex/sessions/**/*.jsonl   rollout files + running token totals
Cursor and Antigravity are deliberately absent — Cursor's workspaceStorage holds UI
state with no token accounting, and Antigravity stores protobuf. Neither exposes a
transcript that could be reported honestly, so this does not guess at one.

Caches per-file stats keyed on (mtime,size); detects LIVE sessions via the pid lock
files in ~/.claude/sessions/; writes session-desk.html next to itself.

Modes:
    python session_desk.py             # build once, print a one-line summary
    python session_desk.py --watch 60  # rebuild every 60s (see below)
    python session_desk.py --hook      # silent, debounced (for a SessionStart hook)

The page carries a meta-refresh, but that only re-reads the file — it does not
regenerate it. Use --watch (or the hook) if you want the numbers to actually move.
"""
import ctypes, html, json, os, re, sys, time
from datetime import datetime, timedelta

HERE      = os.path.dirname(os.path.abspath(__file__))
CLAUDE    = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), ".claude")
PROJECTS  = os.path.join(CLAUDE, "projects")
LOCKS     = os.path.join(CLAUDE, "sessions")
OUT_HTML  = os.path.join(HERE, "session-desk.html")
CACHE_F   = os.path.join(HERE, ".session-desk-cache.json")
DEBOUNCE  = 60  # --hook: skip rebuild if html is fresher than this many seconds

HOOK = "--hook" in sys.argv
if HOOK and os.path.exists(OUT_HTML) and time.time() - os.path.getmtime(OUT_HTML) < DEBOUNCE:
    sys.exit(0)

# ---------- watch mode -----------------------------------------------------
# The page carries a meta-refresh, but that only re-reads the file on disk — it does
# NOT regenerate it. Without something rebuilding the file, the refresh shows the same
# numbers forever. This loop is that something.
if "--watch" in sys.argv:
    import subprocess
    argv = [a for a in sys.argv[1:] if a != "--watch" and not a.isdigit()]
    every = next((int(a) for a in sys.argv[1:] if a.isdigit()), 60)
    print("watching: rebuilding every %ds — Ctrl-C to stop" % every)
    try:
        while True:
            subprocess.run([sys.executable, os.path.abspath(__file__)] + argv)
            time.sleep(every)
    except KeyboardInterrupt:
        sys.exit(0)

# ---------- live pids ----------------------------------------------------
def pid_alive(pid):
    SYNCHRONIZE = 0x00100000
    h = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, 0, int(pid))
    if not h:
        return False
    ctypes.windll.kernel32.CloseHandle(h)
    return True

live = {}  # sessionId -> lock info
if os.path.isdir(LOCKS):
    for fn in os.listdir(LOCKS):
        if not fn.endswith(".json"):
            continue
        try:
            with open(os.path.join(LOCKS, fn), encoding="utf-8") as f:
                o = json.load(f)
            if o.get("sessionId") and pid_alive(o.get("pid", 0)):
                live[o["sessionId"]] = o
        except Exception:
            pass

# ---------- per-file parse (cached) --------------------------------------
try:
    with open(CACHE_F, encoding="utf-8") as f:
        cache = json.load(f)
except Exception:
    cache = {}

def parse_jsonl(path):
    s = dict(first=None, last=None, user=0, asst=0, tools=0,
             tok_in=0, tok_out=0, tok_cr=0, tok_cc=0,
             title=None, cwd=None, models={})
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            ts = o.get("timestamp")
            if ts:
                if s["first"] is None:
                    s["first"] = ts
                s["last"] = ts
            if s["cwd"] is None and o.get("cwd"):
                s["cwd"] = o["cwd"]
            if t == "user":
                s["user"] += 1
            elif t == "assistant":
                s["asst"] += 1
                m = o.get("message") or {}
                u = m.get("usage") or {}
                s["tok_in"]  += u.get("input_tokens", 0) or 0
                s["tok_out"] += u.get("output_tokens", 0) or 0
                s["tok_cr"]  += u.get("cache_read_input_tokens", 0) or 0
                s["tok_cc"]  += u.get("cache_creation_input_tokens", 0) or 0
                mdl = m.get("model")
                if mdl:
                    s["models"][mdl] = s["models"].get(mdl, 0) + 1
                for blk in (m.get("content") or []):
                    if isinstance(blk, dict) and blk.get("type") == "tool_use":
                        s["tools"] += 1
            elif t in ("ai-title", "custom-title"):
                s["title"] = o.get("aiTitle") or o.get("customTitle") or s["title"]
    return s

def parse_codex_jsonl(path):
    """Codex rollout files: ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl.

    Different shape from Claude's transcripts — one `session_meta` header, then
    events. Token usage arrives as a running TOTAL in `payload.info.total_token_usage`,
    so the last one wins rather than summing per message.
    """
    s = dict(first=None, last=None, user=0, asst=0, tools=0,
             tok_in=0, tok_out=0, tok_cr=0, tok_cc=0,
             title=None, cwd=None, models={})
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                o = json.loads(line)
            except Exception:
                continue
            ts = o.get("timestamp")
            if ts:
                if s["first"] is None:
                    s["first"] = ts
                s["last"] = ts
            p = o.get("payload") or {}
            if not isinstance(p, dict):
                continue
            t = o.get("type")
            if t == "session_meta":
                s["cwd"] = p.get("cwd") or s["cwd"]
                mdl = p.get("model") or p.get("model_provider")
                if mdl:
                    s["models"][str(mdl)] = s["models"].get(str(mdl), 0) + 1
            elif t == "response_item":
                role = (p.get("role") or "").lower()
                if role == "user":
                    s["user"] += 1
                elif role == "assistant":
                    s["asst"] += 1
                if p.get("type") in ("function_call", "local_shell_call", "custom_tool_call"):
                    s["tools"] += 1
            info = p.get("info")
            if isinstance(info, dict):
                tot = info.get("total_token_usage")
                if isinstance(tot, dict):          # running total: overwrite, never add
                    s["tok_in"] = tot.get("input_tokens", 0) or 0
                    s["tok_out"] = tot.get("output_tokens", 0) or 0
                    s["tok_cr"] = tot.get("cached_input_tokens", 0) or 0
                    s["tok_cc"] = tot.get("cache_write_input_tokens", 0) or 0
            if s["title"] is None:
                for k in ("title", "summary"):
                    if isinstance(p.get(k), str) and p[k].strip():
                        s["title"] = p[k].strip()[:110]
                        break
    return s


sessions = []
seen_keys = set()
if os.path.isdir(PROJECTS):
    for proj in os.listdir(PROJECTS):
        pdir = os.path.join(PROJECTS, proj)
        if not os.path.isdir(pdir):
            continue
        for fn in os.listdir(pdir):
            if not fn.endswith(".jsonl"):
                continue
            path = os.path.join(pdir, fn)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if st.st_size < 200:          # empty shells
                continue
            key = path
            seen_keys.add(key)
            c = cache.get(key)
            if c and c["mtime"] == st.st_mtime and c["size"] == st.st_size:
                s = c["stats"]
            else:
                s = parse_jsonl(path)
                cache[key] = {"mtime": st.st_mtime, "size": st.st_size, "stats": s}
            sid = fn[:-6]
            sessions.append(dict(s, sid=sid, projdir=proj, size=st.st_size,
                                 mtime=st.st_mtime, live=sid in live, src="claude"))

# ---------- Codex sessions -------------------------------------------------
# Cursor and Antigravity are deliberately absent: Cursor's workspaceStorage holds UI
# state with no token accounting, and Antigravity stores protobuf. Neither exposes a
# transcript we could report honestly, so we do not guess at one.
CODEX = os.path.join(os.environ.get("USERPROFILE", os.path.expanduser("~")), ".codex", "sessions")
if os.path.isdir(CODEX):
    for root, _dirs, files in os.walk(CODEX):
        for fn in files:
            if not fn.endswith(".jsonl"):
                continue
            path = os.path.join(root, fn)
            try:
                st = os.stat(path)
            except OSError:
                continue
            if st.st_size < 200:
                continue
            seen_keys.add(path)
            c = cache.get(path)
            if c and c["mtime"] == st.st_mtime and c["size"] == st.st_size:
                s = c["stats"]
            else:
                try:
                    s = parse_codex_jsonl(path)
                except Exception:
                    continue
                cache[path] = {"mtime": st.st_mtime, "size": st.st_size, "stats": s}
            sid = fn[:-6]
            sessions.append(dict(s, sid=sid, projdir="codex", size=st.st_size,
                                 mtime=st.st_mtime, live=False, src="codex"))

cache = {k: v for k, v in cache.items() if k in seen_keys}
with open(CACHE_F, "w", encoding="utf-8") as f:
    json.dump(cache, f)

# ---------- shape the data ------------------------------------------------
def loc(ts):   # ISO-Z -> local datetime
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except Exception:
        return None

def projname(s):
    cwd = s.get("cwd") or ""
    if cwd:
        return cwd.replace("\\", "/").rstrip("/").split("/")[-1] or cwd
    return s["projdir"]

def short_model(models):
    if not models:
        return "—"
    m = max(models, key=models.get)
    return m.replace("claude-", "")

now = datetime.now().astimezone()
today0 = now.replace(hour=0, minute=0, second=0, microsecond=0)
week0 = today0 - timedelta(days=6)

rows = []
for s in sessions:
    a, b = loc(s["first"] or ""), loc(s["last"] or "")
    if not a or not b:
        continue
    dur = (b - a).total_seconds()
    rows.append(dict(
        sid=s["sid"], proj=projname(s), title=s["title"] or "(untitled)",
        start=a, end=b, dur=dur, user=s["user"], asst=s["asst"], tools=s["tools"],
        tin=s["tok_in"], tout=s["tok_out"], tcr=s["tok_cr"], tcc=s["tok_cc"],
        model=short_model(s["models"]), live=s["live"], src=s.get("src","claude")))
rows.sort(key=lambda r: r["end"], reverse=True)

n_live  = sum(r["live"] for r in rows)
n_today = sum(r["start"] >= today0 for r in rows)
n_week  = sum(r["start"] >= week0 for r in rows)
tout_today = sum(r["tout"] for r in rows if r["end"] >= today0)
tout_all   = sum(r["tout"] for r in rows)
ttot_all   = sum(r["tin"] + r["tcr"] + r["tcc"] for r in rows)
hrs_week   = sum(min(r["dur"], 12 * 3600) for r in rows if r["end"] >= week0) / 3600

days = []
for i in range(13, -1, -1):
    d0 = today0 - timedelta(days=i)
    d1 = d0 + timedelta(days=1)
    ds = [r for r in rows if d0 <= r["start"] < d1]
    days.append(dict(label=d0.strftime("%d %b" if (i == 13 or d0.day == 1) else "%d"),
                     n=len(ds), tout=sum(r["tout"] for r in ds)))

pcount = {}
for r in rows:
    p = pcount.setdefault(r["proj"], dict(n=0, tout=0, live=0))
    p["n"] += 1; p["tout"] += r["tout"]; p["live"] += r["live"]
top_proj = sorted(pcount.items(), key=lambda kv: -kv[1]["n"])[:10]

def fmt_tok(n):
    # Cache-read totals cross a billion quickly; without a B step this renders as
    # "23477.6M", which is both unreadable and too wide for its tile.
    if n >= 1e9:  return f"{n/1e9:.1f}B"
    if n >= 1e6:  return f"{n/1e6:.1f}M"
    if n >= 1000: return f"{n/1e3:.0f}k"
    return str(n)

def fmt_dur(sec):
    sec = int(sec)
    if sec >= 3600: return f"{sec//3600}h {sec%3600//60:02d}m"
    if sec >= 60:   return f"{sec//60}m"
    return f"{sec}s"

def esc(x): return html.escape(str(x), quote=True)

LEDGER = [dict(
    sid=r["sid"][:8], proj=esc(r["proj"]), title=esc(r["title"][:110]),
    start=r["start"].strftime("%d %b %H:%M"), dur=fmt_dur(r["dur"]),
    msgs=f'{r["user"]}/{r["asst"]}', tools=r["tools"],
    tout=fmt_tok(r["tout"]), ttot=fmt_tok(r["tin"] + r["tcr"] + r["tcc"] + r["tout"]),
    model=esc(r["model"]), live=r["live"], src=esc(r.get("src","claude")),
    today=r["start"] >= today0, week=r["start"] >= week0,
) for r in rows[:400]]

live_cards = "".join(f"""
  <div class="card"><div class="top"><span class="nm">{esc(r['proj'])}</span>
    <span class="p5">{fmt_dur((now-r['start']).total_seconds())} old</span></div>
    <div class="sub">{esc(r['title'][:90])}</div>
    <div class="st"><span class="chip g">LIVE</span>
      <span class="mini">last activity {fmt_dur((now-r['end']).total_seconds())} ago · {fmt_tok(r['tout'])} out</span></div>
  </div>""" for r in rows if r["live"]) or '<div class="colnote">No live sessions right now.</div>'

mx_n   = max((d["n"] for d in days), default=1) or 1
mx_t   = max((d["tout"] for d in days), default=1) or 1
day_bars = "".join(
    f'<div class="dcol"><div class="dbar" style="height:{max(3,round(d["n"]/mx_n*72))}px" title="{d["n"]} sessions"></div>'
    f'<div class="dbar t" style="height:{max(2,round(d["tout"]/mx_t*72))}px" title="{fmt_tok(d["tout"])} output tokens"></div>'
    f'<span class="dlab">{d["label"]}</span></div>'
    for d in days)

mx_p = max((v["n"] for _, v in top_proj), default=1) or 1
proj_bars = "".join(
    f'<div class="brow"><span class="lbl">{esc(k[:22])}</span>'
    f'<div class="btrack"><div class="bfill" style="width:{round(v["n"]/mx_p*100)}%"></div></div>'
    f'<span class="val">{v["n"]}</span></div>'
    for k, v in top_proj)

page = f"""<meta charset="utf-8">
<title>Claude Session Desk</title>
<meta http-equiv="refresh" content="60">
<style>
  :root{{
    --bg:#151920; --surface:#1c222b; --surface2:#212936; --line:#2b3340; --line2:#39424f;
    --ink:#e9e6dd; --muted:#98a0ad; --faint:#6b7480;
    --accent:#e2a75c; --accent-ink:#151920;
    --good:#66b98a; --warn:#d9a441; --crit:#d97a6c; --info:#7aa5d8; --neut:#8b93a1;
    --good-bg:rgba(102,185,138,.13); --info-bg:rgba(122,165,216,.13); --neut-bg:rgba(139,147,161,.12);
    --bar:#c98f45; --bar2:#7aa5d8;
    --mono:"Cascadia Code","Consolas",ui-monospace,SFMono-Regular,Menlo,monospace;
    --sans:"Segoe UI",system-ui,-apple-system,sans-serif;
  }}
  @media (prefers-color-scheme: light){{
    :root:not([data-theme="dark"]){{
      --bg:#f1efe9; --surface:#fbfaf7; --surface2:#eeebe2; --line:#dcd7cb; --line2:#c9c3b4;
      --ink:#262a31; --muted:#676e79; --faint:#8d93a0; --accent:#a06f24; --accent-ink:#fbfaf7;
      --good:#2e7d4f; --warn:#95680f; --crit:#b0492f; --info:#33648f; --neut:#6c7480;
      --good-bg:rgba(46,125,79,.10); --info-bg:rgba(51,100,143,.10); --neut-bg:rgba(108,116,128,.10);
      --bar:#b07c2e; --bar2:#33648f;
    }}
  }}
  :root[data-theme="light"]{{
      --bg:#f1efe9; --surface:#fbfaf7; --surface2:#eeebe2; --line:#dcd7cb; --line2:#c9c3b4;
      --ink:#262a31; --muted:#676e79; --faint:#8d93a0; --accent:#a06f24; --accent-ink:#fbfaf7;
      --good:#2e7d4f; --warn:#95680f; --crit:#b0492f; --info:#33648f; --neut:#6c7480;
      --good-bg:rgba(46,125,79,.10); --info-bg:rgba(51,100,143,.10); --neut-bg:rgba(108,116,128,.10);
      --bar:#b07c2e; --bar2:#33648f;
  }}
  *{{box-sizing:border-box}}
  body{{background:var(--bg);color:var(--ink);font-family:var(--sans);margin:0;font-size:14.5px;line-height:1.5}}
  .wrap{{max-width:1180px;margin:0 auto;padding:0 20px 64px}}
  header{{border-bottom:1px solid var(--line);background:var(--surface)}}
  .hd{{max-width:1180px;margin:0 auto;padding:18px 20px 14px;display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 24px}}
  .hd h1{{font:600 17px/1.2 var(--mono);letter-spacing:.14em;margin:0;text-transform:uppercase}}
  .hd h1 .dot{{color:var(--accent)}}
  .stamp{{font:400 12px var(--mono);color:var(--muted)}}
  .desklink{{font:600 11px var(--mono);letter-spacing:.1em;color:var(--accent);text-decoration:none;
            border:1px solid var(--line);border-radius:5px;padding:4px 10px;white-space:nowrap}}
  .desklink:hover{{border-color:var(--accent)}}
  .desklink:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .links{{display:flex;gap:8px;margin-left:auto}}
  .tiles{{--tile-min:150px}}
  h2{{font:600 12px var(--mono);letter-spacing:.16em;text-transform:uppercase;color:var(--muted);margin:34px 0 12px;display:flex;align-items:center;gap:10px}}
  h2::after{{content:"";flex:1;height:1px;background:var(--line)}}
  .tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(var(--tile-min),1fr));gap:10px;margin-top:22px}}
  .tile{{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px 10px}}
  .tile b{{display:block;font:600 26px/1.1 var(--mono);font-variant-numeric:tabular-nums}}
  .tile span{{font-size:11.5px;color:var(--muted)}}
  .tile.g b{{color:var(--good)}} .tile.acc b{{color:var(--accent)}} .tile.i b{{color:var(--info)}}
  .cards{{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:10px}}
  .card{{border:1px solid var(--line);border-radius:6px;padding:10px 12px;background:var(--surface)}}
  .card .top{{display:flex;justify-content:space-between;gap:8px;align-items:baseline}}
  .card .nm{{font:600 13px var(--mono)}}
  .card .p5{{font:400 11.5px var(--mono);color:var(--muted);white-space:nowrap}}
  .card .sub{{font-size:12px;color:var(--muted);margin-top:3px;min-height:2.6em}}
  .card .st{{margin-top:7px;display:flex;align-items:center;gap:8px}}
  .card .mini{{font-size:11px;color:var(--faint)}}
  .chip{{display:inline-block;font:600 10.5px var(--mono);letter-spacing:.05em;border-radius:4px;padding:1.5px 7px}}
  .chip.g{{color:var(--good);background:var(--good-bg)}} .chip.n{{color:var(--neut);background:var(--neut-bg)}}
  .colnote{{font-size:12px;color:var(--faint)}}
  .charts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
  .chart{{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:16px 18px}}
  .chart h3{{font:600 12.5px var(--sans);margin:0 0 2px}}
  .chart .cap{{font-size:11.5px;color:var(--muted);margin-bottom:14px}}
  .dgrid{{display:flex;align-items:flex-end;gap:6px;height:100px}}
  .dcol{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:2px;min-width:0}}
  .dbar{{width:60%;border-radius:3px 3px 0 0;background:var(--bar)}}
  .dbar.t{{background:var(--bar2);width:60%;opacity:.75}}
  .dlab{{font:400 9.5px var(--mono);color:var(--faint);white-space:nowrap}}
  .legend{{display:flex;gap:16px;margin-top:12px;font-size:11.5px;color:var(--muted)}}
  .sw{{display:inline-block;width:10px;height:10px;border-radius:2px;vertical-align:-1px;margin-right:5px}}
  .brow{{display:grid;grid-template-columns:150px 1fr 40px;align-items:center;gap:10px;margin-bottom:7px}}
  .brow .lbl{{font-size:12px;text-align:right;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
  .btrack{{height:14px;border-radius:3px;background:var(--surface2);position:relative;overflow:hidden}}
  .bfill{{position:absolute;inset:0 auto 0 0;border-radius:3px;background:var(--bar);min-width:2px}}
  .brow .val{{font:600 12px var(--mono);color:var(--muted);font-variant-numeric:tabular-nums}}
  .filters{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;align-items:center}}
  .fbtn{{font:600 11px var(--mono);letter-spacing:.06em;border:1px solid var(--line);background:var(--surface);color:var(--muted);border-radius:5px;padding:5px 11px;cursor:pointer}}
  .fbtn:hover{{border-color:var(--line2);color:var(--ink)}}
  .fbtn[aria-pressed="true"]{{background:var(--accent);border-color:var(--accent);color:var(--accent-ink)}}
  .fbtn:focus-visible,#q:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  #q{{font:400 12.5px var(--mono);background:var(--surface);border:1px solid var(--line);color:var(--ink);border-radius:5px;padding:5.5px 10px;width:220px}}
  .count{{font:400 11.5px var(--mono);color:var(--faint);margin-left:auto}}
  .tablewrap{{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--surface)}}
  table{{border-collapse:collapse;width:100%;min-width:980px;font-size:12.5px}}
  th{{font:600 10.5px var(--mono);letter-spacing:.1em;text-transform:uppercase;color:var(--muted);text-align:left;padding:9px 12px;border-bottom:1px solid var(--line2);white-space:nowrap}}
  td{{padding:7px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
  tr:last-child td{{border-bottom:0}}
  td.mono{{font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}}
  td .t2{{color:var(--muted);font-size:11.5px}}
</style>
<header><div class="hd">
  <h1>Claude Session Desk<span class="dot">_</span></h1>
  <span class="stamp">generated {now.strftime("%Y-%m-%d %H:%M:%S")} · auto-refreshes every 60s · regenerated on every Claude Code launch</span>
  <a class="desklink" id="taskdesk" href="taskdesk.html" title="Task desk — per-slot review stage and what each needs">TASK DESK ↗</a>
  <a class="desklink" href="https://github.com/JrKrishh/benchmark-task-authoring" target="_blank" rel="noopener" title="benchmark-task-authoring — hardness laws, the 17-stage CI map, local retrieval">SKILL ↗</a>
</div></header>
<div class="wrap">
  <div class="tiles">
    <div class="tile g"><b>{n_live}</b><span>live now</span></div>
    <div class="tile acc"><b>{n_today}</b><span>sessions today</span></div>
    <div class="tile"><b>{n_week}</b><span>sessions this week</span></div>
    <div class="tile"><b>{len(rows)}</b><span>sessions all time</span></div>
    <div class="tile i"><b>{fmt_tok(tout_today)}</b><span>output tokens today</span></div>
    <div class="tile"><b>{fmt_tok(tout_all)}</b><span>output tokens all time</span></div>
    <div class="tile"><b>{fmt_tok(ttot_all)}</b><span>input+cache all time</span></div>
    <div class="tile"><b>{hrs_week:.0f}h</b><span>session span this week</span></div>
  </div>

  <h2>Live sessions</h2>
  <div class="cards">{live_cards}</div>

  <h2>Activity — last 14 days</h2>
  <div class="charts">
    <div class="chart" style="grid-column:1/-1">
      <h3>Sessions started &amp; output tokens per day</h3>
      <div class="cap">amber = sessions started · blue = output tokens (each scaled to its own max — read shape, not cross-height)</div>
      <div class="dgrid">{day_bars}</div>
      <div class="legend"><span><span class="sw" style="background:var(--bar)"></span>sessions</span>
        <span><span class="sw" style="background:var(--bar2)"></span>output tokens</span></div>
    </div>
    <div class="chart">
      <h3>Sessions per project — top 10</h3>
      <div class="cap">all time · {len(pcount)} projects seen</div>
      {proj_bars}
    </div>
    <div class="chart">
      <h3>Reading this desk</h3>
      <div class="cap" style="margin-bottom:6px">plumbing, so future-you trusts the numbers</div>
      <div class="colnote" style="line-height:1.6">
        Live = a session lock in <span style="font-family:var(--mono)">~/.claude/sessions</span> whose PID is still running.
        Tokens are summed from every assistant message's usage block in the transcript.
        Session span = first→last message timestamp (capped at 12h/session for the weekly figure).
        Ledger shows the 400 most recent sessions. Data source:
        <span style="font-family:var(--mono)">~/.claude/projects/*/*.jsonl</span>, incremental cache in
        <span style="font-family:var(--mono)">.session-desk-cache.json</span>.
      </div>
    </div>
  </div>

  <h2>Session ledger</h2>
  <div class="filters" role="group" aria-label="Filter sessions">
    <button class="fbtn" aria-pressed="false" data-f="live">LIVE</button>
    <button class="fbtn" aria-pressed="true"  data-f="today">TODAY</button>
    <button class="fbtn" aria-pressed="false" data-f="week">WEEK</button>
    <button class="fbtn" aria-pressed="false" data-f="all">ALL</button>
    <input id="q" type="search" placeholder="search title / project…" aria-label="Search sessions">
    <span class="count" id="count"></span>
  </div>
  <div class="tablewrap"><table id="ledger">
    <thead><tr><th>Session</th><th>Project</th><th>Title</th><th>Started</th><th>Span</th>
    <th>Src</th><th>Msgs u/a</th><th>Tools</th><th>Tok out</th><th>Tok total</th><th>Model</th></tr></thead>
    <tbody></tbody>
  </table></div>
</div>
<script>
const ROWS = {json.dumps(LEDGER)};
const tb = document.querySelector('#ledger tbody');
function render(f,q){{
  tb.innerHTML=''; let n=0; q=(q||'').toLowerCase();
  for(const r of ROWS){{
    if(f==='live'&&!r.live) continue;
    if(f==='today'&&!r.today) continue;
    if(f==='week'&&!r.week) continue;
    if(q && !(r.title+' '+r.proj).toLowerCase().includes(q)) continue;
    n++;
    const tr=document.createElement('tr');
    tr.innerHTML=`<td class="mono">${{r.live?'<span class="chip g">LIVE</span> ':''}}${{r.sid}}</td>
      <td class="mono">${{r.proj}}</td><td>${{r.title}}</td>
      <td class="mono">${{r.start}}</td><td class="mono">${{r.dur}}</td>
      <td class="mono"><span class="chip ${{r.src==='codex'?'n':'g'}}">${{r.src}}</span></td><td class="mono">${{r.msgs}}</td><td class="mono">${{r.tools}}</td>
      <td class="mono">${{r.tout}}</td><td class="mono">${{r.ttot}}</td>
      <td class="mono"><span class="t2">${{r.model}}</span></td>`;
    tb.appendChild(tr);
  }}
  document.getElementById('count').textContent=n+' shown';
}}
let curF='today';
document.querySelectorAll('.fbtn').forEach(b=>b.addEventListener('click',()=>{{
  curF=b.dataset.f;
  document.querySelectorAll('.fbtn').forEach(x=>x.setAttribute('aria-pressed',x===b?'true':'false'));
  render(curF,document.getElementById('q').value);
}}));
document.getElementById('q').addEventListener('input',e=>render(curF,e.target.value));
render('today','');
// dual-context link: local file when viewed locally, sibling artifact when hosted
if(location.protocol!=='file:'){{
  const dl=document.getElementById('taskdesk');
  dl.href='https://claude.ai/code/artifact/f163cc56-f5d7-48b8-be17-c0e319aa959d';
  dl.title='Task desk (hosted)';
  document.querySelector('.stamp').textContent+=' · hosted snapshot — local copy is freshest';
}}
</script>
"""

with open(OUT_HTML, "w", encoding="utf-8") as f:
    f.write(page)

if not HOOK:
    print(f"session-desk.html: {len(rows)} sessions ({n_live} live), "
          f"{fmt_tok(tout_all)} output tokens all time -> {OUT_HTML}")
