from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine

# Create an NLP provider to explicitly use the smaller model
provider = NlpEngineProvider(nlp_configuration={
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}]
})
nlp_engine = provider.create_engine()

# Pass the engine to the analyzer
analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
anonymizer = AnonymizerEngine()

# PII types we care about for an Indian enterprise context
ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS", 
    "PHONE_NUMBER",
    "LOCATION",
    "IN_PAN",
    "IN_AADHAAR",
]

def scrub(text: str) -> tuple[str, list]:
    """
    Takes a raw prompt, returns (clean_prompt, audit_log).
    LLM only ever sees clean_prompt.
    audit_log is your compliance paper trail.
    """
    results = analyzer.analyze(text=text, entities=ENTITIES, language="en")

    if not results:
        # Nothing found — pass through unchanged
        return text, []

    cleaned = anonymizer.anonymize(text=text, analyzer_results=results)

    audit_log = [
        {
            "pii_type": r.entity_type,
            "confidence": round(r.score, 2)
        }
        for r in results
    ]

    return cleaned.text, audit_log


# --- Standalone test ---
if __name__ == "__main__":
    test_prompt = """
    Hi, I'm Tarun Sai from New Delhi. 
    Reach me at tarun@yuvayantra.com or +91 9876543210.
    My PAN is ABCDE1234F and Aadhaar is 1234 5678 9012.
    """

    clean, audit = scrub(test_prompt)

    print("[SCRUBBED PROMPT]")
    print(clean)

    print("\n[AUDIT LOG]")
    for item in audit:
        print(f"  → {item['pii_type']} detected (confidence: {item['confidence']})")
