#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sync v0.8.0 content into the English formal tracks (MD + HTML).
Deterministic, repeatable, no external dependencies."""
import html
import pathlib
import re

BASE = pathlib.Path(__file__).resolve().parent.parent
EMD = BASE / "ANE-Specification-AI-Native-Engineering-Paradigm.md"
EHTML = BASE / "ANE-Specification-AI-Native-Engineering-Paradigm.html"

EN_CHAPTERS = r"""
## Chapter 38: Inter-Organism Protocol (IOP)

> **【Original to this specification】** IOP = Inter-Organism Protocol. This chapter extends ANE from a single living system to an ecosystem of living systems. NTP (Chapter 5) handles distress inside one organism; IOP handles identification, delegation, and verification **between independent organisms**.

### 38.1 Why a single-organism protocol is not enough

| Dimension | NTP (Ch. 5) | IOP (this chapter) |
|---|---|---|
| Parties | Cerebellum ↔ Main Brain inside one organism | Organism ↔ organism |
| Trust premise | One sovereignty domain, shared ledger | Separate domains, zero trust by default |
| Payload | Compressed features + error code + budget | Capability claim + task digest + credential |
| Memory | Shared hippocampus | **Not shared by default** (38.5) |
| Failure | Route to `DEGRADED` | Refuse collaboration, keep running independently |

**【MUST】** Every cross-organism call goes through IOP. Never expose the internal NTP channel to an external organism's brain.

### 38.2 Four-layer IOP model

| Layer | Name | Solves | Artefact | Level |
|---|---|---|---|---|
| L1 | Identity | Who are you, who answers for you | Organism Card | 【MUST】 |
| L2 | Capability | What can you do, at which tier | Capability Set | 【MUST】 |
| L3 | Messaging | What is this request, where is the evidence | Envelope | 【MUST】 |
| L4 | Trust | Why should I believe you, who is liable | Credential + ledger ref | 【MUST】 |

Layers cannot be skipped: identity before capability, capability before task, credential before execution.

### 38.3 Organism Card

An Organism Card is the minimal, stable, verifiable self-description of an organism. It exposes identity and boundaries, never internals.

```json
{
  "organism_id": "org-7a31",
  "card_version": "1.0",
  "capabilities": ["classify", "digest"],
  "determinacy": "D1",
  "owner": "human:finlei",
  "card_digest": "sha256:309c06e49be85fc3b26eb8c6f2d1b355678aedef027c5521dba6a8e3b5932821"
}
```

| Field | Type | Plain meaning | Why needed | Level |
|---|---|---|---|---|
| `organism_id` | string | Stable identity | Recognize the same organism across sessions | 【MUST】 |
| `card_version` | string | Card format version | Capability evolves; card must be versioned | 【MUST】 |
| `capabilities` | string[] | Promised capability names | Undeclared capability may not be invoked | 【MUST】 |
| `determinacy` | enum D0–D3 | Highest determinacy tier accepted | Prevents delegating D0 work to a D2-only peer | 【MUST】 |
| `owner` | string | Ultimately responsible human | Axiom 5: liability must land on an accountable subject | 【MUST】 |
| `card_digest` | string | Card fingerprint | Anti-tampering during handshake | 【MUST】 |

**【MUST】** A card must not contain implementation details, model vendors, or secrets. **【MUST】** Card changes require a new `card_version` and a recomputed digest.

### 38.4 Envelope

The envelope carries "who to whom, what, where the evidence is". **The payload body is never inlined** — the same discipline as `candidate.digest` in 5.4.

```json
{
  "iop_version": "1.0",
  "msg_id": "m-4c81",
  "from": "org-7a31",
  "to": "org-9b42",
  "type": "TASK_DELEGATE",
  "payload_ref": "sha256:74490ea0feecf6e8246f97cc81c12544f136f596eb596cbd4ccbeed2c7ec6cbe",
  "payload_format": "ANS-1",
  "traceparent": "00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01",
  "auth_ref": "cred-9d02",
  "ts": "2026-11-21T04:00:00Z",
  "ttl_ms": 30000,
  "determinacy_ceiling": "D1"
}
```

