from src.pipeline import SupportAgentPipeline

def test_full_pipeline_run():
    pipeline = SupportAgentPipeline()
    res = pipeline.process("Can I track my order delivery in the Amazon app?")
    assert res["intent"] == "ORDER_STATUS_DELIVERY"
    assert "draft_reply" in res
    assert len(res["draft_reply"]) <= 280
    assert res["latency_ms"] > 0
