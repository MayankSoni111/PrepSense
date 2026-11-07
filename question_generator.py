import json
import re

from llm import ask_ai, extract_json_string
from job_parser import parse_job_description
from tools.company_research import (
    search_company,
    summarize_company_research,
)

# Maximum resume characters sent to the LLM.
# Resumes rarely need more than this for question generation,
# and a shorter prompt means faster inference on a local model.
MAX_RESUME_CHARS = 2500


def _extract_questions_from_any(data) -> list:
    """Extract questions from any dict, list, or nested structure."""
    candidates = []

    # Case 1: data is directly a list
    if isinstance(data, list):
        candidates = data

    # Case 2: data is a dictionary
    elif isinstance(data, dict):
        for key in ["questions", "interview_questions", "all_questions"]:
            if key in data and isinstance(data[key], list):
                candidates = data[key]
                break

        # Check for separated technical / behavioral keys
        if not candidates:
            tech = data.get("technical_questions") or data.get("technical") or []
            beh = data.get("behavioral_questions") or data.get("behavioral") or []
            if isinstance(tech, list) or isinstance(beh, list):
                t_list = tech if isinstance(tech, list) else []
                b_list = beh if isinstance(beh, list) else []
                for item in t_list:
                    if isinstance(item, dict):
                        item.setdefault("type", "technical")
                    elif isinstance(item, str):
                        item = {"question": item, "type": "technical"}
                    candidates.append(item)
                for item in b_list:
                    if isinstance(item, dict):
                        item.setdefault("type", "behavioral")
                    elif isinstance(item, str):
                        item = {"question": item, "type": "behavioral"}
                    candidates.append(item)

        # Fallback to any list found in dict values
        if not candidates:
            for val in data.values():
                if isinstance(val, list) and len(val) > 0:
                    candidates = val
                    break

    # Normalize every item into {question, type, reason}
    valid = []
    for i, item in enumerate(candidates, 1):
        if isinstance(item, dict):
            q_text = (
                item.get("question")
                or item.get("interview_question")
                or item.get("text")
                or item.get("q")
                or ""
            )
            q_text = str(q_text).strip()
            if not q_text:
                continue

            q_type = str(item.get("type", "technical")).lower()
            if q_type not in ("technical", "behavioral"):
                q_type = "behavioral" if i > 5 else "technical"

            reason = str(item.get("reason") or item.get("relevance") or "Relevant to role requirements.").strip()
            valid.append({"question": q_text, "type": q_type, "reason": reason})

        elif isinstance(item, str) and len(item.strip()) > 8:
            q_type = "behavioral" if i > 5 else "technical"
            valid.append({
                "question": item.strip(),
                "type": q_type,
                "reason": "Relevant to role requirements.",
            })

    return valid


def robust_parse_questions(text: str) -> list:
    """Safely parse questions from JSON, Markdown code fences, or numbered lists."""
    if not text or not text.strip():
        return []

    cleaned = extract_json_string(text)

    # Attempt 1: Standard JSON parse on extracted candidate
    try:
        data = json.loads(cleaned)
        questions = _extract_questions_from_any(data)
        if questions:
            return questions
    except Exception:
        pass

    # Attempt 2: Direct JSON parse on raw text
    try:
        data = json.loads(text.strip())
        questions = _extract_questions_from_any(data)
        if questions:
            return questions
    except Exception:
        pass

    # Attempt 3: Regex extract numbered list
    pattern = r"(?:^|\n)\s*(?:\d+[\.\)]|Question\s*\d+:?)\s*([^\n]+(?:\n(?!\s*(?:\d+[\.\)]|Question\s*\d+:?))[^\n]+)*)"
    matches = re.findall(pattern, text)

    valid = []
    for i, m in enumerate(matches, 1):
        q_text = m.strip()
        if len(q_text) > 10:
            q_type = (
                "behavioral"
                if i > 5 or any(w in q_text.lower() for w in ["tell me", "situation", "conflict", "team", "challenge", "describe a time"])
                else "technical"
            )
            valid.append({
                "question": q_text,
                "type": q_type,
                "reason": "Personalized practice question for this role.",
            })

    return valid

