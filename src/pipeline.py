import time
from typing import Dict, Any, List
from src.intent.classifier import IntentClassifier
from src.retriever.vector_store import HistoricalResolutionRetriever
from src.retriever.context_builder import ContextBuilder
from src.escalation.engine import EscalationEngine
from src.generator.draft_agent import GroundedDraftAgent
from src.utils import clean_tweet_text, Timer, logger

class SupportAgentPipeline:
    """
    End-to-End Production Support Agent Pipeline:
    1. Ingestion & Text Normalization
    2. Intent Classification (Hybrid Lexical + Semantic)
    3. Historical Resolution Retrieval (RAG)
    4. Multi-Signal Escalation Decision Engine
    5. Policy-Grounded Draft Reply Generation
    """

    def __init__(self, top_k_retrieval: int = 3, escalation_threshold: float = 0.70):
        self.classifier = IntentClassifier()
        self.retriever = HistoricalResolutionRetriever()
        self.context_builder = ContextBuilder()
        self.escalation_engine = EscalationEngine(confidence_threshold=escalation_threshold)
        self.generator = GroundedDraftAgent()
        self.top_k = top_k_retrieval
        logger.info("Initialized SupportAgentPipeline.")

    def process(self, raw_text: str) -> Dict[str, Any]:
        with Timer() as timer:
            clean_text = clean_tweet_text(raw_text)

            # Step 1: Intent Classification
            intent_res = self.classifier.predict(clean_text)
            intent = intent_res["intent"]
            confidence = intent_res["confidence"]

            # Step 2: Historical Resolution Retrieval
            retrieved_docs = self.retriever.retrieve(clean_text, top_k=self.top_k)
            context = self.context_builder.build_prompt_context(intent, retrieved_docs)

            # Step 3: Multi-Signal Escalation Evaluation
            escalation_res = self.escalation_engine.evaluate(clean_text, intent, confidence)

            # Step 4: Grounded Response Generation
            draft_reply = self.generator.generate_reply(
                customer_text=clean_text,
                intent=intent,
                escalation_result=escalation_res,
                retrieved_context=context
            )

        return {
            "customer_text": clean_text,
            "intent": intent,
            "confidence": confidence,
            "routing_action": escalation_res["routing_action"],
            "top_candidates": intent_res.get("top_candidates", []),
            "retrieved_context": retrieved_docs,
            "escalation": escalation_res,
            "draft_reply": draft_reply,
            "latency_ms": round(timer.elapsed_ms, 2),
            "pipeline_type": "proposed_agent"
        }

    def batch_process(self, texts: List[str]) -> List[Dict[str, Any]]:
        return [self.process(t) for t in texts]
