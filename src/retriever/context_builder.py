from typing import List, Dict, Any
from src.intent.taxonomy import INTENT_TAXONOMY

class ContextBuilder:
    """Constructs prompt grounding context from retrieved resolutions and brand SOPs."""

    @staticmethod
    def build_prompt_context(intent: str, retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        intent_info = INTENT_TAXONOMY.get(intent, {})
        sop_policy = intent_info.get("policy", "Provide polite customer assistance.")

        exemplars = []
        for doc in retrieved_docs:
            exemplars.append(f"Historical Query: {doc['query']}\nHistorical Resolution: {doc['resolution']}")

        return {
            "intent": intent,
            "sop_policy": sop_policy,
            "grounding_exemplars": "\n---\n".join(exemplars),
            "retrieved_count": len(retrieved_docs)
        }
