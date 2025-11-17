# CyberOracle — Week 3 Progress Report

**Contributor:** Pradip Sapkota  
**Role:** DLP / Presidio Integration / Testing  
**Period:** Nov 11 – Nov 15, 2025  

---

## Objectives
Integrate Microsoft Presidio into the CyberOracle DLP pipeline and validate its accuracy across multiple sensitive-data categories, targeting at least 90% detection performance.

---

## Tasks Completed

| Task | Tool / Library | Status |
|------|----------------|---------|
| Integrated Microsoft Presidio Analyzer & Anonymizer | presidio-analyzer, presidio-anonymizer | Completed |
| Implemented custom recognizers (SSN + API key patterns) | Presidio PatternRecognizer | Completed |
| Built Presidio DLP module (`dlp_presidio.py`) with alerting | FastAPI middleware, Presidio | Completed |
| Prepared controlled dataset for validation (10 samples) | Python, internal script | Completed |
| Implemented validation script to compute Precision/Recall/F1 | `scripts/presidio_validate.py` | Completed |
| Achieved 100% precision, recall, and F1 on test samples | Presidio engine | Completed |
| Generated written accuracy report | Markdown | Completed |

---

## Deliverables

| Deliverable | Description | File / Link |
|-------------|-------------|--------------|
| **Presidio DLP Module** | Detection, anonymization, and alerting for SSNs, credit cards, emails, API keys, phone numbers, and names | `app/middleware/dlp_presidio.py` |
| **Validation Script** | Computes detection accuracy metrics using sample dataset | `scripts/presidio_validate.py` |
| **Accuracy Report** | Documented results with metrics and analysis | `docs/presidio_test_report.md` |

---

## Verification and Results

### Detection Sample Results (Examples)

| Input | Detected Entities | Redacted Output |
|-------|-------------------|------------------|
| `My SSN is 219-09-9999` | GENERIC_SSN | My SSN is `<GENERIC_SSN>` |
| `Use Visa 4111 1111 1111 1111` | CREDIT_CARD | Use Visa `<CREDIT_CARD>` |
| `Contact me at john.doe@example.com` | EMAIL_ADDRESS | Contact me at `<EMAIL_ADDRESS>` |
| `APIKEY=sk_live_1234567890abcdefghi` | GENERIC_API_KEY | `<GENERIC_API_KEY>` |
| `Just a normal message` | None | Just a normal message |

---

## Accuracy Metrics  
Computed using `scripts/presidio_validate.py`:

| Metric | Value |
|--------|--------|
| True Positives | 8 |
| False Positives | 0 |
| False Negatives | 0 |
| Precision | 100% |
| Recall | 100% |
| F1 Score | 100% |

All results exceed the Week 3 requirement of at least 90% accuracy.

---

## Summary of Implementation

- Finalized `presidio_scan()` wrapper to return sanitized text, detected entities, and real-time alerts via `alert_manager.py`.  
- Added custom recognizers for patterns Presidio does not reliably detect (API keys, generic SSNs).  
- Ensured consistent anonymization across all supported entities.  
- Validated engine performance on both positive and negative scenarios.  
- Confirmed compatibility with the middleware pipeline and Phase II DLP requirements.

---

## Progress
Week 3 progress toward the overall project: **22%**

---

## Next Steps
- Integrate Presidio output with the PostgreSQL logging system.  
- Add combined Regex + Presidio hybrid detection pipeline for DLP v2.  
- Expand dataset to include more adversarial red-team prompts.  
- Prepare for Week 4: real-time alerting and webhook integration refinement.  

---
