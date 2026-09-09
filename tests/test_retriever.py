from src.retriever.vector_store import HistoricalResolutionRetriever
from src.retriever.context_builder import ContextBuilder

def test_retriever_basic():
    retriever = HistoricalResolutionRetriever()
    results = retriever.retrieve("Where is my order delivery?", top_k=2)
    assert len(results) == 2
    assert "query" in results[0]
    assert "resolution" in results[0]

def test_context_builder():
    retriever = HistoricalResolutionRetriever()
    docs = retriever.retrieve("My refund hasn't arrived", top_k=2)
    ctx = ContextBuilder.build_prompt_context("REFUND_AND_RETURNS", docs)
    assert ctx["intent"] == "REFUND_AND_RETURNS"
    assert ctx["retrieved_count"] == 2
