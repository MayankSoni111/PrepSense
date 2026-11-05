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


def generate_questions(
    job_info: dict,
    company_research: str,
    resume_text: str = "",
) -> list:
    """
    Generate and validate interview questions using
    job information, company research, and resume context.
    """

    if not isinstance(resume_text, str):
        raise ValueError("Resume text must be a string.")

    if resume_text.strip():
        candidate_context = resume_text.strip()[:MAX_RESUME_CHARS]
    else:
        candidate_context = "No resume information provided."

    prompt = f"""
    You are an interview preparation assistant for PrepSense.

    Generate 8 personalized interview questions using the following:
    1. Job information
    2. Company research
    3. Candidate resume

    Requirements:
    - 5 technical questions and 3 behavioral questions.
    - Make questions relevant to the job role and required skills.
    - Connect candidate experience with job requirements where relevant.
    - Do not invent unsupported company facts or achievements.
    - Avoid duplicate questions.
    - Do not provide answers.

    Return a JSON object with this exact structure:
    {{
        "questions": [
            {{
                "question": "The interview question",
                "type": "technical",
                "reason": "Why this question is relevant"
            }}
        ]
    }}

    Job information:
    {json.dumps(job_info, indent=2)}

    Company research:
    {company_research}

    Candidate resume:
    {candidate_context}
    """

    print("Asking Qwen to generate questions...")
    response = ask_ai(prompt)

    questions = robust_parse_questions(response)

    # Fallback to repair only if absolutely 0 questions were parsed
    if not questions:
        print("Initial response did not yield questions. Attempting repair...")
        repair_prompt = f"""
        Format the following into 8 interview questions as a JSON object:
        {{
            "questions": [
                {{"question": "Question text", "type": "technical", "reason": "Reason"}}
            ]
        }}

        Content:
        {response[:1500]}
        """
        repaired_response = ask_ai(repair_prompt)
        questions = robust_parse_questions(repaired_response)

    if not questions:
        raise ValueError("Unable to generate interview questions. Please try again.")

    # Ensure technical/behavioral normalization
    for q in questions:
        if q["type"] not in ("technical", "behavioral"):
            q["type"] = "technical"

    return questions[:8]


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
