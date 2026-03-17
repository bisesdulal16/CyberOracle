"""
Input Validation Tests
----------------------
Tests for validating text input fields used in API requests.
Ensures proper input handling and adherence to security best practices.
Follows OWASP recommendations and PEP 8 standards.
"""

from app.utils.validation import validate_text_field


def test_validation_pass():
    """
    Verify that valid input passes validation.

    OWASP:
        Ensures expected input is accepted, supporting proper input validation
        and reducing false negatives (OWASP ASVS 5.1 – Input Validation).

    PEP 8:
        Test name is clear and descriptive; assertion is simple and readable.
    """
    assert validate_text_field({"text": "hello"}) is True


def test_validation_fail_missing_key():
    """
    Verify that input missing required fields fails validation.

    OWASP:
        Prevents improper input handling and potential injection risks by enforcing
        required fields (OWASP Top 10 – A03: Injection).

    PEP 8:
        Uses descriptive function naming and consistent formatting.
    """
    assert validate_text_field({}) is False


def test_validation_fail_empty():
    """
    Verify that empty input values fail validation.

    OWASP:
        Ensures input is not empty, preventing weak or invalid data from being processed
        (OWASP ASVS 5.1 – Input Validation).

    PEP 8:
        Maintains clarity and consistency in test structure and naming.
    """
    assert validate_text_field({"text": ""}) is False
