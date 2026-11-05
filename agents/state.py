from typing import TypedDict, List, Dict, Any, Optional


class InterviewState(TypedDict, total=False):
    """
    Central State object passed between nodes in the LangGraph workflow.
    Every node reads needed inputs from this state and returns updated fields.
    """
    # Inputs provided by user
    company_name: str
    job_description: str
    resume_pdf: Any

    # Generated artifacts
    resume_text: str
    company_research: str
    job_info: Dict[str, Any]
    questions: List[Dict[str, Any]]

    # Execution tracking & error reporting
    current_step: str
    error: Optional[str]
