from app.utils.logger import mask_sensitive


def test_masking_sensitive_fields():
    text = "password=abc123&api_key=XYZ&token=999"
    masked = mask_sensitive(text)

    # All sensitive values must be removed
    assert "***MASKED***" in masked
    assert "abc123" not in masked
    assert "XYZ" not in masked
    assert "999" not in masked
