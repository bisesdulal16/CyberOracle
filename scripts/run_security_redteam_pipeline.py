#!/usr/bin/env python3

import os
import sys
import subprocess
import re
from dataclasses import dataclass

from app.utils import alert_manager  # uses your existing implementation

"""
PSFR5 – Security Red-Team Automation Pipeline
Compatible with your existing alert_manager.py (no extra parameters).

This script:
  1. Runs pytest (your full test suite).
  2. Runs the prompt-injection red-team script.
  3. Parses the red-team summary.
  4. Sends alerts via app.utils.alert_manager when needed.
"""

# --- Ensure project root is on sys.path so `import app...` works ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@dataclass
class PytestResult:
    success: bool
    stdout: str
    stderr: str


@dataclass
class RedteamResult:
    stdout: str
    stderr: str
    failed: int
    needs_review: int
    total: int


def run_pytest() -> PytestResult:
    print("[security-pipeline] Running pytest...")
    proc = subprocess.run(["pytest", "-q"], text=True, capture_output=True)
    success = proc.returncode == 0

    if success:
        print("[security-pipeline] Pytest PASSED.")
    else:
        print("[security-pipeline] Pytest FAILED.")

    return PytestResult(success, proc.stdout, proc.stderr)


def run_prompt_redteam() -> RedteamResult:
    """
    Run the prompt-injection red-team script and parse its summary.
    Expects output lines like:

        Total tests:     5
        Failed:          0
        Needs review:    5
    """
    print("[security-pipeline] Running prompt-injection tests...")

    proc = subprocess.run(
        [sys.executable, "scripts/run_prompt_injection_redteam.py"],
        text=True,
        capture_output=True,
    )

    stdout = proc.stdout
    stderr = proc.stderr

    # Default counts
    failed = 0
    needs_review = 0
    total = 0

    m_failed = re.search(r"Failed:\s+(\d+)", stdout)
    if m_failed:
        failed = int(m_failed.group(1))

    m_review = re.search(r"Needs review:\s+(\d+)", stdout)
    if m_review:
        needs_review = int(m_review.group(1))

    m_total = re.search(r"Total tests:\s+(\d+)", stdout)
    if m_total:
        total = int(m_total.group(1))

    print("[security-pipeline] Parsed red-team results:")
    print(f"  Total:       {total}")
    print(f"  Failed:      {failed}")
    print(f"  Needs review:{needs_review}")

    return RedteamResult(stdout, stderr, failed, needs_review, total)


def send_pytest_alert(result: PytestResult):
    """
    High-severity alert when pytest fails.
    We don't include logs here to keep the message short.
    """
    alert_manager.send_alert(
        "Security pipeline FAILED during pytest execution.",
        severity="critical",
        source="security_pipeline",
    )


def send_redteam_alert(result: RedteamResult):
    """
    Alert when red-team results show failures or manual-review cases.
    """
    severity = "warning"
    if result.failed > 0:
        severity = "error"

    msg = (
        "Prompt-injection red-team summary:\n"
        f"Total={result.total}, Failed={result.failed}, NeedsReview={result.needs_review}"
    )

    alert_manager.send_alert(
        msg,
        severity=severity,
        source="security_pipeline",
    )


def main() -> int:
    print("\n[security-pipeline] Starting automated security pipeline...\n")

    # 1. Run pytest
    pytest_result = run_pytest()
    if not pytest_result.success:
        send_pytest_alert(pytest_result)
        return 1  # Non-zero status for CI/n8n

    # 2. Run red-team prompts
    redteam_result = run_prompt_redteam()

    # 3. Trigger alerts if needed
    if redteam_result.failed > 0 or redteam_result.needs_review > 0:
        send_redteam_alert(redteam_result)

    print("\n[security-pipeline] Pipeline completed.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