| Field | Plain meaning | Level |
|---|---|---|
| `iop_version` | Protocol version | 【MUST】 |
| `msg_id` | Unique message ID for dedup and replay | 【MUST】 |
| `from` / `to` | Parties, checked against cards | 【MUST】 |
| `type` | `CAPABILITY_QUERY` / `CAPABILITY_ADVERTISE` / `TASK_DELEGATE` / `RESULT_REPORT` / `VETO` | 【MUST】 |
| `payload_ref` | Digest instead of body | 【MUST】 |
| `payload_format` | Fixed to `ANS-1` so digests can be recomputed | 【MUST】 |
| `traceparent` | Distributed trace ID (**referenced** from W3C Trace Context) | 【SHOULD】 |
| `auth_ref` | Credential reference; requests without one are rejected | 【MUST】 |
| `ts` / `ttl_ms` | Timestamp and expiry to stop replay | 【MUST】 |
| `determinacy_ceiling` | Highest determinacy this message may exercise | 【MUST】 |

**【MUST】** Verify card digest, credential, and `ttl_ms` before accepting; discard and log on any failure. **【MAY】** Batch envelopes in high-throughput settings, but each keeps its own `auth_ref`.

### 38.5 Trust boundaries

| Principle | Meaning | Level |
|---|---|---|
| **No shared memory** | A peer never opens its hippocampus; only `digest`-compressed evidence crosses | 【MUST】 |
| **No inherited capability** | Calling a capability grants no permission; credentials are not forwarded | 【MUST】 |
| **No transferred liability** | The delegator remains responsible | 【MUST】 |
| **Veto retained** | Either side may issue `VETO` at any time | 【MUST】 |

### 38.6 Mandatory and optional

| Item | Level |
|---|---|
| Card identity + digest, capability + determinacy declaration | 【MUST】 |
| Six mandatory envelope fields, digest-only payload, credential + TTL | 【MUST】 |
| `traceparent` | 【SHOULD】 |
| Batched envelopes | 【MAY】 |

---

## Chapter 39: Suite Composition

> **【Original to this specification】** A suite is a temporary capability unit composed of independent organisms under a declarative contract. Composition is not fusion: members keep their own lifecycle, owner, and memory boundary.

### 39.1 Declarative contracts, not implicit fusion

| Approach | Risk | Level |
|---|---|---|
| **Declarative contract** (suite manifest) | Configuration overhead | 【MUST】 |
| Implicit shared memory | Memory poisoning, unclear liability | 【MUST NOT】 |
| Hard-coded call chain | One upgrade breaks the whole chain | 【MUST NOT】 |

### 39.2 Suite Manifest

```json
{
  "suite_id": "suite-1f2e",
  "members": ["org-7a31", "org-9b42"],
  "binding": "declarative",
  "suite_digest": "sha256:41cc1149e9108d1d286063a04c38143bee03aefdce7148ade900ef3c400065a5"
}
```

| Field | Plain meaning | Level |
|---|---|---|
| `suite_id` | Stable suite identity | 【MUST】 |
| `members` | Member organism IDs | 【MUST】 |
| `binding` | Fixed to `declarative`, banning implicit fusion at protocol level | 【MUST】 |
| `suite_digest` | Manifest fingerprint against silent member swapping | 【MUST】 |

**【MUST】** A suite may not lower any member's determinacy floor nor exceed the highest `determinacy` among members.

### 39.3 Three composition modes

| Mode | Structure | Use case | Level |
|---|---|---|---|
| Parallel | Same task, cross-verified results | High-assurance judgment | 【SHOULD】 |
| Pipeline | A's digest feeds B | Staged processing | 【SHOULD】 |
| Federation | Independent runs, conclusions only | Privacy-sensitive cross-domain work | 【MAY】 |

### 39.4 Weakest-link protection

- **【MUST】** Verify each member's card digest and promotion audit (24.3) before admission.
- **【MUST】** If any member trips a circuit breaker (21.4), the whole suite degrades — no "sick assembly".
- **【MUST】** D0 affairs are never delegated into a suite; only the human sovereignty layer may handle them.
- **【MAY】** Run member-replacement drills for resilience.

### 39.5 Retirement

Suites are temporary. **【MUST】** Invalidate the manifest and recompute `suite_digest` when the task ends or a member changes. **【MUST】** Retain all evidence and ledger entries: a suite may dissolve, liability may not.

### 39.6 Mandatory and optional

| Item | Level |
|---|---|
| Declarative manifest + digest, admission check, D0 non-delegation, breaker linkage | 【MUST】 |
| Parallel / pipeline modes | 【SHOULD】 |
| Federation, replacement drills | 【MAY】 |

---

## Chapter 40: Evolution Ladder toward an AGI Organism

> **【Original to this specification】** This chapter does not predict when AGI arrives; it defines how a software organism grades its capability boundary while sovereignty never decays.

