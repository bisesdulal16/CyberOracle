from pathlib import Path

import pytest

from app.utils import redteam_dataset


def test_load_redteam_sections_file_not_found(monkeypatch):
    fake_path = Path("/tmp/does_not_exist_redteam_prompts_v1.md")
    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", fake_path)

    with pytest.raises(FileNotFoundError, match="Red-team dataset not found"):
        redteam_dataset.load_redteam_sections()


def test_load_redteam_sections_parses_known_sections(tmp_path, monkeypatch):
    dataset_file = tmp_path / "redteam_prompts_v1.md"
    dataset_file.write_text(
        "\n".join(
            [
                "# Section 1 — SSN Test Prompts",
                "My SSN is 123-45-6789",
                "",
                "# Section 2 — Credit Card Prompts",
                "Card number is 4111 1111 1111 1111",
                "",
                "# Section 3 — Email Prompts",
                "Email me at test@example.com",
                "",
                "# Section 4 — API Key Prompts",
                "sk-test-123456",
                "",
                "# Section 5 — Obfuscated Tricks",
                "my ssn is one two three four five",
                "",
                "# Section 6 — Non-Sensitive Control Prompts",
                "hello world",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset_file)

    sections = redteam_dataset.load_redteam_sections()

    assert "ssn" in sections
    assert "credit_cards" in sections
    assert "emails" in sections
    assert "api_keys" in sections
    assert "obfuscated" in sections
    assert "control" in sections

    assert sections["ssn"] == ["My SSN is 123-45-6789"]
    assert sections["credit_cards"] == ["Card number is 4111 1111 1111 1111"]
    assert sections["emails"] == ["Email me at test@example.com"]
    assert sections["api_keys"] == ["sk-test-123456"]
    assert sections["obfuscated"] == ["my ssn is one two three four five"]
    assert sections["control"] == ["hello world"]


def test_load_redteam_sections_ignores_comments_and_blank_lines(tmp_path, monkeypatch):
    dataset_file = tmp_path / "redteam_prompts_v1.md"
    dataset_file.write_text(
        "\n".join(
            [
                "",
                "# Section 1 — SSN Test Prompts",
                "",
                "# this is a comment line",
                "Prompt A",
                "",
                "Prompt B",
                "# another comment",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset_file)

    sections = redteam_dataset.load_redteam_sections()

    assert "ssn" in sections
    assert sections["ssn"] == ["Prompt A", "Prompt B"]


def test_load_redteam_sections_fallback_section_name(tmp_path, monkeypatch):
    dataset_file = tmp_path / "redteam_prompts_v1.md"
    dataset_file.write_text(
        "\n".join(
            [
                "# Section 9 — Strange Custom Bucket",
                "Custom prompt 1",
                "Custom prompt 2",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset_file)

    sections = redteam_dataset.load_redteam_sections()

    assert "strange_custom_bucket" in sections
    assert sections["strange_custom_bucket"] == ["Custom prompt 1", "Custom prompt 2"]


def test_load_redteam_sections_fallback_without_dash_separator(tmp_path, monkeypatch):
    dataset_file = tmp_path / "redteam_prompts_v1.md"
    dataset_file.write_text(
        "\n".join(
            [
                "# Section 10",
                "Loose prompt",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset_file)

    sections = redteam_dataset.load_redteam_sections()

    assert "#_section_10" in sections
    assert sections["#_section_10"] == ["Loose prompt"]