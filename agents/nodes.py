import time
from agents.state import InterviewState
from resume_parser import extract_resume_text
from tools.company_research import search_company, summarize_company_research
from job_parser import parse_job_description
from question_generator import (
    generate_questions,
    validate_question_set,
)


def extract_resume_node(state: InterviewState) -> dict:
    """
    Node 1: Extract plain text from candidate resume PDF.
    """
    print("\n[LangGraph Node] 📄 Extracting resume information...")
    start = time.perf_counter()
    resume_pdf = state.get("resume_pdf")
    if not resume_pdf:
        return {
            "resume_text": "",
            "current_step": "resume_extracted",
        }

    resume_text = extract_resume_text(resume_pdf)
    elapsed = time.perf_counter() - start
    print(f"[LangGraph Node] Resume text extracted in {elapsed:.2f}s ({len(resume_text)} chars)")
    return {
        "resume_text": resume_text,
        "current_step": "resume_extracted",
    }


def research_company_node(state: InterviewState) -> dict:
    """
    Node 2: Search web intelligence for target company and synthesize profile.
    """
    company_name = state.get("company_name", "").strip()
    print(f"\n[LangGraph Node] 🌐 Researching company: {company_name}...")
    start = time.perf_counter()

    # Step 1: Web search via Tavily
    search_results = search_company(company_name)

    # Step 2: Synthesize concise company research via LLM
    summary = summarize_company_research(search_results)
    elapsed = time.perf_counter() - start
    print(f"[LangGraph Node] Company research completed in {elapsed:.2f}s")

    return {
        "company_research": summary,
        "current_step": "company_researched",
    }


def parse_job_node(state: InterviewState) -> dict:
    """
    Node 3: Analyze job description and extract skills, tools, and duties.
    """
    job_description = state.get("job_description", "").strip()
    print("\n[LangGraph Node] 📋 Parsing job description and requirements...")
    start = time.perf_counter()

    job_info = parse_job_description(job_description)
    elapsed = time.perf_counter() - start
    print(f"[LangGraph Node] Job parsed in {elapsed:.2f}s ({job_info.get('job_title', 'Role')})")

    return {
        "job_info": job_info,
        "current_step": "job_parsed",
    }


def generate_questions_node(state: InterviewState) -> dict:
    """
    Node 4: Generate tailored technical & behavioral interview questions.
    """
    print("\n[LangGraph Node] 🎯 Generating personalized interview questions...")
    start = time.perf_counter()

    job_info = state.get("job_info", {})
    company_research = state.get("company_research", "")
    resume_text = state.get("resume_text", "")

    questions = generate_questions(
        job_info=job_info,
        company_research=company_research,
        resume_text=resume_text,
    )
    elapsed = time.perf_counter() - start
    print(f"[LangGraph Node] Generated {len(questions)} questions in {elapsed:.2f}s")

    return {
        "questions": questions,
        "current_step": "questions_generated",
    }

def validate_questions_node(state: InterviewState) -> dict:
    """
    Node 5: Validate the generated interview questions.

    The interview is marked ready only when the question
    set contains exactly 5 technical and 3 behavioral questions.
    """

    print("\n[LangGraph Node] Validating generated questions...")

    # Step 1: Read generated questions from shared state
    questions = state.get("questions", [])

    # Step 2: Validate the questions
    validated_questions = validate_question_set(questions)

    # Step 3: Update shared state after successful validation
    print("[LangGraph Node] Question validation successful.")

    return {
        "questions": validated_questions,
        "questions_validated": True,
        "current_step": "interview_ready",
    }
