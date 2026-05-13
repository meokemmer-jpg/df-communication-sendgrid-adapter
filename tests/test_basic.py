"""Basic Tests fuer DF-COMMUNICATION-SENDGRID-ADAPTER [CRUX-MK].

Per env-var-gated-real-integration-default.md Pflicht-Tests:
1. Default-Mock-Test
2. ENV-True + Test-Key → real-test
3. ENV-True + Live-Key ohne PHRONESIS → mock-fallback (Q_0-Schutz)
4. ENV-True + Live-Key + PHRONESIS → real-api
5. Email-Validation (RFC5322)
6. Subject-Length-Validation (255)
7. Body-Size-Validation (1MB)
8. Format-Whitelist (plain/html)
9. Tenant-ID-Pflicht
10. Template-ID Support
11. Audit-Record-Format
"""
from __future__ import annotations

import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.adapter import (
    ALLOWED_FORMATS,
    MAX_SUBJECT_LENGTH,
    MAX_BODY_BYTES,
    EmailResult,
    mock_send_email,
    real_send_email,
    dispatch_send_email,
    to_audit_record,
    _is_valid_email,
)


def _clear_env(monkeypatch):
    monkeypatch.delenv("DF_SENDGRID_REAL_ENABLED", raising=False)
    monkeypatch.delenv("SENDGRID_API_KEY", raising=False)
    monkeypatch.delenv("PHRONESIS_TICKET", raising=False)


def test_default_mock_no_env(monkeypatch):
    """Default-Mock: keine ENV-Var → mock_send_email."""
    _clear_env(monkeypatch)
    result = dispatch_send_email(
        to_email="guest@example.com",
        from_email="hotel@heylou.com",
        subject="Booking Confirmation",
        body="Welcome to HeyLou",
        tenant_id="hildesheim",
    )
    assert result.source == "mock"
    assert result.status == "mock"
    assert result.message_id.startswith("sg_mock_")
    assert result.body_format == "plain"


def test_env_true_test_mode(monkeypatch):
    """ENV=true + Test-Key → real-test."""
    _clear_env(monkeypatch)
    monkeypatch.setenv("DF_SENDGRID_REAL_ENABLED", "true")
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.test_dummy_api_key")
    result = dispatch_send_email(
        to_email="test@example.com",
        from_email="hotel@heylou.com",
        subject="Test Email",
        body="Test body",
        tenant_id="hildesheim",
    )
    assert result.source == "real-test"


def test_env_true_live_without_phronesis_fallback(monkeypatch):
    """ENV=true + Live-Key ohne PHRONESIS → mock-fallback (Q_0-Schutz)."""
    _clear_env(monkeypatch)
    monkeypatch.setenv("DF_SENDGRID_REAL_ENABLED", "true")
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.live_dangerous_real_key_dxxxxxxxxxxx")
    # NO PHRONESIS_TICKET
    result = dispatch_send_email(
        to_email="guest@example.com",
        from_email="hotel@heylou.com",
        subject="Live attempt",
        body="Body",
        tenant_id="hildesheim",
    )
    assert result.source == "mock", "Live ohne Phronesis MUSS mock-fallback (Q_0)"


def test_env_true_live_with_phronesis(monkeypatch):
    """ENV=true + Live-Key + PHRONESIS → real-api."""
    _clear_env(monkeypatch)
    monkeypatch.setenv("DF_SENDGRID_REAL_ENABLED", "true")
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.live_real_key_dxxxxxxxxxxx")
    monkeypatch.setenv("PHRONESIS_TICKET", "PT-2026-05-13-W53-003")
    result = dispatch_send_email(
        to_email="guest@example.com",
        from_email="hotel@heylou.com",
        subject="Live with phronesis",
        body="Body",
        tenant_id="hildesheim",
    )
    assert result.source == "real-api"
    assert result.phronesis_ticket == "PT-2026-05-13-W53-003"


def test_email_validation():
    """RFC5322 Email-Validation."""
    assert _is_valid_email("user@example.com") is True
    assert _is_valid_email("user.name+tag@sub.example.co.uk") is True
    assert _is_valid_email("invalid") is False
    assert _is_valid_email("missing@tld") is False
    assert _is_valid_email("@example.com") is False
    assert _is_valid_email("") is False


def test_validation_invalid_to_email():
    """Invalid to_email Reject."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "invalid-email", "hotel@heylou.com",
            "Subject", "Body", "t1",
        )


def test_validation_invalid_from_email():
    """Invalid from_email Reject."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "no-at-sign",
            "Subject", "Body", "t1",
        )


def test_validation_empty_subject():
    """Empty Subject Reject."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            "", "Body", "t1",
        )


def test_validation_subject_too_long():
    """Subject > 255 chars Reject."""
    long_subject = "x" * (MAX_SUBJECT_LENGTH + 1)
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            long_subject, "Body", "t1",
        )


def test_validation_empty_body():
    """Empty Body Reject."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            "Subject", "", "t1",
        )


def test_validation_body_too_large():
    """Body > 1MB Reject."""
    huge_body = "x" * (MAX_BODY_BYTES + 1)
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            "Subject", huge_body, "t1",
        )


def test_validation_format_whitelist():
    """body_format muss in (plain, html)."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            "Subject", "Body", "t1",
            body_format="markdown",  # nicht erlaubt
        )


def test_validation_missing_tenant_id():
    """tenant_id Pflicht (K11)."""
    with pytest.raises(AssertionError):
        mock_send_email(
            "guest@example.com", "hotel@heylou.com",
            "Subject", "Body", "",  # tenant_id empty
        )


def test_html_format():
    """HTML-Format erlaubt."""
    result = mock_send_email(
        "guest@example.com", "hotel@heylou.com",
        "HTML Subject", "<h1>Welcome</h1>", "hildesheim",
        body_format="html",
    )
    assert result.body_format == "html"


def test_template_id_support():
    """Template-ID-Support."""
    result = mock_send_email(
        "guest@example.com", "hotel@heylou.com",
        "Templated", "Body", "hildesheim",
        template_id="d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    )
    assert result.template_id == "d-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


def test_audit_record_format():
    """Audit-Record Pflicht-Felder."""
    result = mock_send_email(
        "guest@example.com", "hotel@heylou.com",
        "Audit Test", "Body", "tenant_aud",
    )
    rec = to_audit_record(result)
    required = {"ts", "df", "message_id", "tenant_id", "to_email", "from_email",
                "subject", "body_format", "template_id", "status", "source"}
    assert required <= set(rec.keys())
    assert rec["df"] == "DF-COMMUNICATION-SENDGRID-ADAPTER"
