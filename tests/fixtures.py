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
]
