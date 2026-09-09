import os
from typing import Dict, Any, List
from src.intent.taxonomy import INTENT_TAXONOMY
from src.llm_client import LLMClient
from src.utils import clean_tweet_text, logger

class GroundedDraftAgent:
    """
    Generates grounded, policy-compliant Twitter replies.
    Supports:
    1. Open Models via Groq / Gemini / OpenAI APIs
    2. Zero-key deterministic template fallback
    3. Strict Twitter 280-char guardrail
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

    def __init__(self):
        self.llm = LLMClient()

    def generate_reply(
        self,
        customer_text: str,
        intent: str,
        escalation_result: Dict[str, Any],
        retrieved_context: Dict[str, Any]
    ) -> str:
        should_escalate = escalation_result["should_escalate"]
        link = self.BRAND_LINKS.get(intent, "amazon.com/help")

        # If LLM client has an active cloud API (Groq, OpenAI, Gemini), run grounded prompt
        if self.llm.provider in ["groq", "openai", "gemini"]:
            system_prompt = (
                "You are the official Twitter customer service AI agent for @AmazonHelp. "
                "Your job is to draft a polite, empathetic, concise tweet reply (<280 chars) to the customer. "
                f"The customer's intent is classified as: {intent}. "
                f"Standard resolution link: {link}.\n"
                f"Historical resolution context:\n{retrieved_context.get('grounding_exemplars', '')}\n"
                "Rules:\n"
                "1. Keep response strictly UNDER 280 characters.\n"
                "2. If escalation is required, apologize empathetically and instruct them to send a DM with order details.\n"
                "3. If auto-handled, provide clear self-service resolution and mention the verified link.\n"
                "4. NEVER ask for passwords, OTPs, or credit card numbers publicly."
            )
            user_prompt = (
                f"Customer Tweet: {customer_text}\n"
                f"Escalation Decision: {'ESCALATE TO HUMAN' if should_escalate else 'AUTO-HANDLE'}\n"
                f"Reason: {escalation_result.get('stated_reason', '')}"
            )
            llm_reply = self.llm.generate(system_prompt, user_prompt)
            if llm_reply and len(llm_reply.strip()) > 5:
                clean_reply = clean_tweet_text(llm_reply)
                return clean_reply[:277] + "..." if len(clean_reply) > 280 else clean_reply

        # Deterministic Grounded Resolution (Fast / Offline Fallback)
        if should_escalate:
            reason = escalation_result.get("stated_reason", "")
            if any(k in reason.lower() for k in ["safety", "hazard", "legal"]):
                reply = "We take this matter very seriously and sincerely apologize. Please send us a private DM with your order ID immediately so our specialized escalation team can assist you."
            elif any(k in reason.lower() for k in ["security", "compromise", "2fa"]):
                reply = "For your account security, please never share passwords publicly. Please send us a direct message with your account email so our fraud prevention team can secure your account."
            elif any(k in reason.lower() for k in ["repeat", "dispute", "pii"]):
                reply = "We sincerely apologize for this frustration. To look into your order details securely, please send us a direct message with your order number so an agent can resolve this for you directly."
            else:
                reply = "We apologize for the inconvenience. Please send us a DM with your order details so our support team can investigate and resolve this for you!"
        else:
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

        clean_reply = clean_tweet_text(reply)
        return clean_reply[:277] + "..." if len(clean_reply) > 280 else clean_reply
