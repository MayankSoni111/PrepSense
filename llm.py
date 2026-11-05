import re
import time
from langchain_ollama import ChatOllama

# ---------------------------------------------------------------------------
# Singleton LLM client
# Using a module-level guard so ChatOllama is created only once,
# even when Streamlit reimports this module on every rerun.
# ---------------------------------------------------------------------------

_llm = None


def _get_llm() -> ChatOllama:
    """Return the shared ChatOllama instance, creating it only once."""
    global _llm
    if _llm is None:
        print("[LLM] Loading ChatOllama client...")
        _llm = ChatOllama(
            model="qwen3:8b",
            temperature=0.2,
            reasoning=False,   # Disable reasoning/thinking tags in LangChain
            num_ctx=2048,      # Fits in 6GB VRAM on RTX 4050
            num_predict=800,   # Prevent runaway token generation
        )
        print("[LLM] ChatOllama client ready.")
    return _llm


def ask_ai(prompt: str, **kwargs) -> str:
    """Send a prompt to the local model and measure inference."""
    client = _get_llm()
    response = client.invoke(prompt)
    metadata = response.response_metadata
    print("\n--- OLLAMA PERFORMANCE ---")
    for key in [
        "load_duration",
        "prompt_eval_count",
        "prompt_eval_duration",
        "eval_count",
        "eval_duration",
        "total_duration",
    ]:
        value = metadata.get(key)
        if key.endswith("_duration") and isinstance(value, (int, float)):
            value = f"{value / 1_000_000_000:.2f} seconds"
        print(f"{key}: {value}")
    print("--------------------------\n")
    return response.content


def extract_json_string(text: str) -> str:
    """
    Safely extract a JSON substring from an LLM response.
    Handles:
    - Markdown code fences (```json ... ``` or ``` ... ```)
    - JSON Arrays [ ... ] or JSON Objects { ... }
    - Extra conversational text before or after JSON
    """
    if not text:
        return ""

    cleaned = text.strip()

    # Step 1: Strip markdown code fences if present
    fence_pattern = r"```(?:json)?\s*(.*?)\s*```"
    match = re.search(fence_pattern, cleaned, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    elif cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE).strip()

    # Step 2: Determine if outermost JSON is an array [ ... ] or object { ... }
    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")

    # If '[' comes before '{' (or no '{' exists), extract the array
    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        last_bracket = cleaned.rfind("]")
        if last_bracket > first_bracket:
            return cleaned[first_bracket : last_bracket + 1]

    # Otherwise extract the object
    if first_brace != -1:
        last_brace = cleaned.rfind("}")
        if last_brace > first_brace:
            return cleaned[first_brace : last_brace + 1]

    return cleaned


# Alias for backward compatibility
strip_code_fences = extract_json_string
