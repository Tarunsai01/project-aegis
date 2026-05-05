# Project Aegis — LLM Gateway

Built this because I kept seeing the same problem: companies plugging directly into OpenAI with no layer in between. No PII filtering, no caching repeated queries, no logic deciding whether a simple question actually needs GPT-4. Just raw API calls and a growing bill.

Aegis is the interception layer. Every prompt passes through three stages before it touches an LLM.

---

## What It Does

**1. PII Scrubbing**
Strips emails, phone numbers, names, locations, Aadhaar, and PAN from prompts before they leave your server. Using Microsoft Presidio over regex because Presidio catches unstructured PII — "my name is Tarun from New Delhi" — not just formatted patterns.

**2. Semantic Caching**
Stores LLM responses as meaning vectors in ChromaDB. When a similar query comes in — not identical, similar — it serves the cached response instead of making a new API call. "What's your refund policy?" and "how do I return something?" resolve to the same answer. Second query costs $0.

**3. Dynamic Model Routing**
Short, simple queries go to the fast free-tier model. Complex queries (long prompts, reasoning keywords) get routed to the capable model. The router checks token count and intent signals to make the call. Not every question needs GPT-4.

---

## The Pipeline

```
Raw User Prompt
       │
       ▼
  [Scrubber]         strip PII — Presidio
       │
       ▼
  [Cache Check]      semantic similarity ≥ 0.85 → serve cached response, $0
       │
    miss ↓
       ▼
  [Router]           token count + complexity flags → pick model tier
       │
       ▼
  [LLM Call]         Groq (Llama 3) or OpenAI (GPT-4o)
       │
       ▼
  store in cache → return response
```

---

## Stack

| Layer | Tool | Why |
|---|---|---|
| PII Scrubbing | Microsoft Presidio | Catches unstructured PII, not just formatted patterns |
| Embeddings | sentence-transformers (MiniLM) | 80MB, runs fully local, no API cost |
| Vector DB | ChromaDB | Persistent, simple, no infra overhead |
| LLM (fast) | Groq — Llama 3.1 8B | ~300 tokens/sec, free tier |
| LLM (powerful) | OpenAI GPT-4o | Complex reasoning tasks |

---

## Setup

**1. Clone and install**
```bash
git clone https://github.com/yourusername/project-aegis.git
cd project-aegis
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

**2. Add your keys**
```bash
cp .env.example .env
# Add your GROQ_API_KEY — get one free at console.groq.com
```

**3. Run**
```bash
python aegis.py
```

---

## File Structure

```
project-aegis/
├── aegis.py          # main pipeline — entry point
├── scrubber.py       # layer 1: PII interception
├── cache.py          # layer 2: semantic cache
├── router.py         # layer 3: model routing logic
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Cost Impact (Why This Matters)

Running 10,000 queries/day through a direct OpenAI integration with no caching:

- Average cost: ~$0.002/call
- Daily spend: ~$20
- Monthly: ~$600

With Aegis, assuming 40% repeated intent (conservative for most enterprise use cases):

- 4,000 cache hits/day → $0
- 6,000 LLM calls, majority routed to free-tier Groq
- Monthly spend: ~$80–120

That's the unit economics case for building this.

---

## What's Missing / What's Next

This is a working prototype, not a production system. Known gaps:

- Router uses keyword flags — next version should use an intent classifier
- No rate limiting or queue management
- No auth layer (API keys, user sessions)
- OpenAI path is stubbed — needs client setup
- Similarity threshold (0.85) is hardcoded — should be configurable per use case
- No dashboard / observability — audit logs print to console only

---

## Background

I'm a Technical PM and ex-founder (built a hardware brand to ₹14L ARR). Built Aegis to understand AI infrastructure from the inside — specifically the cost levers that most PMs treat as black boxes. Currently incubated at GGSIPU.

Previous project: [Aria](https://github.com/Tarunsai01/ARIA) — Sign-to-speech AI agent built in 48 hours at OpenAI x NxtWave Hackathon. National finalist among 1000+ teams.
