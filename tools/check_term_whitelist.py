#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ANE term whitelist gate: no undefined technical token may enter a normative clause.

This is the reverse side of schemas/banned-terms.json: that manifest blocks known
bad wording; this manifest blocks *unknown new jargon*. A technical token
(backticked term, ALL-CAPS acronym, camelCase identifier) appearing inside a
normative clause must either be listed in schemas/term-whitelist.json or the
clause must carry a source-type annotation (本文原创 / 引用 / Original / Cited).

Usage:
  python tools/check_term_whitelist.py              # check configured tracks
  python tools/check_term_whitelist.py --collect    # dump all tokens found as JSON
  python tools/check_term_whitelist.py --verbose    # print every checked token

Exit code 0 = every technical token is known or source-annotated, 1 = at least
one undefined token found (CI gate). Zero dependency; missing files are skipped
so the gate also runs on a fresh clone where DEBUG tracks are not tracked.
"""
import argparse
import json
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
MANIFEST = BASE / "schemas" / "term-whitelist.json"

LEVELS = r"【(?:必须|应当|可选|禁止|MUST|SHOULD|MAY)】|\b(?:MUST\s+NOT|MUST|SHOULD|MAY)\b"
LEVEL_RE = re.compile(LEVELS)
BACKTICK_RE = re.compile(r"`([^`]+)`")
ACRONYM_RE = re.compile(r"(?<![A-Za-z0-9_-])([A-Z][A-Z0-9-]{2,})(?![A-Za-z0-9_-])")
CAMEL_RE = re.compile(r"\b([a-z][a-zA-Z0-9]*[A-Z][A-Za-z0-9]*)\b")
PASCAL_RE = re.compile(r"\b([A-Z][a-z][A-Za-z0-9]*[A-Z][A-Za-z0-9]*)\b")
HTML_SPLIT_RE = re.compile(r"</(?:tr|div|p|li|h[1-6]|pre)>|<br\s*/?>")


def load_config():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def body_only(text, is_html):
    """Keep normative body only. Appendices are process/meta layers, and may
    quote normative markers in prose (e.g. an audit line discussing 【必须】);
    such quotes are not clauses and must not be scanned (same rule as G8)."""
    marker = "APPENDIX A" if is_html else "## 附录 A"
    i = text.find(marker)
    if i < 0:
        marker = "Appendix A" if is_html else "## Appendix A"
        i = text.find(marker)
    if i < 0:
        return text
    if is_html:
        j = text.rfind("<", 0, i)
        return text[:j] if j >= 0 else text[:i]
    return text[:i]


def chunks(path):
    """Yield (line_no, text) for normative-bearing blocks in a track body."""
    is_html = str(path).endswith(".html")
    text = body_only(pathlib.Path(path).read_text(encoding="utf-8"), is_html)
    if is_html:
        for i, part in enumerate(HTML_SPLIT_RE.split(text), 1):
            if LEVEL_RE.search(part):
                yield i, part
    else:
        for i, line in enumerate(text.splitlines(), 1):
            if LEVEL_RE.search(line):
                yield i, line


def extract_tokens(chunk, cfg):
    """Return the technical tokens in one normative chunk."""
    ex = cfg["matching"]["extraction"]
    found = []
    if ex.get("backticked", True):
        for raw in BACKTICK_RE.findall(chunk):
            t = raw.strip()
            if ex.get("skip_backticked_with_space", True) and re.search(r"\s", t):
                continue
            if t:
                found.append(t)
    if ex.get("uppercase_acronym", True):
        found.extend(ACRONYM_RE.findall(chunk))
    if ex.get("camel_case", True):
        found.extend(CAMEL_RE.findall(chunk))
    if ex.get("pascal_case", True):
        found.extend(PASCAL_RE.findall(chunk))
    return found


def has_source_tag(chunk, cfg):
    return any(tag in chunk for tag in cfg["matching"]["source_tags"])


def check(cfg, verbose):
    allowed = set(cfg["level_tokens"]) | set(cfg["known_tokens"])
    files = cfg["scopes"]["all_tracks"]
    scanned = 0
    checked = 0
    violations = []
    for name in files:
        p = BASE / name
        if not p.exists():
            print(f"[SKIP] {name} (not found)")
            continue
        scanned += 1
        file_violations = 0
        for line_no, chunk in chunks(p):
            if has_source_tag(chunk, cfg):
                continue
            for token in extract_tokens(chunk, cfg):
                checked += 1
                if verbose:
                    print(f"  [TOK] {name}:{line_no} {token!r}")
                if token not in allowed:
                    file_violations += 1
                    violations.append((name, line_no, token, chunk.strip()[:120]))
        print(f"  {name}: {file_violations} undefined token(s)")
    for name, line_no, token, snippet in violations:
        print(f"[FAIL] {name}:{line_no} undefined token '{token}' -> {snippet}")
    print(f"\nTerm-whitelist gate: {checked} token occurrences checked in {scanned} files, "
          f"{len(violations)} undefined")
    return 0 if not violations else 1


def collect(cfg):
    tokens = set()
    for name in cfg["scopes"]["all_tracks"]:
        p = BASE / name
        if p.exists():
            for _, chunk in chunks(p):
                tokens.update(extract_tokens(chunk, cfg))
    print(json.dumps(sorted(tokens), ensure_ascii=False, indent=2))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collect", action="store_true", help="dump all tokens found as JSON")
    ap.add_argument("--verbose", action="store_true", help="print every checked token")
    args = ap.parse_args()
    cfg = load_config()
    return collect(cfg) if args.collect else check(cfg, args.verbose)


if __name__ == "__main__":
    sys.exit(main())
