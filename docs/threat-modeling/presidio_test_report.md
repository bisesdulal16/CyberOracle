# CyberOracle — Presidio Validation Report (Week 3)
**Author:** Pradip Sapkota  
**Date:** November 15 2025  
**Phase:** Week 3 – Integrate Microsoft Presidio & Validate Detection Accuracy  

---

## Objective
Integrate **Microsoft Presidio** into CyberOracle’s DLP module and verify its ability to detect and redact sensitive data such as SSNs, credit cards, emails, and API keys in text payloads.

---

## Components Tested
| Component | File | Description |
|------------|------|-------------|
| Presidio Analyzer | `app/middleware/dlp_presidio.py` | Detects sensitive entities using NLP models |
| Presidio Anonymizer | `app/middleware/dlp_presidio.py` | Redacts detected entities in text |
| Validation Script | `scripts/presidio_validate.py` | Runs controlled dataset through analyzer and computes precision/recall/F1 |

---

## Test Setup
- **Environment:** Ubuntu 22.04 (WSL)  
- **Python:** 3.10 (venv)  
- **Packages:** `presidio-analyzer`, `presidio-anonymizer`, `spacy`, `en_core_web_lg`  
- **Command:**  
  ```bash
  PYTHONPATH=. python3 scripts/presidio_validate.py

## Dataset
10 sample text strings covering SSNs, credit cards, emails, API keys, and normal text.

---

## Sample Inputs & Results

| # | Input | Detected Entities | Redacted Output |
|---|--------|------------------|----------------|
| 1 | My SSN is 219-09-9999 | GENERIC_SSN | My SSN is <GENERIC_SSN> |
| 2 | Use Visa 4111 1111 1111 1111 | CREDIT_CARD | Use Visa <CREDIT_CARD> |
| 3 | Contact me at john.doe@example.com | EMAIL_ADDRESS | Contact me at <EMAIL_ADDRESS> |
| 4 | APIKEY=sk_live_1234567890abcdefghi | GENERIC_API_KEY | <GENERIC_API_KEY> |
| 5 | Just a normal message | — | Just a normal message |

---

## Accuracy Metrics

| Metric | Value | Description |
|---------|-------|-------------|
| True Positives (TP) | 8 | Entities correctly detected |
| False Positives (FP) | 0 | Non-PII incorrectly flagged |
| False Negatives (FN) | 0 | PII missed by model |
| **Precision** | 100 % | TP / (TP + FP) |
| **Recall** | 100 % | TP / (TP + FN) |
| **F1 Score** | 100 % | 2 × (P × R) / (P + R) |

**Result:** Presidio achieved perfect detection (≥ 90 % accuracy requirement met).

---

## Execution Output

Below is the actual console output captured during testing:

(.venv) STUDENTS\ps1093@cyberoracle:~/CyberOracle$ python3 scripts/presidio_validate.py
Input: My SSN is 219-09-9999
Detected: ['GENERIC_SSN']
Redacted: My SSN is <GENERIC_SSN>
------------------------------------------------------------
Input: Employee SSN: 078-05-1120
Detected: ['GENERIC_SSN']
Redacted: Employee SSN: <GENERIC_SSN>
------------------------------------------------------------
Input: Use Visa 4111 1111 1111 1111
Detected: ['CREDIT_CARD']
Redacted: Use Visa <CREDIT_CARD>
------------------------------------------------------------
Input: AMEX 378282246310005 for booking
Detected: ['CREDIT_CARD']
Redacted: AMEX <CREDIT_CARD> for booking
------------------------------------------------------------
Input: Contact me at john.doe@example.com
Detected: ['EMAIL_ADDRESS']
Redacted: Contact me at <EMAIL_ADDRESS>
------------------------------------------------------------
Input: Send it to jane@company.org
Detected: ['EMAIL_ADDRESS']
Redacted: Send it to <EMAIL_ADDRESS>
------------------------------------------------------------
Input: APIKEY=sk_live_1234567890abcdefghi
Detected: ['GENERIC_API_KEY']
Redacted: <GENERIC_API_KEY>
------------------------------------------------------------
Input: Here is api_token=abcdEFGHijklMNOP1234
Detected: ['GENERIC_API_KEY']
Redacted: Here is <GENERIC_API_KEY>
------------------------------------------------------------
Input: Just a normal message
Detected: []
Redacted: Just a normal message
------------------------------------------------------------
Input: Meeting at 3 PM about the roadmap
Detected: []
Redacted: Meeting at 3 PM about the roadmap
------------------------------------------------------------

Metrics on 10 samples
  True Positives : 8
  False Positives: 0
  False Negatives: 0
  Precision: 100.00%
  Recall:    100.00%
  F1 Score:  100.00%

--------------
---

## Observations

- Detected key entities reliably: `GENERIC_SSN`, `CREDIT_CARD`, `EMAIL_ADDRESS`, `GENERIC_API_KEY`.  
- Produced consistent anonymized outputs across multiple formats (hyphenated / spaced / tokenized).  
- No false positives were observed on non-PII content.  
- Performance remained lightweight — typically under **1 second per text block**.  

---

## Outcome

| Deliverable | Status |
|--------------|---------|
| Presidio integrated locally | Completed |
| Detection validated on sample dataset | 100 % accuracy |
| Presidio Test Report Created 

---
