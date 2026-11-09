# PrepSense Answer Evaluator Calibration Report (Week 4)

**Date:** 2026-11-09 14:07:52
**Workstream:** Member 4 — Answer Evaluation Agent
**Model Mode:** Offline / Deterministic Benchmark

## 1. Executive Summary

This report measures the scoring accuracy, rubric breakdown validity, and weak-to-strong calibration consistency of the **Version 3 Answer Evaluator**.

### Key Requirements Tested
- **Monotonicity:** Verify that `Score(Weak) < Score(Average) < Score(Strong)` across all question types.
- **Deterministic Python Math:** Verify that criteria weights correctly compute the composite score.
- **Evidence Quality:** Confirm each scored dimension cites concrete candidate answer evidence.
- **Zero Fabricated Scores:** Strict validation rejects malformed responses without defaulting to arbitrary scores.

---

## 2. Technical Calibration
**Question:** *"How would you optimize a slow PostgreSQL query?"*
**Role Context:** `Role: Backend Developer. Key skills: PostgreSQL, Python, FastAPI.`

| Tier | Expected Range | Actual Score | Breakdown | Target Met? | Reasoning / Evidence Summary |
|---|---|---|---|---|---|
| **WEAK** | `1–3` | **2/10** | `techni`: 2, `proble`: 1, `releva`: 3, `clarit`: 3 | ✅ PASS | Fails to diagnose root cause; restarting or vertical scaling does not optimize query logic. |
| **AVERAGE** | `5–7` | **6/10** | `techni`: 6, `proble`: 5, `releva`: 7, `clarit`: 6 | ✅ PASS | Correct basic concept (indexing) but lacks execution tooling (EXPLAIN ANALYZE), join analysis, or trade-offs. |
| **STRONG** | `8–10` | **9/10** | `techni`: 9, `proble`: 9, `releva`: 9, `clarit`: 9 | ✅ PASS | Production-grade diagnostic flow, exact tooling, buffer analysis, composite/partial indexing, and post-change verification. |

**Tier Separation & Monotonicity:** ✅ PASSED (Weak < Average < Strong) (`2` < `6` < `9`)

## 2. Behavioral Calibration
**Question:** *"Tell me about a time you faced a critical production bug right before a release."*
**Role Context:** `Role: Full Stack Engineer.`

| Tier | Expected Range | Actual Score | Breakdown | Target Met? | Reasoning / Evidence Summary |
|---|---|---|---|---|---|
| **WEAK** | `1–3` | **2/10** | `situat`: 3, `action`: 1, `result`: 2, `commun`: 3 | ✅ PASS | Passive voice, zero personal action or ownership, vague impact. |
| **AVERAGE** | `5–7` | **7/10** | `situat`: 7, `action`: 7, `result`: 6, `commun`: 7 | ✅ PASS | Clear situation and personal action, but lacks quantitative impact, team coordination, or preventive post-mortem measures. |
| **STRONG** | `8–10` | **9/10** | `situat`: 9, `action`: 9, `result`: 9, `commun`: 9 | ✅ PASS | Comprehensive STAR structure: clear stakes, proactive cross-functional action, quantified resolution time, zero customer impact, and lasting prevention. |

**Tier Separation & Monotonicity:** ✅ PASSED (Weak < Average < Strong) (`2` < `7` < `9`)

---

## 3. Reliability & Calibration Summary

| Metric | Target | Result | Status |
|---|---|---|---|
| **Score Range Compliance** | 100% | 6/6 (100.0%) | ✅ PASS |
| **Weak/Avg/Strong Separation** | Weak < Avg < Strong | Confirmed for Technical & Behavioral | ✅ PASS |
| **Python Score Calculation** | Exact weighted sum | 0 calculation discrepancies | ✅ PASS |
| **Rejection of Malformed JSON** | Reject with error | Verified via unit tests (0 fallbacks) | ✅ PASS |

## 4. Next Steps for Week 5

1. **Curate Held-Out Split:** Expand the calibration set to 20+ real-world role scenarios.
2. **Fine-Tuning Experiment:** If proceeding with LoRA/QLoRA in Colab, format these rubric pairs into training prompts.
3. **Team Integration:** Ensure Member 5's Streamlit UI displays the `breakdown` dictionary alongside candidate scores.
