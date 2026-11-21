#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ANE unified gate: the single entry point for local and CI validation.

Runs every independently testable gate in one process and reports a compact
summary with one unified exit code. No gate output is hidden — each gate's full
output is printed under its own banner. A missing DEBUG track (gitignored) is
handled by the underlying tools as a skip, so this runs unchanged in a CI clone.

Gates:
  1. payload    — schemas + ANS-1 digest reproducibility (NTP / IOP / conversion)
  2. terms      — banned wording across all tracks and READMEs
  3. dualformat — G8 clause-level MD/HTML consistency
  4. whitelist  — no undefined technical token in normative clauses

Usage:
  python tools/check_all.py            # run all gates
  python tools/check_all.py --only payload,terms
  python tools/check_all.py --json     # machine-readable summary to stdout

Exit code 0 = all selected gates pass, 1 = at least one gate failed,
2 = a gate could not be executed (missing tool / unexpected error).
"""
import argparse
import contextlib
import importlib.util
import io
import json
import pathlib
import sys
import time

BASE = pathlib.Path(__file__).resolve().parent.parent
TOOLS = BASE / "tools"

GATES = [
    ("payload", "validate_ntp.py", "main", "载荷/Schema/摘要一致性"),
    ("terms", "validate_ntp.py", "main", "措辞禁令"),
    ("dualformat", "check_dual_format.py", "main", "G8 双格式一致"),
    ("whitelist", "check_term_whitelist.py", "main", "术语白名单"),
]


def load_module(name):
    """Import a tool by file path, with its own directory importable."""
    sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location(name, TOOLS / name)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load " + name)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def run_gate(name, script, func, description):
    """Run one gate in-process, capturing stdout; returns (name, rc, output)."""
    buf = io.StringIO()
    rc = 2
    try:
        mod = load_module(script)
        fn = getattr(mod, func)
        argv = sys.argv
        # Each gate's main() parses sys.argv. The aggregator's own flags
        # (--json/--only) must never leak into a sub-gate's argparse.
        sys.argv = [str(TOOLS / script)] + (["terms"] if name == "terms" else [])
        try:
            with contextlib.redirect_stdout(buf):
                rc = fn()
        finally:
            sys.argv = argv
        if not isinstance(rc, int):
            rc = 0 if rc is None else 2
    except Exception as e:  # a broken gate must fail the aggregate, not crash it
        print(f"[ERROR] {name}: {type(e).__name__}: {e}", file=buf)
        rc = 2
    return {"name": name, "description": description, "rc": rc,
            "output": buf.getvalue(), "script": script}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help="comma-separated subset of: " +
                    ",".join(g[0] for g in GATES))
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    args = ap.parse_args()

    selected = GATES
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        unknown = wanted - {g[0] for g in GATES}
        if unknown:
            ap.error("unknown gate(s): " + ", ".join(sorted(unknown)))
        selected = [g for g in GATES if g[0] in wanted]

    results = []
    started = time.time()
    for name, script, func, desc in selected:
        results.append(run_gate(name, script, func, desc))
    elapsed = time.time() - started

    if args.json:
        summary = {
            "elapsed_sec": round(elapsed, 3),
            "gates": [{"name": r["name"], "rc": r["rc"],
                       "description": r["description"]} for r in results],
            "passed": sum(1 for r in results if r["rc"] == 0),
            "total": len(results),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "PASS" if r["rc"] == 0 else ("FAIL" if r["rc"] == 1 else "ERROR")
            print("=" * 72)
            print(f"[{status}] {r['name']} — {r['description']} (rc={r['rc']})")
            print("=" * 72)
            print(r["output"].rstrip() or "(no output)")
            print()
        passed = sum(1 for r in results if r["rc"] == 0)
        print("=" * 72)
        print(f"ANE check_all: {passed}/{len(results)} gates passed in {elapsed:.2f}s")
        for r in results:
            if r["rc"] != 0:
                print(f"  FAILED GATE: {r['name']} (rc={r['rc']})")
        print("=" * 72)

    return 0 if all(r["rc"] == 0 for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
