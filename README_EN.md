# ANE Specification

> **ANE Specification — AI-Native Engineering Paradigm for Living Software Systems**
>
> **A living-software engineering paradigm for the age of AI agents · General edition**

**Created by Feng Lei (冯磊)** · original paradigm proposer and chief architect

[English README](README_EN.md) · [中文 README](README.md)

---

## In one sentence

ANE (AI Native Engineering) is a **general software engineering paradigm** for the age of AI agents. It treats software as a "digital living organism," constraining probabilistic intelligence with a deterministic skeleton, so that "what can be proven goes to the static layer, what is uncertain goes to intelligence, and what crosses a red line goes to humans." It binds to no specific product, framework, or engineering implementation and applies to all teams building AI-native software systems.

Three moats: **Cerebellum first** (high-frequency decisions cost zero tokens) · **memory promotion** (a Main Brain insight becomes a Cerebellum instinct) · **dual-track immunity** (symbolic and statistical tracks must both pass before release).

## Current version

**v0.11.0** (2026-11-21) — gate self-proving and CI evidence layer.

Thirteenth round: §43.10 three ledger lifecycle states (BLOCKED / ROLLED_BACK / CLOSED) with cross-field semantic gates; assetized negative fixtures in `tests/` (9 cases, sandbox execution, evidence assertions, zero worktree pollution) and `check_all --self-test`; whitelist evidence loop (`--collect-evidence` / `--sync-from-evidence --apply` + provenance); CI workflow upgraded to run the self-test; real GitHub Actions receipt and branch-protection script. All four previous recommendations closed with real implementations and end-to-end negative tests. Unified command: `python tools/check_all.py --self-test`.

The full version evolution and revision discipline are specified in Chapters 34–37 of the specification; the eighth 30-round plan (round-level) is in Appendix J of the DEBUG edition.

## File manifest

| File | Description |
|---|---|
| `ANE规范-AI原生软件生命体工程范式.md` | Chinese formal release (Markdown) |
| `ANE规范-AI原生软件生命体工程范式.html` | Chinese formal release (HTML, with sidebar nav and Mermaid diagrams) |
| `ANE-Specification-AI-Native-Engineering-Paradigm.md` | English authoritative translation (Markdown) |
| `ANE-Specification-AI-Native-Engineering-Paradigm.html` | English authoritative translation (HTML) |
| `schemas/iop-1.0.schema.json` | IOP four-payload machine contract (card / envelope / suite / attestation) |
| `schemas/banned-terms.json` | Banned-term manifest (slogans / product names / project names / process traces) |
| `tools/check_dual_format.py` | G8 gate: clause-level MD/HTML verbatim consistency |
| `schemas/conversion-1.0.schema.json` | Ch.43 conversion ledger contract (tiers / stages / grey release / migration / completion) |
| `schemas/term-whitelist.json` | Term whitelist: technical identifiers permitted in normative clauses |
| `tools/check_term_whitelist.py` | Whitelist gate: blocks undefined technical identifiers in normative clauses |
| `tools/check_all.py` | Unified gate: one entry point and exit code for all four gates (CI entry point) |
| `.github/workflows/ane-gates.yml` | GitHub Actions: runs check_all on push/PR |
| `tests/fixtures.py` | Assetized negative cases: digest tamper, schema violation, semantic breach, undefined token, wording, dual-format, missing track |
| `tests/run_self_test.py` | Sandbox runner: disposable copies + evidence assertions, zero pollution |
| `tests/test_evidence_flow.py` | Evidence loop test: discover to evidence to register to orphan rejection |
| `tools/setup_branch_protection.py` | Branch protection: query / idempotently enable the mandatory ANE Gates check (admin token) |
| `README.md` / `README_EN.md` | Chinese / English project notes |
| `LICENSE` / `LICENSE-zh.md` | CC BY 4.0 licence (English legal text / Chinese translation) |

> Formal-release filenames carry **no suffix**; the DEBUG development edition (containing the six-hat audits, iteration plans, and version prehistory as process-layer content) carries a `-DEBUG开发版` suffix and is not among the externally released artefacts.

## Structure

The specification has **37 chapters + a glossary (Appendix A)**, organized in layers:

| Layer | Chapters | Topic |
|---|---|---|
| Foundation | 0–1 | Paradigm positioning, seven core axioms (static-dynamic duality, cerebellum first, memory moat, human sovereignty, etc.) |
| Architecture | 2–8 | Seven-organ model, D0–D3 determinacy grading, Cerebellum / Main Brain / Hippocampus / Immune / Self-Repair specifications |
| Collaboration | 9–16 | Human-machine collaboration and tiered authorization, unified development-maintenance flywheel, interaction-pattern matrix, interaction primitives, MCP tool ecosystem, multi-agent protocols |
| Assurance | 17–24 | OWASP security alignment, cost governance, sublation of traditional engineering, organizational governance and compliance, fail-safe, identity traceability, human factors, memory boundaries |
| Governance | 25–31 | Meta-specification, conformance assessment (ANE-CONF), migration and adoption, observability, evolution-system testing, applicability boundaries, economics |
| Release | 32–37 | Release forms, information grading and gates, single source of truth and deterministic projection, multi-language governance, artefact naming, structural integrity checks |

