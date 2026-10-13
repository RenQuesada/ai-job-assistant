import pytest
from core.tools import _normalize_domain

def test_normalizing_email():
    email = "jobs@google.io"
    expected_res = "google.io"
    assert _normalize_domain(email) == expected_res

def test_normalizing_path():
    path = "https://feathery.io/careers"
    expected_res = "feathery.io"
    assert _normalize_domain(path) == expected_res

def test_normalizing_port():
    port = "claude.com:8080"
    expected_res = "claude.com"
    assert _normalize_domain(port) == expected_res

def test_normalizing_messy_input():
    messy_input = "   HTTPS://wwW.AMAZON.coM/careers   "
    expected_res = "amazon.com"
    assert _normalize_domain(messy_input) == expected_res

def test_normalizing_url_with_username():
    url = "https://user@site.com/path"
    expected_res = "site.com"
    assert _normalize_domain(url) == expected_res

def test_normalizing_empty_string():
    assert _normalize_domain("") == ""
