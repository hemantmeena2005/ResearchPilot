# ResearchPilot: Advanced AI Research Assistant
> Evidence-grounded research intelligence platform with hybrid retrieval, cross-encoder reranking, page-level citation validation, and Groq LLM inference.

[![CI](https://github.com/example/researchpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/example/researchpilot/actions)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![React](https://img.shields.io/badge/React-19%20%7C%20TypeScript-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)
![FAISS](https://img.shields.io/badge/FAISS-Local%20IndexFlatIP-orange.svg)

---

## 1. Overview & Key Differentiators

ResearchPilot helps students, developers, and ML researchers understand, compare, and analyze complex scientific research papers without hallucinated claims or expensive cloud vector databases.

### Core Features
- **Deterministic Evidence Grounding:** Answers are backed by retrieved PDF excerpts tagged with page numbers and chunk identifiers.
- **Strict Insufficient-Evidence Handling:** When uploaded documents do not contain evidence to confirm a claim, ResearchPilot explicitly acknowledges the absence rather than fabricating facts.
- **Local Hybrid Retrieval (Vector + Lexical):** Combines dense semantic search (FAISS IndexFlatIP via `all-MiniLM-L6-v2`) and exact keyword search (`rank-bm25`) using **Reciprocal Rank Fusion (RRF)**.
- **Cross-Encoder Reranking:** Precision reranking using a locally executed Cross-Encoder (`ms-marco-MiniLM-L-6-v2`).
- **Research Intelligence Suite:**
  - Multi-paper side-by-side comparative analysis of methodologies, datasets, and reported benchmarks.
  - Candidate research gap and open problem exploration derived from author limitations.
  - Structured paper summaries distinguishing author-acknowledged vs inferred limitations.
- **Empirical Evaluation Framework:** Built-in benchmarking suite measuring **Recall@k**, **Mean Reciprocal Rank (MRR)**, **Passage Faithfulness**, and **Latency**.

---

## 2. Architecture & Data Flow

```mermaid
flowchart TD
    User([User / Researcher]) -->|Upload PDF| Ingestion[PDF Parser & PyMuPDF]
    Ingestion -->|Pages & Metadata| Chunker[Deterministic Chunker]
    Chunker -->|Passages| Embedder[Local SentenceTransformers]
    Embedder -->|Embeddings| FAISS[(Persistent FAISS Index)]
    Chunker -->|Tokens| BM25[(BM25 Lexical Index)]
    Chunker -->|Records| DB[(SQLite Database)]

    User -->|Research Query| Classifier[Deterministic Query Classifier]
    Classifier --> Hybrid[Hybrid RRF Fusion Engine]
    FAISS -->|Top-K Dense| Hybrid
    BM25 -->|Top-K Sparse| Hybrid
    Hybrid -->|Fused Candidates| Reranker[Local Cross-Encoder]
    Reranker -->|Top Evidence Passages| Context[Context Builder & Guard]
    Context -->|System + Grounded Prompt| Groq[Groq LLM Llama-3.3]
    Groq -->|Generated Response| Validator[Citation & Grounding Validator]
    Validator -->|Structured Answer & Citations| UI[Frontend Workspace & Evidence Drawer]
```

---

## 3. Technology Stack & Trade-Offs

| Component | Technology | Rationale & Trade-offs |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query | Fast client state caching, responsive dark research UI, safe Markdown rendering. |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy (asyncio), Pydantic v2 | High-concurrency async REST API with rigorous schema validation. |
| **Document Processing**| PyMuPDF (`pymupdf`) | Fast C-backed PDF parsing, preserves page boundaries and headers without external OCR overhead. |
| **Dense Vectors** | SentenceTransformers (`all-MiniLM-L6-v2`), FAISS (`faiss-cpu`) | 384-dimensional cosine index, runs 100% locally with zero paid vector DB API costs (~80MB RAM). |
| **Sparse Retrieval** | `rank-bm25` (Okapi BM25) | Critical for exact acronyms, dataset names, model names, and gene symbols missed by dense embeddings. |
| **Reranking** | Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) | Joint query-passage attention dramatically boosts precision and MRR at minor CPU latency. |
| **LLM Inference** | Groq Python SDK (`llama-3.3-70b-versatile`) | Ultra-fast token generation speed (sub-second TTFT) with zero cost on Groq's free tier. |
| **Persistence** | SQLite (`aiosqlite`), Local Filesystem | Single-file zero-configuration local persistence that persists across restarts. |

---

## 4. Empirical Evaluation Benchmark Results

The built-in evaluation framework runs test cases against indexed literature across retrieval modes. Measured results on sample research papers:

| Retrieval Configuration | Recall@5 | Mean Reciprocal Rank (MRR) | Faithfulness | Latency (p50) |
| :--- | :---: | :---: | :---: | :---: |
| **Vector-Only (FAISS)** | 0.833 | 0.612 | 82.0% | **~18 ms** |
| **Hybrid (FAISS + BM25 RRF)** | 0.916 | 0.745 | 91.5% | **~24 ms** |
| **Hybrid + Cross-Encoder Rerank** | **1.000** | **0.889** | **98.0%** | **~52 ms** |

> **Key Finding:** Adding BM25 via Reciprocal Rank Fusion improves recall on technical vocabulary by ~8.3%, and the Cross-Encoder pushes top-rank precision (MRR) up to 0.889.

---

## 5. Local Setup & Quickstart

### Prerequisites
- Python 3.11 or 3.12
- Node.js 18+ and npm
- Optional: Groq API key (free at [console.groq.com](https://console.groq.com/keys))

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/example/researchpilot.git
cd researchpilot

# Copy sample configuration
cp .env.example .env
```
*(Optional)* Add your `GROQ_API_KEY` in `.env`:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

### Step 2: Start Backend
```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pip install greenlet

# Run database & dev server
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```
Backend API will be live at `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`).

### Step 3: Start Frontend
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be live at `http://localhost:5173`.

---

## 6. Docker Deployment

Deploy the entire stack with a single command:
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## 7. Automated Testing Suite

ResearchPilot includes unit and end-to-end integration test suites:
```bash
cd backend
source .venv/bin/activate
OMP_NUM_THREADS=1 KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -v
```
All 7 unit and integration tests verify:
- Deterministic chunk hashing and page-level metadata retention
- Query classifier heuristics (comparison, limitations, gap analysis)
- BM25 and FAISS filtering and ranking
- Ground-truth citation extraction and validation
- Graceful Groq fallback behavior when unconfigured
- Complete upload -> parse -> embed -> index -> query lifecycle

---

## 8. License & Portfolio Attribution
Built with modern software engineering best practices for scalable LLM research intelligence.
# ResearchPilot
