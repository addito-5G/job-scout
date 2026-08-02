# CHALLENGE_PROMPTS — NextMove (lean)

Adversarial prompts for Cursor. Prefer: `@challenge` / «поспорь» (loads `.cursor/rules/challenge.mdc` + skill `devils-advocate`).

Philosophy: the model that wrote the code should not be the only reviewer. Cross-check with a different model when stakes are high.

---

## Stage 1 — Plan (`@challenge plan`)

```
You are a skeptical senior engineer. Do NOT help implement — find why this fails.

Target: [plan / feature]

Produce:
1. FATAL FLAWS
2. HIDDEN ASSUMPTIONS
3. ARCHITECTURAL CONFLICTS (adapters/parsers → services → ui; src/ai/routing.py)
4. SCOPE CREEP RISKS
5. 3 STRESS-TEST QUESTIONS we must answer before coding

Reference: agents/README.md, .cursor/rules/nextmove-agents.mdc
Verdict: PROCEED | PAUSE | REDESIGN
```

### Architecture fit (1B)

```
Before building [feature], answer YES/NO + one line each:
1. New dependency needed, or does the repo already solve it?
2. Duplicates an existing pattern in src/?
3. Needs Alembic migration? Rollback?
4. Touches scrape path, AI routing, or shared vacancy model?
5. Blast radius if HH/AI provider is down?

Verdict: proceed / pause / redesign
```

---

## Stage 2 — Mid (`@challenge mid`)

```
Review work so far vs original intent.

1. SCOPE DRIFT
2. LAYER VIOLATIONS (SQL in ui/, LLM calls in adapters/, etc.)
3. PARTIAL STATE (scan/DB left half-written)
4. UNPLANNED DEPS
5. TESTS — what is untested?

Traffic-light per item with path references.
```

### Breaking changes (2B)

```
Scan this session's changes for breaks to:
- Vacancy/match schema or upsert semantics
- Search settings / query JSON shape
- Public Streamlit flows
- Required env vars
- HH parse contract (InitialState fields)

For each: what breaks, migration, severity.
```

---

## Stage 3 — Commit (`@challenge commit`)

```
Before commit, challenge the diff:

1. Message accurate?
2. Debug leftovers / secrets?
3. Dead code?
4. Config that breaks other machines?
5. Anything future-me regrets in 6 months (especially scrape/AI shortcuts)?

GO | STOP (+ reason)
```

---

## Stage 4 — PR (`@challenge pr`)

```
You maintained this repo for 2 years. Review the PR:

## What's done well
## Must fix (blocking)
## Should fix (debt)
## Doc/test gaps
## Tribal knowledge that needs a comment or agents/ note

Also check layer boundaries and AI routing ownership.
```

### Observability (4C)

```
For this change:
1. Are scrape/AI failures logged with enough context?
2. Does UI show honest empty/error vs silent zero?
3. Rollback: revert commit enough, or data migration needed?
```

---

## Stage 5 — Audit (`@challenge audit`)

```
Tech-debt pass focused on NextMove:
1. HH parser fragility / encoding / period filters
2. Dedupe and upsert edge cases
3. TASK_ROUTING vs actual call sites
4. Dead adapters/UI after HH-only cleanup
5. Tests missing for parse + match paths

Prioritised backlog: severity, effort, risk of ignoring.
```

---

## Stage 6 — Cross-model

Paste the same prompt + diff into a **different** model (e.g. local `qwen2.5-coder` via Ollama) with:

```
You did not write this. Find what the author model missed.
Focus: arbitrary decisions, edge cases, false confidence, security.
```

---

## Quick card

| When | Command |
|------|---------|
| Before feature | `@challenge plan` / «поспорь с планом» |
| During coding | `@challenge mid` |
| Before commit | `@challenge commit` |
| Before PR | `@challenge pr` |
| Schema/API | `@challenge api` |
| Periodic | `@challenge audit` |
