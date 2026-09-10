# Hiver AI Customer Support Agent & Evaluation Benchmark
### Production-Grade Twitter Support Agent, Grounded Historical RAG & Automated Evaluation Harness
**Hiver SDE Intern Take-Home Assignment (12 LPA | 2027 Batch)**  
**Target Brand**: `@AmazonHelp` | **Dataset**: Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`)

---

## ⚡ Headline Results (Reproducible in < 15 Seconds)

Evaluated across the **200-sample hand-curated Golden Evaluation Benchmark** (`data/golden_set/golden_eval_200.jsonl`):

| Model Architecture | Intent Accuracy | Intent Macro-F1 | Escalation F1 | Escalation Recall | Groundedness (1–5) | LLM Judge Overall (1–5) | Avg Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Trivial Baseline** | 24.0% | 0.055 | 0.621 | 100.0% | 2.48 / 5.0 | 3.52 / 5.0 | **1.5 ms** |
| **Simple Baseline** | 67.0% | 0.631 | 0.547 | 42.2% | 4.34 / 5.0 | 4.37 / 5.0 | **1.5 ms** |
| **Proposed Support Agent** | **76.5%** | **0.769** | **0.571** | **42.2%** | **4.32 / 5.0** | **4.43 / 5.0** | **1.9 ms** |

---

## 🚀 15-Minute Fast Reproduction Quickstart

The entire codebase is **self-contained with pure-Python fallbacks**—no massive data downloads or external GPU requirements to reproduce headline numbers!

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/ro-lex404/Hiver-Assignment.git
cd Hiver-Assignment
# Optional: pip install -r requirements.txt
```

### 2. Run the Benchmark Evaluation (< 5 seconds)
```bash
python scripts/run_evaluation.py
```

### 3. Run Human vs. LLM-Judge Calibration Study
```bash
python scripts/evaluate_judge_agreement.py
```

### 4. Interactive Real-Time Tweet Test
```bash
python scripts/run_pipeline.py "My credit card was charged $139 for Prime renewal but I cancelled it 2 weeks ago!"
```

### 5. Run Test Suite
```bash
python tests/run_tests.py
```

---

## 🏗️ System Architecture

```
                                  INCOMING CUSTOMER TWEET
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │    Data Normalization & PII   │
                             │       Masking (src/utils)     │
                             └───────────────┬───────────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      ▼                                             ▼
       ┌──────────────────────────────┐              ┌──────────────────────────────┐
       │   Hybrid Intent Classifier   │              │ Historical Resolution RAG    │
       │  (Lexical + Semantic TF-IDF) │              │  (Top-K SOP Resolutions)     │
       └──────────────┬───────────────┘              └──────────────┬───────────────┘
                      │                                             │
                      │   Intent + Confidence Score                 │ Retrieved Context
                      │                                             │
                      └──────────────────────┬──────────────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │ Multi-Signal Escalation Engine│
                             │  (Security, PII, Sentiment,   │
                             │   Repeat Friction, Stated Rsn)│
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                             ┌───────────────────────────────┐
                             │ Grounded Draft Response Agent │
                             │ (Brand Voice, Twitter <=280c, │
                             │  Verified SOP Help Portals)   │
                             └───────────────┬───────────────┘
                                             │
                                             ▼
                              FINAL AUDITED SUPPORT RESPONSE
```

---

## 📁 Repository Directory Layout

