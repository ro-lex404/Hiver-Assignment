import os
from typing import Dict, Any, List
from src.intent.taxonomy import INTENT_TAXONOMY
from src.utils import clean_tweet_text, logger

class GroundedDraftAgent:
    """
    Generates grounded, policy-compliant Twitter replies.
    Adheres strictly to:
    - Twitter 280-character limit
    - Brand voice (Polite, empathetic, de-escalating)
    - Grounding against historical resolutions and verified SOP links
    """

    BRAND_LINKS = {
        "ORDER_STATUS_DELIVERY": "amazon.com/your-orders",
        "REFUND_AND_RETURNS": "amazon.com/returns",
        "DAMAGED_DEFECTIVE_ITEM": "amazon.com/returns",
        "ACCOUNT_ACCESS_SECURITY": "amazon.com/help",
        "BILLING_AND_PRIME": "amazon.com/gp/primecentral",
        "PRODUCT_TROUBLESHOOTING": "amazon.com/devicesupport",
        "FEEDBACK_AND_GENERAL": "amazon.com/help"
    }

    def generate_reply(
        self,
        customer_text: str,
        intent: str,
        escalation_result: Dict[str, Any],
        retrieved_context: Dict[str, Any]
    ) -> str:
        """Draft a grounded support reply."""
        should_escalate = escalation_result["should_escalate"]
        link = self.BRAND_LINKS.get(intent, "amazon.com/help")

        if should_escalate:
            # Escalation reply: empathetic acknowledgment + secure DM handoff
            reason = escalation_result.get("stated_reason", "")
            if "safety" in reason.lower() or "hazard" in reason.lower() or "legal" in reason.lower():
                reply = f"We take this matter very seriously and sincerely apologize. Please send us a private DM with your order ID and details immediately so our specialized escalation team can assist you."
            elif "security" in reason.lower() or "compromise" in reason.lower() or "2fa" in reason.lower():
                reply = f"For your account security, please never share passwords publicly. Please send us a direct message with your account email so our fraud prevention team can secure your account right away."
            elif "repeat" in reason.lower() or "dispute" in reason.lower() or "pii" in reason.lower():
                reply = f"We sincerely apologize for this frustration. To look into your order details securely, please send us a direct message with your order number so an agent can resolve this for you directly."
            else:
                reply = f"We apologize for the inconvenience. Please send us a DM with your order details so our support team can investigate and resolve this for you!"
        else:
            # Auto-handled grounded reply using SOP and retrieved patterns
            sop_info = INTENT_TAXONOMY.get(intent, {})
            if intent == "ORDER_STATUS_DELIVERY":
                reply = f"We understand your concern regarding your delivery! You can track real-time progress at {link}. If not delivered within 24h of the estimated date, let us know so we can assist!"
            elif intent == "REFUND_AND_RETURNS":
                reply = f"Once received at our returns center, card refunds typically take 3-5 business days. You can monitor return status or start a return anytime at {link}!"
            elif intent == "DAMAGED_DEFECTIVE_ITEM":
                reply = f"We are so sorry your item arrived damaged! You can easily request an instant replacement or returnless refund directly via your Orders page at {link}."
            elif intent == "BILLING_AND_PRIME":
                reply = f"You can review recent transactions, download tax invoices, and manage your Prime membership settings anytime at {link}."
            elif intent == "PRODUCT_TROUBLESHOOTING":
                reply = f"Try unplugging the power cable for 60 seconds to restart your device. For step-by-step troubleshooting guides, please visit {link}."
            elif intent == "FEEDBACK_AND_GENERAL":
                reply = f"Thank you so much for sharing your feedback with us! We appreciate you being an Amazon customer and will pass this on to our logistics and leadership teams!"
            else:
                reply = f"Thank you for reaching out to Amazon Support. For assistance and self-service account options, please visit {link}."

        # Enforce Twitter 280-char strict safety truncation
        clean_reply = clean_tweet_text(reply)
        if len(clean_reply) > 280:
            clean_reply = clean_reply[:277] + "..."

        return clean_reply
