# aegis.py
# The full pipeline — all three layers wired together.
#
# Flow:
#   Raw prompt → [Scrubber] → [Cache] → [Router] → [LLM] → Response
#
# Every prompt passes through all layers in sequence.
# Cache hits short-circuit at Layer 2 — no router, no LLM call, $0 cost.

import os
from groq import Groq
from dotenv import load_dotenv

from scrubber import scrub
from cache import check_cache, store_in_cache
from router import route

load_dotenv()

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# OpenAI client — uncomment when you add an OpenAI key to .env
# from openai import OpenAI
# openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def call_llm(prompt: str, model_config: dict) -> str:
    """
    Sends the clean, routed prompt to the correct LLM provider.
    Logs token breakdown for P&L visibility.
    """
    provider = model_config["provider"]

    if provider == "groq":
        response = groq_client.chat.completions.create(
            model=model_config["id"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
    elif provider == "openai":
        # OpenAI path — wire this up when budget allows
        raise NotImplementedError("OpenAI client not configured. Add key to .env and uncomment client above.")
    else:
        raise ValueError(f"Unknown provider: {provider}")

    text = response.choices[0].message.content
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    total_tokens = response.usage.total_tokens

    print(f"[LLM] Prompt: {prompt_tokens} | Completion: {completion_tokens} | Total: {total_tokens}")

    return text


def process(raw_prompt: str) -> str:
    """
    The Aegis pipeline. Single entry point for all queries.

    Args:
        raw_prompt: Raw user input, potentially containing PII.

    Returns:
        Clean LLM response — either from cache or live inference.
    """
    print("\n" + "=" * 55)
    print(f"[AEGIS] Input: {raw_prompt[:60]}...")
    print("=" * 55)

    # --- Layer 1: PII Scrubbing ---
    clean_prompt, audit = scrub(raw_prompt)

    if audit:
        redacted = [f"{i['pii_type']} ({i['confidence']})" for i in audit]
        print(f"[SCRUBBER] Redacted: {redacted}")
    else:
        print("[SCRUBBER] Clean — no PII detected")

    # --- Layer 2: Semantic Cache ---
    cached_response = check_cache(clean_prompt)

    if cached_response:
        print("[AEGIS] Returning cached response")
        return cached_response

    # --- Layer 3: Model Routing ---
    model_config = route(clean_prompt)

    # --- Layer 4: LLM Inference ---
    response = call_llm(clean_prompt, model_config)

    # Store for future hits
    store_in_cache(clean_prompt, response)

    return response


if __name__ == "__main__":
    # Test queries — designed to exercise all three routing tiers
    # and demonstrate cache hit on the second refund-related query

    queries = [
        # Tier 1: Simple — should route to fast model
        "What is your return policy for damaged products?",

        # Cache hit test — different words, same intent as query 1
        "How do I get a refund on something I bought?",

        # Tier 3: Complex — should route to powerful model
        "Analyze the tradeoffs between synchronous and async API design "
        "for a high-throughput LLM gateway handling 10,000 requests per day.",
    ]

    for query in queries:
        result = process(query)
        print(f"\n[RESPONSE]\n{result}\n")
