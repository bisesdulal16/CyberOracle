"""
app/utils/redteam_dataset.py

Utility functions for loading and parsing the red-team PII dataset
from `datasets/redteam_prompts_v1.md`.

This is used by automated tests to validate that our DLP pipeline
(regex + Presidio + middleware) correctly detects and/or ignores
various prompts.
"""

from pathlib import Path
from typing import Dict, List


# Path to the dataset file, relative to the project root.
# Adjust if your structure changes.
DATASET_PATH = (
    Path(__file__).resolve().parents[2]  # go from app/utils/ -> project root
    / "datasets"
    / "redteam_prompts_v1.md"
)


def load_redteam_sections() -> Dict[str, List[str]]:
    """
    Parse the markdown dataset into sections.

    Returns:
        Dict[str, List[str]] mapping a section key (e.g. "ssn", "credit_cards")
        to a list of prompt strings from that section.

    Parsing logic:
    - Lines starting with '#' are treated as comments/headers.
    - Section headers look like: '# Section X — Name'
    - All non-empty, non-comment lines below a section header are prompts,
      until the next section header is found.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Red-team dataset not found at: {DATASET_PATH}")

    sections: Dict[str, List[str]] = {}
    current_key: str | None = None

    with DATASET_PATH.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()

            # Skip completely empty lines
            if not line:
                continue

            # Detect section header lines starting with '# Section'
            if line.startswith("# Section"):
                # Example: "# Section 1 — SSN Test Prompts"
                # We convert the trailing name into a simple key: "ssn_test_prompts" -> "ssn"
                parts = line.split("—", maxsplit=1)
                if len(parts) == 2:
                    name = parts[1].strip().lower()
                else:
                    # Fallback: use the whole line
                    name = line.lower()

                # Very simple mapping -> you can tweak as needed
                if "ssn" in name:
                    current_key = "ssn"
                elif "credit card" in name or "credit cards" in name:
                    current_key = "credit_cards"
                elif "email" in name:
                    current_key = "emails"
                elif "api keys" in name or "api key" in name:
                    current_key = "api_keys"
                elif "obfuscated" in name or "tricks" in name:
                    current_key = "obfuscated"
                elif "non-sensitive" in name or "control" in name:
                    current_key = "control"
                else:
                    # Generic fallback: normalized section name
                    current_key = name.replace(" ", "_")

                sections.setdefault(current_key, [])
                continue

            # Ignore other comment lines (starting with '#')
            if line.startswith("#"):
                continue

            # If we have a current section, treat this line as a prompt
            if current_key is not None:
                sections.setdefault(current_key, []).append(line)

    return sections
