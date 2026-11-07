"""
LangGraph Agent Workflow Definition
Connects nodes into an orchestrated StateGraph workflow.
"""

from langgraph.graph import StateGraph, START, END

from agents.state import InterviewState
from agents.nodes import (
    extract_resume_node,
    research_company_node,
    parse_job_node,
    generate_questions_node,
    validate_questions_node,
)


def create_interview_graph():
    """Build and compile the single-agent StateGraph workflow."""
    builder = StateGraph(InterviewState)

    # 1. Register graph nodes
    builder.add_node("extract_resume", extract_resume_node)
    builder.add_node("research_company", research_company_node)
    builder.add_node("parse_job", parse_job_node)
    builder.add_node("generate_questions", generate_questions_node)
    builder.add_node("validate_questions", validate_questions_node)

    # 2. Connect nodes with directed execution edges
    builder.add_edge(START, "extract_resume")
    builder.add_edge("extract_resume", "research_company")
    builder.add_edge("research_company", "parse_job")
    builder.add_edge("parse_job", "generate_questions")
    builder.add_edge(
    "generate_questions",
    "validate_questions"
    )

    builder.add_edge("validate_questions", END)

    # 3. Compile graph into an executable Runnable
    return builder.compile()


# Shared compiled graph instance
interview_graph = create_interview_graph()
