import unittest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_intent import test_intent_classifier_delivery, test_intent_classifier_refund, test_intent_classifier_security, test_intent_classifier_empty
from tests.test_retriever import test_retriever_basic, test_context_builder
from tests.test_escalation import test_escalation_security_fraud, test_escalation_severe_hazard, test_auto_handle_standard_query
from tests.test_pipeline import test_full_pipeline_run
from tests.test_evaluation import test_automated_metrics, test_llm_judge

class StandaloneTestSuite(unittest.TestCase):
    def test_all_intent(self):
        test_intent_classifier_delivery()
        test_intent_classifier_refund()
        test_intent_classifier_security()
        test_intent_classifier_empty()

    def test_all_retriever(self):
        test_retriever_basic()
        test_context_builder()

    def test_all_escalation(self):
        test_escalation_security_fraud()
        test_escalation_severe_hazard()
        test_auto_handle_standard_query()

    def test_all_pipeline(self):
        test_full_pipeline_run()

    def test_all_evaluation(self):
        test_automated_metrics()
        test_llm_judge()

if __name__ == "__main__":
    unittest.main(verbosity=2)
