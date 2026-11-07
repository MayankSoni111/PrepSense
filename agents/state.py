from typing import TypedDict, List, Dict, Any, Optional


class InterviewState(TypedDict, total=False):
    """
    Shared state passed between nodes in the PrepSense
    LangGraph workflow.

    Every node reads the information it needs and returns
    only the fields it updates.
    """

    # ==============================================
    # 1. USER INPUTS
    # ==============================================

    company_name: str
    job_description: str
    resume_pdf: Any

    # ==============================================
    # 2. RESUME AND COMPANY RESEARCH
    # ==============================================

    resume_text: str
    company_research: str

    # ==============================================
    # 3. JOB DESCRIPTION PROCESSING
    # ==============================================

    job_info: Dict[str, Any]

    # ==============================================
    # 4. QUESTION GENERATION
    # ==============================================
    questions: List[Dict[str, Any]]
    questions_validated: bool

    # ==============================================
    # 5. ANSWER EVALUATION
    # ==============================================

    selected_question: Dict[str, Any]
    candidate_answer: str
    feedback: Dict[str, Any]

    # ==============================================
    # 6. EXECUTION TRACKING
    # ==============================================

    current_step: str
    error: Optional[str]
