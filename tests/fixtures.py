#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reproducible negative-test fixtures for the ANE gates.

Each fixture mutates ONLY a disposable sandbox copy of the repository. The
real working tree is never touched. A case declares both the expected exit
code and the exact evidence string that must appear in the gate output, so a
case cannot pass merely because an unrelated error made the gate fail.
"""
import hashlib
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate_ntp import canonicalize  # noqa: E402  (reuse the real ANS-1 implementation)

ZH_FORMAL_MD = "ANE规范-AI原生软件生命体工程范式.md"
ZH_DEBUG_MD = "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.md"
ZH_DEBUG_HTML = "ANE规范-AI原生软件生命体工程范式-DEBUG开发版.html"

JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def _replace_conversion(sandbox, mutate, name=ZH_FORMAL_MD, conversion_id=None):
    """Locate a conversion ledger block in one track and apply a mutation."""
    path = sandbox / name
    text = path.read_text(encoding="utf-8")
    blocks = JSON_BLOCK.findall(text)
    if conversion_id:
        needle = f'"conversion_id": "{conversion_id}"'
    else:
        needle = '"conversion_version"'
    idx = next(i for i, b in enumerate(blocks) if needle in b)
    raw = blocks[idx]
    obj = json.loads(raw)
    mutate(obj)
    replacement = json.dumps(obj, ensure_ascii=False, indent=2)
    assert text.count(raw) == 1, "conversion block is not unique in sandbox"
    path.write_text(text.replace(raw, replacement, 1), encoding="utf-8")


def mutate_digest_tamper(sandbox):
    """Change a signed field but leave the ANS-1 digest untouched."""
    def change(obj):
        obj["completion"]["human_signoff"] = True
    _replace_conversion(sandbox, change)


def mutate_schema_violation(sandbox):
    """Introduce an out-of-enum tier, but RECOMPUTE the digest so the failure
    is attributable to the Schema rather than to a stale digest."""
    def change(obj):
        obj["fitness_tier"] = "T9"
        unsigned = {k: v for k, v in obj.items() if k != "conversion_digest"}
        obj["conversion_digest"] = "sha256:" + hashlib.sha256(
            canonicalize(unsigned).encode("utf-8")).hexdigest()
    _replace_conversion(sandbox, change)


def _resign(obj):
    """Recompute the ANS-1 digest so a test isolates SEMANTIC failure only."""
    unsigned = {k: v for k, v in obj.items() if k != "conversion_digest"}
    obj["conversion_digest"] = "sha256:" + hashlib.sha256(
        canonicalize(unsigned).encode("utf-8")).hexdigest()


def mutate_blocked_verified(sandbox):
    """A BLOCKED stage must never claim exit verification (re-signed)."""
    def change(obj):
        for stage in obj["stages"]:
            if stage["state"] == "BLOCKED":
                stage["exit_verified"] = True
                break
        _resign(obj)
    _replace_conversion(sandbox, change,
                        conversion_id="conv-legacy-core-blocked-01")


def mutate_closed_not_retired(sandbox):
    """All completion flags true but grey mode not RETIRED (re-signed)."""
    def change(obj):
        obj["gray_release"]["mode"] = "SHADOW"
        _resign(obj)
    _replace_conversion(sandbox, change,
                        conversion_id="conv-legacy-core-closed-01")


def mutate_undefined_token(sandbox):
    """Inject an undefined PascalCase identifier into a normative clause."""
    path = sandbox / ZH_FORMAL_MD
    text = path.read_text(encoding="utf-8")
    anchor = "**【必须】** 转换台账必须通过转换台账 Schema 校验"
    assert anchor in text, "normative anchor missing in sandbox"
    path.write_text(
        text.replace(anchor,
                     "**【必须】** QuantumFoobarService 必须经转换台账 Schema 校验", 1),
        encoding="utf-8")


def mutate_banned_term(sandbox):
    """Inject a known banned slogan into a delivery track."""
    with (sandbox / ZH_FORMAL_MD).open("a", encoding="utf-8") as fh:
        fh.write("\n三句话沟通是本规范的推荐做法。\n")


def mutate_dualformat_drift(sandbox):
    """Add a clause on the Markdown side only; the HTML side is left intact."""
    path = sandbox / ZH_FORMAL_MD
    text = path.read_text(encoding="utf-8")
    marker = "## 附录 A"
    assert marker in text, "body/appendix boundary missing in sandbox"
    injected = "**【必须】** SelfTestDriftMarker2026 条款仅在 Markdown 侧存在。\n\n"
    path.write_text(text.replace(marker, injected + marker, 1), encoding="utf-8")


def mutate_missing_debug(sandbox):
    """Simulate a fresh CI clone: gitignored DEBUG tracks are absent."""
    for name in (ZH_DEBUG_MD, ZH_DEBUG_HTML):
        path = sandbox / name
        if path.exists():
            path.unlink()


def _replace_experience(sandbox, mutate, name=ZH_FORMAL_MD):
    """Locate the experience record block and apply a mutation to it."""
    path = sandbox / name
    text = path.read_text(encoding="utf-8")
    blocks = JSON_BLOCK.findall(text)
    raw = next(b for b in blocks if '"experience_version"' in b)
    obj = json.loads(raw)
    mutate(obj)
    replacement = json.dumps(obj, ensure_ascii=False, indent=2)
    assert text.count(raw) == 1, "experience block is not unique in sandbox"
    path.write_text(text.replace(raw, replacement, 1), encoding="utf-8")


def _resign_experience(obj):
    """Recompute the experience digest so a case isolates semantic failure only."""
    unsigned = {k: v for k, v in obj.items() if k != "experience_digest"}
    obj["experience_digest"] = "sha256:" + hashlib.sha256(
        canonicalize(unsigned).encode("utf-8")).hexdigest()


def mutate_level_skip(sandbox):
    """An L3 rule with no evidence from the level below: promotion skipped ranks."""
    def change(obj):
        obj.pop("previous_level_evidence", None)
        _resign_experience(obj)
    _replace_experience(sandbox, change)


def mutate_no_staleness_probe(sandbox):
    """A cerebellar rule whose failure cannot be observed."""
    def change(obj):
        obj["admissibility"]["staleness_probe"] = "none"
        _resign_experience(obj)
    _replace_experience(sandbox, change)


def mutate_negative_frozen(sandbox):
    """Negative knowledge frozen into a lookup table (L4)."""
    def change(obj):
        obj["process_kind"] = "negative"
        obj["distill_level"] = "L4"
        obj["failure_evidence"] = ["trace://build/0427/failed-path"]
        _resign_experience(obj)
    _replace_experience(sandbox, change)


def mutate_retired_still_cerebellar(sandbox):
    """A retired rule that still sits at a cerebellar level."""
    def change(obj):
        obj["review_state"] = "RETIRED"
        _resign_experience(obj)
    _replace_experience(sandbox, change)


# id -> gate command (relative to sandbox/tools), expected rc, must-appear evidence
GATE_COMMANDS = {
    "payload": ["validate_ntp.py"],
    "terms": ["validate_ntp.py", "terms"],
    "dualformat": ["check_dual_format.py"],
    "whitelist": ["check_term_whitelist.py"],
    "evidence_flow": ["../tests/test_evidence_flow.py"],
}

CASES = [
    {
        "id": "digest_tamper",
        "description": "签名后改字段，ANS-1 摘要不可重算",
        "gate": "payload", "expect": 1,
        "evidence": "not reproducible via ANS-1",
        "mutate": mutate_digest_tamper,
    },
    {
        "id": "schema_enum_violation",
        "description": "摘要正确但适配分级越界，Schema 必须拒绝",
        "gate": "payload", "expect": 1,
        "evidence": "not in enum",
        "mutate": mutate_schema_violation,
    },
    {
        "id": "blocked_stage_verified",
        "description": "BLOCKED 阶段却标记退出验证通过，跨字段语义必须拒绝（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "BLOCKED stage must not have exit_verified=true",
        "mutate": mutate_blocked_verified,
    },
    {
        "id": "closed_without_retirement",
        "description": "完成判据全 true 但灰度未退役，跨字段语义必须拒绝（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "completed conversion requires RETIRED mode",
        "mutate": mutate_closed_not_retired,
    },
    {
        "id": "undefined_pascal_token",
        "description": "规范性条款引入未定义 PascalCase 标识",
        "gate": "whitelist", "expect": 1,
        "evidence": "undefined token 'QuantumFoobarService'",
        "mutate": mutate_undefined_token,
    },
    {
        "id": "banned_slogan",
        "description": "交付轨出现禁令清单中的口号化表述",
        "gate": "terms", "expect": 1,
        "evidence": "三句话",
        "mutate": mutate_banned_term,
    },
    {
        "id": "dualformat_drift",
        "description": "MD 侧新增条款而 HTML 未同步",
        "gate": "dualformat", "expect": 1,
        "evidence": "[MD-ONLY]",
        "mutate": mutate_dualformat_drift,
    },
    {
        "id": "missing_debug_tracks",
        "description": "CI 克隆缺 DEBUG 轨，四类门禁应优雅跳过而非崩溃",
        "gate": ["payload", "dualformat", "whitelist"], "expect": 0,
        "evidence": "[SKIP]",
        "mutate": mutate_missing_debug,
    },
    {
        "id": "whitelist_evidence_flow",
        "description": "白名单发现→举证→入册：无举证被拒、举证后放行、孤立证据被拒",
        "gate": "evidence_flow", "expect": 0,
        "evidence": "Evidence loop: 7/7 checks passed",
        "mutate": lambda sandbox: None,  # the flow tool builds its own sandbox
    },
    {
        "id": "experience_level_skip",
        "description": "L3 规则缺失下一级证据，跨级升格必须被拒（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "level skipping is forbidden",
        "mutate": mutate_level_skip,
    },
    {
        "id": "experience_no_probe",
        "description": "小脑规则无失效探针，不可观测的规则必须被拒（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "require a staleness_probe",
        "mutate": mutate_no_staleness_probe,
    },
    {
        "id": "experience_negative_frozen",
        "description": "否决型经验被固化为常量表，必须被拒（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "negative knowledge must not be frozen",
        "mutate": mutate_negative_frozen,
    },
    {
        "id": "experience_retired_cerebellar",
        "description": "已退役规则仍停留在小脑级别，台账矛盾必须被拒（摘要正确）",
        "gate": "payload", "expect": 1,
        "evidence": "retired experience must fall back to L1",
        "mutate": mutate_retired_still_cerebellar,
    },
]
