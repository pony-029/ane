#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ANE G8 gate: clause-level MD/HTML consistency check (zero dependency).

The two formats are hand-maintained in the DEBUG tracks, so the same clause can
drift (this actually happened in v0.8.0: HTML said "three sentences" while MD
said "three-sentence rule"). This gate extracts every normative clause from both
formats, normalizes markup away, and compares clause-by-clause with fuzzy
matching. Any missing or materially divergent clause fails the gate.

Usage:
  python tools/check_dual_format.py                 # check all configured pairs
  python tools/check_dual_format.py --verbose       # also print matched clauses
  python tools/check_dual_format.py --md A.md --html A.html

Exit code 0 = all clauses aligned, 1 = divergence found.
"""
import argparse
import difflib
import html
import pathlib
import re
import sys

BASE = pathlib.Path(__file__).resolve().parent.parent
PAIRS = [
    # DEBUG pair is gitignored: skipped locally-day-one but graceful in CI clone.
    ("ANE规范-AI原生软件生命体工程范式-DEBUG开发版.md",
     "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.html"),
    # Chinese formal pair IS tracked — the meaningful CI gate.
    ("ANE规范-AI原生软件生命体工程范式.md",
     "ANE规范-AI原生软件生命体工程范式.html"),
    ("ANE-Specification-AI-Native-Engineering-Paradigm.md",
     "ANE-Specification-AI-Native-Engineering-Paradigm.html"),
]
LEVELS = r"【(?:必须|应当|可选|禁止|MUST|SHOULD|MAY)】|\b(?:MUST|SHOULD|MAY|MUST\s+NOT)\b"
MENTION_RE = re.compile(r"【(?:必须|应当|可选|禁止)】\s*[/*、,，]|\b(?:MUST|SHOULD|MAY)\s*/")
THRESHOLD = 0.72

TAG_RE = re.compile(r"<[^>]+>")
MD_MARK_RE = re.compile(r"[*_`>|#]+")
SPACE_RE = re.compile(r"\s+")
PUNCT_RE = re.compile(r"[：:，,；;。.、\"'“”‘’（）()]")


def normalize(raw):
    """Strip format markup and unify punctuation so wording can be compared."""
    s = html.unescape(raw)
    s = TAG_RE.sub(" ", s)
    s = MD_MARK_RE.sub(" ", s)
    s = PUNCT_RE.sub(" ", s)
    s = SPACE_RE.sub(" ", s).strip()
    return s


def atomize(norm):
    """Split one normalized block into one clause per normative marker.

    HTML callouts often bundle several MUSTs in one <div> while MD keeps them
    on separate lines; atomizing both sides makes the comparison like-for-like.
    """
    if MENTION_RE.search(norm):
        return []
    parts = re.split(r"(?=" + LEVELS + r")", norm)
    return [p.strip() for p in parts if re.search(LEVELS, p) and len(p.strip()) >= 4]


def body_only_md(text):
    """Keep normative body only; appendices are process/meta layers."""
    i = text.find("## 附录 A")
    return text if i < 0 else text[:i]


def body_only_html(text):
    i = text.find("APPENDIX A")
    if i < 0:
        return text
    j = text.rfind("<", 0, i)
    return text[:j] if j >= 0 else text[:i]


def extract_md(text):
    """One clause per line (MD normative statements are line-oriented)."""
    out = []
    for line in body_only_md(text).splitlines():
        if re.search(LEVELS, line):
            out.extend(atomize(normalize(line)))
    return out


def extract_html(text):
    """One clause per HTML block element, then normalize and atomize."""
    chunks = re.split(r"</(?:tr|div|p|li|h[1-6]|pre)>|<br\s*/?>", body_only_html(text))
    out = []
    for chunk in chunks:
        if re.search(LEVELS, chunk):
            out.extend(atomize(normalize(chunk)))
    return out


def compare(md_items, html_items):
    """Return (matched pairs, md-only, html-only) using greedy best match."""
    pool = list(html_items)
    pairs, md_only = [], []
    for item in md_items:
        if not pool:
            md_only.append(item)
            continue
        scores = [difflib.SequenceMatcher(None, item, c, autojunk=False).ratio() for c in pool]
        idx = max(range(len(pool)), key=lambda i: scores[i])
        if scores[idx] >= THRESHOLD:
            pairs.append((item, pool.pop(idx), scores[idx]))
        else:
            md_only.append(item)
    return pairs, md_only, pool


def check_pair(md_path, html_path, verbose):
    mdp, htmlp = pathlib.Path(md_path), pathlib.Path(html_path)
    if not mdp.exists() or not htmlp.exists():
        missing = mdp.name if not mdp.exists() else htmlp.name
        print(f"\n=== {pathlib.Path(md_path).name} ===\n  [SKIP] {missing} not present (untracked debug track)")
        return 0
    md_text = mdp.read_text(encoding="utf-8")
    html_text = htmlp.read_text(encoding="utf-8")
    md_items = extract_md(md_text)
    html_items = extract_html(html_text)
    pairs, md_only, html_only = compare(md_items, html_items)
    name = pathlib.Path(md_path).name
    print(f"\n=== {name} ===")
    print(f"  MD clauses: {len(md_items)}  HTML clauses: {len(html_items)}  "
          f"aligned: {len(pairs)}  MD-only: {len(md_only)}  HTML-only: {len(html_only)}")
    if verbose:
        for a, b, score in pairs:
            print(f"  [OK {score:.2f}] {a[:90]}")
    for item in md_only:
        print(f"  [MD-ONLY] {item[:140]}")
    for item in html_only:
        print(f"  [HTML-ONLY] {item[:140]}")
    return len(md_only) + len(html_only)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md")
    ap.add_argument("--html")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    if args.md or args.html:
        if not (args.md and args.html):
            ap.error("--md and --html must be given together")
        pairs = [(args.md, args.html)]
    else:
        pairs = [(str(BASE / m), str(BASE / h)) for m, h in PAIRS]
    failures = sum(check_pair(m, h, args.verbose) for m, h in pairs)
    print(f"\nG8 gate: {failures} divergent clauses")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
