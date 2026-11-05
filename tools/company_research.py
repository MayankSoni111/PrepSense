import os

from dotenv import load_dotenv
from tavily import TavilyClient
from llm import ask_ai

# Load variables from the project's .env file
load_dotenv()

# Read the API key securely
api_key = os.getenv("TAVILY_API_KEY")

if not api_key:
    raise ValueError(
        "TAVILY_API_KEY not found. Check your .env file."
    )

# Create the Tavily client
tavily = TavilyClient(api_key=api_key)


def search_company(company_name: str) -> dict:
    """Search the web for useful information about a company."""

    if not company_name.strip():
        raise ValueError("Company name cannot be empty.")

    response = tavily.search(
        query=f"{company_name} company overview products technology",
        search_depth="basic",
        max_results=5,
    )

    return response


def summarize_company_research(search_results: dict) -> str:
    """Summarize Tavily results into a concise company research profile."""

    results = search_results.get("results", [])

    if not results:
        return "No company research results were found."

    research_text = ""

    for result in results:
        research_text += (
            f"\nTitle: {result.get('title', '')}\n"
            f"Content: {result.get('content', '')}\n"
        )

    # Keep snippet under 2000 chars so prompt processing is fast
    snippet = research_text[:2000].strip()

    prompt = f"""
    You are a company research assistant for PrepSense, an interview preparation workspace.

    Summarize the company research in under 150 words using exactly these 3 concise sections:
    1. Overview & Core Mission (1-2 sentences)
    2. Main Products & Technologies
    3. Suggested Interview Topics (2-3 bullet points)

    Be direct, brief, and factual. Do not write essays or introductory filler.

    Research:
    {snippet}
    """

    return ask_ai(prompt)


if __name__ == "__main__":
    results = search_company("Microsoft")
    summary = summarize_company_research(results)

    print("\nCOMPANY RESEARCH PROFILE")
    print("=" * 50)
    print(summary)
