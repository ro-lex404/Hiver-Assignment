from typing import Dict, Any

class TrivialBaselineAgent:
    """
    Trivial Baseline:
    1. Majority class intent prediction (ORDER_STATUS_DELIVERY)
    2. Static generic canned reply
    3. Always escalates to human
    """

    def process(self, text: str) -> Dict[str, Any]:
        return {
            "intent": "ORDER_STATUS_DELIVERY",
            "confidence": 0.20,
            "retrieved_context": [],
            "escalation": {
                "should_escalate": True,
                "stated_reason": "Trivial baseline default escalation rule.",
                "risk_score": 1.0
            },
            "draft_reply": "Thanks for reaching out! Please send us a direct message with your details so our team can help you.",
            "pipeline_type": "trivial_baseline"
        }
