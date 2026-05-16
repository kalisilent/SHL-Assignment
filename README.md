# Conversational SHL Assessment Recommender — RAG Agent

A production-ready conversational AI agent that helps hiring managers discover and compare SHL assessments through natural dialogue. Built with **FastAPI**, **FAISS retrieval**, and **Google Gemini LLM**.

**Live Demo:** https://shl-assignment-2-tljr.onrender.com

---

## 🎯 Problem Statement

Hiring managers often struggle to find the right assessment from large catalogs without knowing the exact vocabulary. Traditional keyword search and faceted filtering assume users know what they want upfront. This agent bridges that gap through multi-turn dialogue, clarifying requirements and delivering grounded recommendations.

---

## ✨ Key Capabilities

### 1. **Clarify Vague Queries**
User: *"I need an assessment"*  
Agent: *"What role are you hiring for, and what's their seniority level?"*

### 2. **Recommend from Catalog**
User: *"Mid-level Java backend developer with Spring, SQL, Docker"*  
Agent: Returns 1-10 relevant SHL assessments with names and catalog URLs.

### 3. **Refine Mid-Conversation**
User: *"Actually, add Node.js and JavaScript to the stack"*  
Agent: Updates shortlist to reflect new constraints.

### 4. **Compare Assessments**
User: *"What's the difference between OPQ and GSA?"*  
Agent: Explains using only catalog evidence (no hallucination).

### 5. **Refuse Off-Topic Requests**
User: *"Give me legal advice on firing employees"*  
Agent: *"I can only help with SHL assessment selection."*

---

## 🏗️ Architecture

### Tech Stack
- **Framework:** FastAPI (Python)
- **Retrieval:** FAISS (semantic search) + hybrid lexical scoring
- **LLM:** Google Gemini 2.5-flash
- **Deployment:** Render (free tier with Docker)
- **Embeddings:** SentenceTransformers (all-MiniLM-L6-v2)

### Core Components

```
┌─────────────────────────────────────────┐
│         FastAPI Service                 │
│  GET /health    POST /chat              │
└──────────────┬──────────────────────────┘
               │
       ┌───────┴──────────┬────────────┐
       │                  │            │
   ┌───▼──────┐  ┌────────▼────┐  ┌───▼──────┐
   │ FAISS    │  │  Policy     │  │ Gemini   │
   │ Index    │  │  Engine     │  │ LLM      │
   │          │  │             │  │          │
   └──────────┘  └─────────────┘  └──────────┘
       │                  │            │
       └───────┬──────────┴────────────┘
               │
        ┌──────▼─────────┐
        │ Catalog JSON   │
        │ (canonical)    │
        └────────────────┘
```

### Key Design Decisions

**1. Hybrid Retrieval (FAISS + Lexical)**
- FAISS provides semantic understanding of user intent
- IDF-weighted lexical scoring re-ranks for exact matches
- Abbreviation expansion bridges vocabulary gaps (e.g., OPQ → Occupational Personality Questionnaire)

**2. LLM-Minimal Architecture**
- LLM only generates conversational replies, not recommendations
- All recommendations come directly from catalog (no hallucination)
- Gemini 2.5-flash chosen for cost, speed, and JSON schema support

**3. Conservative Safety Enforcement**
- Strict Pydantic request/response schemas with `extra="forbid"`
- Response sanitizer validates all URLs against catalog before returning
- Recommendations capped at 10 items; invalid URLs dropped automatically
- 8-turn conversation limit enforced at API level

**4. Stateless Design**
- Every request includes full conversation history (no server-side sessions)
- Enables horizontal scaling and handles cold-starts gracefully
- 30-second timeout compliance built in

---

## 📊 Evaluation Metrics

### Recall@10 Scoring
- **Metric:** Fraction of relevant assessments in top-10 recommendations
- **Result:** Mean Recall@10 = 1.00 on 10 public test traces
- **Test Coverage:** 
  - Vague → clarify flows
  - Rich context → recommend flows
  - Multi-turn refinement scenarios
  - Assessment comparison queries
  - Off-topic refusal probes

### Robustness Testing
- **Perturbation tests:** Typos, paraphrases, punctuation variations
- **Finding:** Sensitivity to very short/generic queries and punctuation
- **Mitigation:** Heuristic expansions for known domain patterns

---

## 🚀 Deployment

### Live Endpoint
```bash
# Health check (cold-start: ~30-60s first request)
curl https://shl-assignment-2-tljr.onrender.com/health

# Chat endpoint (POST only)
curl -X POST https://shl-assignment-2-tljr.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"I need an assessment"}]}'
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY="your-api-key"

# Start server
uvicorn app.main:app --port 8000

# Run evaluation suite
python3 eval/evaluate.py
```

### Rendering Deployment (Docker)
Configured for free Tier (~512MB RAM):
- Dockerfile uses `python:3.11-slim` for minimal footprint
- FAISS and sentence-transformers disabled by default (set `ENABLE_DENSE_RETRIEVAL=1` to enable)
- Lifespan startup loads models once on boot, not per-request

---

## 📁 Project Structure

