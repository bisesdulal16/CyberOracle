from pathlib import Path

import pytest

from app.utils import redteam_dataset


def test_dataset_path_points_to_markdown_file():
    assert redteam_dataset.DATASET_PATH.name == "redteam_prompts_v1.md"
    assert redteam_dataset.DATASET_PATH.suffix == ".md"


def test_load_redteam_sections_file_not_found(monkeypatch):
    fake_path = Path("/tmp/does_not_exist_redteam_prompts_v1.md")
    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", fake_path)

    with pytest.raises(FileNotFoundError):
        redteam_dataset.load_redteam_sections()


def test_load_redteam_sections_parses_known_sections(tmp_path, monkeypatch):
    dataset = tmp_path / "redteam_prompts_v1.md"
    dataset.write_text(
        "\n".join(
            [
                "# Section 1 — SSN Test Prompts",
                "My SSN is 123-45-6789",
                "",
                "# Section 2 — Credit Card Test Prompts",
                "Card number 4111-1111-1111-1111",
                "",
                "# Section 3 — Email Test Prompts",
                "Contact me at test@example.com",
                "",
                "# Section 4 — API Keys",
                "sk-test-1234567890",
                "",
                "# Section 5 — Obfuscated Tricks",
                "my ssn is one two three four five six seven eight nine",
                "",
                "# Section 6 — Non-sensitive Control Prompts",
                "What is the weather today?",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset)

    sections = redteam_dataset.load_redteam_sections()

    assert "ssn" in sections
    assert "credit_cards" in sections
    assert "emails" in sections
    assert "api_keys" in sections
    assert "obfuscated" in sections
    assert "control" in sections

    assert sections["ssn"] == ["My SSN is 123-45-6789"]
    assert sections["credit_cards"] == ["Card number 4111-1111-1111-1111"]
    assert sections["emails"] == ["Contact me at test@example.com"]
    assert sections["api_keys"] == ["sk-test-1234567890"]
    assert sections["obfuscated"] == [
        "my ssn is one two three four five six seven eight nine"
    ]
    assert sections["control"] == ["What is the weather today?"]


def test_load_redteam_sections_ignores_blank_and_comment_lines(tmp_path, monkeypatch):
    dataset = tmp_path / "redteam_prompts_v1.md"
    dataset.write_text(
        "\n".join(
            [
                "# Random heading to ignore",
                "",
                "# Section 1 — SSN Test Prompts",
                "",
                "# another comment",
                "Prompt one",
                "",
                "Prompt two",
                "",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset)

    sections = redteam_dataset.load_redteam_sections()

    assert "ssn" in sections
    assert sections["ssn"] == ["Prompt one", "Prompt two"]


def test_load_redteam_sections_uses_fallback_normalized_name(tmp_path, monkeypatch):
    dataset = tmp_path / "redteam_prompts_v1.md"
    dataset.write_text(
        "\n".join(
            [
                "# Section 9 — Strange Custom Bucket",
                "custom prompt",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(redteam_dataset, "DATASET_PATH", dataset)

    sections = redteam_dataset.load_redteam_sections()

    assert "strange_custom_bucket" in sections
    assert sections["strange_custom_bucket"] == ["custom prompt"]
