from pathlib import Path


def _get_repo_root() -> Path:
    """
    Return the repository root directory.

    This test file lives in:
      app/tests/infra/test_secret_scan_workflow.py

    So we go up three levels to reach the repo root.
    """
    return Path(__file__).resolve().parents[3]


def test_secret_scan_workflow_file_exists():
    """The TruffleHog GitHub Actions workflow file should exist."""
    repo_root = _get_repo_root()
    workflow_path = repo_root / ".github" / "workflows" / "secret-scan.yml"
    assert workflow_path.exists(), f"Expected workflow file at {workflow_path}, but it does not exist."


def test_secret_scan_workflow_uses_trufflehog():
    """
    The workflow should use the TruffleHog GitHub Action and have the expected job name.
    This verifies that our repo security plugin for secret scanning is configured.
    """
    repo_root = _get_repo_root()
    workflow_path = repo_root / ".github" / "workflows" / "secret-scan.yml"
    content = workflow_path.read_text()

    assert "Secret Scan (TruffleHog)" in content
    assert "trufflesecurity/trufflehog@main" in content