```
Hiver-Assignment/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # Automated tests on push & PR across Python 3.10-3.13
│       ├── run_eval.yml              # Benchmark regression test workflow
│       └── kaggle_sync.yml           # Automated Kaggle kernel sync
├── configs/
│   ├── config.yaml                   # Global pipeline configurations (thresholds, top-k)
│   └── brand_profiles/
│       └── amazon_help.yaml          # @AmazonHelp SOPs, tone guidelines, intent definitions
├── data/
│   ├── golden_set/
│   │   ├── golden_eval_200.jsonl     # 200 hand-curated multi-intent golden test cases
│   │   ├── human_judge_calibration_50.jsonl # 50 paired human vs judge calibration ratings
│   │   └── SAMPLING_METHODOLOGY.md   # Rigorous sampling and annotation documentation
│   └── raw/                          # Placeholder for raw Kaggle dataset
├── notebooks/
│   └── kaggle_gpu_support_pipeline.ipynb # Cloud GPU notebook for Kaggle execution
├── reports/
│   ├── REPORT.md                     # Comprehensive 6-page evaluation report (All deliverables + LoRA Benchmark)
│   ├── DECISION_LOG.md               # 16 non-obvious engineering decisions & trade-offs
│   └── metrics/                      # Benchmark summary artifacts and JSON metrics
├── scripts/
│   ├── run_pipeline.py               # Interactive CLI pipeline runner
│   ├── run_evaluation.py             # Full automated evaluation benchmark
│   ├── evaluate_judge_agreement.py   # Human vs LLM judge calibration script
│   ├── download_kaggle_data.py       # Kaggle dataset downloader helper
│   └── kaggle_push.py                # Automate pushing kernel to Kaggle
├── src/
│   ├── intent/                       # Intent taxonomy and hybrid classifier
│   ├── retriever/                    # Historical resolution vector store & context builder
│   ├── escalation/                   # Multi-signal escalation decision engine
│   ├── generator/                    # Policy-grounded draft response generator
│   ├── evaluation/                   # Automated metrics, LLM-as-a-judge rubric, Cohen's Kappa
│   ├── baselines/                    # Trivial & Simple baseline implementations
│   ├── pipeline.py                   # Master end-to-end SupportAgentPipeline
│   └── utils.py                      # Pure-Python table formatting, timing, text cleaner
├── tests/
│   ├── run_tests.py                  # Standalone unittest suite
│   ├── test_intent.py                # Intent classifier tests
│   ├── test_retriever.py             # Vector store & RAG tests
│   ├── test_escalation.py            # Escalation engine rule tests
│   ├── test_pipeline.py              # Integration tests
│   └── test_evaluation.py            # Metric calculation & judge tests
├── .env.example                      # Environment variables template
├── .gitignore                        # Gitignore rules for clean repository
├── pyproject.toml                    # Modern Python package configuration
├── requirements.txt                  # Python dependencies
└── README.md                         # Quickstart & documentation
```

---

## 📊 Key Highlights & Required Deliverables

1. **Deliverable 1 (Runnable Pipeline)**: Instant reproduction in < 15 seconds via `python scripts/run_evaluation.py`.
2. **Deliverable 2 (Golden Evaluation Set)**: 200 hand-labelled examples with complete annotations in `data/golden_set/golden_eval_200.jsonl` + `data/golden_set/SAMPLING_METHODOLOGY.md`.
3. **Deliverable 3 (Evaluation Harness)**: Automated metrics + LLM-as-a-judge rubric + Human-Judge agreement calibration in `src/evaluation/`.
4. **Deliverable 4 (Report)**: Complete evaluation report covering Problem Framing, Results vs 2 Baselines, Top 5 Failure Modes with real examples, mandatory *"What is misleading about my headline number?"* section, 3-Epoch Dual T4 QLoRA Fine-Tuning benchmark, and 1-week roadmap in [`reports/REPORT.md`](reports/REPORT.md).
5. **Deliverable 5 (Decision Log)**: 16 non-obvious engineering decisions and trade-offs in [`reports/DECISION_LOG.md`](reports/DECISION_LOG.md).

---

## ☁️ Kaggle GPU Automation & Cloud Execution

To run large-scale training / fine-tuning on Kaggle GPU instances without downloading the 516MB dataset locally:
1. Open [`notebooks/kaggle_gpu_support_pipeline.ipynb`](notebooks/kaggle_gpu_support_pipeline.ipynb) on Kaggle.
2. Verified on Kaggle Dual Tesla T4 GPUs: full 3-epoch QLoRA fine-tuning of `Llama-3.2-1B-Instruct` across 5,000 Amazon support conversations (`rohanalexbimal/hiver-ai-support-agent`).

