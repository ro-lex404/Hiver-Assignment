import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sys
import json
from src.pipeline import SupportAgentPipeline

def main():
    pipeline = SupportAgentPipeline()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Where is my package tracking TBA982348123019? It was supposed to be delivered yesterday!"

    print("="*70)
    print(f"Customer Tweet: {query}")
    print("="*70)

    result = pipeline.process(query)
    print(f"Predicted Intent : {result['intent']} (Confidence: {result['confidence']})")
    print(f"Escalate to Human: {result['escalation']['should_escalate']} (Risk Score: {result['escalation']['risk_score']})")
    print(f"Stated Reason    : {result['escalation']['stated_reason']}")
    print(f"Draft Reply      : {result['draft_reply']}")
    print(f"Latency          : {result['latency_ms']} ms")
    print("="*70)

if __name__ == "__main__":
    main()
