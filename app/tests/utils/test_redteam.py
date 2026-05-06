"""
Redteam Dataset Tests
"""

import pytest
from unittest.mock import patch
import app.utils.redteam_dataset as redteam_module
from app.utils.redteam_dataset import load_redteam_sections

EM = "\u2014"

MOCK_DATASET = (
    "# Section 1 \u2014 SSN Test Prompts\n"
    "My SSN is 123-45-6789\n"
    "Another SSN: 987-65-4321\n"
    "# Section 2 \u2014 Credit Cards\n"
    "Card: 4111111111111111\n"
    "# Section 3 \u2014 Emails\n"
    "user@example.com\n"
    "# Section 4 \u2014 API Keys\n"
    "api_key=ABCDEFGHIJKLMNOP\n"
    "# Section 5 \u2014 Obfuscated Tricks\n"
    "some obfuscated prompt\n"
    "# Section 6 \u2014 Non-Sensitive Control\n"
    "hello world\n"
)


class FakePath:
    def exists(self):
        return True

    def open(self, *args, **kwargs):
        from io import StringIO

        return StringIO(MOCK_DATASET)


def _load_mock(content=None):
    fake = FakePath()
    if content:
        from io import StringIO

        fake.open = lambda *a, **k: StringIO(content)
    with patch.object(redteam_module, "DATASET_PATH", fake):
        return load_redteam_sections()


def test_load_returns_dict():
    assert isinstance(_load_mock(), dict)


def test_ssn_section_loaded():
    assert "ssn" in _load_mock()


def test_ssn_section_has_two_prompts():
    assert len(_load_mock()["ssn"]) == 2


def test_credit_cards_section_loaded():
    assert "credit_cards" in _load_mock()


def test_emails_section_loaded():
    assert "emails" in _load_mock()


def test_api_keys_section_loaded():
    assert "api_keys" in _load_mock()


def test_obfuscated_section_loaded():
    assert "obfuscated" in _load_mock()


def test_file_not_found_raises():
    class MissingPath:
        def exists(self):
            return False

    with patch.object(redteam_module, "DATASET_PATH", MissingPath()):
        with pytest.raises(FileNotFoundError):
            load_redteam_sections()


def test_empty_lines_skipped():
    content = "# Section 1 \u2014 SSN Test Prompts\n\nMy SSN is 123-45-6789\n\n"
    sections = _load_mock(content)
    assert sections["ssn"] == ["My SSN is 123-45-6789"]
