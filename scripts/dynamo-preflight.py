"""Local replica of the Dynamo pipeline's static checks.

The real checks live in the private `handshake-orchestration-tb2` reusable workflow, so
they cannot be run locally. These are reimplemented from the exact check names the
pipeline reports, so a task can be cleared before spending a push and a CI round-trip.

Passing this does NOT guarantee the pipeline passes — it catches the mechanical failures
that gate everything downstream.

    python dynamo-preflight.py <path-to-task-dir> [--refs <path-to-references>]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

CAP_TIMEOUT = 3600.0
CAP_INSTRUCTION_TOKENS = 1500
REQUIRED_META = ["category", "subcategory", "model_tested", "agent_tested",
                 "task_objective", "artifact_type", "expert_time_estimate_hours",
                 "difficulty_explanation", "solution_explanation",
                 "verification_explanation"]
PLACEHOLDER = re.compile(r"\b(TODO|FIXME|XXX|TBD|<[a-z_]+>|lorem ipsum)\b", re.I)

results: list[tuple[bool, str, str]] = []


def check(name):
    def deco(fn):
        def wrapped(ctx):
            try:
                ok, detail = fn(ctx)
            except Exception as exc:                      # a crashing check is a failure
                ok, detail = False, f"check raised {type(exc).__name__}: {exc}"
            results.append((ok, name, detail))
        wrapped._name = name
        return wrapped
    return deco


# --------------------------------------------------------------------------- task.toml

@check("task.toml has all required metadata fields")
def c_meta_fields(ctx):
    meta = ctx["toml"].get("metadata", {})
    missing = [k for k in REQUIRED_META if k not in meta]
    if "artifacts" not in ctx["toml"]:
        missing.append("artifacts (top level)")
    return not missing, ("missing: " + ", ".join(missing)) if missing else ""


@check("all required task.toml fields are filled in (no placeholders)")
def c_no_placeholders(ctx):
    meta = ctx["toml"].get("metadata", {})
    bad = []
    for k in REQUIRED_META:
        v = meta.get(k)
        if isinstance(v, str):
            if not v.strip():
                bad.append(f"{k} is empty")
            elif PLACEHOLDER.search(v):
                bad.append(f"{k} contains a placeholder")
        elif isinstance(v, list) and not v:
            bad.append(f"{k} is an empty list")
    return not bad, "; ".join(bad)


@check("task.toml category/objective/artifact labels are from the taxonomy")
def c_taxonomy(ctx):
    tax_path = ctx["refs"] / "diversity-taxonomy.toml"
    if not tax_path.exists():
        return True, "taxonomy file not found — skipped"
    tax = tomllib.loads(tax_path.read_text(encoding="utf-8"))
    meta = ctx["toml"]["metadata"]

    def allowed(*keys):
        node = tax
        for k in keys:
            if not isinstance(node, dict) or k not in node:
                return None
            node = node[k]
        if isinstance(node, dict):
            for cand in ("labels", "values", "options"):
                if cand in node:
                    node = node[cand]
                    break
        return {x["name"] if isinstance(x, dict) else x for x in node} \
            if isinstance(node, list) else None

    bad = []
    for field in ("task_objective", "artifact_type"):
        pool = allowed(field) or allowed("taxonomy", field)
        if pool is None:
            continue
        for label in meta.get(field, []):
            if label not in pool:
                bad.append(f"{field}: {label!r} not in taxonomy")
    return not bad, "; ".join(bad)


@check("task slug is concise (<=3 tokens)")
def c_slug(ctx):
    name = ctx["toml"]["task"]["name"]
    slug = name.split("/", 1)[1] if "/" in name else name
    n = len(slug.split("-"))
    return n <= 3, f"{slug!r} has {n} tokens"


@check("allow_internet is true")
def c_internet(ctx):
    v = ctx["toml"].get("environment", {}).get("allow_internet")
    return v is True, f"allow_internet={v}"


@check("agent/verifier timeouts within the cap")
def c_timeouts(ctx):
    bad = []
    for sect in ("agent", "verifier"):
        t = ctx["toml"].get(sect, {}).get("timeout_sec")
        if t is None:
            bad.append(f"{sect}.timeout_sec missing")
        elif t > CAP_TIMEOUT:
            bad.append(f"{sect}.timeout_sec={t} exceeds {CAP_TIMEOUT}")
    return not bad, "; ".join(bad)


@check("gpu_types are canonical names")
def c_gpus(ctx):
    env = ctx["toml"].get("environment", {})
    if env.get("gpus", 0) == 0 and not env.get("gpu_types"):
        return True, ""
    known = {"a100", "h100", "l4", "t4", "a10g", "v100"}
    bad = [g for g in env.get("gpu_types", []) if g.lower() not in known]
    return not bad, "; ".join(bad)


# ----------------------------------------------------------------------- instruction

@check("instruction.md uses absolute paths")
def c_abs_paths(ctx):
    text = ctx["instruction"]
    rel = re.findall(r"(?<![\w/`.])(?:\./)?((?:data|tests|solution|app)/[\w./-]+)", text)
    rel = [r for r in rel if not text.count("/" + r)]
    return not rel, ("relative paths: " + ", ".join(sorted(set(rel))[:5])) if rel else ""


@check("instruction.md is <= 1500 tokens (o200k_base)")
def c_instruction_len(ctx):
    text = ctx["instruction"]
    try:
        import tiktoken
        n = len(tiktoken.get_encoding("o200k_base").encode(text))
        how = "tiktoken"
    except Exception:
        n = len(text) // 4
        how = "approximated at chars/4 — install tiktoken for the exact count"
    return n <= CAP_INSTRUCTION_TOKENS, f"{n} tokens ({how})"


@check("expected output files are documented in instruction.md")
def c_artifacts_documented(ctx):
    missing = [a for a in ctx["toml"].get("artifacts", [])
               if a not in ctx["instruction"]]
    return not missing, ("not mentioned: " + ", ".join(missing)) if missing else ""


# ------------------------------------------------------------------------ Dockerfile

@check("Dockerfile base image is a pre-approved image (non-approved -> warning)")
def c_base_image(ctx):
    script = ctx["refs"] / "check-base-image.sh"
    if not script.exists():
        return True, "check-base-image.sh not found — skipped"
    # Prefer Git Bash: a bare `bash` on Windows often resolves to WSL, which neither
    # understands `E:/...` nor shares the same toolchain. Fall back to whatever `bash`
    # is on PATH. The path is passed relative to the task dir so both can resolve it.
    rel = os.path.relpath(script, ctx["task"]).replace("\\", "/")
    shells = [r"C:\Program Files\Git\bin\bash.exe",
              r"C:\Program Files (x86)\Git\bin\bash.exe", "bash"]
    shell = next((s for s in shells if s == "bash" or Path(s).exists()), "bash")
    proc = subprocess.run([shell, rel], cwd=str(ctx["task"]),
                          capture_output=True, text=True)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    ok = proc.returncode == 0
    return ok, "" if ok else (tail[-1] if tail else f"exit {proc.returncode}")


@check("no source embedded via Dockerfile heredoc")
def c_no_heredoc(ctx):
    ok = "<<" not in ctx["dockerfile"]
    return ok, "" if ok else "Dockerfile contains a heredoc"


@check("no apt-get upgrade in Dockerfiles")
def c_no_apt_upgrade(ctx):
    hit = re.search(r"apt-get\s+(-\S+\s+)*upgrade", ctx["dockerfile"])
    return not hit, "apt-get upgrade present" if hit else ""


@check("no broad recursive chmod in Dockerfiles")
def c_no_chmod(ctx):
    hit = re.search(r"chmod\s+-R\s+\S+\s+(/|/app|/usr|/etc)\b", ctx["dockerfile"])
    return not hit, "broad recursive chmod present" if hit else ""


@check("Dockerfile does not COPY solution/ or tests/")
def c_no_copy_secrets(ctx):
    # The pipeline scans the WHOLE Dockerfile for a solution/ or tests/ reference,
    # not just COPY/ADD lines — a comment mentioning tests/test.sh fails it
    # (measured on a real run). Match that, or this check
    # passes locally and costs a CI round-trip.
    bad = [ln.strip() for ln in ctx["dockerfile"].splitlines()
           if re.search(r"(^|[\s/])(solution|tests)/", ln)]
    return not bad, "; ".join(bad)


@check("Dockerfile apt hygiene (no pins, update + cleanup)")
def c_apt_hygiene(ctx):
    df = ctx["dockerfile"]
    if "apt-get install" not in df:
        return True, ""
    bad = []
    if "apt-get update" not in df:
        bad.append("install without update")
    if "rm -rf /var/lib/apt/lists" not in df:
        bad.append("no apt list cleanup")
    if re.search(r"apt-get install[^\n]*\w=\S+", df):
        bad.append("version-pinned apt package")
    return not bad, "; ".join(bad)


@check("Dockerfile is not pinned to a CPU platform")
def c_no_platform(ctx):
    hit = re.search(r"^\s*FROM\s+--platform=", ctx["dockerfile"], re.M)
    return not hit, "FROM --platform= present" if hit else ""


@check("no bare nproc (use a fixed CPU count)")
def c_no_nproc(ctx):
    files = [ctx["dockerfile"]] + [p.read_text(encoding="utf-8", errors="ignore")
                                   for p in ctx["task"].rglob("*.sh")]
    hit = any("nproc" in f for f in files)
    return not hit, "nproc used" if hit else ""


@check("pip/uv installs are version-pinned")
def c_pinned(ctx):
    unpinned = []
    for m in re.finditer(r"(?:pip|pip3|uv pip)\s+install\s+([^\n\\]*)", ctx["dockerfile"]):
        for tok in m.group(1).split():
            if tok.startswith("-") or tok in {"install", "."}:
                continue
            if not re.search(r"[=<>~]=?", tok):
                unpinned.append(tok)
    return not unpinned, ("unpinned: " + ", ".join(unpinned)) if unpinned else ""


@check("non-trivial build context has a .dockerignore")
def c_dockerignore(ctx):
    envdir = ctx["task"] / "environment"
    subdirs = [p for p in envdir.iterdir() if p.is_dir()]
    if not subdirs:
        return True, "build context is flat"
    ok = (envdir / ".dockerignore").exists()
    return ok, "" if ok else (
        f"context has subdirectories ({', '.join(p.name for p in subdirs)}) "
        f"but no .dockerignore")


# ---------------------------------------------------------------------------- tests

@check("verifier writes /logs/verifier/reward.txt (not pre-created)")
def c_reward(ctx):
    if "reward.txt" not in ctx["testsh"]:
        return False, "test.sh never writes reward.txt"
    stray = list((ctx["task"] / "tests").rglob("reward.txt"))
    return not stray, "reward.txt is pre-created in tests/" if stray else ""


@check("tests/test.sh installs nothing at verify time")
def c_no_verify_installs(ctx):
    bad = [w for w in ("pip install", "uv pip", "uvx", "apt-get install", "npm install")
           if w in ctx["testsh"]]
    return not bad, "; ".join(bad)


@check("verifier does not fetch external resources at trial time")
def c_no_fetch(ctx):
    blob = ctx["testsh"] + "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in (ctx["task"] / "tests").rglob("*.py"))
    bad = [w for w in ("curl ", "wget ", "requests.get", "urllib.request",
                       "httpx.") if w in blob]
    return not bad, "; ".join(bad)


@check("tests/ has test_outputs.py and test.sh runs it")
def c_tests_present(ctx):
    has = (ctx["task"] / "tests" / "test_outputs.py").exists()
    runs = "test_outputs.py" in ctx["testsh"]
    if not has:
        return False, "tests/test_outputs.py missing"
    return runs, "" if runs else "test.sh does not run test_outputs.py"


# ------------------------------------------------------------------ extra safety net

@check("no extraneous files (caches, job artifacts)")
def c_no_strays(ctx):
    strays = [str(p.relative_to(ctx["task"]))
              for p in ctx["task"].rglob("*")
              if p.name in {"__pycache__", "jobs", ".pytest_cache"}
              or p.suffix == ".pyc"]
    return not strays, ", ".join(sorted(set(strays))[:5])


@check("all text files are LF (no CRLF)")
def c_lf(ctx):
    bad = []
    for p in ctx["task"].rglob("*"):
        if p.is_file() and p.suffix in {".md", ".py", ".sh", ".toml", ".json", ".log"} \
                or p.name == "Dockerfile":
            if b"\r\n" in p.read_bytes():
                bad.append(str(p.relative_to(ctx["task"])))
    return not bad, ", ".join(bad[:5])


# ---------------------------------------------------------------------------
# Difficulty probe (opt-in, costs tokens): run the REAL gate agent locally.
#
# Harbor bundles terminus-2 — the same agent the Dynamo difficulty gate uses —
# backed by LiteLLM, so any provider works. This is the documented calibration
# ladder (oracle -> nop -> frontier agent), not a workaround.
#
# Use it as a ONE-WAY FILTER:
#   any trial solves  -> the task is too easy; redesign BEFORE burning billed CI
#   no trial solves   -> promising, but only real CI decides the gate
#
# Historical justification: 3 of 4 dead designs were solved by the gate agent in
# under 20 minutes each, after a full billed pass@2 cycle had already been spent.
# ---------------------------------------------------------------------------
PROBE_PROFILES = {
    # TokenRouter is an OpenAI-COMPATIBLE gateway, so LiteLLM talks to it through
    # its `openai/` provider with a base-URL override — even though the model
    # being served is an Anthropic one. Set TOKENROUTER_API_KEY and
    # TOKENROUTER_BASE_URL; the probe maps them onto the OPENAI_* vars.
    # Serves anthropic/claude-opus-4.8 — the exact model task.toml pins as
    # `model_tested`, so this probe runs the real gate model locally.
    "tokenrouter": dict(
        model="openai/anthropic/claude-opus-4.8",
        key_env="TOKENROUTER_API_KEY",
        base_env="TOKENROUTER_BASE_URL",   # https://api.tokenrouter.com/v1
        key_dest="OPENAI_API_KEY",
        base_dests=("OPENAI_BASE_URL", "OPENAI_API_BASE"),
        validate="openai",
    ),
    # AgentRouter is an ANTHROPIC-compatible proxy: its own docs tell clients to
    # set ANTHROPIC_BASE_URL (no /v1 suffix) and ANTHROPIC_AUTH_TOKEN, so LiteLLM
    # talks to it through the native `anthropic/` provider with a base override,
    # NOT through `openai/`. Set AGENTROUTER_API_KEY and AGENTROUTER_BASE_URL
    # (https://agentrouter.org). Model slugs use hyphens — claude-opus-4-8, not
    # claude-opus-4.8 — and 4-8 is what task.toml pins as `model_tested`, so this
    # runs the real gate model. Override with -m for 4-6/4-7.
    "agentrouter": dict(
        model="anthropic/claude-opus-4-8",
        key_env="AGENTROUTER_API_KEY",
        base_env="AGENTROUTER_BASE_URL",   # https://agentrouter.org
        key_dest="ANTHROPIC_API_KEY",
        base_dests=("ANTHROPIC_API_BASE", "ANTHROPIC_BASE_URL"),
        validate="anthropic",
    ),
    # Fireworks is a native LiteLLM provider — no base-URL override needed.
    # deepseek-v4-pro is what the official trials log header showed terminus-2
    # running, so this is the closest second opinion on the real gate. For a
    # cheaper pre-filter pass:
    #   -m fireworks_ai/accounts/fireworks/models/deepseek-v4-flash-0731
    # but treat a flash solve as decisive and a flash non-solve as weak evidence.
    "fireworks": dict(
        model="fireworks_ai/accounts/fireworks/models/deepseek-v4-pro",
        key_env="FIREWORKS_AI_API_KEY",
        base_env=None,
        key_dest="FIREWORKS_AI_API_KEY",
        base_dests=(),
        validate=None,
    ),
}


def _validate_gateway(base, key, model, style="openai"):
    """Cheap GET /models against the gateway before spending an agent run.

    Catches a wrong base URL, a dead key, or a bad model slug in seconds instead
    of after a 45-minute agent run. Gateways disagree on auth header even when
    they proxy the same models, so try both shapes and accept either:
      * OpenAI style    -> Authorization: Bearer <key>
      * Anthropic style -> x-api-key: <key> + anthropic-version
    Returns (ok, detail).
    """
    import json as _json
    import urllib.request
    import urllib.error

    root = base.rstrip("/")
    url = root + ("/models" if root.endswith("/v1") else "/v1/models")
    openai_hdr = {"Authorization": f"Bearer {key}"}
    anthropic_hdr = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    orders = ([anthropic_hdr, openai_hdr] if style == "anthropic"
              else [openai_hdr, anthropic_hdr])

    payload, errors = None, []
    for headers in orders:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                payload = _json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            errors.append(f"HTTP {exc.code} via {list(headers)[0]}")
        except Exception as exc:
            errors.append(f"{type(exc).__name__} via {list(headers)[0]}")
    if payload is None:
        detail = "; ".join(errors)
        if all("401" in e or "403" in e for e in errors) and errors:
            return False, (f"gateway {url} rejected the key ({detail}) — the "
                           f"credential is dead or not provisioned for this account")
        return False, f"gateway {url} unusable ({detail})"

    ids = [m.get("id") for m in (payload.get("data") or []) if isinstance(m, dict)]
    if not ids:
        return True, "gateway reachable (model list empty; slug unverified)"
    wanted = model.split("/", 1)[1] if "/" in model else model
    if wanted in ids:
        return True, f"gateway OK, model {wanted!r} served"
    close = [i for i in ids if wanted.split("-")[0] in i][:6] or ids[:6]
    return False, (f"model {wanted!r} not served by the gateway. "
                   f"Available include: {', '.join(close)}")


def run_probe(task, profile, model, attempts, out_dir, timeout_min):
    """Run the gate agent locally. Returns (verdict_ok, detail)."""
    import subprocess, json, shutil, tempfile, os

    spec = PROBE_PROFILES.get(profile)
    if spec is None:
        return "inconclusive", f"unknown profile {profile!r} (have: {', '.join(PROBE_PROFILES)})"
    if shutil.which("harbor") is None:
        return "inconclusive", "harbor not on PATH"

    env = dict(os.environ)
    # Harbor's progress renderer emits braille spinner chars. With stdout captured on
    # Windows the default cp1252 codec raises UnicodeEncodeError, which kills the parent
    # process and CANCELS the running trials — producing an empty, useless job dir.
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    key = env.get(spec["key_env"])
    if not key:
        return "inconclusive", (f"{spec['key_env']} is not set — export it first "
                                f"(never paste the value into a command line)")
    env[spec["key_dest"]] = key
    chosen = model or spec["model"]
    if spec["base_env"]:
        base = env.get(spec["base_env"])
        if not base:
            return "inconclusive", f"{spec['base_env']} is not set (gateway base URL required)"
        for dest in spec["base_dests"]:
            env[dest] = base
        if spec.get("validate"):
            ok, why = _validate_gateway(base, key, chosen, spec["validate"])
            print(f"  gateway check: {why}")
            if not ok:
                return "inconclusive", why

    out = Path(out_dir or tempfile.mkdtemp(prefix="dynamo-probe-"))
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["harbor", "run", "-p", str(task), "-a", "terminus-2",
           "-m", chosen, "-k", str(attempts),
           "-n", str(attempts), "-o", str(out)]
    print(f"  probing: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, env=env, timeout=timeout_min * 60,
                       capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return "inconclusive", (f"probe wall-clock cap ({timeout_min}m) hit before trials finished — no solve observed, but this is NOT evidence of difficulty")

    # Classify every trial directory. `verifier/reward.txt` is the authoritative
    # artifact (harbor writes it); the JSON shapes vary and are empty when a trial
    # is cancelled, which is exactly the case that must NOT read as a clean run.
    rewards, broken = [], []
    trial_dirs = sorted({p.parent for p in out.rglob("*/config.json")
                         if p.parent.name.startswith("task__")})
    for d in trial_dirs:
        reward_file = d / "verifier" / "reward.txt"
        value = None
        if reward_file.is_file():
            try:
                value = float(reward_file.read_text(encoding="utf-8").strip())
            except Exception:
                value = None
        if value is None:                       # fall back to any parsable result.json
            for res in (d / "result.json", d.parent / "result.json"):
                if not res.is_file() or not res.read_text(encoding="utf-8").strip():
                    continue
                try:
                    data = json.loads(res.read_text(encoding="utf-8"))
                except Exception:
                    continue
                for trial in (data.get("trials") or [data]):
                    r = ((trial.get("verifier_result") or {}).get("rewards") or {}).get("reward")
                    if r is not None:
                        value = r
        if value is None:
            exc = d / "exception.txt"
            why = "errored" if exc.is_file() and exc.stat().st_size else "no verifier result"
            broken.append(f"{d.name}({why})")
        else:
            rewards.append(value)

    if not trial_dirs:
        return "inconclusive", f"no trials ran under {out} — check credentials/model and re-run"
    solved = [r for r in rewards if r >= 1.0]
    if solved:                                  # decisive: kill the design
        return "fail", (f"TOO EASY — {len(solved)}/{len(rewards)} local trials SOLVED it. "
                        f"Redesign before spending billed CI.")
    if broken:                                  # NOT evidence of difficulty
        return "inconclusive", (
            f"{len(broken)}/{len(trial_dirs)} trials produced no reward "
            f"({', '.join(broken)}); {len(rewards)} usable" +
            (f" (rewards={rewards})" if rewards else "") +
            ". This proves NOTHING about difficulty — re-run (try -n 1 to avoid "
            "provider rate-limit retry storms) before trusting it.")
    return "pass", f"0/{len(rewards)} local trials solved (rewards={rewards}) — proceed to CI"


CHECKS = [v for v in list(globals().values())
          if callable(v) and hasattr(v, "_name")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--refs", default=None)
    ap.add_argument("--probe", metavar="PROFILE", default=None,
                    help="run the real gate agent (terminus-2) locally after the static "
                         f"checks; profiles: {', '.join(PROBE_PROFILES)}")
    ap.add_argument("--probe-model", default=None,
                    help="override the profile's default model")
    ap.add_argument("--probe-attempts", type=int, default=2,
                    help="local trials to run (default 2, mirrors the pass@2 pre-gate)")
    ap.add_argument("--probe-minutes", type=int, default=45,
                    help="wall-clock cap for the whole probe (default 45)")
    ap.add_argument("--probe-out", default=None,
                    help="job output dir; MUST be outside the task repo")
    args = ap.parse_args()

    task = Path(args.task).resolve()
    refs = Path(args.refs).resolve() if args.refs else task.parent / "references"

    ctx = dict(
        task=task, refs=refs,
        toml=tomllib.loads((task / "task.toml").read_text(encoding="utf-8")),
        instruction=(task / "instruction.md").read_text(encoding="utf-8"),
        dockerfile=(task / "environment" / "Dockerfile").read_text(encoding="utf-8"),
        testsh=(task / "tests" / "test.sh").read_text(encoding="utf-8"),
    )

    for fn in CHECKS:
        fn(ctx)

    failed = [r for r in results if not r[0]]
    width = max(len(r[1]) for r in results)
    for ok, name, detail in results:
        mark = "PASS" if ok else "FAIL"
        line = f"  [{mark}] {name.ljust(width)}"
        print(line + (f"  -- {detail}" if detail else ""))

    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    if failed:
        print("\nBLOCKED — fix these before pushing:")
        for _, name, detail in failed:
            print(f"  * {name}" + (f": {detail}" if detail else ""))

    probe_failed = False
    if args.probe:
        if failed:
            print("\nSkipping difficulty probe — fix the static checks first.")
        else:
            print(f"\n--- difficulty probe ({args.probe}) — costs tokens, "
                  f"cap {args.probe_minutes}m ---")
            status, detail = run_probe(task, args.probe, args.probe_model,
                                       args.probe_attempts, args.probe_out,
                                       args.probe_minutes)
            label = {"pass": "PASS", "fail": "FAIL",
                     "inconclusive": "????"}[status]
            print(f"  [{label}] local difficulty probe  -- {detail}")
            if status == "inconclusive":
                print("         INCONCLUSIVE is not a green light: the probe learned "
                      "nothing about difficulty. Re-run it before pushing.")
            probe_failed = status != "pass"

    return 1 if (failed or probe_failed) else 0


if __name__ == "__main__":
    sys.exit(main())