### 40.1 Evolution is boundary expansion, not permission inflation

| Misconception | Correct reading | Level |
|---|---|---|
| "Stronger AGI automatically earns more authority" | Authority is granted explicitly by humans only | 【MUST】 |
| "Self-improvement may recurse without limit" | Recursion is bounded and every step leaves a verifiable credential | 【MUST】 |
| "Stronger intelligence replaces sovereignty" | Sovereignty is non-delegable (25.5) | 【MUST】 |

### 40.2 Five capability tiers A0–A4

| Tier | Name | Boundary | Authorization | Level |
|---|---|---|---|---|
| A0 | Reflex | Deterministic rules only; `UnknownSignal` on miss | No per-action approval | 【MUST】 start |
| A1 | Memory | Rules + promoted experience | Promotion needs human endorsement | 【MUST】 |
| A2 | Coordinator | A1 + external capability calls | Tool gates (15.6) | 【SHOULD】 |
| A3 | Reasoner | A2 + generalization; proposals only | Dual-track + human review per adoption | 【SHOULD】 |
| A4 | Evolver | A3 + controlled self-improvement proposals | Full promotion audit + human signature | 【MAY】 |

**【MUST】** A4 and above never receive D0 authority. **【MUST】** No direct jump from A3 execution to A4.

### 40.3 Non-decaying authority and bounded recursion

| Constraint | Meaning | Level |
|---|---|---|
| Non-decaying authority | Human veto, breaker, and audit rights never shrink | 【MUST】 |
| Bounded recursion | Improvement depth capped; over the cap returns to human approval | 【MUST】 |
| Reversible capability | Every tier can fall back to a lower tier, drilled in advance | 【MUST】 |
| Credential per step | Every upgrade leaves a verifiable credential in the ledger | 【MUST】 |

### 40.4 Evolution Attestation

```json
{
  "organism_id": "org-7a31",
  "level": "A3",
  "evidence_refs": ["exp_077", "run_2048"],
  "attestation_digest": "sha256:7326a58cd20787f5dd97e8cb551354360aff2abe48e351c01ce14c1d28068f58"
}
```

| Field | Plain meaning | Level |
|---|---|---|
| `organism_id` | Which organism upgraded | 【MUST】 |
| `level` | Target tier A0–A4 | 【MUST】 |
| `evidence_refs` | Evidence IDs — upgrades rely on evidence, not claims | 【MUST】 |
| `attestation_digest` | Anti-forgery, replayable fingerprint | 【MUST】 |

### 40.5 RSI compatibility floor

**【Referenced】** RSI is an upper-bound reference, not a promise. **【MUST】** Three floors hold for any RSI form: human breaker, replayable decisions, traceable liability. **【MAY】** Reserve interfaces for A4; reservation is not activation.

### 40.6 Mandatory and optional

| Item | Level |
|---|---|
| A0/A1 baseline, non-decaying authority, bounded recursion, reversibility, attestation | 【MUST】 |
| A2/A3 | 【SHOULD】 |
| A4, RSI interface reservation | 【MAY】 |

---

## Chapter 41: Communication Data Format, Storage, and Connectivity

### 41.1 Data temperature tiers

| Tier | Holds | Retention | Level |
|---|---|---|---|
| Hot | Rules, state machine, current context | Process lifetime | 【MUST】 |
| Warm | Experience records, promotion audits, recent ledger | Migratable, rebuildable | 【MUST】 |
| Cold | Audit logs, evidence packs | Append-only, searchable | 【SHOULD】 |
| Frozen | Legal retention, liability credentials | Write-once | 【MAY】 |

**【MUST】** Hot data is never persisted to an external service. **【MUST】** Migrating warm data across organisms transfers digests only, never raw memory.

### 41.2 Three format classes

| Class | Format | Prohibited | Level |
|---|---|---|---|
| Envelope | ANS-1 JSON (38.4) | Inlined body, glosses inside values | 【MUST】 |
| Digest | `sha256:<64 lowercase hex>` | Truncated or non-hex digests | 【MUST】 |
| Credential | Unforgeable signature/token ref bound to `msg_id` + `ttl_ms` | Plaintext secrets, replayable tokens | 【MUST】 |

### 41.3 Storage: local-first, layered, migratable

- **【MUST】** Local-first: routine transactions never depend on remote storage.
- **【MUST】** Rebuildable: warm data can be reconstructed from the ledger and evidence packs.
- **【SHOULD】** Decouple tiers so one backend failure cannot take down all layers.
- **【MAY】** Cross-device migration preserving `organism_id` and experience lineage.

