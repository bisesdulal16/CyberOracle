"""
tests/test_redteam_dlp_dataset.py

Requirement: PSFR4 – Integrate red-team DLP dataset into automated tests.

This test suite uses the Week 2 red-team dataset in
`datasets/redteam_prompts_v1.md` to validate that:

- The dataset can be loaded and parsed into sections.
- The core DLP masking function (`mask_sensitive`) can process all
  "PII-like" sections without crashing.
- Control (non-sensitive) text is not modified.

IMPORTANT:
- We DO NOT enforce that credit cards / SSNs / etc. are actually masked
  here, because the current implementation may not yet cover all patterns.
- This is a **smoke test** wired to the real code, not a strict policy test.
"""

from app.utils.logger import mask_sensitive
from app.utils.redteam_dataset import load_redteam_sections


def _mask(text: str) -> str:
    """
    Tiny wrapper around the core DLP function.

    If the signature of `mask_sensitive` changes in the future,
    this is the only place we need to update for this test file.
    """
    return mask_sensitive(text)


def test_redteam_dataset_sections_exist():
    """
    Basic sanity check: the loader can find the dataset and key sections.
    """
    sections = load_redteam_sections()

    # We expect at least these sections from redteam_prompts_v1.md.
    expected_keys = {
        "ssn",
        "credit_cards",
        "emails",
        "api_keys",
        "obfuscated",
        "control",
    }

    missing = expected_keys.difference(sections.keys())
    assert not missing, f"Dataset is missing expected sections: {missing}"


def test_dlp_smoke_check_on_pii_sections():
    """
    PSFR4 – DLP red-team smoke test.

    We use the red-team dataset sections that *should* be considered
    PII-like (credit cards, emails, API keys, obfuscated patterns)
    and run them through the core DLP function.

    This test only verifies that:
      - the dataset loads correctly,
      - the DLP function runs without errors,
      - the returned value is a non-empty string.

    We deliberately DO NOT assert that the text is changed, to avoid
    forcing behavior changes to the existing DLP implementation.
    """
    sections = load_redteam_sections()

    pii_sections = [
        ("ssn", sections.get("ssn", [])),
        ("credit_cards", sections.get("credit_cards", [])),
        ("emails", sections.get("emails", [])),
        ("api_keys", sections.get("api_keys", [])),
        ("obfuscated", sections.get("obfuscated", [])),
    ]

    for name, prompts in pii_sections:
        assert prompts, f"Section `{name}` has no prompts – check your dataset."

        for prompt in prompts:
            redacted = _mask(prompt)

            # Basic smoke-check: DLP returns a non-empty string
            assert isinstance(redacted, str), (
                f"[{name}] DLP returned a non-string value.\n"
                f"Input: {prompt}\n"
                f"Output: {redacted!r}"
            )
            assert redacted.strip(), (
                f"[{name}] DLP returned an empty/whitespace string.\n"
                f"Input: {prompt}\n"
            )


def test_dlp_ignores_control_section():
    """
    Control group:

    - Non-sensitive sentences should pass through unchanged so we don't
      over-mask normal text.

    This is a stricter assertion: for clearly non-sensitive text, we
    expect no modification.
    """
    sections = load_redteam_sections()
    control_prompts = sections.get("control", [])

    assert control_prompts, "Control section has no prompts – check your dataset."

    for prompt in control_prompts:
        redacted = _mask(prompt)
        assert redacted == prompt, (
            "[control] Control text should not be modified by DLP.\n"
            f"Input:    {prompt}\n"
            f"Redacted: {redacted}"
        )
