import pytest
from app.services.documents.chunker import TextChunker
from app.services.retrieval.query_classifier import QueryClassifier
from app.services.retrieval.bm25_retriever import BM25Retriever
from app.services.research.citation_validator import CitationValidator
from app.services.llm.groq_client import GroqClientService


def test_chunker_stable_ids():
    chunker = TextChunker(chunk_size=50, chunk_overlap=10)
    pages = [
        {"page_number": 1, "text": "This is page one. It introduces the Transformer architecture. Self-attention is key."},
        {"page_number": 2, "text": "This is page two. Empirical results demonstrate strong performance across benchmarks."},
    ]
    chunks = chunker.chunk_document("doc-123", pages)
    assert len(chunks) >= 2
    assert chunks[0]["document_id"] == "doc-123"
    assert chunks[0]["page_number"] == 1
    # Check stable deterministic hash
    chunks_again = chunker.chunk_document("doc-123", pages)
    assert chunks[0]["id"] == chunks_again[0]["id"]


def test_query_classification():
    # Comparison
    res = QueryClassifier.classify("Compare the methodologies of paper A and paper B")
    assert res["category"] == "comparison"
    assert res["needs_multi_doc"] is True

    # Limitation
    res = QueryClassifier.classify("What are the main limitations acknowledged by the authors?")
    assert res["category"] == "limitation_analysis"

    # Gaps
    res = QueryClassifier.classify("What future work and open problems exist?")
    assert res["category"] == "research_gap_exploration"

    # Factual lookup
    res = QueryClassifier.classify("What was the learning rate used in training?")
    assert res["category"] == "factual_lookup"


def test_bm25_retriever():
    retriever = BM25Retriever()
    corpus = [
        {"id": "c1", "document_id": "d1", "content": "Transformer model uses multi-head attention mechanisms."},
        {"id": "c2", "document_id": "d1", "content": "Convolutional networks are effective for image processing."},
        {"id": "c3", "document_id": "d2", "content": "Reinforcement learning optimizes reward policy parameters."},
    ]
    retriever.update_corpus(corpus)

    results = retriever.search("multi-head attention", top_k=2)
    assert len(results) >= 1
    assert results[0][0]["id"] == "c1"

    # Test doc filtering
    filtered_res = retriever.search("attention", top_k=2, filter_document_ids=["d2"])
    assert len(filtered_res) == 0


def test_citation_validator():
    chunks = [
        {"id": "chunk-1", "document_id": "doc-a", "filename": "attention.pdf", "page_number": 3, "content": "Attention is all you need."},
        {"id": "chunk-2", "document_id": "doc-b", "filename": "bert.pdf", "page_number": 5, "content": "BERT improves language representation."},
    ]
    answer = "The Transformer utilizes self-attention [1] and pre-training representations [2]."
    citations, is_sufficient = CitationValidator.extract_and_validate(answer, chunks)
    assert len(citations) == 2
    assert citations[0].document_id == "doc-a"
    assert citations[0].page_number == 3
    assert is_sufficient is True

    # Insufficient evidence test
    insufficient_answer = "The provided research documents contain insufficient evidence to confirm this claim."
    _, is_sufficient_false = CitationValidator.extract_and_validate(insufficient_answer, chunks)
    assert is_sufficient_false is False


def test_groq_fallback_when_unconfigured():
    client = GroqClientService(api_key="")
    assert not client.is_configured()
    res = client.generate_chat_completion(messages=[{"role": "user", "content": "Hello"}])
    assert "Groq API Key Not Configured" in res["content"]