### 41.4 Connectivity tri-state

| State | Trigger | Allowed | Level |
|---|---|---|---|
| OFFLINE_FIRST | Default | Local rules + promoted experience handle all routine work | 【MUST】 |
| ON_DEMAND | Local miss + authorization | IOP request or Main Brain call under `budget_hint` | 【SHOULD】 |
| DEGRADED | Timeout / unreachable / budget exhausted | Fall back to Cerebellum-only L2 (21.3b); no guessing | 【MUST】 |

> Must a living organism be online? **It may work offline, but must not only work online.** Connectivity is an enhancement 【SHOULD】; offline capability is a survival floor 【MUST】.

| Risk | Countermeasure | Level |
|---|---|---|
| Data leakage | Transmit digests/features only | 【MUST】 |
| Supply-chain attack | Gate every carrier and tool (5.6 / 15.6) | 【MUST】 |
| Availability dependency | Timeout always degrades | 【MUST】 |
| Cross-sovereignty flow | Align with 20.2; block unlawful transfer | 【MUST】 |

### 41.5 Privacy across organisms

**【MUST】** When an organism executes forgetting (24.4), it notifies peers that received related digests. **【MUST】** Frozen personal data needs a legal basis, not merely audit convenience. **【MAY】** Keep a privacy budget ledger of cumulative outbound volume.

### 41.6 Mandatory and optional

| Item | Level |
|---|---|
| Hot layer never externalized, ANS-1 digests, offline-first + degraded | 【MUST】 |
| On-demand connectivity; cold/frozen tiers | 【SHOULD】/【MAY】 |
| Privacy budget ledger | 【MAY】 |

---

## Chapter 42: Normative Levels and Mandatory Checklist

> **【Referenced】** MUST / SHOULD / MAY follow RFC 2119 and RFC 8174 conventions (**referenced**), adapted into ANE's Chinese labels.

### 42.1 Four labels

| Label | English | Meaning | Consequence |
|---|---|---|---|
| 【MUST】 | MUST / REQUIRED | Mandatory | ANE-CONF fails if unmet |
| 【SHOULD】 | SHOULD / RECOMMENDED | Default expectation | Allowed with written rationale |
| 【MAY】 | MAY / OPTIONAL | Discretionary | No impact |
| 【MUST NOT】 | MUST NOT | Absolutely forbidden | Violates constitutional red line (25.5) |

### 42.2 Syntax and scope

- **【MUST】** Every normative clause carries exactly one level label.
- **【MUST】** The label sits next to the clause, not collected at chapter end.
- **【SHOULD】** Mixed-level clauses label each item separately.
- **【MAY】** The DEBUG view adds origin labels (original/referenced); the formal release keeps normative levels.

### 42.3 Mandatory quick reference

| Chapters | Mandatory items |
|---|---|
| 0–3 | Seven axioms, seven-organ model, D0–D3 |
| 4 | Cerebellum hard boundaries: offline / growable / no speculation |
| 5 | Proposal-only brain, NTP iron laws, ANS-1, binding credential |
| 6–9 | Promotion audit, dual-track verification, sovereignty, two folds |
| 10–21 | Flywheel, five-step order, compliance, fail-safe |
| 22–37 | Stable IDs, AI-BOM, memory isolation, single source, projection, G7 |
| 38 | Card, capability, envelope fields, credential, no shared memory |
| 39 | Declarative suite, admission, D0 non-delegation, breaker linkage |
| 40 | Non-decaying authority, bounded recursion, reversibility, attestation |
| 41 | Local-first, ANS-1, offline-first and degraded |

### 42.4 Conformance and exceptions

