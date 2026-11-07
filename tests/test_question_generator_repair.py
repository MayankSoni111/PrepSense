import json
import unittest
from unittest.mock import patch

from question_generator import generate_questions


def create_questions(technical_count, behavioral_count):
    """Create simulated LLM questions for testing."""
    questions = []

    for i in range(technical_count):
        questions.append({
            "question": f"Technical question number {i + 1}?",
            "type": "technical",
            "reason": "Tests technical knowledge.",
        })

    for i in range(behavioral_count):
        questions.append({
            "question": f"Behavioral question number {i + 1}?",
            "type": "behavioral",
            "reason": "Tests behavioral skills.",
        })

    return {"questions": questions}


class TestQuestionRepair(unittest.TestCase):

    @patch("question_generator.ask_ai")
    def test_repairs_missing_behavioral_question(self, mock_ai):
        initial_response = json.dumps(create_questions(5, 2))

        # This must be a new question, not "Behavioral question number 1?",
        # which is already present in the initial response.
        repair_response = json.dumps({
            "questions": [
                {
                    "question": "How do you handle disagreements with teammates?",
                    "type": "behavioral",
                    "reason": "Tests conflict resolution and teamwork.",
                }
            ]
        })

        mock_ai.side_effect = [initial_response, repair_response]

        result = generate_questions(
            job_info={"job_title": "Backend Developer Intern"},
            company_research="Sample company research",
            resume_text="Python and PostgreSQL experience",
        )

        self.assertEqual(len(result), 8)

        technical = sum(q["type"] == "technical" for q in result)
        behavioral = sum(q["type"] == "behavioral" for q in result)

        self.assertEqual(technical, 5)
        self.assertEqual(behavioral, 3)
        self.assertIn(
            "How do you handle disagreements with teammates?",
            [q["question"] for q in result],
        )

        # One initial generation call + one targeted repair call.
        self.assertEqual(mock_ai.call_count, 2)

        repair_prompt = mock_ai.call_args_list[1].args[0]
        self.assertIn("Behavioral: 1", repair_prompt)
        self.assertIn("Technical: 0", repair_prompt)

        print("\nPASS: Only the missing behavioral question was requested.")

    @patch("question_generator.ask_ai")
    def test_valid_questions_do_not_trigger_repair(self, mock_ai):
        mock_ai.return_value = json.dumps(create_questions(5, 3))

        result = generate_questions(
            job_info={"job_title": "Backend Developer Intern"},
            company_research="Sample research",
            resume_text="Python developer",
        )

        self.assertEqual(len(result), 8)
        self.assertEqual(mock_ai.call_count, 1)

        print("\nPASS: No unnecessary repair call was made.")

    @patch("question_generator.ask_ai")
    def test_incomplete_repair_raises_error(self, mock_ai):
        mock_ai.side_effect = [
            json.dumps(create_questions(5, 2)),
            json.dumps({"questions": []}),
        ]

        with self.assertRaisesRegex(
            ValueError,
            "could not satisfy the required distribution",
        ):
            generate_questions(
                job_info={"job_title": "Backend Developer Intern"},
                company_research="Sample research",
                resume_text="Python developer",
            )

        self.assertEqual(mock_ai.call_count, 2)
        print("\nPASS: Incomplete repair was correctly rejected.")

    @patch("question_generator.ask_ai")
    def test_duplicate_repair_question_does_not_fill_missing_slot(self, mock_ai):
        initial_response = json.dumps(create_questions(5, 2))
        duplicate_repair_response = json.dumps({
            "questions": [
                {
                    "question": "Behavioral question number 1?",
                    "type": "behavioral",
                    "reason": "Tests behavioral skills.",
                }
            ]
        })
        mock_ai.side_effect = [initial_response, duplicate_repair_response]

        with self.assertRaisesRegex(
            ValueError,
            "could not satisfy the required distribution",
        ):
            generate_questions(
                job_info={"job_title": "Backend Developer Intern"},
                company_research="Sample research",
                resume_text="Python developer",
            )

        self.assertEqual(mock_ai.call_count, 2)
        print("\nPASS: A duplicate repair question was not accepted.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