def validate_question_set(questions: list) -> list:
    """
    Validate that the generated interview contains exactly
    5 technical and 3 behavioral questions.
    """

    if not isinstance(questions, list):
        raise ValueError("Questions must be provided as a list.")

    if len(questions) != 8:
        raise ValueError(
            f"Expected exactly 8 questions, but received {len(questions)}."
        )

    seen_questions = set()
    technical_count = 0
    behavioral_count = 0

    for index, question in enumerate(questions, start=1):

        if not isinstance(question, dict):
            raise ValueError(
                f"Question {index} must be a dictionary."
            )

        question_text = question.get("question", "")

        if not isinstance(question_text, str) or not question_text.strip():
            raise ValueError(
                f"Question {index} has empty question text."
            )

        question_type = question.get("type")

        if question_type not in ("technical", "behavioral"):
            raise ValueError(
                f"Question {index} has an invalid type: {question_type}"
            )

        reason = question.get("reason")

        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(
                f"Question {index} has no valid relevance reason."
            )

        # Normalize text to identify exact duplicates
        normalized = re.sub(
            r"\s+",
            " ",
            question_text.lower().strip()
        )

        if normalized in seen_questions:
            raise ValueError(
                f"Duplicate question detected at position {index}."
            )

        seen_questions.add(normalized)

        if question_type == "technical":
            technical_count += 1
        else:
            behavioral_count += 1

    if technical_count != 5:
        raise ValueError(
            f"Expected 5 technical questions, "
            f"but received {technical_count}."
        )

    if behavioral_count != 3:
        raise ValueError(
            f"Expected 3 behavioral questions, "
            f"but received {behavioral_count}."
        )

    print(
        "\n[Validation] Question set passed: "
        "5 technical + 3 behavioral = 8 questions."
    )

    return questions


def deduplicate_questions(questions: list) -> list:
    """Remove exact duplicate questions while preserving order."""

    unique_questions = []
    seen = set()

    for question in questions:
        text = re.sub(
            r"\s+",
            " ",
            question["question"].strip().lower()
        )

        if text not in seen:
            seen.add(text)
            unique_questions.append(question)

    removed = len(questions) - len(unique_questions)

    if removed:
        print(f"[Validation] Removed {removed} duplicate question(s).")

    return unique_questions



def generate_questions(
    job_info: dict,
    company_research: str,
    resume_text: str = "",
) -> list:
    """
    Generate exactly 5 technical and 3 behavioral
    interview questions, with targeted repair if necessary.
    """

    if not isinstance(job_info, dict):
        raise ValueError("Job information must be a dictionary.")

    if not isinstance(company_research, str):
        raise ValueError("Company research must be a string.")

    if not isinstance(resume_text, str):
        raise ValueError("Resume text must be a string.")

    # ----------------------------------------------
    # 1. Prepare candidate context
    # ----------------------------------------------

    if resume_text.strip():
        candidate_context = resume_text.strip()[:MAX_RESUME_CHARS]
    else:
        candidate_context = "No resume information provided."

    # ----------------------------------------------
    # 2. Generate initial questions
    # ----------------------------------------------

    prompt = f"""
    /no_think

    You are an interview preparation assistant for PrepSense.

    Generate exactly 8 personalized interview questions.

    REQUIRED DISTRIBUTION:
    - Exactly 5 technical questions.
    - Exactly 3 behavioral questions.

    PERSONALIZATION RULES:

- Use the job information, company research and resume.
- Connect demonstrated candidate experience with job requirements.

RESUME-GROUNDING RULES:

1. Treat the resume as the only source of information
   about the candidate's past experience and achievements.

2. Only ask "How have you..." or "Describe your experience..."
   when the resume explicitly establishes that experience.

3. If a technology appears in the resume's project or
   experience section, you may ask about its actual use.

4. If a technology appears only in the resume's skills
   section, ask about familiarity or knowledge rather
   than assuming project experience.

5. If a technology appears only in the job description
   and not in the resume, use hypothetical questions
   such as "How would you..." or "How would you approach...".

6. Never invent candidate projects, responsibilities,
   achievements, tools used or professional experience.

7. Do not infer that the candidate used a technology
   simply because it is required by the job description.

OTHER RULES:

- Generate distinct technical and behavioral questions.
- Avoid duplicate or repetitive questions.
- Every question must have a meaningful relevance reason.
- Do not provide answers.

    Return ONLY valid JSON in this structure:

    {{
        "questions": [
            {{
                "question": "Question text",
                "type": "technical",
                "reason": "Why this question is relevant"
            }}
        ]
    }}

    Job information:
    {json.dumps(job_info, indent=2)}

    Company research:
    {company_research[:3000]}

    Candidate resume:
    {candidate_context}
    """

    print("\nAsking Qwen to generate initial questions...")

    response = ask_ai(prompt)

    questions = robust_parse_questions(response)

    # ----------------------------------------------
    # 3. Remove duplicates and excess questions
    # ----------------------------------------------

    questions = deduplicate_questions(questions)

    expected = {
        "technical": 5,
        "behavioral": 3,
    }

    # Keep no more than the required number per category.
    # Any missing slots will be filled using targeted repair.
    selected_questions = []
    counts = {
        "technical": 0,
        "behavioral": 0,
    }

    for question in questions:

        question_type = question["type"]

        if counts[question_type] < expected[question_type]:
            selected_questions.append(question)
            counts[question_type] += 1

    questions = selected_questions

    # ----------------------------------------------
    # 4. Identify missing questions
    # ----------------------------------------------

    missing = {
        question_type: expected[question_type] - counts[question_type]
        for question_type in expected
    }

    total_missing = sum(missing.values())

    print("\n[Validation] Initial question distribution:")
    print(f"Technical: {counts['technical']}/5")
    print(f"Behavioral: {counts['behavioral']}/3")

    # ----------------------------------------------
    # 5. Generate only missing questions
    # ----------------------------------------------

    if total_missing > 0:

        print(
            f"\n[Repair] {total_missing} question(s) missing. "
            "Generating only missing questions..."
        )

        existing_questions = [
            question["question"] for question in questions
        ]

        repair_prompt = f"""
        /no_think

        You are repairing an incomplete interview question set.

        Generate ONLY the missing interview questions.

        REQUIRED MISSING QUESTIONS:
        - Technical: {missing['technical']}
        - Behavioral: {missing['behavioral']}
        - Total: {total_missing}

        Existing questions (DO NOT REPEAT THESE):
        {json.dumps(existing_questions, indent=2)}

        Job information:
        {json.dumps(job_info, indent=2)}

        Company research:
        {company_research[:2000]}

        Candidate resume:
        {candidate_context}

        RULES:

        - Generate exactly the requested missing question counts.
        - Use the correct type for every question.
        - Do not repeat existing questions.
        - Use the candidate resume as the source of truth
          for past experience and achievements.
        - If a technology appears in a resume project or
          work experience, you may ask about its actual use.
        - If a technology appears only in the resume skills
          section, ask about familiarity or knowledge.
        - If a technology appears only in the job description,
          ask hypothetical questions using "How would you..."
          rather than assuming previous experience.
        - Never invent candidate projects, responsibilities
          or achievements.
        - Give every question a meaningful relevance reason.
        - Do not provide answers.

        Return ONLY valid JSON:

        {{
            "questions": [
                {{
                    "question": "Question text",
                    "type": "technical",
                    "reason": "Why this question is relevant"
                }}
            ]
        }}
        """

        repaired_response = ask_ai(repair_prompt)

        repaired_questions = robust_parse_questions(
            repaired_response
        )

        repaired_questions = deduplicate_questions(
            repaired_questions
        )

        # Append only the missing categories.
        seen = {
            re.sub(
                r"\s+",
                " ",
                question["question"].strip().lower()
            )
            for question in questions
        }

        for question in repaired_questions:

            question_type = question["type"]

            if counts[question_type] >= expected[question_type]:
                continue

            question_key = re.sub(
                r"\s+",
                " ",
                question["question"].strip().lower()
            )

            if question_key in seen:
                continue

            questions.append(question)
            seen.add(question_key)
            counts[question_type] += 1

            print(
                f"[Repair] Added one {question_type} question."
            )

    # ----------------------------------------------
    # 6. Final strict validation
    # ----------------------------------------------

    if counts != expected:
        raise ValueError(
            "Question generation could not satisfy the required "
            "distribution after repair. "
            f"Received {counts['technical']} technical and "
            f"{counts['behavioral']} behavioral questions."
        )

    questions = validate_question_set(questions)

    print("\n[Generator] Interview question generation successful.")

    return questions


