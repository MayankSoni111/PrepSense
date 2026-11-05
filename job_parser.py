import json
import re
from llm import ask_ai, extract_json_string


def robust_parse_job_info(text: str) -> dict:
    """
    Parse job information from any LLM response format:
    1. Valid JSON
    2. Markdown-fenced JSON (```json ... ```)
    3. Conversational JSON
    4. Plain-text / YAML-style bullet lists
    """
    default_structure = {
        "job_title": "",
        "technical_skills": [],
        "tools_and_technologies": [],
        "responsibilities": [],
        "qualifications": [],
    }

    if not text or not text.strip():
        return default_structure

    cleaned = extract_json_string(text)

    # Attempt 1: Standard JSON parse from extracted candidate
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return _normalize_job_dict(parsed)
    except Exception:
        pass

    # Attempt 2: Direct JSON parse on raw text
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, dict):
            return _normalize_job_dict(parsed)
    except Exception:
        pass

    # Attempt 3: Fallback regex parser for plain-text / YAML headers
    result = {
        "job_title": "",
        "technical_skills": [],
        "tools_and_technologies": [],
        "responsibilities": [],
        "qualifications": [],
    }

    title_match = re.search(r"job_title\s*:\s*[\"']?([^\n,\"]+)", text, re.IGNORECASE)
    if title_match:
        result["job_title"] = title_match.group(1).strip()

    sections = [
        ("technical_skills", r"(?:technical_skills|technical skills)\s*:"),
        ("tools_and_technologies", r"(?:tools_and_technologies|tools and technologies)\s*:"),
        ("responsibilities", r"responsibilities\s*:"),
        ("qualifications", r"qualifications\s*:"),
    ]

    found_headers = []
    for key, pattern in sections:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            found_headers.append((m.start(), m.end(), key))

    found_headers.sort(key=lambda x: x[0])

    for i, (start_pos, end_pos, key) in enumerate(found_headers):
        next_start = found_headers[i + 1][0] if i + 1 < len(found_headers) else len(text)
        section_body = text[end_pos:next_start].strip()

        items = re.split(r"\n\s*[-*•]\s*|\s*[-*•]\s*", section_body)
        cleaned_items = [
            item.strip().strip('"').strip("'").strip(",")
            for item in items
            if item.strip() and len(item.strip()) > 1
        ]
        result[key] = cleaned_items

    return result


def _normalize_job_dict(data: dict) -> dict:
    required_keys = [
        "job_title",
        "technical_skills",
        "tools_and_technologies",
        "responsibilities",
        "qualifications",
    ]
    result = {}
    for k in required_keys:
        val = data.get(k)
        if k == "job_title":
            result[k] = str(val).strip() if val else ""
        else:
            if isinstance(val, list):
                result[k] = [str(item).strip() for item in val if item]
            elif isinstance(val, str) and val.strip():
                result[k] = [item.strip() for item in val.split("\n") if item.strip()]
            else:
                result[k] = []
    return result


def parse_job_description(job_description: str) -> dict:
    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    job_text = job_description.strip()[:2500]

    prompt = f"""
    Analyze the following job description and extract information.

    Return ONLY a JSON object with this exact structure:
    {{
        "job_title": "Role title",
        "technical_skills": ["skill 1", "skill 2"],
        "tools_and_technologies": ["tool 1", "tool 2"],
        "responsibilities": ["duty 1", "duty 2"],
        "qualifications": ["requirement 1"]
    }}

    Rules:
    - Return ONLY the JSON object. Do not include markdown explanation.
    - Keep lists concise (top 4-6 items per category).

    Job description:
    {job_text}
    """

    response = ask_ai(prompt)

    job_info = robust_parse_job_info(response)

    return job_info


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

    result = parse_job_description(sample_job)

    print(json.dumps(result, indent=2))
