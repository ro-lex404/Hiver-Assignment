from src.escalation.engine import EscalationEngine

def test_escalation_security_fraud():
    engine = EscalationEngine()
    res = engine.evaluate("Account locked and unauthorized charge of $500", "ACCOUNT_ACCESS_SECURITY", 0.95)
    assert res["should_escalate"] is True
    assert "Security" in res["stated_reason"] or "account" in res["stated_reason"].lower()

def test_escalation_severe_hazard():
    engine = EscalationEngine()
    res = engine.evaluate("The blender started smoking and exploded with fire in my kitchen!", "DAMAGED_DEFECTIVE_ITEM", 0.90)
    assert res["should_escalate"] is True
    assert "safety hazard" in res["stated_reason"].lower() or "Executive" in res["stated_reason"]

def test_auto_handle_standard_query():
    engine = EscalationEngine()
    res = engine.evaluate("How long do I have to return an item at Whole Foods?", "REFUND_AND_RETURNS", 0.92)
    assert res["should_escalate"] is False
    assert "self-service" in res["stated_reason"].lower()
