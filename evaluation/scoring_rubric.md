# PrepSense Version 3 Interview Scoring Rubric

This document defines the formal scoring criteria, evaluation dimensions, and weight distribution used by the **Answer Evaluation Agent (Member 4)**.

---

## 1. Core Principles

1. **Deterministic Python Scoring:** 
   The language model does not calculate or guess the overall final score. Instead, it scores individual rubric criteria (0–10) and provides grounded evidence. The final score is computed deterministically in Python using established weights.
2. **Evidence-Grounded Feedback:** 
   Every criterion score must be backed by a specific citation or observation directly from the candidate's answer.
3. **No Fabricated Default Scores:**
   If the LLM returns an invalid schema, unparseable JSON, or out-of-bounds criteria, the evaluator raises a structured `EvaluationError` rather than fabricating an arbitrary default score.
4. **Weak / Average / Strong Calibration:**
   - **Weak (0–3):** Incomplete, materially incorrect, or irrelevant.
   - **Average (4–6):** Mentions basic keywords or high-level steps but lacks depth, trade-offs, or concrete ownership.
   - **Strong (7–8):** Thorough, competent, logically organized, with sound technical or behavioral rationale.
   - **Exceptional (9–10):** Production-grade depth, explicit trade-offs, metrics, or comprehensive STAR execution.

---

## 2. Technical Evaluation Rubric

Total Score: `0–10` (Weighted sum of 4 criteria)

| Criterion | Weight | Focus Areas |
|---|---|---|
| `technical_accuracy` | **35%** (0.35) | Factual correctness of frameworks, systems, protocols, algorithms, and code logic. |
| `problem_solving_depth` | **30%** (0.30) | Consideration of edge cases, scalability, bottlenecks, performance, and trade-offs. |
| `relevance` | **20%** (0.20) | Direct alignment with the specific question asked and role expectations. |
| `clarity_and_structure` | **15%** (0.15) | Structured progression, clear technical vocabulary, and concise explanations. |

$$\text{Final Technical Score} = \text{round}\left(0.35 \times C_{\text{acc}} + 0.30 \times C_{\text{depth}} + 0.20 \times C_{\text{rel}} + 0.15 \times C_{\text{clarity}}\right)$$

---

## 3. Behavioral Evaluation Rubric (STAR Method)

Total Score: `0–10` (Weighted sum of 4 criteria)

| Criterion | Weight | Focus Areas |
|---|---|---|
| `situation_task` | **25%** (0.25) | Clear context, business problem, stakes, and the candidate's specific scope/ownership. |
| `action` | **35%** (0.35) | Specific personal actions taken, technical execution, leadership, and conflict resolution. |
| `result_impact` | **25%** (0.25) | Measurable business/technical outcomes, percentages, metrics, and key learnings. |
| `communication_relevance` | **15%** (0.15) | Alignment with the behavioral question, professional delivery, and structure. |

$$\text{Final Behavioral Score} = \text{round}\left(0.25 \times C_{\text{st}} + 0.35 \times C_{\text{action}} + 0.25 \times C_{\text{result}} + 0.15 \times C_{\text{comm}}\right)$$

---

## 4. Output Contract

```json
{
  "score": 8,
  "breakdown": {
    "technical_accuracy": 9,
    "problem_solving_depth": 8,
    "relevance": 9,
    "clarity_and_structure": 8
  },
  "evidence": [
    {
      "criterion": "technical_accuracy",
      "score": 9,
      "evidence": "Correctly referenced EXPLAIN ANALYZE and B-Tree indexing on join columns."
    }
  ],
  "strengths": [
    "Accurate database diagnosis approach using query plans."
  ],
  "missing_points": [
    "Could touch upon autovacuum statistics or work_mem configuration."
  ],
  "suggestions": [
    "Discuss buffer cache hit ratios when tuning query memory."
  ],
  "star_feedback": "Not applicable"
}
```

