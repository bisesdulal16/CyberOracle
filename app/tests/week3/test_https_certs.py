import os


def test_https_certificates_exist():
    assert os.path.exists("certs/server.crt")
    assert os.path.exists("certs/server.key")
