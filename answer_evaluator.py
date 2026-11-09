"""
Answer Evaluator Module (Version 3 Rubric)
PrepSense - Company-Aware AI Interview Preparation System

Responsible for:
- Evaluating candidate interview responses against Version 3 technical and behavioral rubrics.
- Deterministic score computation in Python (eliminates LLM math hallucinations).
- Extracting evidence-backed feedback, strengths, missing points, and STAR analysis.
- Robust JSON repair and normalized key matching for local LLM resilience.
- Rejecting invalid/malformed outputs with clear errors (never fabricating default scores).
"""

import json
import re
from typing import Any

# Import shared LLM connectivity with fallback for headless test runners
try:
    from llm import ask_ai, extract_json_string
except ImportError:
    def ask_ai(prompt: str, **kwargs) -> str:
        raise NotImplementedError("LLM client requires langchain_ollama or a mock in tests.")

    def extract_json_string(text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        fence_pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(fence_pattern, cleaned, re.DOTALL | re.IGNORECASE)
        if match:
            cleaned = match.group(1).strip()
        elif cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()
        first_brace = cleaned.find("{")
        if first_brace != -1:
            last_brace = cleaned.rfind("}")
            if last_brace > first_brace:
                return cleaned[first_brace : last_brace + 1]
        return cleaned


class EvaluationError(Exception):
    """Raised when answer evaluation fails or returns invalid rubric data."""
    pass


# ============================================================================
# VERSION 3 RUBRIC DEFINITIONS AND WEIGHTS
# ============================================================================

TECHNICAL_RUBRIC_WEIGHTS: dict[str, float] = {
    "technical_accuracy": 0.35,       # Correctness of facts, tools, architectures, trade-offs
    "problem_solving_depth": 0.30,   # Depth of solution, handling edge cases and scaling
    "relevance": 0.20,               # Direct alignment with question and job context
    "clarity_and_structure": 0.15,   # Structured explanation, professional terminology
}

BEHAVIORAL_RUBRIC_WEIGHTS: dict[str, float] = {
    "situation_task": 0.25,          # Clarity of background context and candidate role/scope
    "action": 0.35,                  # Concrete personal decisions, execution, and skills
    "result_impact": 0.25,           # Measurable outcome, metrics, impact, and learnings
    "communication_relevance": 0.15, # Relevance to prompt, conciseness, and professionalism
}


def _normalize_key(key: Any) -> str:
    """Normalize rubric keys (e.g., 'Technical Accuracy' -> 'technical_accuracy')."""
    return re.sub(r"[\s\-]+", "_", str(key).strip().lower())


def _repair_json_text(text: str) -> str:
    """Pre-repair common local LLM JSON quirks like trailing commas."""
    candidate = extract_json_string(text)
    if not candidate:
        return ""
    # Strip trailing commas before closing braces/brackets
    repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
    return repaired


def get_performance_level(score: int) -> str:
    """Map numerical 0-10 score to candidate performance tier."""
    if score >= 9:
        return "Exceptional / Production-Grade"
    elif score >= 7:
        return "Strong / Competent"
    elif score >= 4:
        return "Basic / Developing"
    return "Needs Significant Improvement"


def compute_python_score(
    criteria_scores: dict[str, Any],
    question_type: str = "technical",
) -> tuple[int, dict[str, int]]:
    """
    Compute final interview score (0-10) deterministically in Python.

    Validates that all expected criteria for the given rubric are present
    and valid numbers between 0 and 10. Rejects fabricated or malformed scores.
    Supports fuzzy/normalized keys (e.g. 'Technical Accuracy' matches 'technical_accuracy').
    """
    is_behavioral = str(question_type).lower() == "behavioral"
    weights = BEHAVIORAL_RUBRIC_WEIGHTS if is_behavioral else TECHNICAL_RUBRIC_WEIGHTS

    if not isinstance(criteria_scores, dict):
        raise EvaluationError("Rubric criteria scores must be provided as a dictionary.")

    # Normalize input dictionary keys for resilience
    normalized_input = {_normalize_key(k): v for k, v in criteria_scores.items()}

    validated_breakdown: dict[str, int] = {}
    weighted_sum = 0.0

    for criterion, weight in weights.items():
        if criterion not in normalized_input:
            raise EvaluationError(f"Missing required rubric criterion: '{criterion}'.")

        raw_val = normalized_input[criterion]
        # Handle dict with nested score or direct value
        if isinstance(raw_val, dict):
            raw_val = raw_val.get("score")

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            raise EvaluationError(
                f"Invalid score value for criterion '{criterion}': expected number, got {raw_val!r}."
            )

        if not (0.0 <= val <= 10.0):
            raise EvaluationError(
                f"Criterion '{criterion}' score {val} out of bounds (must be between 0 and 10)."
            )

        # Normalize to integer 0-10 for individual criteria breakdown
        int_score = int(round(val))
        validated_breakdown[criterion] = int_score
        weighted_sum += val * weight

    # Final overall score rounded to nearest integer (0-10)
    final_score = int(round(weighted_sum))
    final_score = max(0, min(10, final_score))

    return final_score, validated_breakdown


def parse_evaluation_output(text: str, question_type: str = "technical") -> dict[str, Any]:
    """
    Safely parse, repair, and validate the LLM evaluation JSON response.

    Strictly validates required schema and raises EvaluationError on malformed
    output (satisfying the requirement to NEVER return a fabricated default score).
    """
    if not text or not str(text).strip():
        raise EvaluationError("LLM returned an empty evaluation response.")

    cleaned = _repair_json_text(text)
    data = None

    # Attempt 1: Parse repaired JSON
    try:
        data = json.loads(cleaned)
    except Exception:
        # Attempt 2: Direct parse on original text
        try:
            data = json.loads(text.strip())
        except Exception as exc:
            raise EvaluationError(f"Malformed evaluator JSON response: {exc}") from exc

    if not isinstance(data, dict):
        raise EvaluationError("Evaluator output must be a JSON object.")

    # Validate criteria scores
    raw_criteria = data.get("criteria_scores")
    if not isinstance(raw_criteria, dict):
        raise EvaluationError("Evaluator response missing 'criteria_scores' dictionary.")

    # Calculate score in Python
    final_score, score_breakdown = compute_python_score(raw_criteria, question_type=question_type)

    # Extract evidence citations with normalized criterion names
    evidence: list[dict[str, Any]] = []
    for raw_crit, item in raw_criteria.items():
        norm_crit = _normalize_key(raw_crit)
        if isinstance(item, dict) and "evidence" in item:
            evidence.append({
                "criterion": norm_crit,
                "score": score_breakdown.get(norm_crit, 0),
                "evidence": str(item.get("evidence", "")).strip(),
            })

    def _extract_string_list(key: str, default_msg: str) -> list[str]:
        val = data.get(key)
        if isinstance(val, list):
            items = [str(x).strip() for x in val if str(x).strip()]
            if items:
                return items[:3]
        elif isinstance(val, str) and val.strip():
            return [val.strip()]
        return [default_msg]

    strengths = _extract_string_list("strengths", "Addressed the core aspects of the question.")
    missing_points = _extract_string_list("missing_points", "Could provide deeper technical/operational trade-offs.")
    suggestions = _extract_string_list("suggestions", "Use real-world examples with measurable outcomes.")

    is_behavioral = str(question_type).lower() == "behavioral"
    raw_star = data.get("star_feedback", "")
    if is_behavioral:
        star_feedback = str(raw_star).strip() if raw_star else "STAR structure demonstrated in practice answer."
    else:
        star_feedback = "Not applicable"

    return {
        "score": final_score,
        "performance_level": get_performance_level(final_score),
        "breakdown": score_breakdown,
        "evidence": evidence,
        "strengths": strengths,
        "missing_points": missing_points,
        "suggestions": suggestions,
        "star_feedback": star_feedback,
    }


def evaluate_answer(
    question: str,
    answer: str,
    job_context: str = "",
    question_type: str = "technical",
) -> dict[str, Any]:
    """
    Evaluate an interview answer using the Version 3 rubric.

    Parameters:
        question: The interview question asked.
        answer: Candidate's submitted response.
        job_context: Relevant role and required skills context.
        question_type: 'technical' or 'behavioral'.

    Returns:
        Structured evaluation dictionary containing:
        - score: Final integer score (0-10) computed in Python
        - performance_level: Descriptive tier label
        - breakdown: Criterion-by-criterion scores
        - evidence: Cited evidence/observations from candidate answer
        - strengths: Bulleted candidate strengths
        - missing_points: What was omitted or weak
        - suggestions: Actionable coaching tips
        - star_feedback: STAR method analysis (or 'Not applicable')
    """
    if not isinstance(question, str) or not question.strip():
        raise ValueError("Interview question cannot be empty.")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Candidate answer cannot be empty.")

    q_type = "behavioral" if str(question_type).lower() == "behavioral" else "technical"
    context_snippet = str(job_context).strip()[:400] if job_context else "Standard engineering role"

    if q_type == "behavioral":
        rubric_description = """
        Behavioral Rubric Criteria (Score each 0-10 with direct evidence from candidate answer):
        1. situation_task: Context clarity, challenges, and candidate's role/ownership.
        2. action: Concrete individual actions, technical and soft skills demonstrated.
        3. result_impact: Tangible outcome, business/team impact, metrics, and learnings.
        4. communication_relevance: Direct relevance to question and structured communication.
        """
        star_instruction = 'Provide a 1-2 sentence STAR (Situation, Task, Action, Result) evaluation for "star_feedback".'
        criteria_keys_json = """
        "criteria_scores": {
            "situation_task": {"score": 8, "evidence": "<quote or specific observation from candidate answer>"},
            "action": {"score": 7, "evidence": "<quote or specific observation from candidate answer>"},
            "result_impact": {"score": 6, "evidence": "<quote or specific observation from candidate answer>"},
            "communication_relevance": {"score": 8, "evidence": "<quote or specific observation from candidate answer>"}
        },
        """
    else:
        rubric_description = """
        Technical Rubric Criteria (Score each 0-10 with direct evidence from candidate answer):
        1. technical_accuracy: Correctness of facts, tools, architectures, protocols, or code logic.
        2. problem_solving_depth: Depth of explanation, handling edge cases, scaling, and trade-offs.
        3. relevance: Direct focus on the specific question asked and role context.
        4. clarity_and_structure: Structured explanation, professional terminology, and logical progression.
        """
        star_instruction = 'Set "star_feedback" to "Not applicable".'
        criteria_keys_json = """
        "criteria_scores": {
            "technical_accuracy": {"score": 8, "evidence": "<quote or specific observation from candidate answer>"},
            "problem_solving_depth": {"score": 7, "evidence": "<quote or specific observation from candidate answer>"},
            "relevance": {"score": 8, "evidence": "<quote or specific observation from candidate answer>"},
            "clarity_and_structure": {"score": 8, "evidence": "<quote or specific observation from candidate answer>"}
        },
        """

    prompt = f"""
    You are an expert interview coach for PrepSense.
    Evaluate the candidate's answer strictly against the Version 3 rubric.

    Role Context: {context_snippet}
    Question [{q_type.upper()}]: {question}
    Candidate Answer: {answer}

    {rubric_description}

    Scoring Guide (0-10 per criterion):
    - 0-3: Weak / incorrect / missing entirely.
    - 4-6: Average / basic keywords but lacks depth or concrete details.
    - 7-8: Strong / competent with sound technical/behavioral reasoning.
    - 9-10: Exceptional / industry-grade depth with specific verification or quantified impact.

    Return ONLY a JSON object with this exact structure:
    {{
        {criteria_keys_json}
        "strengths": ["1-2 concise bullet points"],
        "missing_points": ["1-2 concise bullet points"],
        "suggestions": ["1-2 actionable tips"],
        "star_feedback": "{'STAR assessment' if q_type == 'behavioral' else 'Not applicable'}"
    }}

    Rules:
    - You must include all 4 criteria in "criteria_scores".
    - Each criterion must have an integer "score" (0-10) and a concise "evidence" observation.
    - Strengths, missing_points, suggestions must be short lists of at most 2 items each.
    - {star_instruction}
    - Output valid JSON only. Do not add markdown commentary outside the JSON block.
    """

    response = ask_ai(prompt)
    return parse_evaluation_output(response, question_type=q_type)


if __name__ == "__main__":
    sample_question = "How would you optimize a slow PostgreSQL query?"
    sample_answer = (
        "First, I would inspect the query plan using EXPLAIN ANALYZE to identify sequential scans and costly joins. "
        "Then I would check index usage on filtered and joined columns, and consider a suitable B-Tree or composite index. "
        "Finally, I would test execution time and buffer usage after adding the index."
    )
    sample_context = "Role: Backend Developer. Key skills: PostgreSQL, Python, FastAPI."

    print("Evaluating sample answer using Version 3 Rubric...")
    try:
        result = evaluate_answer(
            question=sample_question,
            answer=sample_answer,
            job_context=sample_context,
            question_type="technical",
        )
        print("\nEVALUATION RESULT (Score computed in Python):")
        print(json.dumps(result, indent=2))
    except Exception as err:
        print(f"Evaluation error: {err}")
