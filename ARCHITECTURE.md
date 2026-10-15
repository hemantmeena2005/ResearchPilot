# ResearchPilot System Architecture & Data Flow

```mermaid
graph TD
    subgraph Client ["Frontend Workspace (React 19 + TypeScript + Tailwind)"]
        UI[Research Workspace & Chat]
        Lib[Document Library & Uploader]
        Comp[Multi-Paper Comparison View]
        EvalUI[Evaluation & Benchmark Dashboard]
        Drawer[Evidence & Citation Drawer]
    end

    subgraph API ["FastAPI Modular Backend (Python 3.12)"]
        RouterDoc["/api/v1/documents"]
        RouterRes["/api/v1/research"]
        RouterConv["/api/v1/conversations"]
        RouterEval["/api/v1/evaluation"]
    end

    subgraph Ingestion ["Document Processing Engine"]
        PDFP[PyMuPDF Parser]
        Chunker[Deterministic Text Chunker]
    end

    subgraph Retrieval ["Hybrid Retrieval & Reranker"]
        DenseModel[SentenceTransformers: all-MiniLM-L6-v2]
        FAISS[(FAISS IndexFlatIP Cosine Index)]
        BM25[(Okapi BM25 Lexical Index)]
        RRF[Reciprocal Rank Fusion]
        CE[CrossEncoder Reranker: ms-marco-MiniLM-L-6-v2]
    end

    subgraph LLM ["Inference & Grounding"]
        QClass[Deterministic Query Classifier]
        PromptEngine[Context Constructor & Prompt Guard]
        GroqClient[Groq SDK: Llama-3.3-70b-versatile]
        CiteVal[Citation & Insufficiency Validator]
    end

    subgraph Storage ["Local Persistence"]
        SQLite[(SQLite DB: Metadata & Chunks)]
        Filesystem[(Local PDF Upload Storage)]
    end

    %% Workflows
    Lib --> RouterDoc
    RouterDoc --> PDFP --> Chunker
    Chunker --> DenseModel --> FAISS
    Chunker --> BM25
    Chunker --> SQLite
    RouterDoc --> Filesystem

    UI --> RouterRes
    RouterRes --> QClass --> Hybrid
    Hybrid --> FAISS & BM25
    FAISS & BM25 --> RRF --> CE --> PromptEngine
    PromptEngine --> GroqClient --> CiteVal
    CiteVal --> UI
    CiteVal -.-> Drawer

    RouterEval --> EvalUI
```

## Security & Reliability Design
1. **Zero Secret Leakage:** Groq API keys remain strictly on the backend. Frontend queries only talk to the internal API.
2. **Untrusted Document Content Guard:** Document text injected into prompts is wrapped in explicit context delimiters and treated as untrusted text to prevent prompt injection.
3. **Deterministic ID Stability:** SHA-256 chunk hashing ensures chunk identifiers and citations remain stable across application restarts.
4. **Local Hardware Efficiency:** Quantized, lightweight embedding and cross-encoder models (~80MB RAM) execute locally without requiring a dedicated GPU or paid cloud vector services.
