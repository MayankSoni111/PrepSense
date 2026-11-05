import json
import re
from typing import Any

from llm import ask_ai, extract_json_string


def robust_parse_evaluation(text: str) -> dict[str, Any]:
    """Safely parse evaluation JSON from any LLM response."""
    default_feedback = {
        "score": 7,
        "strengths": ["Answer demonstrates relevant knowledge."],
        "missing_points": ["Could provide more concrete operational examples."],
        "suggestions": ["Structure your answer with more specific details."],
        "star_feedback": "Not applicable",
    }

    if not text or not text.strip():
        return default_feedback

    cleaned = extract_json_string(text)

    # Attempt 1: Standard JSON parse on extracted candidate
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return _normalize_evaluation_dict(data)
    except Exception:
        pass

    # Attempt 2: Direct JSON parse on raw text
    try:
        data = json.loads(text.strip())
        if isinstance(data, dict):
            return _normalize_evaluation_dict(data)
    except Exception:
        pass

    # Fallback score extraction
    score = 7
    match = re.search(r"(?:score|rating)\s*[:=]\s*(\d+)", text, re.IGNORECASE)
    if match:
        try:
            val = int(match.group(1))
            if 0 <= val <= 10:
                score = val
        except Exception:
            pass

    return {
        "score": score,
        "strengths": ["Addressed the question directly."],
        "missing_points": ["Could go into deeper technical or operational depth."],
        "suggestions": ["Use real-world project examples with measurable outcomes."],
        "star_feedback": "Structure responses using the STAR method (Situation, Task, Action, Result).",
    }


def _normalize_evaluation_dict(data: dict) -> dict[str, Any]:
    raw_score = data.get("score", 7)
    try:
        score = int(raw_score)
        score = max(0, min(10, score))
    except (ValueError, TypeError):
        score = 7

    def _to_str_list(val, default_item):
        if isinstance(val, list):
            items = [str(x).strip() for x in val if str(x).strip()]
            return items[:3] if items else [default_item]
        elif isinstance(val, str) and val.strip():
            return [val.strip()]
        return [default_item]

    return {
        "score": score,
        "strengths": _to_str_list(data.get("strengths"), "Addressed the core aspects of the question."),
        "missing_points": _to_str_list(data.get("missing_points"), "Could include more specific metrics or trade-offs."),
        "suggestions": _to_str_list(data.get("suggestions"), "Focus on clear structure and practical examples."),
        "star_feedback": str(data.get("star_feedback", "Not applicable")).strip(),
    }


def evaluate_answer(
    question: str,
    answer: str,
    job_context: str = "",
    question_type: str = "technical",
) -> dict[str, Any]:
    """Evaluate an interview answer quickly with concise structured feedback."""

    if not isinstance(question, str) or not question.strip():
        raise ValueError("Interview question cannot be empty.")
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Candidate answer cannot be empty.")

    q_type = "behavioral" if str(question_type).lower() == "behavioral" else "technical"

    # Compact role context for fast prompt evaluation
    context_snippet = str(job_context).strip()[:400] if job_context else "Standard software engineering role"

    star_instruction = (
        'Assess candidate\'s Situation, Task, Action, and Result in 1-2 concise sentences for "star_feedback".'
        if q_type == "behavioral"
        else 'Set "star_feedback" to "Not applicable".'
    )

    prompt = f"""
    You are an expert interview coach for PrepSense.
    Evaluate the candidate's answer fairly, accurately, and concisely.

    Role Context: {context_snippet}
    Question [{q_type}]: {question}
    Candidate Answer: {answer}

    Scoring Guidelines (Score 0-10):
    - 0-3: Irrelevant or materially incorrect.
    - 4-6: Basic or keyword-only; lacks depth or practical application.
    - 7-8: Good, competent answer with sound approach.
    - 9-10: Exceptional answer with specific technical/STAR reasoning and verification.

    Return ONLY a JSON object with this exact structure:
    {{
        "score": 8,
        "strengths": ["1-2 concise bullet points"],
        "missing_points": ["1-2 concise bullet points"],
        "suggestions": ["1-2 actionable tips"],
        "star_feedback": "{'STAR assessment' if q_type == 'behavioral' else 'Not applicable'}"
    }}

    Rules:
    - score must be an integer from 0 to 10.
    - strengths, missing_points, suggestions must be short lists of at most 2 concise bullet points.
    - {star_instruction}
    - Keep total response under 150 words. Do not write essays.
    """

    response = ask_ai(prompt)
    return robust_parse_evaluation(response)


if __name__ == "__main__":

    sample_question = "How would you optimize a slow PostgreSQL query?"
    sample_answer = """
    First, I would inspect the query plan using EXPLAIN ANALYZE to identify sequential scans and costly joins.
    Then I would check index usage on filtered and joined columns, and consider a suitable B-Tree or composite index.
    Finally, I would test execution time and buffer usage after adding the index.
    """
    sample_context = "Role: Backend Developer. Key skills: PostgreSQL, Python, FastAPI."

    print("Evaluating sample answer...")
    result = evaluate_answer(
        question=sample_question,
        answer=sample_answer,
        job_context=sample_context,
        question_type="technical",
    )
    print("\nEVALUATION RESULT:")
    print(json.dumps(result, indent=2))
