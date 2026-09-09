# Golden Evaluation Set — Sampling & Labelling Methodology

## 1. Executive Summary
This document defines the curation and sampling methodology for the **200-sample Golden Evaluation Benchmark** and the **50-sample Human-Judge Calibration Set** constructed for the Hiver AI Customer Support Agent assignment.

The target domain is Twitter customer support interactions for `@AmazonHelp` from the Kaggle dataset (`thoughtvector/customer-support-on-twitter`).

---

## 2. Intent Taxonomy & Class Distribution

The taxonomy comprises **7 mutually exclusive and collectively exhaustive (MECE)** intents derived from customer support conversations:

1. **`ORDER_STATUS_DELIVERY`** (18.5%): Inquiries regarding transit tracking, late deliveries, carrier scans, and missing parcels.
2. **`REFUND_AND_RETURNS`** (16.5%): Return label creation, drop-off locations (UPS/Kohl's/Whole Foods), refund timelines (3-5 days), and gift card refund options.
3. **`DAMAGED_DEFECTIVE_ITEM`** (15.5%): Broken on arrival, defective hardware, wrong items/sizes, leaking liquids, expired goods.
4. **`ACCOUNT_ACCESS_SECURITY`** (14.5%): 2FA verification issues, compromised accounts, phishing text alerts, GDPR data access.
5. **`BILLING_AND_PRIME`** (14.0%): Prime subscription renewals, unauthorized digital charges, tax exemption, payment failures.
6. **`PRODUCT_TROUBLESHOOTING`** (11.0%): Fire TV, Kindle Paperwhite, Echo/Alexa devices, smart home plugs, Prime Video streaming quality.
7. **`FEEDBACK_AND_GENERAL`** (10.0%): Delivery driver compliments, website feedback, policy inquiries, general compliments.

---

## 3. Sampling Strategy & Noise Modeling
To reflect the authentic messiness of customer support on Twitter:
- **Linguistic Noise**: Typos, missing punctuation, capitalization emphasis ("ASAP", "URGENT"), Twitter handles, order ID tokens (`#112-9848192-3849182`), and carrier tracking codes (`TBA982348123019`, `1Z9999`).
- **Sentiment Stratification**:
  - *Neutral / Informational* (38%)
  - *Frustrated / Impatient* (34%)
  - *Angry / Urgent* (22%)
  - *Adversarial / Safety Critical* (6%)
- **Difficulty Stratification**:
  - *Easy (Core)*: 60%
  - *Medium (Multi-hop/Mild frustration)*: 25%
  - *Hard / Ambiguous*: 10%
  - *Adversarial*: 5%

---

## 4. Escalation Ground Truth Protocol
Each record has a boolean `true_escalation` flag and a categorized `true_escalation_reason`:

- **`PII_OR_ACCOUNT_ACCESS_REQUIRED`**: Resolving the query requires accessing private customer records, email, or order history via secure DM.
- **`FINANCIAL_DISPUTE_LIMIT`**: Disputed charges, refund mismatches, or cancellation refund appeals.
- **`REPEATED_UNRESOLVED_CONTACT`**: Multiple failed attempts or severe delays (e.g. 2nd broken replacement).
- **`SECURITY_FRAUD_ALERT`**: Suspected account hijacking, unauthorized purchases, phishing reports.
- **`SEVERE_FRUSTRATION_OR_LEGAL`**: Property damage, bodily hazard (sparks/smoke), police report mentions, abusive driver conduct.
- **`NONE`**: Self-service resolution possible via public information, standard SOP instructions, or help link guidance.

---

## 5. Human-Judge Calibration Protocol
- 50 samples were independently scored by a human evaluator across 4 dimensions:
  1. *Groundedness* (1–5)
  2. *Helpfulness* (1–5)
  3. *Tone & Safety* (1–5)
  4. *Escalation Appropriateness* (1–5)
- The evaluation harness computes **Cohen's Kappa ($\kappa$)** and **Pearson correlation ($r$)** between human ratings and the automated LLM Judge.
