"""
Unit Tests for Answer Evaluator Agent (Member 4)
PrepSense - Company-Aware AI Interview Preparation System

Tests:
- Technical answer evaluation with Version 3 rubric.
- Behavioral answer evaluation with STAR assessment.
- Deterministic score computation in Python.
- Strict rejection of invalid inputs and malformed LLM responses (no fabricated scores).
- Calibration tests: Weak < Average < Strong scoring progression.
"""

import json
import unittest
from unittest.mock import patch

from answer_evaluator import (
    TECHNICAL_RUBRIC_WEIGHTS,
    BEHAVIORAL_RUBRIC_WEIGHTS,
    EvaluationError,
    compute_python_score,
    evaluate_answer,
    parse_evaluation_output,
)
from agents.evaluator import evaluate_answer_node


class TestAnswerEvaluator(unittest.TestCase):

    def test_compute_python_score_technical(self):
        """Verify deterministic score calculation using technical weights."""
        criteria_scores = {
            "technical_accuracy": 9,        # 9 * 0.35 = 3.15
            "problem_solving_depth": 8,    # 8 * 0.30 = 2.40
            "relevance": 10,               # 10 * 0.20 = 2.00
            "clarity_and_structure": 7,    # 7 * 0.15 = 1.05
        }
        # Expected sum: 3.15 + 2.40 + 2.00 + 1.05 = 8.60 -> round(8.60) = 9
        score, breakdown = compute_python_score(criteria_scores, question_type="technical")
        self.assertEqual(score, 9)
        self.assertEqual(breakdown["technical_accuracy"], 9)
        self.assertEqual(breakdown["problem_solving_depth"], 8)

    def test_compute_python_score_fuzzy_keys(self):
        """Verify that humanized/spaced keys are normalized properly."""
        fuzzy_criteria = {
            "Technical Accuracy": 9,
            "problem-solving-depth": 8,
            "RELEVANCE": 10,
            "Clarity and Structure": 7,
        }
        score, breakdown = compute_python_score(fuzzy_criteria, question_type="technical")
        self.assertEqual(score, 9)
        self.assertEqual(breakdown["technical_accuracy"], 9)
        self.assertEqual(breakdown["problem_solving_depth"], 8)

    def test_repair_trailing_commas_in_json(self):
        """Ensure trailing commas from LLM output are repaired before parsing."""
        bad_json = """
        {
            "criteria_scores": {
                "technical_accuracy": {"score": 8, "evidence": "good",},
                "problem_solving_depth": {"score": 8, "evidence": "deep",},
                "relevance": {"score": 8, "evidence": "relevant",},
                "clarity_and_structure": {"score": 8, "evidence": "clear",},
            },
            "strengths": ["point 1",],
            "missing_points": ["point 2",],
            "suggestions": ["tip 1",],
            "star_feedback": "Not applicable",
        }
        """
        parsed = parse_evaluation_output(bad_json, question_type="technical")
        self.assertEqual(parsed["score"], 8)
        self.assertEqual(parsed["performance_level"], "Strong / Competent")

    def test_compute_python_score_behavioral(self):
        """Verify deterministic score calculation using behavioral weights."""
        criteria_scores = {
            "situation_task": 6,           # 6 * 0.25 = 1.50
            "action": 7,                   # 7 * 0.35 = 2.45
            "result_impact": 6,            # 6 * 0.25 = 1.50
            "communication_relevance": 8,  # 8 * 0.15 = 1.20
        }
        # Expected sum: 1.50 + 2.45 + 1.50 + 1.20 = 6.65 -> round(6.65) = 7
        score, breakdown = compute_python_score(criteria_scores, question_type="behavioral")
        self.assertEqual(score, 7)
        self.assertEqual(breakdown["action"], 7)

    def test_reject_missing_criterion(self):
        """Ensure EvaluationError is raised if any rubric criterion is omitted."""
        incomplete_scores = {
            "technical_accuracy": 8,
            "problem_solving_depth": 7,
            # 'relevance' and 'clarity_and_structure' missing
        }
        with self.assertRaises(EvaluationError):
            compute_python_score(incomplete_scores, question_type="technical")

    def test_reject_out_of_bounds_criterion_score(self):
        """Ensure EvaluationError is raised if a score is outside 0-10 range."""
        invalid_scores = {
            "technical_accuracy": 15,  # Invalid
            "problem_solving_depth": 7,
            "relevance": 8,
            "clarity_and_structure": 8,
        }
        with self.assertRaises(EvaluationError):
            compute_python_score(invalid_scores, question_type="technical")

    def test_reject_empty_inputs(self):
        """Ensure ValueError is raised on empty question or empty answer."""
        with self.assertRaises(ValueError):
            evaluate_answer(question="", answer="Valid answer text.")
        with self.assertRaises(ValueError):
            evaluate_answer(question="Valid question?", answer="   ")

    def test_reject_malformed_llm_json(self):
        """Strictly reject malformed JSON without fabricating default scores."""
        malformed_responses = [
            "",
            "I cannot evaluate this answer.",
            "```json\n{ not valid json }\n```",
            '{"score": 8}',  # missing criteria_scores
        ]
        for bad_resp in malformed_responses:
            with self.assertRaises(EvaluationError):
                parse_evaluation_output(bad_resp, question_type="technical")

    @patch("answer_evaluator.ask_ai")
    def test_evaluate_technical_answer_with_mock_ai(self, mock_ask_ai):
        """Verify full technical evaluation pipeline with mocked LLM output."""
        mock_payload = {
            "criteria_scores": {
                "technical_accuracy": {"score": 8, "evidence": "Used EXPLAIN ANALYZE correctly."},
                "problem_solving_depth": {"score": 7, "evidence": "Suggested indexes but omitted partition trade-offs."},
                "relevance": {"score": 9, "evidence": "Directly solved Postgres query performance."},
                "clarity_and_structure": {"score": 8, "evidence": "Logical 3-step breakdown."},
            },
            "strengths": ["Clear step-by-step methodology using EXPLAIN."],
            "missing_points": ["Could mention database statistics and vacuuming."],
            "suggestions": ["Include buffer hit metrics."],
            "star_feedback": "Not applicable",
        }
        mock_ask_ai.return_value = json.dumps(mock_payload)

        result = evaluate_answer(
            question="How would you optimize a slow PostgreSQL query?",
            answer="I would run EXPLAIN ANALYZE and inspect index scan costs.",
            job_context="Backend Engineer (PostgreSQL, Python)",
            question_type="technical",
        )

        # Expected score: 8*0.35 + 7*0.30 + 9*0.20 + 8*0.15 = 2.80 + 2.10 + 1.80 + 1.20 = 7.90 -> 8
        self.assertEqual(result["score"], 8)
        self.assertEqual(result["breakdown"]["technical_accuracy"], 8)
        self.assertEqual(result["star_feedback"], "Not applicable")
        self.assertTrue(len(result["strengths"]) >= 1)
        self.assertTrue(len(result["evidence"]) == 4)

    @patch("answer_evaluator.ask_ai")
    def test_evaluate_behavioral_answer_with_star_mock(self, mock_ask_ai):
        """Verify behavioral evaluation with STAR feedback."""
        mock_payload = {
            "criteria_scores": {
                "situation_task": {"score": 8, "evidence": "Described production outage context well."},
                "action": {"score": 8, "evidence": "Led communication and isolated bad commit."},
                "result_impact": {"score": 7, "evidence": "Restored service in 15 mins."},
                "communication_relevance": {"score": 8, "evidence": "Good structured storytelling."},
            },
            "strengths": ["Strong personal ownership."],
            "missing_points": ["Could quantify impact on users during downtime."],
            "suggestions": ["Share long-term post-mortem takeaways."],
            "star_feedback": "STAR Assessment: Situation and Action were crisp; Result could include quantitative uptime stats.",
        }
        mock_ask_ai.return_value = json.dumps(mock_payload)

        result = evaluate_answer(
            question="Tell me about a time you handled a production emergency.",
            answer="When an outage occurred, I identified the failing commit and rolled it back.",
            job_context="Site Reliability Engineer",
            question_type="behavioral",
        )

        # Expected score: 8*0.25 + 8*0.35 + 7*0.25 + 8*0.15 = 2.00 + 2.80 + 1.75 + 1.20 = 7.75 -> 8
        self.assertEqual(result["score"], 8)
        self.assertIn("STAR", result["star_feedback"])
        self.assertEqual(result["breakdown"]["action"], 8)

    def test_calibration_progression(self):
        """Verify weak < average < strong ordering across calibrated criteria."""
        weak_scores = {
            "technical_accuracy": 2,
            "problem_solving_depth": 2,
            "relevance": 4,
            "clarity_and_structure": 3,
        }
        avg_scores = {
            "technical_accuracy": 6,
            "problem_solving_depth": 5,
            "relevance": 7,
            "clarity_and_structure": 6,
        }
        strong_scores = {
            "technical_accuracy": 9,
            "problem_solving_depth": 9,
            "relevance": 9,
            "clarity_and_structure": 8,
        }

        weak_final, _ = compute_python_score(weak_scores, "technical")
        avg_final, _ = compute_python_score(avg_scores, "technical")
        strong_final, _ = compute_python_score(strong_scores, "technical")

        self.assertTrue(weak_final < avg_final < strong_final)
        self.assertLessEqual(weak_final, 3)
        self.assertGreaterEqual(strong_final, 8)

    @patch("answer_evaluator.ask_ai")
    def test_evaluator_node_technical_success(self, mock_ask_ai):
        """Test LangGraph evaluate_answer_node with technical question in state."""
        mock_payload = {
            "criteria_scores": {
                "technical_accuracy": {"score": 9, "evidence": "Used proper index syntax."},
                "problem_solving_depth": {"score": 8, "evidence": "Discussed query plan."},
                "relevance": {"score": 9, "evidence": "Directly addressed SQL tuning."},
                "clarity_and_structure": {"score": 8, "evidence": "Well organized."},
            },
            "strengths": ["Strong SQL knowledge."],
            "missing_points": ["Could mention memory config."],
            "suggestions": ["Test with large datasets."],
            "star_feedback": "Not applicable",
        }
        mock_ask_ai.return_value = json.dumps(mock_payload)

        state = {
            "selected_question": {
                "question": "How do you optimize a slow SQL query?",
                "type": "technical",
            },
            "candidate_answer": "I run EXPLAIN to see execution costs and add needed indexes.",
            "job_info": {
                "job_title": "Database Engineer",
                "technical_skills": ["SQL", "PostgreSQL"],
            },
        }

        output = evaluate_answer_node(state)
        self.assertEqual(output["current_step"], "answer_evaluated")
        self.assertIsNone(output["error"])
        self.assertIn("feedback", output)
        self.assertEqual(output["feedback"]["score"], 9)

    @patch("answer_evaluator.ask_ai")
    def test_evaluator_node_behavioral_success(self, mock_ask_ai):
        """Test LangGraph evaluate_answer_node with behavioral question in state."""
        mock_payload = {
            "criteria_scores": {
                "situation_task": {"score": 8, "evidence": "Clear project context."},
                "action": {"score": 8, "evidence": "Took leadership role."},
                "result_impact": {"score": 8, "evidence": "Delivered on schedule."},
                "communication_relevance": {"score": 8, "evidence": "Crisp communication."},
            },
            "strengths": ["Demonstrated leadership."],
            "missing_points": ["Could mention follow-up."],
            "suggestions": ["Mention retrospective takeaways."],
            "star_feedback": "STAR assessment demonstrates solid execution.",
        }
        mock_ask_ai.return_value = json.dumps(mock_payload)

        state = {
            "selected_question": {
                "question": "Describe a difficult deadline you met.",
                "type": "behavioral",
            },
            "candidate_answer": "When the deadline moved up, I prioritized core features and delivered on time.",
            "job_info": {"job_title": "Software Engineer"},
        }

        output = evaluate_answer_node(state)
        self.assertEqual(output["current_step"], "answer_evaluated")
        self.assertIsNone(output["error"])
        self.assertEqual(output["feedback"]["score"], 8)

    def test_evaluator_node_invalid_state(self):
        """Test LangGraph evaluate_answer_node when required state fields are missing."""
        # Missing selected_question
        out1 = evaluate_answer_node({"candidate_answer": "Some answer"})
        self.assertEqual(out1["current_step"], "evaluation_failed")
        self.assertIn("selected_question", out1["error"])

        # Missing candidate_answer
        out2 = evaluate_answer_node({
            "selected_question": {"question": "Some question?", "type": "technical"},
            "candidate_answer": "",
        })
        self.assertEqual(out2["current_step"], "evaluation_failed")
        self.assertIn("candidate_answer", out2["error"])

    @patch("answer_evaluator.ask_ai")
    def test_evaluator_node_handles_malformed_llm(self, mock_ask_ai):
        """Test LangGraph evaluate_answer_node handles malformed LLM response gracefully."""
        mock_ask_ai.return_value = "invalid response"

        state = {
            "selected_question": {"question": "Some question?", "type": "technical"},
            "candidate_answer": "Candidate answered here.",
        }

        output = evaluate_answer_node(state)
        self.assertEqual(output["current_step"], "evaluation_failed")
        self.assertIn("Evaluation failed", output["error"])


if __name__ == "__main__":
    unittest.main()
