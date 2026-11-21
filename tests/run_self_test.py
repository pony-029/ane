#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run ANE negative fixtures in disposable sandboxes.

The real working tree is never mutated: each case gets a fresh temporary copy
of the tracked documents, schemas and gate tools, and the gate subprocess
resolves its own BASE from that copy.

Usage:
  python tests/run_self_test.py
  python tests/run_self_test.py --only digest_tamper,undefined_pascal_token
  python tests/run_self_test.py --json
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from fixtures import CASES, GATE_COMMANDS  # noqa: E402

COPY_SUFFIXES = {".md", ".html", ".json"}
COPY_DIRS = ("tools", "schemas", "tests")


def build_sandbox(sandbox):
    for directory in COPY_DIRS:
        shutil.copytree(REPO / directory, sandbox / directory)
    for item in REPO.iterdir():
        if item.is_file() and item.suffix in COPY_SUFFIXES:
            shutil.copy2(item, sandbox / item.name)


def run_gate_in_sandbox(sandbox, gate):
    parts = list(GATE_COMMANDS[gate])
    relative = parts.pop(0)
    # Gate tools live in tools/; composite flow tests live in tests/.
    script = (sandbox / relative[3:]) if relative.startswith("../") \
        else (sandbox / "tools" / relative)
    cmd = [sys.executable, str(script)] + parts
    proc = subprocess.run(cmd, cwd=sandbox, capture_output=True, text=True)
    return {"gate": gate, "rc": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr}


def run_case(case):
    sandbox = pathlib.Path(tempfile.mkdtemp(prefix="ane-selftest-"))
    try:
        build_sandbox(sandbox)
        case["mutate"](sandbox)
        gates = case["gate"] if isinstance(case["gate"], list) else [case["gate"]]
        results = []
        passed = True
        for gate in gates:
            res = run_gate_in_sandbox(sandbox, gate)
            evidence = case.get("evidence")
            if isinstance(evidence, dict):
                evidence = evidence.get(gate)
            evidence_ok = (evidence in res["stdout"]) if evidence else True
            rc_ok = res["rc"] == case["expect"]
            ok = rc_ok and evidence_ok
            passed = passed and ok
            results.append({
                "gate": gate, "rc": res["rc"], "expected_rc": case["expect"],
                "evidence": evidence, "evidence_found": evidence_ok, "ok": ok,
                "tail": "\n".join(res["stdout"].strip().splitlines()[-4:]),
                "stderr": res["stderr"][-300:],
            })
        return {"id": case["id"], "description": case["description"],
                "passed": passed, "results": results}
    except Exception as exc:
        return {"id": case["id"], "description": case["description"],
                "passed": False, "error": f"{type(exc).__name__}: {exc}",
                "results": []}
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    ap.add_argument("--only", help="comma-separated case ids")
    args = ap.parse_args(argv)

    selected = CASES
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        unknown = wanted - {c["id"] for c in CASES}
        if unknown:
            ap.error("unknown case(s): " + ", ".join(sorted(unknown)))
        selected = [c for c in CASES if c["id"] in wanted]

    results = [run_case(c) for c in selected]
    passed = sum(1 for r in results if r["passed"])
    if args.json:
        print(json.dumps({"passed": passed, "total": len(results),
                          "cases": results}, ensure_ascii=False, indent=2))
    else:
        for r in results:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"[{status}] {r['id']} — {r['description']}")
            if r.get("error"):
                print("   ERROR:", r["error"])
            for g in r["results"]:
                print(f"   {g['gate']}: rc={g['rc']} (expect {g['expected_rc']}), "
                      f"evidence={g['evidence']!r} found={g['evidence_found']}")
                if not g["ok"]:
                    print("   tail:", g["tail"].replace("\n", " | ")[:300])
        print(f"\nANE self-test: {passed}/{len(results)} negative cases behaved as expected")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
