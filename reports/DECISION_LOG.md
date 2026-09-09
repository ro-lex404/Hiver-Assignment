# Decision Log — 15 Non-Obvious Engineering Decisions

**Project**: Hiver AI Customer Support Agent & Evaluation Benchmark  
**Author**: Engineering Candidate (Hiver SDE Intern Take-Home)  

---

### Decision 1: Picked `@AmazonHelp` Over Single-Product Brands (e.g. `@SpotifyCares`)
- **Choice**: Selected `@AmazonHelp` from the 3M Twitter Customer Support dataset.
- **Rationale**: Amazon encompasses physical deliveries, digital services, subscriptions, hardware devices, and account security. This complex multi-intent domain provides a rigorous test for escalation boundaries compared to single-domain streaming services.
- **Trade-off**: Higher taxonomy complexity and larger potential intent overlap.

---

### Decision 2: Multi-Signal Hybrid Escalation Engine Over Pure LLM Prompting
- **Choice**: Built a multi-signal deterministic + heuristic + semantic escalation engine instead of relying solely on an LLM prompt (`"Should this be escalated? (yes/no)"`).
- **Rationale**: Production safety requires deterministic guarantees for critical keywords (e.g., "fire", "police", "unauthorized charge", "lawyer") that cannot fail due to LLM temperature or prompt drift.
- **Trade-off**: Requires maintaining domain-specific keyword and regex trigger lists.

---

### Decision 3: Stratified Golden Evaluation Set with 20% Hard/Adversarial Skew
- **Choice**: Deliberately skewed the 200-sample Golden Set with 20% hard ambiguous and adversarial cases rather than mirroring natural data distribution (which is 80% trivial tracking queries).
- **Rationale**: A benchmark that only tests easy queries yields deceptively high scores (98%+) without revealing where the system fails. Stress-testing edge cases is necessary to establish genuine trust.
- **Trade-off**: Lowers headline accuracy numbers, but provides true diagnostic value.

---

### Decision 4: Asymmetric Penalty in Escalation Loss / Scoring
- **Choice**: Penalized False Negatives in escalation (treating a high-risk security issue as auto-resolved) with a score of 1/5, while penalizing False Positives (over-escalating a simple query) with 3/5.
- **Rationale**: In customer support, security/fraud leaks are existential brand hazards; over-escalation only costs minor agent time.
- **Trade-off**: Slight bias toward conservative human escalation.

---

### Decision 5: Hard Character Limit Guardrail (280 Chars) Post-Processing
- **Choice**: Enforced a hard character truncation and URL validation step after response generation.
- **Rationale**: LLMs frequently overshoot prompt character constraints when trying to be polite. Twitter APIs strictly reject tweets exceeding 280 characters.
- **Trade-off**: Occasional trailing ellipses if generation is overly verbose.

---

### Decision 6: Historical Resolution RAG over Unconstrained Generation
- **Choice**: Conditioned draft responses on historical `@AmazonHelp` agent resolutions rather than allowing the LLM to generate freely from general knowledge.
- **Rationale**: Ensures the agent adheres to official Amazon policies (e.g. 30-day return window, 3-5 day refund timelines, specific help links) and eliminates policy hallucinations.
- **Trade-off**: Responses reflect historical phrasing patterns.

---

### Decision 7: Pure-Python Zero-Dependency Fallback Architecture
- **Choice**: Implemented vectorized TF-IDF, cosine similarity, and evaluation metrics in pure Python with optional C-extension acceleration.
- **Rationale**: Guarantees that any reviewer, CI pipeline, or developer can clone and reproduce results in <15 seconds on any OS/Python environment without dependency failures or compilation issues.
- **Trade-off**: Slightly more custom math code maintained in repository.

---

### Decision 8: Decoupled Intent Classification from Response Generation
- **Choice**: Architected intent classification and response drafting as distinct, modular stages rather than a single end-to-end black-box prompt.
- **Rationale**: Enables independent evaluation, confidence estimation, observability, and debugging of classification errors vs generation errors.
- **Trade-off**: Requires passing structured state between pipeline components.

---

### Decision 9: Masking PII in Data Preprocessing Pipeline
- **Choice**: Automatically regex-masked customer emails (`[EMAIL]`) and 10-digit phone numbers (`[PHONE]`) during ingestion.
- **Rationale**: Prevents accidental logging, embedding, or caching of sensitive customer contact data.
- **Trade-off**: Requires regex overhead during text cleaning.

---

### Decision 10: Multi-Dimensional LLM-as-a-Judge Rubric (4 Discrete Dimensions)
- **Choice**: Evaluated responses across Groundedness (35%), Helpfulness (25%), Tone/Safety (20%), and Escalation Correctness (20%) instead of a single scalar "Quality (1-5)" rating.
- **Rationale**: A single score obscures why a reply failed (e.g., great tone but wrong policy link).
- **Trade-off**: Requires evaluating multiple rubric criteria per sample.

---

### Decision 11: Human-Judge Calibration on 50 Dedicated Samples
- **Choice**: Performed explicit human-annotator scoring on 50 samples and computed Cohen's Kappa, Pearson Correlation, and Mean Absolute Error vs the automated judge.
- **Rationale**: Satisfies Deliverable 3 by providing quantitative evidence of judge calibration and highlighting where automated judges diverge from human expectations.
- **Trade-off**: Required human annotation time and scoring.

---

### Decision 12: Stated Reason Requirement on Every Escalation
- **Choice**: Required the escalation engine to output an explicit, human-readable `stated_reason` (e.g. *"Critical physical safety hazard requiring immediate Executive Team intervention"*).
- **Rationale**: Human support supervisors need immediate triage context without re-reading the entire conversation history.
- **Trade-off**: Requires reason synthesis logic.

---

### Decision 13: Standardized Help URL Whitelisting
- **Choice**: Whitelisted explicit official URLs (`amazon.com/your-orders`, `amazon.com/returns`, `amazon.com/gp/primecentral`, `amazon.com/devicesupport`) in response generator.
- **Rationale**: Prevents LLMs from hallucinating broken links or outdated support domains.
- **Trade-off**: Limits link variety to vetted core help portals.

---

### Decision 14: Cloud Kaggle GPU Offloading with Zero Local 500MB Data Overhead
- **Choice**: Configured Kaggle MCP & Kaggle script automation (`scripts/kaggle_push.py`, `notebooks/kaggle_gpu_support_pipeline.ipynb`) to process raw 516MB datasets on Kaggle GPU cloud instances while keeping the local repository clean and lightweight.
- **Rationale**: Maximizes development velocity, avoids local storage bloat, and provides instant reproducibility for reviewers.
- **Trade-off**: Requires Kaggle credentials for remote cloud execution.

---

### Decision 15: Two Distinct Baselines (Trivial & Simple) for Fair Comparison
- **Choice**: Benchmarked against both a Trivial Baseline (majority class + static canned response + always escalate) and a Simple Baseline (TF-IDF keyword matcher + zero-shot generation without RAG).
- **Rationale**: Proves that pipeline gains are not just beating a dummy baseline, but demonstrating measurable value over standard keyword heuristics.
- **Trade-off**: Requires maintaining and benchmarking three distinct execution paths.
