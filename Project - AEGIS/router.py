# router.py
# Layer 3 of the Aegis pipeline — routes each query to the right model.
#
# The core insight: not every query needs GPT-4. A refund status check
# doesn't need the same model as a legal contract analysis. Paying for
# GPT-4 on simple queries is the biggest controllable cost in an LLM product.
#
# Routing logic:
#   Short + no complexity flags  →  fast model   (free tier)
#   Medium OR some complexity    →  balanced model
#   Long OR high complexity      →  powerful model (paid)
#
# Current routing uses token count + keyword flags.
# Next version: replace keyword flags with a trained intent classifier.

MODELS = {
    "fast": {
        "id": "llama-3.1-8b-instant",
        "provider": "groq",
        "cost_per_1k_tokens": 0.0,
        "max_tokens_input": 8000,
    },
    "balanced": {
        "id": "llama-3.3-70b-versatile",
        "provider": "groq",
        "cost_per_1k_tokens": 0.0008,
        "max_tokens_input": 32000,
    },
    "powerful": {
        "id": "gpt-4o",
        "provider": "openai",
        "cost_per_1k_tokens": 0.005,
        "max_tokens_input": 128000,
    }
}

# These signal that the query needs actual reasoning, not just retrieval
COMPLEXITY_FLAGS = [
    "compare", "analyze", "analyse", "explain why", "evaluate",
    "contract", "legal", "strategy", "architecture", "tradeoff",
    "trade-off", "pros and cons", "recommend", "financial", "audit",
    "difference between", "which is better", "should i"
]

FAST_TOKEN_LIMIT = 150
BALANCED_TOKEN_LIMIT = 500


def count_tokens(text: str) -> int:
    """
    Rough token estimate — 1 token ≈ 4 characters.
    Not billing-accurate but good enough for routing decisions.
    """
    return len(text) // 4


def has_complexity_flags(text: str) -> bool:
    text_lower = text.lower()
    triggered = [f for f in COMPLEXITY_FLAGS if f in text_lower]
    if triggered:
        print(f"[ROUTER] Complexity flags: {triggered}")
        return True
    return False


def route(prompt: str) -> dict:
    """
    Takes a prompt, returns the model config dict to use for inference.
    """
    token_count = count_tokens(prompt)
    is_complex = has_complexity_flags(prompt)

    print(f"[ROUTER] Token estimate: {token_count}")

    if token_count > BALANCED_TOKEN_LIMIT or is_complex:
        selected = "powerful"
    elif token_count > FAST_TOKEN_LIMIT:
        selected = "balanced"
    else:
        selected = "fast"

    model = MODELS[selected]
    estimated_cost = model["cost_per_1k_tokens"] * token_count / 1000

    print(f"[ROUTER] → {selected.upper()} | Model: {model['id']}")
    print(f"[ROUTER] Estimated cost: ${estimated_cost:.6f}")

    return model
