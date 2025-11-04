"""
Presidio Validation Script
--------------------------
CyberOracle Week 3: Detection Accuracy Evaluation

Purpose:
    Validate Microsoft Presidio's ability to detect and anonymize
    PII/PHI entities — SSNs, credit cards, emails, and API keys —
    after integrating custom recognizers.

Usage:
    python3 scripts/presidio_validate.py

Outputs:
    - Detected entities per sample
    - Redacted text
    - Overall Precision / Recall / F1 metrics
"""

import os
import sys

# Ensure app/ modules can be imported when running from root
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # noqa: E402

from app.middleware.dlp_presidio import presidio_scan  # noqa: E402

# ---------------------------------------------------------------------------
# Test Dataset
# ---------------------------------------------------------------------------
# 10 representative samples: 8 positives + 2 negatives
samples = [
    # SSNs (valid-looking)
    ("My SSN is 219-09-9999", ["GENERIC_SSN"]),
    ("Employee SSN: 078-05-1120", ["GENERIC_SSN"]),
    # Credit Cards
    ("Use Visa 4111 1111 1111 1111", ["CREDIT_CARD"]),
    ("AMEX 378282246310005 for booking", ["CREDIT_CARD"]),
    # Emails
    ("Contact me at john.doe@example.com", ["EMAIL_ADDRESS"]),
    ("Send it to jane@company.org", ["EMAIL_ADDRESS"]),
    # API Keys
    ("APIKEY=sk_live_1234567890abcdefghi", ["GENERIC_API_KEY"]),
    ("Here is api_token=abcdEFGHijklMNOP1234", ["GENERIC_API_KEY"]),
    # Negative controls (should detect nothing)
    ("Just a normal message", []),
    ("Meeting at 3 PM about the roadmap", []),
]

# ---------------------------------------------------------------------------
# Validation Logic
# ---------------------------------------------------------------------------
tp = 0
fp = 0
fn = 0

for text, expected in samples:
    redacted, found = presidio_scan(text)
    found_set = set(found)
    exp_set = set(expected)

    tp += len(found_set & exp_set)
    fp += len(found_set - exp_set)
    fn += len(exp_set - found_set)

    print(f"Input: {text}")
    print(f"Detected: {sorted(found)}")
    print(f"Redacted: {redacted}")
    print("-" * 60)

# ---------------------------------------------------------------------------
# Metrics Calculation
# ---------------------------------------------------------------------------
precision = 100.0 if (tp + fp) == 0 else (tp / (tp + fp)) * 100
recall = 100.0 if (tp + fn) == 0 else (tp / (tp + fn)) * 100
f1 = (
    0.0
    if (precision + recall) == 0
    else (2 * precision * recall) / (precision + recall)
)

print(f"\nMetrics on {len(samples)} samples")
print(f"  True Positives : {tp}")
print(f"  False Positives: {fp}")
print(f"  False Negatives: {fn}")
print(f"  Precision: {precision:.2f}%")
print(f"  Recall:    {recall:.2f}%")
print(f"  F1 Score:  {f1:.2f}%")
