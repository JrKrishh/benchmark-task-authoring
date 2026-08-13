#!/usr/bin/env python
"""
dr.py - local retrieval + cache for the benchmark task-authoring corpus.

The corpus (~900 KB / ~228k tokens of memory files, proposals, rules and the
program reference) does not fit in a context window, and re-reading whole
war-chest narratives to re-extract a handful of transferable laws is where the
tokens go.  This indexes the corpus as atomic cards and answers a question with
a token-budgeted slice of it.

Query path deliberately avoids torch/sentence_transformers (17s of imports) and
runs the exported ONNX encoder instead (~0.7s cold, ~10ms warm).

Commands
  index     build/refresh the index (incremental: only changed chunks embed)
  ask       retrieve cards for a question, budgeted to a token ceiling
  boot      the fixed minimal pack to load at session start
  laws      the distilled, deduplicated law deck
  check     precheck a draft proposal against the laws it is likely to break
  cache     derived-artifact cache (preflight/probe results keyed by content)
  stats     corpus and savings report
"""
from __future__ import print_function

import argparse
import hashlib
import io
import json
import math
import os
import re
import sqlite3
import sys
import time
import zlib
from collections import Counter, defaultdict

# ---------------------------------------------------------------- console ---
# The corpus is full of emoji markers; cp1252 stdout on Windows would abort.
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
MODELS = os.path.join(HERE, "models")
DB = os.path.join(CACHE, "index.sqlite")
SKILL = os.path.abspath(os.path.join(HERE, ".."))        # the skill root (…/benchmark-task-authoring)
HACK = os.environ.get("BENCH_WORK", SKILL)              # your working dir: proposals, design records
MEM = os.environ.get("BENCH_MEM", "")                   # your own notes dir; empty until you have one

# Where the corpus lives, and how much each class is worth at retrieval time.
# A measured law outranks the narrative that produced it.
#
# The first block is the skill's own bundled references, so retrieval works on a
# fresh install with no notes of your own: index once and every query against the
# field manual costs ~1-2k tokens instead of the ~35k a full read would.
# The second block picks up your notes and working files as they accumulate —
# set BENCH_MEM (notes) and BENCH_WORK (proposals/design records) to enable it.
SOURCES = [
    # (glob-root, pattern, doc_class, weight)
    (os.path.join(SKILL, "references"), r"^hardness-laws\.md$", "law", 1.45),
    (os.path.join(SKILL, "references", "rules"), r"\.md$", "rule", 1.35),
    (os.path.join(SKILL, "references"), r"^claiming\.md$", "reference", 1.15),
    (SKILL, r"^SKILL\.md$", "rule", 1.30),
    (os.path.join(SKILL, "assets"), r"\.md$", "reference", 1.10),
]
if MEM:
    SOURCES += [
        # Any note whose filename ends -law.md is treated as a distilled, transferable
        # law rather than the narrative that produced it, and ranked above war-chests.
        # Match order matters: this must precede the generic pattern below.
        (MEM, r"^the program-.*-law\.md$", "law", 1.38),
        (MEM, r"^the program-.*\.md$", "warchest", 1.00),
        (MEM, r"\.md$", "warchest", 0.95),
    ]
if HACK != SKILL:
    SOURCES += [
        (HACK, r"^proposal-.*\.md$", "proposal", 0.85),
        (HACK, r"^design-.*\.md$", "case", 1.10),
        (os.path.join(HACK, "design-records"), r"\.md$", "case", 1.10),
    ]

# Cards carrying these markers are laws, not narration.
SALIENCE = [
    (re.compile(r"⭐"), 0.55),
    (re.compile(r"🚨"), 0.55),
    (re.compile(r"⚠️|⚠"), 0.35),
    (re.compile(r"\bLAW\b"), 0.45),
    (re.compile(r"kill[- ]list", re.I), 0.40),
    (re.compile(r"\b(never|always|non-negotiable|standing rule)\b", re.I), 0.25),
    (re.compile(r"\b(measured|MEASURED)\b"), 0.20),
    (re.compile(r"\bdo not push\b", re.I), 0.15),
    (re.compile(r"\bpost-?mortem\b", re.I), 0.20),
]

TASK_RE = re.compile(r"\b([0-9a-f]{7})\b")
HEAD_RE = re.compile(r"^(#{1,4})\s+(.*)$")
TARGET = 1100      # chars per card before splitting
MIN_CARD = 180     # merge anything smaller into its neighbour
HEAD_MAX = 120     # some headings in this corpus are a full paragraph; they would
                   # otherwise be repeated onto every sub-card and dominate BM25
SATURATION = 0.55  # per-file discount for each card a source has already placed
SCORER = "v3-cov-phrase-sat"   # bump on any ranking change; keys the query cache
                               # so tuning can never be masked by a stale answer
