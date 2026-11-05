import json
import time

from answer_evaluator import evaluate_answer
from agents.graph import interview_graph


def prepare_interview(
    company_name: str,
    job_description: str,
    resume_pdf,
    progress_callback=None,
) -> dict:
    """
    Prepare personalized interview questions using the LangGraph agent workflow.
    Executes the StateGraph and streams progress node by node to progress_callback.
    """

    # Step 1: Validate user inputs
    if not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    if not job_description.strip():
        raise ValueError("Job description cannot be empty.")

    initial_state = {
        "company_name": company_name.strip(),
        "job_description": job_description.strip(),
        "resume_pdf": resume_pdf,
    }

    step_labels = {
        "extract_resume": "📄 Extracting resume information...",
        "research_company": f"🌐 Searching web intelligence for {company_name.strip()}...",
        "parse_job": "📋 Analyzing job description and key skills...",
        "generate_questions": "🎯 Generating personalized interview questions...",
    }

    final_state = dict(initial_state)

    print("\n--- [LANGGRAPH] Starting Agent Execution ---")
    start = time.perf_counter()

    # Stream graph execution so each node reports completion in real time
    for output in interview_graph.stream(initial_state):
        for node_name, node_output in output.items():
            print(f"[LANGGRAPH Stream] Node '{node_name}' finished.")
            if progress_callback and node_name in step_labels:
                progress_callback(step_labels[node_name])
            if isinstance(node_output, dict):
                final_state.update(node_output)

    total_time = time.perf_counter() - start
    print(f"--- [LANGGRAPH] Agent Finished in {total_time:.2f}s ---\n")

    return {
        "company_name": company_name.strip(),
        "company_research": final_state.get("company_research", ""),
        "job_info": final_state.get("job_info", {}),
        "resume_text": final_state.get("resume_text", ""),
        "questions": final_state.get("questions", []),
    }


def evaluate_candidate_answer(
    question: dict,
    candidate_answer: str,
    job_info: dict,
) -> dict:
    """
    Evaluate a candidate's answer using the generated
    interview question and job information.
    """

    if not isinstance(question, dict):
        raise ValueError("Question must be a dictionary.")

    question_text = question.get("question", "")
    question_type = question.get("type", "")

    if not isinstance(question_text, str) or not question_text.strip():
        raise ValueError("Invalid interview question.")

    # Build a concise role context so prompt evaluation is near-instant (<25 tokens)
    role_title = job_info.get("job_title", "Candidate Role") if isinstance(job_info, dict) else "Role"
    key_skills = ", ".join(job_info.get("technical_skills", [])[:5]) if isinstance(job_info, dict) else ""
    job_context = f"Role: {role_title}. Key skills: {key_skills}."

    feedback = evaluate_answer(
        question=question_text,
        answer=candidate_answer,
        job_context=job_context,
        question_type=question_type,
    )

    return feedback


if __name__ == "__main__":

    sample_company = "Microsoft"

    sample_job_description = """
    Backend Developer Intern

    Required skills:
    Python, PostgreSQL, FastAPI and REST APIs.

    Tools and technologies:
    Git, Docker and Postman.

    Responsibilities:
    Build and test REST API endpoints.
    Debug backend services.
    Write unit tests and improve application performance.

    Qualifications:
    Currently pursuing a Computer Science degree.
    Basic knowledge of databases and programming.
    """

    resume_pdf_path = input(
        "Enter the path to your resume PDF: "
    ).strip().strip('"')

    if not resume_pdf_path:
        raise ValueError("Resume PDF path cannot be empty.")

    print("\nStarting PrepSense LangGraph Agent...")

    result = prepare_interview(
        company_name=sample_company,
        job_description=sample_job_description,
        resume_pdf=resume_pdf_path,
    )

    print("\nCOMPANY RESEARCH")
    print("=" * 50)
    print(result["company_research"])

    print("\nJOB INFORMATION")
    print("=" * 50)
    print(json.dumps(result["job_info"], indent=2))

    print("\nRESUME INFORMATION")
    print("=" * 50)
    print(f"Extracted characters: {len(result['resume_text'])}")

    print("\nGENERATED INTERVIEW QUESTIONS")
    print("=" * 50)
    for index, question in enumerate(result["questions"], start=1):
        print(f"\nQuestion {index}: {question['question']}")
        print(f"Type: {question['type']}")
        print(f"Reason: {question['reason']}")