### Five additions and four fixes in v0.8.0 (v0.7.0 archived below)

1. **Model Carrier Governance (5.6)** — six selection criteria · mandatory model card · upgrade/retirement gate · replaceable carrier that never becomes an architectural dependency.
2. **Prompt Asset Governance (18.4)** — versioned templates with stable IDs · frozen-glossary interface · injection guard · change evaluation and rollback.
3. **Incident Response and Blameless Postmortem (21.5)** — turns "same-round failure reporting" into a detect → contain → root-cause → recover → postmortem → promotion loop; concealment and ledger tampering are the real red lines.
4. **Substantive ISO 42001 Alignment (20.2)** — adds the seven-element management-system mapping previously claimed in the summary but absent from the body.
5. **NTP Timeout and Deduplication Parameters (5.5)** — D-tier timeout ranges, same-source merge windows, uplink caps, and cooling windows; timeouts always route to DEGRADED.
6. **Three Arbitration Observability Metrics (12.1)** — quota exhaustion rate / rejection rate / D0-D1 preemption rate, making arbitration fairness auditable.

Also fixes four classes of issue: three misplaced cross-references (Promotion Audit → 24.3, two-brain extreme states → 21.3b), one name–reality mismatch, three stale "new this round" labels, and the parseability of the NTP payload examples (5.2 / 5.4) — all three are now valid JSON, with enum catalogues and field glosses moved into per-field glossaries, environment variables expressed as abstract tiers, and downlink candidates carrying only a `candidate.digest` fingerprint instead of inlined bodies, enforcing "the Main Brain never lands directly" at the protocol layer.

### Four groups of enhancements in v0.6.0 (archived)

1. **Five-Step Evolution Algorithm (10.4)** — delete → simplify → optimize → accelerate → automate; the order may not be inverted, and skipping a step pipelines debt.
2. **Execution Discipline (10.5)** — structured escalation (problem / tried / needed) · same-round failure reporting · integrated high-cohesion fusion · grey release at 99%.
3. **Two-Brain Hard Boundary and High-Order NTP Channel (4.4 / 5.3 / 5.4 / 5.5)** — three hard boundaries of the Cerebellum (offline capability / growable / no speculation) · uplink distress and downlink proposal schemas · four iron laws · communication state machine, channel arbitration, and explore/exploit rate limiting.
4. **Two-Brain Extreme States (21.3b)** — Main Brain unreachable falls back to Cerebellum-only L2; memory contamination freezes promotion and degrades to a memoryless state; neither permits "escalating while sick."

### Five enhancements in v0.5.0 (archived)

1. **Cold Start and Knowledge Quenching (6.4)** — seed-rule injection + explore/exploit adaptive switching, solving "cost overruns on an empty memory from day one."
2. **Hardware-Topology Awareness (2.3 / 8.5)** — the semantic layer adaptively optimizes by processor capabilities, accelerator count, and memory and storage characteristics.
3. **Domestic Regulatory Alignment (20.2)** — alignment with China's Data Security Law, Personal Information Protection Law, and MLPS 2.0 Level 3, explaining how human sovereignty and anti-self-deception satisfy "traceability and controllability."
4. **Dual-Fold Collaboration (13.4 / 14.3)** — a mandatory human-machine pattern (Fold 1 judgment / Cognitive Summary + Fold 2 authorization / Intent Binding) and its primitive encoding.
5. **Promotion Audit (24.3)** — N consecutive independent reproductions + human signature endorsement + anti-inbreeding check before experience promotion, guarding against memory-promotion poisoning.

## Core ideas

- **Static-dynamic integration**: the static is the foundation, the dynamic is the soul; stillness within motion, motion within stillness.
- **Unified development and maintenance**: running is sensing, sensing is maintenance, maintenance is development, development is evolution.
- **Stability first, mutation controlled**: every AI mutation must pass immune gates, and humans always hold ultimate sovereignty.
- **Full-spectrum white box, no silence**: every conclusion is replayable and auditable; silent failures equal zero.

## Licence

The content of this specification is licensed under [CC BY 4.0](LICENSE) — free to share and adapt, with attribution to Feng Lei. See [LICENSE](LICENSE) (English legal text) and [LICENSE-zh.md](LICENSE-zh.md) (Chinese translation).

---

*ANE = AI Native Engineering · the static is bone and blood, the dynamic is nerve and thought; memory and immunity make it "itself."*

## CI evidence receipt

| Item | Fact |
|---|---|
| Workflow | `ANE Gates` (id `425704765`, state `active`) |
| Real run | `44869211636`, conclusion `success`, at `2026-11-21T05:05:29Z`, commit `fdc1882` |
| Query | read-only GitHub API: `GET /repos/pony-029/ane/actions/workflows/ane-gates.yml/runs` |
| Local equivalent | fresh-clone simulation (no DEBUG tracks): 5/5 gates, 9/9 negative cases |
| Branch protection | **not enabled yet**: API returned `401 Requires authentication` (no admin token); run `GITHUB_TOKEN=... python tools/setup_branch_protection.py --apply`, which reads the state back |

> The real run above used the v0.10.0 configuration. This version adds `--self-test`; its configuration was verified by a fresh-clone simulation, and the post-push run conclusion is authoritative via the API.