**【MUST】** ANE-CONF passes only when all 【MUST】 items pass and no 【MUST NOT】 is violated. **【MUST】** Conclusions state deviations with rationale — no bare pass/fail. **【MUST】** Any exception to a 【MUST】 requires written human approval with scope, expiry, and recovery plan. **【MUST】** Exceptions never touch constitutional red lines. **【MAY】** Exceptions auto-expire.
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def convert(md_text):
    lines, out, para = md_text.split("\n"), [], []
    open_section, counter = False, 38

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            flush(); i += 1; continue
        if line.startswith("## Chapter"):
            flush()
            if open_section:
                out.append("</section>")
            title = line[3:].strip()
            m = re.match(r"Chapter (\d+):\s*(.*)", title)
            num, rest = (m.group(1), m.group(2)) if m else (str(counter), title)
            counter += 1
            out.append('<section id="ch%s">' % num)
            out.append('<h2 class="sec"><span class="num">Chapter %s</span>%s</h2>' % (num, inline(rest)))
            open_section = True; i += 1; continue
        if line.startswith("### "):
            flush(); out.append("<h3>" + inline(line[4:].strip()) + "</h3>"); i += 1; continue
        if line.startswith("> "):
            flush(); out.append('<div class="callout quote">' + inline(line[2:].strip()) + "</div>"); i += 1; continue
        if line.startswith("```"):
            flush(); j = i + 1; buf = []
            while j < len(lines) and not lines[j].startswith("```"):
                buf.append(lines[j]); j += 1
            out.append('<pre style="background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:18px;overflow-x:auto;font-size:12.5px;color:var(--ink2)"><code>' + html.escape("\n".join(buf), quote=False) + "</code></pre>")
            i = j + 1; continue
        if line.startswith("|"):
            flush(); rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            parsed = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
            out.append('<div class="tw"><table><thead><tr>')
            out.extend("<th>" + inline(c) + "</th>" for c in parsed[0])
            out.append("</tr></thead><tbody>")
            for row in parsed[2:]:
                out.append("<tr>")
                out.extend("<td>" + inline(c) + "</td>" for c in row)
                out.append("</tr>")
            out.append("</tbody></table></div>")
            continue
        if re.match(r"^-\s", line):
            flush(); items = []
            while i < len(lines) and re.match(r"^-\s", lines[i]):
                items.append(re.sub(r"^-\s+", "", lines[i])); i += 1
            out.append("<ul>" + "".join("<li>" + inline(x) + "</li>" for x in items) + "</ul>"); continue
        if re.match(r"^\d+\.\s", line):
            flush(); items = []
            while i < len(lines) and re.match(r"^\d+\.\s", lines[i]):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i])); i += 1
            out.append("<ol>" + "".join("<li>" + inline(x) + "</li>" for x in items) + "</ol>"); continue
        if line == "---":
            flush(); i += 1; continue
        para.append(line.strip()); i += 1
    flush()
    if open_section:
        out.append("</section>")
    return "\n".join(out)


SUMMARY_ROW_MD = "| **Living-system ecosystem and normative levels (v0.8.0)** | Inter-Organism Protocol (38) · declarative suite composition (39) · A0–A4 evolution ladder (40) · data temperature tiers and connectivity tri-state (41) · MUST/SHOULD/MAY checklist (42). Previous three recommendations closed: JSON Schema gate, ANS-1, binding credential. |"
SUMMARY_ROW_HTML = "<tr><td><b>Living-system ecosystem and normative levels (v0.8.0)</b></td><td>IOP (38) · declarative suites (39) · A0–A4 ladder (40) · data tiers and connectivity tri-state (41) · MUST/SHOULD/MAY checklist (42); three previous recommendations closed.</td></tr>"


def sync_md():
    s = EMD.read_text(encoding="utf-8")
    s = s.replace("v0.7.0", "v0.8.0")
    if "## Chapter 38: Inter-Organism Protocol" not in s:
        s = s.replace("## Appendix A · Glossary", EN_CHAPTERS.strip() + "\n\n## Appendix A · Glossary", 1)
    if "Living-system ecosystem and normative levels" not in s:
        marker = "| **Carrier governance and engineering closure (v0.7.0)** |"
        idx = s.find(marker)
        if idx >= 0:
            end = s.find("\n", idx)
            s = s[:end + 1] + SUMMARY_ROW_MD + "\n" + s[end + 1:]
    EMD.write_text(s, encoding="utf-8")
    print("EN MD synced:", len(s), "chars")


def sync_html():
    s = EHTML.read_text(encoding="utf-8")
    s = s.replace("v0.7.0", "v0.8.0")
    if '<section id="ch38">' not in s:
        anchor = "<!-- ================= APPENDIX A ================= -->"
        s = s.replace(anchor, convert(EN_CHAPTERS) + "\n\n" + anchor, 1)
    if "Living-system ecosystem and normative levels" not in s:
        marker = "<tr><td><b>Carrier governance and engineering closure"
        idx = s.find(marker)
        if idx >= 0:
            end = s.find("</tr>", idx) + 5
            s = s[:end] + "\n      " + SUMMARY_ROW_HTML + s[end:]
    EHTML.write_text(s, encoding="utf-8")
    print("EN HTML synced:", len(s), "chars, sections", s.count("<section"))


if __name__ == "__main__":
    sync_md()
    sync_html()
