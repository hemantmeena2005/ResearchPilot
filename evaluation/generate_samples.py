import os
import pymupdf as fitz


def create_sample_paper(filepath: str, title: str, authors: str, sections: dict):
    doc = fitz.open()
    
    # Page 1: Title, Abstract, Introduction
    page1 = doc.new_page()
    rect = fitz.Rect(50, 50, 550, 750)
    
    content_page1 = f"""TITLE: {title}
AUTHORS: {authors}
YEAR: 2024

ABSTRACT
{sections.get('abstract', '')}

1. INTRODUCTION
{sections.get('intro', '')}
"""
    page1.insert_text((50, 70), content_page1, fontsize=10)
    
    # Page 2: Methodology & Architecture
    page2 = doc.new_page()
    content_page2 = f"""2. METHODOLOGY & ARCHITECTURE
{sections.get('method', '')}

3. EXPERIMENTAL SETUP & DATASETS
{sections.get('setup', '')}
"""
    page2.insert_text((50, 70), content_page2, fontsize=10)
    
    # Page 3: Results, Limitations, and Future Work
    page3 = doc.new_page()
    content_page3 = f"""4. EXPERIMENTAL RESULTS
{sections.get('results', '')}

5. LIMITATIONS & FAILURE MODES
{sections.get('limitations', '')}

6. CONCLUSION & FUTURE WORK
{sections.get('future', '')}
"""
    page3.insert_text((50, 70), content_page3, fontsize=10)
    
    doc.save(filepath)
    doc.close()
    print(f"Generated sample paper at: {filepath}")


if __name__ == "__main__":
    os.makedirs("evaluation/samples", exist_ok=True)
    
    # Paper 1: Dense Retrieval & Cross-Encoders
    create_sample_paper(
        "evaluation/samples/paper_dense_retrieval.pdf",
        "Dense Multi-Vector Retrieval for Academic Literature Search",
        "Alice Chen, Bob Vance, Clara Oswald",
        {
            "abstract": "We investigate dense multi-vector representations combined with late interaction cross-encoders for scientific research papers.",
            "intro": "Scientific paper search requires precise keyword matching alongside semantic conceptual alignment. Traditional lexical approaches like BM25 struggle with vocabulary mismatch.",
            "method": "Our architecture utilizes a dual-encoder transformer pre-trained on contrastive citation graphs. For scoring, top candidates are reranked using a 6-layer cross-encoder.",
            "setup": "We benchmark on the SciDocs and MS-MARCO academic subsets comprising 50,000 papers. Evaluation metrics include Recall@5, MRR@10, and nDCG@10.",
            "results": "The cross-encoder reranker improves MRR@10 from 0.642 to 0.781 on SciDocs. BM25 alone achieves 0.589.",
            "limitations": "The authors explicitly acknowledge high computational latency during late-interaction cross-encoder inference (averaging 85ms per query). Furthermore, performance degrades when documents exceed 10,000 tokens.",
            "future": "Future work will explore sparse distillation and quantized vector embeddings to reduce memory requirements.",
        }
    )

    # Paper 2: Hybrid RRF Fusion
    create_sample_paper(
        "evaluation/samples/paper_hybrid_fusion.pdf",
        "Reciprocal Rank Fusion in Scientific Information Retrieval",
        "David Miller, Elena Rostova",
        {
            "abstract": "This work analyzes the robustness of Reciprocal Rank Fusion (RRF) when combining dense vector similarity with sparse BM25 indices.",
            "intro": "While dense neural embeddings excel at semantic paraphrasing, they frequently fail on rare technical terminology, acronyms, and gene symbols.",
            "method": "We implement an unsupervised Reciprocal Rank Fusion pipeline combining FAISS IndexFlatIP cosine similarity and Okapi BM25 scoring with smoothing parameter k=60.",
            "setup": "We evaluate on TREC-COVID and ArXiv CS corpora across 100,000 documents using Recall@5 and passage faithfulness scores.",
            "results": "Hybrid RRF outperforms standalone vector search by 14.2% on technical keyword queries and achieves 0.94 Recall@5.",
            "limitations": "The authors acknowledge that RRF relies on equal heuristic weighting between sparse and dense channels, which can be suboptimal for purely conceptual queries.",
            "future": "Investigate learned adaptive fusion weights based on query classification heuristics.",
        }
    )
