#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ANE document gates: JSON Schema subset validator, ANS-1 canonicalization, banned-term gate.

Usage:
  python tools/validate_ntp.py                       # validate all NTP/IOP/conversion/experience payloads
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
DEFAULT_CONVERSION_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "conversion-1.0.schema.json"
DEFAULT_EXPERIENCE_SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "schemas" / "experience-1.0.schema.json"
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


CONVERSION_MARKER = "conversion_version"
CONVERSION_DIGEST = "conversion_digest"

EXPERIENCE_MARKER = "experience_version"
EXPERIENCE_DIGEST = "experience_digest"


def experience_semantics(inst):
    """Cross-field rules that turn cerebellar promotion from rhetoric into a gate.

    Enforces five things a structural Schema cannot see:
    cerebellar levels must pass all admissibility dimensions, level skipping is
    forbidden, negative knowledge may never be frozen into tables, brain-assisted
    experience must carry model lineage, and retired rules may not stay in the
    cerebellum.
    """
    errors = []
    level = inst.get("distill_level")
    kind = inst.get("process_kind")
    adm = inst.get("admissibility", {})
    cases = adm.get("boundary_cases", {})
    probe = adm.get("staleness_probe")
    cerebellar = level in ("L2", "L3", "L4", "L5")

    if cerebellar:
        if adm.get("decidable") is not True:
            errors.append("$.admissibility: cerebellar levels require decidable=true")
        if adm.get("stability_reps", 0) < 3:
            errors.append("$.admissibility: cerebellar levels require stability_reps>=3")
        if cases.get("positive", 0) < 3 or cases.get("negative", 0) < 2:
            errors.append("$.admissibility: cerebellar levels require >=3 positive and "
                          ">=2 negative cases")
        if not probe or probe == "none":
            errors.append("$.admissibility: cerebellar levels require a staleness_probe "
                          "(rules whose failure cannot be observed are not admissible)")
        if adm.get("net_benefit", 0) < 1:
            errors.append("$.admissibility: cerebellar levels require net_benefit>=1.0")

    if level in ("L1", "L2", "L3", "L4", "L5") and not inst.get("replay_ref"):
        errors.append("$.replay_ref: levels L1 and above require a replayable trace")

    if level in ("L3", "L4", "L5") and not inst.get("previous_level_evidence"):
        errors.append("$.previous_level_evidence: level skipping is forbidden; register "
                      "the evidence of the level below")

    if kind == "negative":
        if level in ("L4", "L5"):
            errors.append("$.distill_level: negative knowledge must not be frozen into "
                          "lookup tables or the compiled baseline")
        if not inst.get("failure_evidence"):
            errors.append("$.failure_evidence: negative experience requires failure evidence")

    if kind == "seed":
        if not inst.get("human_expert_ref"):
            errors.append("$.human_expert_ref: seed rules require a domain expert source")
    elif not inst.get("brain_meta"):
        errors.append("$.brain_meta: brain-assisted experience must record model lineage")

    created, review = inst.get("created_at", ""), inst.get("review_after", "")
    if created and review and review <= created:
        errors.append("$.review_after: must be later than created_at")

    if inst.get("review_state") == "RETIRED" and cerebellar:
        errors.append("$.review_state: retired experience must fall back to L1 "
                      "(cerebellar levels must not keep a retired rule)")
    return errors


def conversion_semantics(inst):
    """Cross-field lifecycle rules a structural Schema cannot express.

    Makes the three ledger lifecycle states machine-checkable:
    BLOCKED (stage exit interrupted), ROLLED_BACK (grey release retreated),
    CLOSED (conversion completed). Returns human-readable violations.
    """
    errors = []
    stages = inst.get("stages", [])
    for i, stage in enumerate(stages):
        state = stage.get("state")
        verified = stage.get("exit_verified", False)
        if state == "BLOCKED" and verified:
            errors.append(f"$.stages[{i}]: BLOCKED stage must not have exit_verified=true")
        if state == "EXIT_VERIFIED" and not verified:
            errors.append(f"$.stages[{i}]: EXIT_VERIFIED stage requires exit_verified=true")
    gray = inst.get("gray_release", {})
    if gray.get("current_step") == "RETIRED" and gray.get("mode") != "RETIRED":
        errors.append("$.gray_release: RETIRED step requires RETIRED mode")
    completion = inst.get("completion", {})
    keys = ("conformity_passed", "old_retired_or_declared", "ledger_archived",
            "human_signoff", "observation_cycle_done")
    if all(completion.get(k) is True for k in keys):
        if gray.get("mode") != "RETIRED":
            errors.append("$.gray_release: completed conversion requires RETIRED mode")
        if any(s.get("state") not in ("EXIT_VERIFIED", "SKIPPED") for s in stages):
            errors.append("$.stages: completed conversion requires all stages "
                          "EXIT_VERIFIED or SKIPPED")
    return errors


def classify(inst):
    """Route a JSON object to the right schema: NTP, IOP kind, conversion, or experience."""
    if "ntp_version" in inst:
        return "ntp", None
    if CONVERSION_MARKER in inst:
        return "conversion", None
    if EXPERIENCE_MARKER in inst:
        return "experience", None
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
    conversion_validator = Validator(json.loads(DEFAULT_CONVERSION_SCHEMA.read_text(encoding="utf-8")))
    experience_validator = Validator(json.loads(DEFAULT_EXPERIENCE_SCHEMA.read_text(encoding="utf-8")))
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
                if ("ntp_version" in raw or CONVERSION_MARKER in raw
                        or EXPERIENCE_MARKER in raw
                        or any(m in raw for _, m in IOP_MARKERS)):
                    failures += 1
                    print(f"[FAIL] {p.name} block#{i}: invalid JSON: {e}")
                continue
            kind, sub = classify(inst)
            if kind == "skip":
                continue
            total += 1
            kinds[kind] = kinds.get(kind, 0) + 1
            if kind == "ntp":
                target = validator
            elif kind == "conversion":
                target = conversion_validator
            elif kind == "experience":
                target = experience_validator
            else:
                target = iop_validators[sub]
            errors = target.validate(inst)
            if kind == "conversion":
                errors += conversion_semantics(inst)
            elif kind == "experience":
                errors += experience_semantics(inst)
            if errors:
                failures += 1
                print(f"[FAIL] {p.name} block#{i} ({kind}/{sub or '-'}):")
                for e in errors:
                    print("       - " + e)
                continue
            digest_key = IOP_DIGESTS.get(sub) if kind == "iop" else (
                CONVERSION_DIGEST if kind == "conversion" else (
                    EXPERIENCE_DIGEST if kind == "experience" else None))
            if digest_key:
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
