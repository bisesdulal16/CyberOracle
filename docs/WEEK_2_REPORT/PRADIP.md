# CyberOracle — Week 2 Progress Report

**Contributor:** Pradip Sapkota  
**Role:** Security Engineering / DLP Research  
**Period:** Nov 4 – Nov 8, 2025  

---

## Objectives
Develop foundational regex-based Data Loss Prevention (DLP) capabilities and prepare an initial red-team dataset for early testing. Establish standalone scanning logic separate from the main middleware.

---

## Tasks Completed

| Task | Tool / Library | Status |
|------|----------------|---------|
| Implemented standalone regex-based DLP scanner (`scan_text`) for SSN, credit card, email, and API key detection | Python `re` | Completed |
| Added unit tests for all detection patterns (SSN, credit card, email, API key, clean text) | PyTest | Completed |
| Created initial red-team prompt dataset for DLP testing | Text dataset | Completed |
| Verified scanning logic independently from the FastAPI middleware | CLI runner | Completed |

---

## Deliverables

| Deliverable | Description | File / Link |
|-------------|-------------|-------------|
| **Regex-based DLP scanner** | Standalone script to scan text and return redacted output and detected entities | `app/middleware/dlp_regex.py` |
| **Unit Tests** | Tests confirming detection accuracy and expected behavior | `tests/test_dlp_regex.py` |
| **Red-team Prompt Dataset** | Dataset of example phrases containing SSNs, API keys, emails, and credit card numbers | `datasets/redteam_prompts_v1.txt` |


---

## Verification & Results

| Check | Result |
|-------|--------|
| Regex detection validated through unit tests | All test cases passed |
| Scanner correctly identifies and redacts sensitive patterns | Confirmed through manual and automated testing |
| Dataset successfully loaded and used to validate detection behaviors | Confirmed |

---

## Progress
Week 2 progress toward the overall project: **17% (cumulative)**

---

## Next Steps
- Integrate regex scanner with FastAPI middleware  
- Begin Presidio integration for Week 3 detection accuracy validation  
- Expand dataset for more complex red-team scenarios  
- Prepare for merging regex and Presidio into a unified DLP v2  

---
