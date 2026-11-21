#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Make the ANE Gates check mandatory on main (idempotent; needs admin token).

This script does NOT claim that protection is already enabled. It queries the
live GitHub API and reports the truth. Without a token it exits 2 and prints the
exact steps to obtain one — a configuration file is not evidence of enforcement.

Usage:
  GITHUB_TOKEN=... python tools/setup_branch_protection.py --check
  GITHUB_TOKEN=... python tools/setup_branch_protection.py --apply

Environment:
  GITHUB_TOKEN / GH_TOKEN   token with admin rights on the repository
  ANE_GITHUB_REPO           owner/repo (default: pony-029/ane)
  ANE_GITHUB_BRANCH         branch to protect (default: main)
  ANE_REQUIRED_CONTEXT      status check name (default: parsed from workflow)
"""
import argparse
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.request

BASE = pathlib.Path(__file__).resolve().parent.parent
WORKFLOW = BASE / ".github" / "workflows" / "ane-gates.yml"
DEFAULT_CONTEXT = "Payload / terms / dual-format / whitelist"


def required_context():
    """Read the job display name from the workflow so it cannot drift."""
    if WORKFLOW.exists():
        text = WORKFLOW.read_text(encoding="utf-8")
        match = re.search(r"^  validate:\n    name:\s*(.+?)\s*$", text, re.M)
        if match:
            return match.group(1).strip().strip("'\"")
    return DEFAULT_CONTEXT


def api(method, url, token, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "ane-branch-protection/1.0",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if data:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return response.status, json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {"message": body[:300]}
        return exc.code, parsed
    except Exception as exc:
        return -1, {"message": f"{type(exc).__name__}: {exc}"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="only report current protection state")
    parser.add_argument("--apply", action="store_true",
                        help="write/merge protection (requires admin token)")
    parser.add_argument("--json", action="store_true", help="emit JSON summary")
    args = parser.parse_args()
    if args.check and args.apply:
        parser.error("--check and --apply are mutually exclusive")
    apply_changes = args.apply

    repo = os.environ.get("ANE_GITHUB_REPO", "pony-029/ane")
    branch = os.environ.get("ANE_GITHUB_BRANCH", "main")
    context = os.environ.get("ANE_REQUIRED_CONTEXT") or required_context()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com/repos/{repo}/branches/{branch}/protection"

    if not token:
        message = ("No GITHUB_TOKEN/GH_TOKEN found. Cannot read or set branch "
                   "protection. Export a token with admin rights and rerun; "
                   "do not treat the workflow YAML as enforcement.")
        if args.json:
            print(json.dumps({"ok": False, "reason": "no_token",
                              "message": message}, ensure_ascii=False, indent=2))
        else:
            print("[BLOCKED] " + message)
        return 2

    status, current = api("GET", url, token)
    if status == 401 or status == 403:
        message = "Token lacks admin rights: " + str(current.get("message"))
        if args.json:
            print(json.dumps({"ok": False, "reason": "unauthorized", "http": status,
                              "message": message}, ensure_ascii=False, indent=2))
        else:
            print("[BLOCKED] " + message)
        return 2
    if status not in (200, 404):
        message = f"Unexpected GET status {status}: {current.get('message')}"
        print(json.dumps({"ok": False, "reason": "api_error", "http": status,
                          "message": message}, ensure_ascii=False, indent=2))
        return 2

    existing = []
    if status == 200:
        existing = list((current.get("required_status_checks") or {}).get("contexts", []))

    if context in existing:
        summary = {"ok": True, "action": "already_configured", "repo": repo,
                   "branch": branch, "context": context, "contexts": existing}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    if not apply_changes:
        summary = {"ok": False, "action": "would_enable",
                   "reason": "dry_run" if status == 200 else "not_protected",
                   "repo": repo, "branch": branch, "context": context,
                   "contexts_before": existing,
                   "apply_hint": "GITHUB_TOKEN=... python tools/setup_branch_protection.py --apply"}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1

    payload = {
        "required_status_checks": {"strict": True, "contexts": existing + [context]},
        "enforce_admins": False,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    write_status, written = api("PUT", url, token, payload)
    if write_status not in (200, 201):
        summary = {"ok": False, "action": "write_failed", "http": write_status,
                   "message": written.get("message")}
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 2
    summary = {"ok": True, "action": "enabled", "repo": repo, "branch": branch,
               "contexts": (written.get("required_status_checks") or {}).get("contexts", [])}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
