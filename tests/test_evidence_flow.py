#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end test of the whitelist evidence loop.

Verifies: discover -> evidence -> register, that uncited tokens stay blocked,
and that an orphan provenance entry (token deleted by hand) is rejected.
Runs entirely in a disposable sandbox.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from run_self_test import build_sandbox  # noqa: E402

ZH = "ANE规范-AI原生软件生命体工程范式.md"
TOOL = "check_term_whitelist.py"


def main():
    sandbox = pathlib.Path(tempfile.mkdtemp(prefix="ane-evidence-"))
    try:
        build_sandbox(sandbox)
        path = sandbox / ZH
        text = path.read_text(encoding="utf-8")
        marker = "## 附录 A"
        assert marker in text, "body/appendix boundary missing"
        injected = (
            "**【本文原创】** **【必须】** EvidenzedToken2026 属于带来源标注的新术语。\n"
            "**【必须】** UncitedToken2026 属于无来源标注的新术语。\n\n"
        )
        path.write_text(text.replace(marker, injected + marker, 1), encoding="utf-8")

        def run(*args):
            return subprocess.run(
                [sys.executable, str(sandbox / "tools" / TOOL), *args],
                cwd=sandbox, capture_output=True, text=True)

        manifest_path = sandbox / "schemas" / "term-whitelist.json"
        checks = []

        result = run("--sync-from-evidence")
        data = json.loads(result.stdout)
        checks.append((
            "dry-run separates evidenced from uncited tokens",
            [a["token"] for a in data["admissible"]] == ["EvidenzedToken2026"]
            and [r["token"] for r in data["rejected"]] == ["UncitedToken2026"]))
        checks.append((
            "dry-run does not modify the manifest",
            "EvidenzedToken2026" not in manifest_path.read_text(encoding="utf-8")))

        run("--sync-from-evidence", "--apply")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        provenance = manifest.get("provenance", {}).get("EvidenzedToken2026", {})
        checks.append((
            "--apply registers evidenced token with source + evidence_ref",
            "EvidenzedToken2026" in manifest["known_tokens"]
            and provenance.get("source_type") == "本文原创"
            and provenance.get("evidence_ref", "").startswith(ZH + ":")))
        checks.append((
            "--apply keeps uncited token out of the manifest",
            "UncitedToken2026" not in manifest["known_tokens"]))

        result = run()
        checks.append((
            "gate still blocks the uncited token after apply",
            result.returncode == 1 and "UncitedToken2026" in result.stdout))

        amended = path.read_text(encoding="utf-8").replace(
            "**【必须】** UncitedToken2026",
            "**【本文原创】** **【必须】** UncitedToken2026", 1)
        path.write_text(amended, encoding="utf-8")
        run("--sync-from-evidence", "--apply")
        checks.append((
            "source annotation then admission turns the gate green",
            run().returncode == 0))

        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["known_tokens"].remove("EvidenzedToken2026")
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                 encoding="utf-8")
        result = run()
        checks.append((
            "orphan provenance is rejected",
            result.returncode == 1 and "orphan" in result.stdout))

        for label, ok in checks:
            print(f"[{'PASS' if ok else 'FAIL'}] {label}")
        passed = sum(1 for _, ok in checks if ok)
        print(f"\nEvidence loop: {passed}/{len(checks)} checks passed")
        return 0 if passed == len(checks) else 1
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
