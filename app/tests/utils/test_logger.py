from app.utils.logger import mask_sensitive


def test_mask_password():
    msg = "password=hello123"
    masked = mask_sensitive(msg)
    assert "hello123" not in masked
    assert "password=***MASKED***" in masked


def test_mask_api_key():
    msg = "api_key=XYZ123"
    masked = mask_sensitive(msg)
    assert "XYZ123" not in masked
    assert "api_key=***MASKED***" in masked


def test_mask_token():
    msg = "token=abc.def.ghi"
    masked = mask_sensitive(msg)
    assert "abc.def.ghi" not in masked
    assert "token=***MASKED***" in masked
