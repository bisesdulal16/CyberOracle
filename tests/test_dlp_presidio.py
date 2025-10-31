"""
Unit Test for Presidio DLP Integration
-------------------------------------
Ensures Microsoft Presidio detects at least one entity (e.g., PERSON, PHONE_NUMBER)
when scanning text containing identifiable information.
"""

from app.middleware import dlp_presidio


def test_presidio_detects_entities():
    sample = "Contact John Doe at 555-123-4567 for the meeting."
    sanitized_text, entities = dlp_presidio.presidio_scan(sample)

    # Sanity checks
    assert isinstance(sanitized_text, str)
    assert isinstance(entities, list)

    # Presidio should identify at least one entity (PHONE_NUMBER or PERSON)
    assert len(entities) > 0, "Presidio failed to detect any entities"
