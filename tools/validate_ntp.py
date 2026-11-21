#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ANE document gates: JSON Schema subset validator, ANS-1 canonicalization, banned-term gate.

Usage:
  python tools/validate_ntp.py                       # validate all NTP payloads in all six tracks
  python tools/validate_ntp.py terms                 # banned-term gate on all tracks + READMEs
  python tools/validate_ntp.py --schema PATH --docs PATH [PATH ...]
  python tools/validate_ntp.py canonicalize FILE.json  # print ANS-1 form and sha256 digest

Exit code 0 = all checks pass (CI gate), 1 = at least one failure.

Supported JSON Schema keywords (the subset used by schemas/ntp-1.1.schema.json):
  type, const, enum, pattern, minimum, maximum, minLength, minItems, maxItems,
  items, required, properties, additionalProperties, oneOf, $ref (#/$defs/...).
"""
import argparse
import hashlib
import json
import pathlib
import re
import sys

DEFAULT_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "ntp-1.1.schema.json"
DEFAULT_IOP_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "iop-1.0.schema.json"
DEFAULT_BANNED = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "banned-terms.json"
DEFAULT_DOCS = [
    "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.md",
    "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.html",
    "ANE规范-AI原生软件生命体工程范式.md",
    "ANE规范-AI原生软件生命体工程范式.html",
    "ANE-Specification-AI-Native-Engineering-Paradigm.md",
    "ANE-Specification-AI-Native-Engineering-Paradigm.html",
]

TYPE_NAMES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "null": type(None), "number": (int, float), "integer": int,
}


class Validator:
    """Self-contained validator for the documented JSON Schema subset."""

    def __init__(self, schema):
        self.root = schema

    def validate(self, inst):
        errors = []
        self._check(inst, self.root, "$", errors)
        return errors

    def _resolve(self, ref):
        if not ref.startswith("#/"):
            raise ValueError("only local #/$defs refs are supported: " + ref)
        node = self.root
        for part in ref[2:].split("/"):
            node = node[part]
        return node

    def _check(self, inst, schema, path, errors):
        if "$ref" in schema:
            self._check(inst, self._resolve(schema["$ref"]), path, errors)
            return

        if "type" in schema:
            expected = schema["type"]
            py = TYPE_NAMES.get(expected)
            if py is None:
                errors.append(f"{path}: unknown type {expected!r} in schema")
                return
            ok = isinstance(inst, py)
            if expected in ("number", "integer") and isinstance(inst, bool):
                ok = False
            if not ok:
                errors.append(f"{path}: expected {expected}, got {type(inst).__name__}")
                return

        if "const" in schema and inst != schema["const"]:
            errors.append(f"{path}: expected const {schema['const']!r}, got {inst!r}")

        if "enum" in schema and inst not in schema["enum"]:
            errors.append(f"{path}: {inst!r} not in enum {schema['enum']!r}")

        if isinstance(inst, str):
            if "pattern" in schema and not re.search(schema["pattern"], inst):
                errors.append(f"{path}: {inst!r} does not match {schema['pattern']!r}")
            if "minLength" in schema and len(inst) < schema["minLength"]:
                errors.append(f"{path}: string shorter than {schema['minLength']}")

        if isinstance(inst, (int, float)) and not isinstance(inst, bool):
            if "minimum" in schema and inst < schema["minimum"]:
                errors.append(f"{path}: {inst} < minimum {schema['minimum']}")
            if "maximum" in schema and inst > schema["maximum"]:
                errors.append(f"{path}: {inst} > maximum {schema['maximum']}")

        if isinstance(inst, list):
            if "minItems" in schema and len(inst) < schema["minItems"]:
                errors.append(f"{path}: array shorter than {schema['minItems']}")
            if "maxItems" in schema and len(inst) > schema["maxItems"]:
                errors.append(f"{path}: array longer than {schema['maxItems']}")
            if "items" in schema:
                for i, item in enumerate(inst):
                    self._check(item, schema["items"], f"{path}[{i}]", errors)

        if isinstance(inst, dict):
            for key in schema.get("required", []):
                if key not in inst:
                    errors.append(f"{path}: missing required property {key!r}")
            props = schema.get("properties", {})
            for key, value in inst.items():
                if key in props:
                    self._check(value, props[key], f"{path}.{key}", errors)
                elif schema.get("additionalProperties") is False:
                    errors.append(f"{path}: unexpected property {key!r}")

        if "oneOf" in schema:
            passed = 0
            branch_errors = []
            for branch in schema["oneOf"]:
                candidate = []
                self._check(inst, branch, path, candidate)
                if not candidate:
                    passed += 1
                else:
                    branch_errors.append(candidate)
            if passed != 1:
                detail = " | ".join(b[0] for b in branch_errors if b) or "no branch matched"
                errors.append(f"{path}: oneOf matched {passed} branches ({detail})")


def extract_blocks(path):
    """Extract all JSON-looking blocks from an MD or HTML track."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    if str(path).endswith(".md"):
        blocks = re.findall(r"```json\s*(.*?)```", text, re.S)
    else:
        blocks = re.findall(r"<pre[^>]*><code>(\{.*?\})</code></pre>", text, re.S)
    return blocks


IOP_KINDS = [
    ("card", "card_digest", "card_digest"),
    ("envelope", "iop_version", None),  # envelope carries payload_ref, no self-digest
    ("suite", "suite_digest", "suite_digest"),
    ("attestation", "attestation_digest", "attestation_digest"),
]
IOP_MARKERS = [(kind, marker) for kind, marker, _ in IOP_KINDS]
IOP_DIGESTS = {kind: digest for kind, _, digest in IOP_KINDS if digest}


def classify(inst):
    """Route a JSON object to the right schema: NTP or one of four IOP kinds."""
    if "ntp_version" in inst:
        return "ntp", None
    for kind, marker in IOP_MARKERS:
        if marker in inst:
            return "iop", kind
    return "skip", None


def check_digest(inst, digest_key):
    """Verify a *_{digest} equals ANS-1(object without that field) sha256."""
    if digest_key not in inst:
        return None
    stated = inst[digest_key]
    clone = dict(inst)
    clone.pop(digest_key)
    computed = "sha256:" + hashlib.sha256(canonicalize(clone).encode("utf-8")).hexdigest()
    return stated == computed


def utf16_key(key):
    """JSON Schema/RFC 8785 ordering: sort by UTF-16 code units."""
    return key.encode("utf-16-be")


def canonicalize(value):
    """ANS-1 canonical serialization (RFC 8785 restricted subset)."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite numbers are not allowed in ANS-1")
        return format(value, ".15g")
    if isinstance(value, list):
        return "[" + ",".join(canonicalize(v) for v in value) + "]"
    if isinstance(value, dict):
        items = sorted(value.items(), key=lambda kv: utf16_key(kv[0]))
        return "{" + ",".join(
            canonicalize(k) + ":" + canonicalize(v) for k, v in items
        ) + "}"
    raise TypeError("unsupported ANS-1 value: " + type(value).__name__)


def term_pattern(term, cfg):
    """Compile a banned term with boundary rules from the manifest.

    ASCII words use full word boundaries so UIR does not match REQUIRED;
    phrases allow an optional trailing 's' (three-sentence -> three-sentences);
    CJK terms use literal substring matching.
    """
    esc = re.escape(term)
    first = term[0]
    is_ascii_word = cfg.get("ascii_word_boundary", True) and re.match(r"^[A-Za-z]+$", term)
    if is_ascii_word:
        return re.compile(r"(?<![A-Za-z0-9_])" + esc + r"(?![A-Za-z0-9_])")
    if cfg.get("ascii_word_boundary", True) and re.match(r"^[A-Za-z0-9][A-Za-z0-9 -]*$", term):
        return re.compile(r"(?<![A-Za-z0-9])" + esc + r"s?(?![A-Za-z0-9-])")
    return re.compile(esc)


def check_terms(base):
    """Scan every delivery track for banned slogans, product names and project names."""
    cfg = json.loads(DEFAULT_BANNED.read_text(encoding="utf-8"))
    scopes = cfg["scopes"]
    failures = 0
    checked = 0
    for scope_name, files in scopes.items():
        for name in files:
            p = base / name
            if not p.exists():
                print(f"[SKIP] {name} (not found)")
                continue
            text = p.read_text(encoding="utf-8")
            lines = text.splitlines()
            for entry in cfg["terms"]:
                if entry["scope"] != scope_name:
                    continue
                if cfg["matching"].get("case_insensitive"):
                    flags = re.IGNORECASE
                else:
                    flags = 0
                rx = term_pattern(entry["term"], cfg["matching"])
                if flags:
                    rx = re.compile(rx.pattern, flags)
                for ln, line in enumerate(lines, 1):
                    if rx.search(line):
                        failures += 1
                        print(f"[FAIL] {name}:{ln} [{entry['category']}] "
                              f"'{entry['term']}' -> '{entry['replacement']}': {line.strip()[:100]}")
            checked += 1
    print(f"\nBanned-term gate: {checked} files scanned, {failures} violations")
    return 0 if failures == 0 else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", nargs="?", default="validate", choices=["validate", "terms", "canonicalize"])
    ap.add_argument("target", nargs="?", help="JSON file for canonicalize")
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    ap.add_argument("--docs", nargs="*", default=DEFAULT_DOCS)
    args = ap.parse_args()

    if args.command == "canonicalize":
        if not args.target:
            ap.error("canonicalize requires a JSON file path")
        obj = json.loads(pathlib.Path(args.target).read_text(encoding="utf-8"))
        form = canonicalize(obj)
        print(form)
        print("sha256:" + hashlib.sha256(form.encode("utf-8")).hexdigest())
        return 0

    base = pathlib.Path(__file__).resolve().parent.parent

    if args.command == "terms":
        return check_terms(base)

    schema = json.loads(pathlib.Path(args.schema).read_text(encoding="utf-8"))
    validator = Validator(schema)
    iop_root = json.loads(DEFAULT_IOP_SCHEMA.read_text(encoding="utf-8"))
    iop_validators = {
        kind: Validator({"$defs": iop_root["$defs"], "$ref": "#/$defs/" + kind})
        for kind, _, _ in IOP_KINDS
    }
    failures = 0
    total = 0
    digests = 0
    for doc in args.docs:
        p = pathlib.Path(doc)
        if not p.is_absolute():
            p = base / p
        if not p.exists():
            print(f"[SKIP] {doc} (not found)")
            continue
        blocks = extract_blocks(p)
        if not blocks:
            print(f"[SKIP] {doc} (no JSON payloads)")
            continue
        kinds = {}
        for i, raw in enumerate(blocks, 1):
            try:
                inst = json.loads(raw)
            except json.JSONDecodeError as e:
                if "ntp_version" in raw or any(m in raw for _, m in IOP_MARKERS):
                    failures += 1
                    print(f"[FAIL] {p.name} block#{i}: invalid JSON: {e}")
                continue
            kind, sub = classify(inst)
            if kind == "skip":
                continue
            total += 1
            kinds[kind] = kinds.get(kind, 0) + 1
            target = validator if kind == "ntp" else iop_validators[sub]
            errors = target.validate(inst)
            if errors:
                failures += 1
                print(f"[FAIL] {p.name} block#{i} ({kind}/{sub or '-'}):")
                for e in errors:
                    print("       - " + e)
                continue
            if kind == "iop" and sub in IOP_DIGESTS:
                digest_key = IOP_DIGESTS[sub]
                ok = check_digest(inst, digest_key)
                if ok is False:
                    failures += 1
                    print(f"[FAIL] {p.name} block#{i}: {digest_key} not reproducible via ANS-1")
                elif ok is True:
                    digests += 1
            print(f"[PASS] {p.name} block#{i} [{kind}{'/' + sub if sub else ''}]")
        print(f"  {p.name}: " + (", ".join(f"{k}={v}" for k, v in kinds.items()) or "no contract payload"))
    print(f"\nPayload gate: {total - failures}/{total} payloads valid; "
          f"{digests} IOP digests reproducible")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
