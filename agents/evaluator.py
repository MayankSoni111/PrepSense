"""
Evaluator Agent Node (Member 4 - Week 3 Deliverable)
PrepSense - Company-Aware AI Interview Preparation System

Responsible for:
- LangGraph agent node wrapping Version 3 answer evaluation.
- Preserving rubric breakdown, evidence citations, and STAR analysis.
- Validating score totals against rubric criteria.
- Updating shared InterviewState with structured evaluation feedback.
"""

import time
from typing import Any

from agents.state import InterviewState
from answer_evaluator import (
    EvaluationError,
    evaluate_answer,
    compute_python_score,
)


def evaluate_answer_node(state: InterviewState) -> dict[str, Any]:
    """
    LangGraph Node: Evaluates a candidate's answer to a selected interview question.

    Reads from InterviewState:
    - selected_question: dict containing 'question' and 'type' ('technical' or 'behavioral')
    - candidate_answer: str containing the candidate's submitted practice response
    - job_info: dict containing extracted job metadata (role, skills)

    Returns state update:
    - feedback: Structured evaluation dictionary with score, breakdown, evidence, etc.
    - current_step: 'answer_evaluated' (or 'evaluation_failed' on error)
    - error: None or error message
    """
    print("\n[LangGraph Node: Evaluator Agent] 📝 Evaluating candidate answer...")
    start = time.perf_counter()

    # 1. Validate selected question
    selected_question = state.get("selected_question")
    if not isinstance(selected_question, dict):
        error_msg = "Evaluator node error: 'selected_question' must be a dictionary in state."
        print(f"[LangGraph Node: Evaluator Agent] ❌ {error_msg}")
        return {
            "error": error_msg,
            "current_step": "evaluation_failed",
        }

    question_text = str(selected_question.get("question", "")).strip()
    question_type = str(selected_question.get("type", "technical")).strip().lower()

    if not question_text:
        error_msg = "Evaluator node error: 'question' text cannot be empty."
        print(f"[LangGraph Node: Evaluator Agent] ❌ {error_msg}")
        return {
            "error": error_msg,
            "current_step": "evaluation_failed",
        }

    # 2. Validate candidate answer
    candidate_answer = str(state.get("candidate_answer", "")).strip()
    if not candidate_answer:
        error_msg = "Evaluator node error: 'candidate_answer' cannot be empty."
        print(f"[LangGraph Node: Evaluator Agent] ❌ {error_msg}")
        return {
            "error": error_msg,
            "current_step": "evaluation_failed",
        }

    # 3. Construct concise job context from state
    job_info = state.get("job_info", {})
    job_title = job_info.get("job_title", "Candidate Role") if isinstance(job_info, dict) else "Role"
    key_skills = ""
    if isinstance(job_info, dict):
        skills = job_info.get("technical_skills", [])
        if isinstance(skills, list):
            key_skills = ", ".join(str(s) for s in skills[:5])
    job_context = f"Role: {job_title}. Key skills: {key_skills}."

    # 4. Invoke Version 3 evaluation
    try:
        feedback = evaluate_answer(
            question=question_text,
            answer=candidate_answer,
            job_context=job_context,
            question_type=question_type,
        )

        # 5. Sanity-check score totals against rubric breakdown
        breakdown = feedback.get("breakdown", {})
        expected_score, _ = compute_python_score(breakdown, question_type=question_type)
        if feedback.get("score") != expected_score:
            raise EvaluationError(
                f"Score mismatch: reported {feedback.get('score')} but breakdown computes {expected_score}."
            )

        elapsed = time.perf_counter() - start
        print(
            f"[LangGraph Node: Evaluator Agent] ✅ Evaluated {question_type} answer "
            f"in {elapsed:.2f}s (Score: {feedback['score']}/10)"
        )

        return {
            "feedback": feedback,
            "current_step": "answer_evaluated",
            "error": None,
        }

    except Exception as err:
        error_msg = f"Evaluation failed: {err}"
        print(f"[LangGraph Node: Evaluator Agent] ❌ {error_msg}")
        return {
            "error": error_msg,
            "current_step": "evaluation_failed",
        }

