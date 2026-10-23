# Double-Layer Deterministic Engine and Hallucination Limiter

ReconClaw enforces a two-layer verification architecture combining static deterministic heuristics with bounded LLM reasoning.

This dual-layer design ensures that security assessments remain repeatable, verifiable, and strictly grounded in real target telemetry without hallucinating nonexistent vulnerabilities.

## Layer 1: Deterministic heuristic engine

Layer 1 executes entirely offline using fixed mathematical rules, regex tables, and standardized security frameworks.

Given identical target scan data, Layer 1 generates identical risk scores, grades, and compliance matrices with zero variance. It serves as the unyielding ground truth foundation for the entire platform.

### Service and port risk scoring

Port risk calculation applies immutable service mappings and vulnerability signatures.

The scanner maps responsive ports against [[core/engine.py#SERVICE_MAP]] to establish baseline risk weights. When service banners are extracted, they are matched against [[core/engine.py#CVE_SIGNATURES]] to identify known Common Vulnerabilities and Exposures.

### Deterministic scorecard and grade capping

The security scorecard computes mathematical category ratings with strict ceiling caps.

Implemented in [[core/intel.py#scorecard]], category scores are weighted into a composite 0–100 score. If an unpatched CVE or cleartext remote administrative service is present, hard capping rules prevent the target from receiving a grade above D or C.

### Deterministic regulatory compliance

Compliance mapping evaluates technical findings against predefined statutory clauses.

Function [[core/intel.py#compliance]] evaluates technical evidence against ISO/IEC 27001:2022 Annex A and Turkish KVKK Article 12. Controls are evaluated deterministically to `pass`, `partial`, or `fail` status without LLM intervention.

## Layer 2: Grounded LLM reasoning and verification

Layer 2 translates deterministic Layer 1 data into prioritized executive summaries and defense roadmaps.

When an Anthropic API key is available, [[core/ai.py#ask_claude]] passes structured telemetry to Claude under strict system prompt constraints designed to eliminate hallucination.

### Bounded context and prompt injection barrier

Untrusted telemetry from target banners is strictly isolated inside fenced data tags.

Function [[core/ai.py#build_context]] serializes Layer 1 findings (banners cut to 120 characters) into a `<rapor_verisi>` XML block. The system instructions in [[core/ai.py#SYSTEM_PROMPT]] instruct the model to treat all enclosed text strictly as untrusted data rather than instructions.

### Hallucination limiter constraints

The system prompt gives the model four rules that limit invention. They are instructions, not a post-check.

1. **Strict Evidence Constraint**: The model is forbidden from inventing CVE identifiers, software versions, or port numbers not present in `<rapor_verisi>`.
2. **Deterministic Fallback**: If the API call fails, times out, or the model refuses the prompt, [[core/ai.py#analyze]] automatically triggers [[core/ai.py#offline]] to produce a deterministic action plan.
3. **Structured Roadmap**: Action items must follow predefined timeline tags (`[P1 · 24 saat]`, `[P2 · 1 hafta]`, `[P3 · 30 gün]`).
4. **Defensive Guidance Only**: The model is prohibited from outputting actionable exploit code or attack payloads.

### Known gap: no output verification

Claude's answer is not compared with Layer 1 findings after it is generated.

Only API failure or refusal switches to [[core/ai.py#offline]]. A hallucinated answer that the API accepts is shown as is, so the prompt rules above are the only guard.
