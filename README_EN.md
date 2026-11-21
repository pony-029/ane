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

**v0.7.0** (2026-11-21) — model carrier, prompt asset, incident response, and substantive compliance layer.

The full version evolution and revision discipline are specified in Chapters 34–37 of the specification.

## File manifest

| File | Description |
|---|---|
| `ANE规范-AI原生软件生命体工程范式.md` | Chinese formal release (Markdown) |
| `ANE规范-AI原生软件生命体工程范式.html` | Chinese formal release (HTML, with sidebar nav and Mermaid diagrams) |
| `ANE-Specification-AI-Native-Engineering-Paradigm.md` | English authoritative translation (Markdown) |
| `ANE-Specification-AI-Native-Engineering-Paradigm.html` | English authoritative translation (HTML) |
| `README.md` / `README_EN.md` | Chinese / English project overview |
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

### Six enhancements and four fixes in v0.7.0

1. **Model Carrier Governance (5.6)** — six selection criteria · mandatory model card · upgrade/retirement gate · replaceable carrier that never becomes an architectural dependency.
2. **Prompt Asset Governance (18.4)** — versioned templates with stable IDs · frozen-glossary interface · injection guard · change evaluation and rollback.
3. **Incident Response and Blameless Postmortem (21.5)** — turns "no overnight bad news" into a detect → contain → root-cause → recover → postmortem → promotion loop; concealment and ledger tampering are the real red lines.
4. **Substantive ISO 42001 Alignment (20.2)** — adds the seven-element management-system mapping previously claimed in the summary but absent from the body.
5. **NTP Timeout and Deduplication Parameters (5.5)** — D-tier timeout ranges, same-source merge windows, uplink caps, and cooling windows; timeouts always route to DEGRADED.
6. **Three Arbitration Observability Metrics (12.1)** — quota exhaustion rate / rejection rate / D0-D1 preemption rate, making arbitration fairness auditable.

Also fixes four classes of issue: three misplaced cross-references (Promotion Audit → 24.3, two-brain extreme states → 21.3b), one name–reality mismatch, three stale "new this round" labels, and the parseability of the NTP payload examples (5.2 / 5.4) — all three are now valid JSON, with enum catalogues and field glosses moved into per-field glossaries, environment variables expressed as abstract tiers, and downlink candidates carrying only a `candidate.digest` fingerprint instead of inlined bodies, enforcing "the Main Brain never lands directly" at the protocol layer.

### Four groups of enhancements in v0.6.0 (archived)

1. **Five-Step Evolution Algorithm (10.4)** — delete → simplify → optimize → accelerate → automate; the order may not be inverted, and skipping a step pipelines debt.
2. **Execution Discipline (10.5)** — three-sentence communication (problem / tried / needed) · no overnight bad news · integrated die-casting · grey release at 99%.
3. **Two-Brain Hard Boundary and High-Order NTP Channel (4.4 / 5.3 / 5.4 / 5.5)** — three hard boundaries of the Cerebellum (offline capability / growable / no speculation) · uplink distress and downlink proposal schemas · four iron laws · communication state machine, channel arbitration, and explore/exploit rate limiting.
4. **Two-Brain Extreme States (21.3b)** — Main Brain unreachable falls back to Cerebellum-only L2; memory contamination freezes promotion and degrades to a memoryless state; neither permits "escalating while sick."

### Five enhancements in v0.5.0 (archived)

1. **Cold Start and Knowledge Quenching (6.4)** — seed-rule injection + explore/exploit adaptive switching, solving "burning money on an empty memory from day one."
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