STOP = set("""a an the and or but if then else of to in on at for with without by from as is are was
were be been being it its this that these those we you they i he she not no do does did done have has
had can could should would will shall may might must so such than too very just only also more most
other some any each which who whom what when where why how all both few many own same s t don now""".split())


def die(msg):
    print("error: " + msg, file=sys.stderr)
    sys.exit(1)


def sha(s):
    if not isinstance(s, bytes):
        s = s.encode("utf-8", "replace")
    return hashlib.sha1(s).hexdigest()


def toks(n):
    """Cheap token estimate. Deliberately conservative (over-counts slightly)."""
    return int(len(n) / 3.7) + 1


def words(s):
    return [w for w in re.findall(r"[a-z0-9_@#]+", s.lower()) if w not in STOP and len(w) > 1]


def phrases(s, n=3):
    """Contiguous content-word n-grams, for verbatim-match scoring."""
    w = words(s)
    return [" ".join(w[i:i + k]) for k in (n, n - 1) for i in range(len(w) - k + 1)]


# ------------------------------------------------------------------- store ---
def db():
    if not os.path.isdir(CACHE):
        os.makedirs(CACHE)
    c = sqlite3.connect(DB)
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
    CREATE TABLE IF NOT EXISTS chunk(
        id INTEGER PRIMARY KEY, hash TEXT UNIQUE, file TEXT, rel TEXT, line INT,
        doc_class TEXT, weight REAL, heading TEXT, task TEXT, salience REAL,
        text TEXT, ntok INT);
    CREATE TABLE IF NOT EXISTS emb(hash TEXT PRIMARY KEY, vec BLOB);
    CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
    CREATE TABLE IF NOT EXISTS qcache(k TEXT PRIMARY KEY, out TEXT, ts REAL, hits INT DEFAULT 0);
    CREATE TABLE IF NOT EXISTS artifact(
        k TEXT PRIMARY KEY, fingerprint TEXT, body BLOB, note TEXT, ts REAL, hits INT DEFAULT 0);
    CREATE TABLE IF NOT EXISTS usage(ts REAL, cmd TEXT, saved INT, spent INT);
    CREATE INDEX IF NOT EXISTS chunk_task ON chunk(task);
    CREATE INDEX IF NOT EXISTS chunk_class ON chunk(doc_class);
    """)
    return c


def mget(c, k, d=None):
    r = c.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
    return r[0] if r else d


def mset(c, k, v):
    c.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (k, str(v)))


# ---------------------------------------------------------------- chunking ---
def discover():
    out = []
    seen = set()
    for root, pat, klass, w in SOURCES:
        if not os.path.isdir(root):
            continue
        rx = re.compile(pat)
        for fn in sorted(os.listdir(root)):
            p = os.path.join(root, fn)
            if not os.path.isfile(p) or not rx.search(fn):
                continue
            if p.lower() in seen:
                continue
            seen.add(p.lower())
            out.append((p, klass, w))
    return out


def split_md(text):
    """Markdown -> [(heading_path, body_first_line, [lines])] on headings 1-4.

    Carries the true 1-based file line of the body's first line so every card
    can cite a position that actually resolves in the source.
    """
    lines = text.splitlines()
    stack, secs, buf, fence = [], [], [], False
    head, bstart = "", 1
    for i, ln in enumerate(lines, 1):
        if ln.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else HEAD_RE.match(ln)
        if m:
            if buf:
                secs.append((head, bstart, buf))
            lvl = len(m.group(1))
            title = m.group(2).strip()
            if len(title) > HEAD_MAX:
                title = title[:HEAD_MAX].rsplit(" ", 1)[0] + "…"
            stack[:] = stack[:lvl - 1]
            while len(stack) < lvl - 1:
                stack.append("")
            stack.append(title)
            head = " > ".join([s for s in stack if s])
            buf, bstart = [], i + 1
        else:
            buf.append(ln)
    if buf:
        secs.append((head, bstart, buf))
    return [(h, s, b) for h, s, b in secs if any(x.strip() for x in b) or h]


def subsplit(lines, limit):
    """Break an oversized section at paragraph/bullet boundaries.

    Returns [(line_offset_within_section, text)] with exact offsets, so a card
    from the middle of a long section still cites its own line.
    """
    # group into paragraphs, each tagged with its offset
    paras, cur, cs, fence = [], [], 0, False
    for i, ln in enumerate(lines):
        if ln.lstrip().startswith("```"):
            fence = not fence
        if not cur:
            cs = i
        cur.append(ln)
        if not fence and not ln.strip():
            paras.append((cs, cur))
            cur = []
    if cur:
        paras.append((cs, cur))
    if not paras:
        return []

    out, acc, aoff = [], [], None
    for off, p in paras:
        clen = sum(len(x) + 1 for x in acc)
        if acc and clen + sum(len(x) + 1 for x in p) > limit:
            out.append((aoff, acc))
            acc, aoff = list(p), off
        else:
            if aoff is None:
                aoff = off
            acc.extend(p)
    if acc:
        out.append((aoff, acc))

    # trim blank edges (adjusting the offset), then absorb slivers
    trimmed = []
    for off, ls in out:
        k = 0
        while k < len(ls) and not ls[k].strip():
            k += 1
        end = len(ls)
        while end > k and not ls[end - 1].strip():
            end -= 1
        if end > k:
            trimmed.append((off + k, "\n".join(ls[k:end])))
    merged = []
    for off, t in trimmed:
        if merged and len(t) < MIN_CARD:
            merged[-1] = (merged[-1][0], merged[-1][1] + "\n" + t)
        else:
            merged.append((off, t))
    return merged


def salience(text, heading, klass):
    s = 0.0
    both = heading + "\n" + text
    for rx, v in SALIENCE:
        if rx.search(both):
            s += v
    if klass in ("law", "rule"):
        s += 0.25
    return min(s, 2.0)


def build_cards():
    cards = []
    for path, klass, w in discover():
        try:
            with io.open(path, encoding="utf-8", errors="replace") as f:
                raw = f.read()
        except Exception:
            continue
        # Strip YAML frontmatter. A skill/note header is metadata about the file,
        # not content from it — and a description listing every keyword in the
        # domain otherwise wins slot 1 on nearly every query and returns noise.
        if raw.startswith("---\n"):
            end = raw.find("\n---\n", 4)
            if end != -1:
                blank = "\n" * (raw.count("\n", 0, end + 5))  # keep line numbers honest
                raw = blank + raw[end + 5:]
        rel = os.path.relpath(path, HACK) if path.lower().startswith(HACK.lower()) else "memory/" + os.path.basename(path)
        rel = rel.replace("\\", "/")
        ftask = TASK_RE.search(os.path.basename(path))
        for head, bstart, blines in split_md(raw):
            for off, part in subsplit(blines, TARGET):
                cline = bstart + off      # the sub-card's own line, not the heading's
                if len(part.strip()) < 40 and not head:
                    continue
                full = (("### " + head + "\n") if head else "") + part
                m = TASK_RE.search(head) or TASK_RE.search(part[:400]) or ftask
                cards.append(dict(
                    hash=sha(rel + "|" + head + "|" + part),
                    file=path, rel=rel, line=cline, doc_class=klass, weight=w,
                    heading=head, task=(m.group(1) if m else ""),
                    salience=salience(part, head, klass),
                    text=full, ntok=toks(full)))
    return cards


# ------------------------------------------------------------------ encode ---
_ENC = [None]


def encoder():
    """ONNX encoder; ~0.7s cold. Falls back to sentence_transformers if absent."""
    if _ENC[0]:
        return _ENC[0]
    onnx = os.path.join(MODELS, "bge-small.onnx")
    tokj = os.path.join(MODELS, "tokenizer.json")
    if os.path.exists(onnx) and os.path.exists(tokj):
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer
        tk = Tokenizer.from_file(tokj)
        tk.enable_truncation(512)
        so = ort.SessionOptions()
        so.log_severity_level = 3
        sess = ort.InferenceSession(onnx, so, providers=["CPUExecutionProvider"])

        def enc(texts, bs=16):
            outs = []
            for i in range(0, len(texts), bs):
                chunk = texts[i:i + bs]
                e = [tk.encode(x) for x in chunk]
                L = max(len(x.ids) for x in e)
                ids = np.array([x.ids + [0] * (L - len(x.ids)) for x in e], dtype=np.int64)
                am = np.array([x.attention_mask + [0] * (L - len(x.attention_mask)) for x in e], dtype=np.int64)
                h = sess.run(None, {"input_ids": ids, "attention_mask": am,
                                    "token_type_ids": np.zeros_like(ids)})[0]
                v = h[:, 0].astype("float32")           # bge uses CLS pooling
                v /= (np.linalg.norm(v, axis=1, keepdims=True) + 1e-9)
                outs.append(v)
            return np.vstack(outs)
        _ENC[0] = enc
        return enc
    # fallback
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")
    _ENC[0] = lambda t, bs=16: m.encode(t, normalize_embeddings=True, batch_size=bs)
    return _ENC[0]


def blob(v):
    return zlib.compress(v.astype("float32").tobytes(), 1)


def unblob(b):
    import numpy as np
    return np.frombuffer(zlib.decompress(b), dtype="float32")


# ------------------------------------------------------------------- index ---
def cmd_index(a):
    import numpy as np
    t0 = time.time()
    c = db()
    cards = build_cards()
    have = set(r[0] for r in c.execute("SELECT hash FROM emb"))
    live = set(x["hash"] for x in cards)

    c.execute("DELETE FROM chunk")
    c.executemany("""INSERT OR REPLACE INTO chunk
        (hash,file,rel,line,doc_class,weight,heading,task,salience,text,ntok)
        VALUES(:hash,:file,:rel,:line,:doc_class,:weight,:heading,:task,:salience,:text,:ntok)""", cards)

    todo = [x for x in cards if x["hash"] not in have]
    if todo and not a.no_embed:
        enc = encoder()
        print("embedding %d new cards (%d cached)..." % (len(todo), len(cards) - len(todo)))
        B = 64
        for i in range(0, len(todo), B):
            part = todo[i:i + B]
            V = enc([x["text"][:2000] for x in part])
            c.executemany("INSERT OR REPLACE INTO emb VALUES(?,?)",
                          [(p["hash"], blob(V[j])) for j, p in enumerate(part)])
            sys.stdout.write("\r  %d/%d" % (min(i + B, len(todo)), len(todo)))
            sys.stdout.flush()
        print("")
    stale = have - live
    if stale:
        c.executemany("DELETE FROM emb WHERE hash=?", [(h,) for h in stale])

    mset(c, "version", sha("".join(sorted(live)))[:12])
    mset(c, "built", time.time())
    mset(c, "ncards", len(cards))
    c.execute("DELETE FROM qcache")          # index moved; answers may change
    c.commit()
    kb = sum(len(x["text"]) for x in cards) / 1024.0
    print("indexed %d cards / %d files / %.0f KB (~%dk tokens) in %.1fs"
          % (len(cards), len(set(x["rel"] for x in cards)), kb,
             sum(x["ntok"] for x in cards) // 1000, time.time() - t0))
    print("  new=%d reused=%d dropped=%d" % (len(todo), len(cards) - len(todo), len(stale)))


# --------------------------------------------------------------- retrieval ---
class Index(object):
    def __init__(self, c):
        self.c = c
        self.rows = c.execute(
            "SELECT id,hash,rel,line,doc_class,weight,heading,task,salience,text,ntok FROM chunk").fetchall()
        if not self.rows:
            die("index is empty - run:  python dr.py index")
        self.N = len(self.rows)
        self.df = Counter()
        self.tf = []
        self.len = []
        for r in self.rows:
            w = words(r[6] + " " + r[9])
            tf = Counter(w)
            self.tf.append(tf)
            self.len.append(len(w) or 1)
            for t in tf:
                self.df[t] += 1
        self.avg = sum(self.len) / float(self.N)
        self.post = defaultdict(list)
        for i, tf in enumerate(self.tf):
            for t, f in tf.items():
                self.post[t].append((i, f))

    def bm25(self, q, k1=1.5, b=0.75):
        sc = defaultdict(float)
        for t in words(q):
            if t not in self.post:
                continue
            idf = math.log(1 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5))
            for i, f in self.post[t]:
                sc[i] += idf * f * (k1 + 1) / (f + k1 * (1 - b + b * self.len[i] / self.avg))
        return sc

    def dense(self, q):
        import numpy as np
        rows = self.c.execute("SELECT hash,vec FROM emb").fetchall()
        if not rows:
            return {}
        pos = dict((r[1], i) for i, r in enumerate(self.rows))
        idx, M = [], []
        for h, v in rows:
            if h in pos:
                idx.append(pos[h])
                M.append(unblob(v))
        if not M:
            return {}
        M = np.vstack(M)
        # bge asks for this prefix on the query side only
        qv = encoder()(["Represent this sentence for searching relevant passages: " + q])[0]
        s = M @ qv
        return dict((idx[i], float(s[i])) for i in range(len(idx)))

    def search(self, q, k=40, fast=False, task=None, klass=None):
        lex = self.bm25(q)
        den = {} if fast else self.dense(q)
        rl = dict((i, r) for r, (i, _) in enumerate(sorted(lex.items(), key=lambda x: -x[1])[:200]))
        rd = dict((i, r) for r, (i, _) in enumerate(sorted(den.items(), key=lambda x: -x[1])[:200]))
        # Coverage: what share of the query's *rare* terms does this card actually
        # contain? Rank fusion alone lets a topically-central, heavily-starred
        # summary card outrank the card that literally states the law, because
        # RRF barely separates BM25 rank 1 from rank 5. Coverage restores that.
        qt = [t for t in set(words(q)) if t in self.df]
        idf = dict((t, math.log(1 + (self.N - self.df[t] + 0.5) / (self.df[t] + 0.5))) for t in qt)
        mass = sum(idf.values()) or 1.0
        phr = [p for p in phrases(q) if len(p) > 8]

        fused = {}
        for i in set(list(rl) + list(rd)):
            # reciprocal rank fusion, then class weight and law-salience boost
            s = 1.0 / (60 + rl.get(i, 500)) + (0.0 if fast else 1.0 / (60 + rd.get(i, 500)))
            r = self.rows[i]
            s *= r[5]
            s *= (1.0 + 0.18 * r[8])
            cov = sum(idf[t] for t in qt if t in self.tf[i]) / mass
            s *= (1.0 + 1.10 * cov)
            if phr:
                low = r[9].lower()
                if any(p in low for p in phr):
                    s *= 1.35          # verbatim phrase: the strongest signal there is
            fused[i] = s

        # Saturation: the big summary file (the program brief) is close to
        # every query and would otherwise fill every slot, burying the specific
        # war-chest that actually measured the thing. Each additional card from a
        # file it has already placed is discounted, so distinct sources surface.
        out, per_file = [], Counter()
        pool = sorted(fused.items(), key=lambda x: -x[1])
        picked = set()
        while len(out) < k:
            best, bs = None, -1.0
            for i, s in pool:
                if i in picked:
                    continue
                r = self.rows[i]
                if task and r[7] != task:
                    continue
                if klass and r[4] != klass:
                    continue
                adj = s * (SATURATION ** per_file[r[2]])
                if adj > bs:
                    best, bs = i, adj
            if best is None:
                break
            picked.add(best)
            r = self.rows[best]
            per_file[r[2]] += 1
            out.append((bs, r, lex.get(best, 0.0), den.get(best, 0.0)))
        return out


def render(hits, budget, why=False, header=None, per_file=2):
    """Pack cards until the token budget is spent. Bounded output is the point.

    Cards are packed in two passes so one verbose file cannot monopolise the
    answer: pass 1 honours `per_file`, pass 2 spends any leftover budget.
    """
    used, out, n = 0, [], 0
    if header:
        out.append(header)
        used += toks(header)
    seen_file = Counter()
    taken = set()

    def emit(idx, s, r, lx, dn, truncate=False):
        nonlocal used, n
        body = r[9].strip()
        cite = "%s:%d" % (r[2], r[3])
        tag = "[%s%s]" % (r[4], ("/" + r[7]) if r[7] else "")
        head = "--- %s %s" % (tag, cite) + ("  score=%.4f lex=%.1f dense=%.3f" % (s, lx, dn) if why else "")
        if truncate:
            body = body[:max(0, int((budget - used) * 3.5))].rsplit("\n", 1)[0] + "\n…[truncated]"
        cost = toks(body) + toks(head)
        if used + cost > budget:
            return False
        out.append(head + "\n" + body)
        used += cost
        n += 1
        taken.add(idx)
        seen_file[r[2]] += 1
        return True

    for p in (0, 1):
        for i, (s, r, lx, dn) in enumerate(hits):
            if i in taken:
                continue
            if p == 0 and seen_file[r[2]] >= per_file:
                continue
            emit(i, s, r, lx, dn)
    if n == 0 and hits:                      # nothing fit: emit the top card, clipped
        s, r, lx, dn = hits[0]
        emit(0, s, r, lx, dn, truncate=True)
    return "\n\n".join(out), used, n


# ----------------------------------------------------------------- command ---
def cmd_ask(a):
    c = db()
    q = " ".join(a.query)
    key = sha("|".join([q, str(a.budget), str(a.k), str(a.fast), str(a.task or ""),
                        str(a.klass or ""), mget(c, "version", "0"), SCORER]))
    if not a.no_cache:
        r = c.execute("SELECT out FROM qcache WHERE k=?", (key,)).fetchone()
        if r:
            c.execute("UPDATE qcache SET hits=hits+1 WHERE k=?", (key,))
            c.commit()
            print(r[0])
            print("\n[cache hit - 0 new retrieval cost]")
            return
    t0 = time.time()
    ix = Index(c)
    hits = ix.search(q, k=max(a.k, 40), fast=a.fast, task=a.task, klass=a.klass)
    hdr = "# scripts: %s\n# %d cards indexed; showing the slice that fits %d tokens." % (q, ix.N, a.budget)
    body, used, n = render(hits, a.budget, a.why, hdr)
    tail = "\n\n[%d cards | ~%d tokens | %.1fs | corpus ~%dk tokens]" % (
        n, used, time.time() - t0, sum(r[10] for r in ix.rows) // 1000)
    out = body + tail
    c.execute("INSERT OR REPLACE INTO qcache VALUES(?,?,?,0)", (key, out, time.time()))
    c.execute("INSERT INTO usage VALUES(?,?,?,?)",
              (time.time(), "ask", sum(r[10] for r in ix.rows) - used, used))
    c.commit()
    print(out)


BOOT_Q = [
    ("Kill-list: design archetypes measured dead at the difficulty gate", 900),
    ("The proven recipe for clearing the difficulty gate", 700),
    ("Wall-clock law: naive search archetype at the disclosed cap", 500),
    ("Local pipeline must be green before any push; gate to local pre-check map", 600),
    ("artifact_type and task_objective report taxonomy labels standing rule", 400),
    ("Never fabricate a measurement; authorship split human-written", 350),
]


def cmd_boot(a):
    """The fixed pack to load at session start instead of MEMORY.md + the platform."""
    c = db()
    ver = mget(c, "version", "0")
    key = sha("BOOT|" + ver + "|" + SCORER + "|" + str(a.budget))
    if not a.no_cache:
        r = c.execute("SELECT out FROM qcache WHERE k=?", (key,)).fetchone()
        if r:
            c.execute("UPDATE qcache SET hits=hits+1 WHERE k=?", (key,))
            c.commit()
            print(r[0])
            return
    ix = Index(c)
    seen, chosen = set(), []
    scale = a.budget / float(sum(b for _, b in BOOT_Q))
    for q, b in BOOT_Q:
        for h in ix.search(q, k=12, fast=False):
            if h[1][1] in seen:
                continue
            seen.add(h[1][1])
            chosen.append((h, int(b * scale)))
    out, used = [], 0
    hdr = ("# BOOT PACK  (replaces reading MEMORY.md + the program brief)\n"
           "# Ask for anything else with:  python scripts/dr.py ask \"<question>\"")
    out.append(hdr)
    used += toks(hdr)
    perq = defaultdict(int)
    for h, cap in chosen:
        s, r, lx, dn = h
        gid = r[2]
        body = r[9].strip()
        cost = toks(body)
        if used + cost > a.budget or perq[gid] > 3:
            continue
        out.append("--- [%s] %s:%d\n%s" % (r[4], r[2], r[3], body))
        used += cost
        perq[gid] += 1
    txt = "\n\n".join(out) + "\n\n[boot pack: ~%d tokens vs ~%dk for the source files]" % (
        used, (os.path.getsize(os.path.join(MEM, "the program brief"))
               + os.path.getsize(os.path.join(MEM, "MEMORY.md"))) // 4000)
    c.execute("INSERT OR REPLACE INTO qcache VALUES(?,?,?,0)", (key, txt, time.time()))
    c.commit()
    print(txt)


def cmd_laws(a):
    """Distil the corpus to its law cards, near-duplicates collapsed."""
    import numpy as np
    c = db()
    ix = Index(c)
    cand = [r for r in ix.rows if r[8] >= a.min_salience]
    cand.sort(key=lambda r: (-r[8], -r[5]))
    vec = dict(c.execute("SELECT hash,vec FROM emb").fetchall())
    kept, mats = [], []
    for r in cand:
        if r[1] not in vec:
            continue
        v = unblob(vec[r[1]])
        if mats:
            sim = float(np.max(np.vstack(mats) @ v))
            if sim > a.dedup:
                continue
        kept.append(r)
        mats.append(v)
        if len(kept) >= a.max:
            break
    groups = defaultdict(list)
    for r in kept:
        groups[r[4]].append(r)
    order = ["law", "rule", "case", "warchest", "reference", "proposal"]
    lines = ["# LAW DECK",
             "",
             "Auto-distilled from %d cards across %d files by `dr.py laws`." % (ix.N, len(set(x[2] for x in ix.rows))),
             "Each card is kept only if no higher-salience card was >%.2f cosine to it." % a.dedup,
             "Regenerate after any memory write:  `python scripts/dr.py laws --write`",
             ""]
    tot = 0
    for g in order + [k for k in groups if k not in order]:
        if g not in groups:
            continue
        lines.append("## %s" % g.upper())
        lines.append("")
        for r in groups[g]:
            body = r[9].strip()
            tot += toks(body)
            lines.append("<!-- %s:%d salience=%.2f -->" % (r[2], r[3], r[8]))
            lines.append(body)
            lines.append("")
    txt = "\n".join(lines)
    if a.write:
        p = os.path.join(HERE, "LAWS.md")
        with io.open(p, "w", encoding="utf-8") as f:
            f.write(txt)
        print("wrote %s  (%d cards, ~%d tokens, from ~%dk-token corpus)"
              % (p, len(kept), tot, sum(r[10] for r in ix.rows) // 1000))
    else:
        print(txt)


def cmd_check(a):
    """Retrieve the laws a draft is most likely to be breaking."""
    c = db()
    if not os.path.exists(a.file):
        die("no such file: " + a.file)
    with io.open(a.file, encoding="utf-8", errors="replace") as f:
        draft = f.read()
    ix = Index(c)
    # probe the draft from the angles that have historically killed tasks
    probes = [
        ("does this design match a dead archetype (naive search, greedy, printed optimum, "
         "N independent one-line rules, library-solvable)?", 1000),
        ("difficulty gate: is the crux implementation-difficulty or merely reading-difficulty?", 800),
        ("can the agent measure the constraint one coordinate at a time -- does the legality "
         "predicate factorise over independent fields, making it checkable not constructive?", 700),
        ("wall clock timeout budget under contention at the disclosed cap", 700),
        ("verifier coverage, AVA, reference solution must never exit nonzero", 700),
        ("cosine similarity to previous same-author tasks", 500),
        ("report taxonomy labels artifact_type task_objective", 400),
        ("difficulty_explanation_quality audience framing", 400),
    ]
    key_terms = " ".join(sorted(set(words(draft)), key=lambda w: -draft.lower().count(w))[:60])
    print("# PRECHECK: %s" % os.path.basename(a.file))
    print("# %d chars of draft vs %d indexed cards. Laws that fire, most-relevant first.\n" % (len(draft), ix.N))
    seen = set()
    total = 0
    for q, b in probes:
        hits = [h for h in ix.search(q + " " + key_terms[:400], k=8, fast=a.fast)
                if h[1][1] not in seen]
        if not hits:
            continue
        body, used, n = render(hits[:3], int(b * a.budget / 4500.0), False,
                               "## probe: %s" % q)
        for h in hits[:3]:
            seen.add(h[1][1])
        total += used
        print(body + "\n")
    print("[~%d tokens; full corpus is ~%dk]" % (total, sum(r[10] for r in ix.rows) // 1000))


def cmd_cache(a):
    """Content-keyed store for expensive derived artifacts (preflight, probes)."""
    c = db()
    if a.op == "put":
        if not a.key:
            die("put needs a key, e.g.  cache put preflight-<hash> --stdin --watch <task-dir>")
        srcs = [bool(a.value), bool(a.from_file), bool(a.stdin)]
        if sum(srcs) != 1:
            die("put needs exactly one of --stdin, --from-file or --value\n"
                "  usual form:  python preflight.py <task-dir> | "
                "dr.py cache put preflight-<hash> --stdin --watch <task-dir>")
        if a.stdin:
            body = sys.stdin.read()
        elif a.from_file:
            if not os.path.exists(a.from_file):
                die("--from-file not found: %s\n"
                    "  (to capture a command's output directly, pipe it and use --stdin)" % a.from_file)
            with io.open(a.from_file, "rb") as f:
                body = f.read().decode("utf-8", "replace")
        else:
            body = a.value
        if not body.strip():
            die("refusing to cache an empty result")
        fp = a.fingerprint or ""
        if a.watch:
            fp = dirhash(a.watch)
        c.execute("INSERT OR REPLACE INTO artifact VALUES(?,?,?,?,?,0)",
                  (a.key, fp, zlib.compress(body.encode("utf-8"), 6), a.note or "", time.time()))
        c.commit()
        print("cached %r (%d chars, fingerprint=%s)" % (a.key, len(body), fp[:12] or "-"))
    elif a.op == "get":
        r = c.execute("SELECT fingerprint,body,note,ts,hits FROM artifact WHERE k=?", (a.key,)).fetchone()
        if not r:
            print("MISS", file=sys.stderr)
            sys.exit(3)
        if a.watch:
            if dirhash(a.watch) != r[0]:
                print("STALE (watched tree changed since cache) - re-run it, "
                      "do not quote the old number", file=sys.stderr)
                sys.exit(4)
        elif r[0]:
            # stored with a fingerprint but fetched without one: we cannot say
            # this is current, so say so rather than implying freshness
            sys.stderr.write("[WARNING: entry has a fingerprint but no --watch given; "
                             "freshness NOT verified]\n")
        c.execute("UPDATE artifact SET hits=hits+1 WHERE k=?", (a.key,))
        c.commit()
        age = (time.time() - r[3]) / 3600.0
        sys.stderr.write("[cache hit, %.1fh old%s]\n" % (age, (" " + r[2]) if r[2] else ""))
        print(zlib.decompress(r[1]).decode("utf-8"))
    elif a.op == "list":
        rows = c.execute("SELECT k,fingerprint,length(body),note,ts,hits FROM artifact ORDER BY ts DESC").fetchall()
        if not rows:
            print("(empty)")
        for k, fp, n, note, ts, h in rows:
            print("%-34s %8dB  hits=%-3d  %s  %s" % (
                k, n, h, time.strftime("%m-%d %H:%M", time.localtime(ts)), note or ""))
    elif a.op == "drop":
        c.execute("DELETE FROM artifact WHERE k=?", (a.key,))
        c.commit()
        print("dropped", a.key)


def dirhash(root):
    """Fingerprint a tree so a cached result can be invalidated by real edits.

    A missing path is fatal, never a fingerprint. Hashing nothing returns the
    SHA1 of the empty string - a constant - so a typo'd --watch would make put
    and get agree and the cache would serve a stale measurement while claiming
    the tree was unchanged. That is precisely the failure this cache exists to
    prevent, so it must be loud.
    """
    if not os.path.exists(root):
        die("--watch path does not exist: %s\n"
            "  refusing to fingerprint a missing tree (it would silently match)" % root)
    h = hashlib.sha1()
    if os.path.isfile(root):
        with open(root, "rb") as f:
            h.update(f.read())
        return h.hexdigest()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in sorted(dn) if d not in (".git", "__pycache__", "node_modules", ".pytest_cache")]
        for f in sorted(fn):
            p = os.path.join(dp, f)
            try:
                h.update(os.path.relpath(p, root).replace("\\", "/").encode())
                h.update(str(os.path.getsize(p)).encode())
                with open(p, "rb") as fh:
                    h.update(fh.read(65536))
            except Exception:
                pass
    return h.hexdigest()


def cmd_stats(a):
    c = db()
    ix = Index(c)
    print("index version %s, built %s" % (
        mget(c, "version", "?"),
        time.strftime("%Y-%m-%d %H:%M", time.localtime(float(mget(c, "built", "0"))))))
    print("cards %d | files %d | corpus ~%dk tokens\n" % (
        ix.N, len(set(r[2] for r in ix.rows)), sum(r[10] for r in ix.rows) // 1000))
    by = defaultdict(lambda: [0, 0])
    for r in ix.rows:
        by[r[4]][0] += 1
        by[r[4]][1] += r[10]
    print("%-11s %6s %10s" % ("class", "cards", "tokens"))
    for k, (n, t) in sorted(by.items(), key=lambda x: -x[1][1]):
        print("%-11s %6d %9dk" % (k, n, t // 1000))
    q = c.execute("SELECT count(*), sum(hits) FROM qcache").fetchone()
    ar = c.execute("SELECT count(*), sum(hits) FROM artifact").fetchone()
    u = c.execute("SELECT count(*), sum(spent), sum(saved) FROM usage").fetchone()
    print("\nquery cache   %d entries, %d hits" % (q[0] or 0, q[1] or 0))
    print("artifact cache %d entries, %d hits" % (ar[0] or 0, ar[1] or 0))
    if u[0]:
        print("retrievals     %d, ~%d tokens returned (avg %d/query)" % (u[0], u[1] or 0, (u[1] or 0) // u[0]))


def main():
    p = argparse.ArgumentParser(prog="dr.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("index", help="build/refresh the index")
    s.add_argument("--no-embed", action="store_true", help="lexical only, skip the encoder")
    s.set_defaults(fn=cmd_index)

    s = sub.add_parser("ask", help="retrieve cards for a question")
    s.add_argument("query", nargs="+")
    s.add_argument("--budget", type=int, default=2500, help="token ceiling on the answer")
    s.add_argument("-k", type=int, default=12)
    s.add_argument("--fast", action="store_true", help="lexical only (~0.2s, no encoder)")
    s.add_argument("--task", help="restrict to one task hash, e.g. the 7-char repo id")
    s.add_argument("--klass", help="restrict to a doc class: law|rule|warchest|proposal|reference|case")
    s.add_argument("--why", action="store_true", help="show fusion scores")
    s.add_argument("--no-cache", action="store_true")
    s.set_defaults(fn=cmd_ask)

    s = sub.add_parser("boot", help="minimal session-start pack")
    s.add_argument("--budget", type=int, default=3000)
    s.add_argument("--no-cache", action="store_true")
    s.set_defaults(fn=cmd_boot)

    s = sub.add_parser("laws", help="distilled law deck")
    s.add_argument("--write", action="store_true", help="write LAWS.md")
    s.add_argument("--max", type=int, default=110)
    s.add_argument("--dedup", type=float, default=0.88)
    s.add_argument("--min-salience", type=float, default=0.55)
    s.set_defaults(fn=cmd_laws)

    s = sub.add_parser("check", help="precheck a draft against the laws")
    s.add_argument("file")
    s.add_argument("--budget", type=int, default=4500)
    s.add_argument("--fast", action="store_true")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("cache", help="derived-artifact cache")
    s.add_argument("op", choices=["put", "get", "list", "drop"])
    s.add_argument("key", nargs="?", default="")
    s.add_argument("--value")
    s.add_argument("--from-file")
    s.add_argument("--stdin", action="store_true", help="read the result from a pipe (usual form)")
    s.add_argument("--watch", help="dir/file whose content fingerprints this entry")
    s.add_argument("--fingerprint")
    s.add_argument("--note")
    s.set_defaults(fn=cmd_cache)

    s = sub.add_parser("stats", help="corpus and cache report")
    s.set_defaults(fn=cmd_stats)

    a = p.parse_args()
    if not a.cmd:
        p.print_help()
        return
    a.fn(a)


if __name__ == "__main__":
    main()
