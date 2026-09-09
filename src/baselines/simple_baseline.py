import re
from typing import Dict, Any

class SimpleBaselineAgent:
    """
    Simple Baseline:
    1. Basic regex keyword intent matching
    2. Zero-shot template generation (No RAG retrieval / historical resolution grounding)
    3. Binary keyword escalation detector
    """

    INTENT_KEYWORDS = {
        "ORDER_STATUS_DELIVERY": ["track", "where", "delivery", "late", "package"],
        "REFUND_AND_RETURNS": ["refund", "return", "money"],
        "DAMAGED_DEFECTIVE_ITEM": ["broken", "damage", "defective"],
        "ACCOUNT_ACCESS_SECURITY": ["hacked", "password", "otp", "locked"],
        "BILLING_AND_PRIME": ["prime", "charge", "bill"],
        "PRODUCT_TROUBLESHOOTING": ["alexa", "kindle", "fire tv", "remote"],
        "FEEDBACK_AND_GENERAL": ["thanks", "good", "bad"]
    }

    def process(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        predicted_intent = "FEEDBACK_AND_GENERAL"
        
        for intent, kw_list in self.INTENT_KEYWORDS.items():
            if any(k in text_lower for k in kw_list):
                predicted_intent = intent
                break

        # Simple keyword escalation rule
        should_escalate = any(k in text_lower for k in ["dm", "account", "human", "stolen", "lawyer", "refund"])
        
        if should_escalate:
            reply = "We apologize for the issue. Please DM us your order information so we can take a closer look."
        else:
            reply = f"For help with {predicted_intent.replace('_', ' ').lower()}, please visit amazon.com/help."

        return {
            "intent": predicted_intent,
            "confidence": 0.55,
            "retrieved_context": [],
            "escalation": {
                "should_escalate": should_escalate,
                "stated_reason": "Simple keyword escalation match." if should_escalate else "No trigger keywords found.",
                "risk_score": 0.70 if should_escalate else 0.20
            },
            "draft_reply": reply,
            "pipeline_type": "simple_baseline"
        }