if __name__ == "__main__":

    sample_job = """
    Backend Developer Intern.

    Required skills: Python, PostgreSQL, and FastAPI.
    Tools: Git, Docker, and Postman.

    Responsibilities: Build and test REST API endpoints,
    debug backend services, and write unit tests.

    Qualifications: Currently pursuing a Computer Science
    degree, basic knowledge of databases, and 0-1 years
    of experience.
    """

    sample_resume = """
    Computer Science undergraduate specializing in AI/ML.

    Skills: Python, SQL, PySpark, Machine Learning.

    Projects:
    - Built a wealth management analytics platform.
    - Created data pipelines using PySpark.
    - Developed a data warehouse using a star schema.

    Experience:
    Wealth Management Analytics Internship.
    """

    try:
        print("\nSTEP 1: Parsing the job description...")
        job_info = parse_job_description(sample_job)

        print("\nSTEP 2: Researching Microsoft...")
        company_results = search_company("Microsoft")
        company_research = summarize_company_research(company_results)

        print("\nSTEP 3: Generating personalized questions...")
        questions = generate_questions(
            job_info=job_info,
            company_research=company_research,
            resume_text=sample_resume,
        )

        print("\n" + "=" * 55)
        print("       PREPSENSE INTERVIEW QUESTIONS")
        print("=" * 55)

        for number, question in enumerate(questions, start=1):
            print(f"\n{number}. [{question['type'].upper()}]")
            print(question["question"])
            print(f"   Reason: {question['reason']}")

        print(f"\nSuccess! {len(questions)} questions ready.")

    except (ValueError, RuntimeError) as error:
        print(f"\nPrepSense encountered a problem: {error}")