```
.
├── app/
│   ├── main.py                    # FastAPI server + endpoints
│   ├── agent.py                   # Gemini LLM agent logic
│   ├── retriever.py               # FAISS + hybrid retrieval
│   ├── conversation_policy.py     # Policy: when to clarify/recommend/refuse
│   ├── models.py                  # Pydantic schemas (request/response)
│   ├── sanitizer.py               # Response validation & catalog grounding
│   ├── name_match.py              # Fuzzy assessment name matching
│   └── query_builder.py           # Multi-query composition
│
├── data/
│   ├── catalog.json               # Scraped SHL catalog (canonical)
│   └── catalog.index              # FAISS vector index
│
├── eval/
│   ├── evaluate.py                # End-to-end Recall@10 harness
│   ├── evaluate_retriever.py      # Retriever-only metrics
│   └── traces/                    # 10 test conversation traces (C1.md - C10.md)
│
├── scripts/
│   ├── build_index.py             # Index catalog into FAISS
│   ├── scrape_catalog.py          # Scrape SHL website → catalog.json
│   ├── debug_retrieval.py         # Per-trace retrieval diagnostics
│   ├── perturb_eval.py            # Robustness testing (typos, paraphrases)
│   ├── run_agent_eval.py          # Run eval against live /chat endpoint
│   └── convert_md_to_pdf.py       # Approach document converter
│
├── Dockerfile                     # Production image (Render-compatible)
├── Procfile                       # Render deployment config
├── requirements.txt               # Python dependencies (minimal)
├── Approach_Document.md / .pdf    # 2-page technical approach summary
└── README.md                      # This file
```

---

## 🔧 Technical Highlights

### Retrieval Heuristics
- **Abbreviation expansion:** OPQ, G+, GSA, SVAR, etc. → full names
- **Domain-specific injection:** Java queries get Spring/Docker/SQL assessments
- **Role + skill matching:** E.g., "backend developer" + "microservice" + "Docker" → advanced Java/Spring recommendations
- **Language matching:** Spanish → Spanish-language assessments

### Policy Engine
Decides when to clarify vs. recommend based on:
- Turn count (8-turn cap)
- User text length & specificity
- Keyword signals (role, skill, seniority)
- Conversation stage (first turn vs. refinement)

### Safety Guards
- URL canonicalization: all returned URLs verified against catalog
- Empty recommendations when off-topic/comparing (no spurious list)
- Schema validation: strict request/response formats
- Fallback responses: always return valid JSON even if LLM fails

---

## 🧪 Testing & Evaluation

### Run Full Evaluation
```bash
# Against local server
python3 eval/evaluate.py

# Against live deployment
python3 scripts/run_agent_eval.py https://shl-assignment-2-tljr.onrender.com/chat
```

### Run Retriever Tests
```bash
python3 eval/evaluate_retriever.py
```

### Debug Single Trace
```bash
python3 scripts/debug_retrieval.py C1
```

### Perturbation Tests (Robustness)
```bash
python3 scripts/perturb_eval.py
```

---

## 🎓 What I Learned

### What Worked Well
1. **Hybrid retrieval:** Combining semantic + lexical scoring captures both intent and exact matches
2. **Server-side safety:** Overriding LLM recommendations with catalog entries eliminates hallucination risk
3. **Conservative policy:** Asking clarifying questions → higher recommendation quality
4. **Catalog grounding:** Every URL validated ensures 100% compliance

### What Was Challenging
1. **Vocabulary gap:** Users use shorthand (OPQ, G+, SVAR) — required hand-curated abbreviation maps
2. **Short queries:** Single-word or vague queries need intelligent heuristics, not just embeddings
3. **Cold-start:** Free-tier Render has ~30-60s first request; mitigated with lifespan loading

### Improvements for Production
1. Add a cross-encoder reranker for better paraphrase robustness
2. Implement Redis caching for frequently recommended combinations
3. Add per-trace observability (Datadog/Prometheus) for monitoring
4. Build admin UI to edit heuristics without code changes

---

## 🛠️ AI Tool Usage

**GitHub Copilot** was used for:
- Boilerplate FastAPI/Pydantic code generation
- Iterative debugging and test harness scaffolding
- Documentation and comment generation

**All code was reviewed, validated, and adapted** to meet strict requirements. Critical logic (retrieval heuristics, policy decisions, safety guards) was authored and validated directly by me.

---

## 📋 Submission Details

- **Approach Document:** [Approach_Document.pdf](Approach_Document.pdf)
- **Live API:** https://shl-assignment-2-tljr.onrender.com
- **Cold-start:** ~30-60 seconds (Render free tier)
- **LLM:** Google Gemini 2.5-flash
- **Evaluation:** Recall@10 = 1.00 on 10 test traces

---

## 📞 Contact & Questions

This project demonstrates:
- ✅ Full-stack RAG system design
- ✅ Production API architecture
- ✅ Grounded LLM outputs (no hallucination)
- ✅ Rigorous evaluation & robustness testing
- ✅ Safety-first design patterns

Feel free to explore the code, run the evaluation suite, or test the live endpoint!

---

**Last Updated:** May 16, 2026  
**Status:** ✅ Production-Ready
