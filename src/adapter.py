"""DF-COMMUNICATION-SENDGRID-ADAPTER Engine [CRUX-MK].

Welle-53 Real-API-Wave-1 Top-5-Priority. SendGrid Transactional Email API.

ENV-Var-gated Default-Disabled. Mock-Fallback bei Real-Mode-Disabled.

Pre/Post-Conditions:
- Pre: to_email (RFC5322), from_email (RFC5322), subject (1-255), body (1-1MB), tenant_id (str)
- Post: EmailResult mit source ("mock"|"real-api"|"real-test"), message_id, status
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# Constants
# Simplified RFC5322 regex (does not cover all edge-cases, but practical)
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
MAX_SUBJECT_LENGTH = 255
MAX_BODY_BYTES = 1_000_000  # 1MB Hard-Cap per SendGrid Policy
ALLOWED_FORMATS = ("plain", "html")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class EmailResult:
    """Pflicht-Felder per env-var-gated-real-integration-default.md Property-3."""
    message_id: str
    status: str               # "queued"|"sent"|"delivered"|"bounced"|"mock"
    to_email: str
    from_email: str
    subject: str
    body_format: str          # "plain"|"html"
    tenant_id: str
    template_id: Optional[str]
    source: str               # "mock"|"real-api"|"real-test"
    iso_timestamp: str
    phronesis_ticket: Optional[str] = None
    raw_response: dict = field(default_factory=dict)


def _is_valid_email(email: str) -> bool:
    """RFC5322 simplified validation."""
    if not email or len(email) > 320:  # RFC5321 SMTP limit
        return False
    return bool(EMAIL_REGEX.match(email))


def _validate_email_input(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    tenant_id: str,
    body_format: str,
) -> None:
    """Pre-Conditions Validation (K11+K12)."""
    assert _is_valid_email(to_email), f"to_email invalid RFC5322: {to_email}"
    assert _is_valid_email(from_email), f"from_email invalid RFC5322: {from_email}"
    assert subject, "subject required"
    assert len(subject) <= MAX_SUBJECT_LENGTH, \
        f"subject too long [{len(subject)} > {MAX_SUBJECT_LENGTH}]"
    assert body, "body required"
    assert len(body.encode("utf-8")) <= MAX_BODY_BYTES, \
        f"body exceeds 1MB limit"
    assert tenant_id, "tenant_id required (K11 Tenant-Isolation)"
    assert body_format in ALLOWED_FORMATS, \
        f"body_format must be in {ALLOWED_FORMATS}: {body_format}"


def mock_send_email(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    tenant_id: str,
    body_format: str = "plain",
    template_id: Optional[str] = None,
) -> EmailResult:
    """Mock-Email-Send (Default ohne Real-API).

    Pre: validation passing
    Post: EmailResult mit source='mock', status='mock', deterministic Mock-Message-ID
    """
    _validate_email_input(to_email, from_email, subject, body, tenant_id, body_format)
    mock_id = f"sg_mock_{tenant_id[:8]}_{to_email.split('@')[0][:8]}"
    return EmailResult(
        message_id=mock_id,
        status="mock",
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        body_format=body_format,
        tenant_id=tenant_id,
        template_id=template_id,
        source="mock",
        iso_timestamp=iso_now(),
        phronesis_ticket=None,
        raw_response={"mock": True},
    )


def real_send_email(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    tenant_id: str,
    body_format: str = "plain",
    template_id: Optional[str] = None,
    phronesis_ticket: Optional[str] = None,
) -> EmailResult:
    """Real-Email-Send via SendGrid API.

    Pre: SENDGRID_API_KEY env-var gesetzt; PHRONESIS_TICKET fuer Live-Mode
    Post: EmailResult mit source='real-api'|'real-test'; fallback zu mock bei Auth-Fehler.

    NOTE: Skeleton-Implementation. Echte HTTP-Calls in Welle-54+.
    """
    _validate_email_input(to_email, from_email, subject, body, tenant_id, body_format)
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        return mock_send_email(to_email, from_email, subject, body, tenant_id, body_format, template_id)

    # SendGrid Test/Sandbox-Mode: Convention SG.test_* oder mail_settings.sandbox_mode=true
    is_test_mode = "test" in api_key.lower()
    is_live_mode = not is_test_mode

    if is_live_mode:
        if not phronesis_ticket:
            phronesis_ticket = os.environ.get("PHRONESIS_TICKET")
        if not phronesis_ticket:
            # Q_0-Schutz: kein Live-Send ohne Phronesis
            return mock_send_email(to_email, from_email, subject, body, tenant_id, body_format, template_id)

    # Skeleton: Stub fuer SendGrid-HTTP-Call
    # Welle-54+ vervollstaendigt mit `requests.post("https://api.sendgrid.com/v3/mail/send", headers={"Authorization": f"Bearer {api_key}"})`
    source = "real-api" if is_live_mode else "real-test"
    return EmailResult(
        message_id=f"sg_{source.replace('-', '_')}_{tenant_id[:8]}_{to_email.split('@')[0][:8]}",
        status="queued",  # Skeleton default-state
        to_email=to_email,
        from_email=from_email,
        subject=subject,
        body_format=body_format,
        tenant_id=tenant_id,
        template_id=template_id,
        source=source,
        iso_timestamp=iso_now(),
        phronesis_ticket=phronesis_ticket,
        raw_response={"skeleton": True, "live_mode": is_live_mode},
    )


def dispatch_send_email(
    to_email: str,
    from_email: str,
    subject: str,
    body: str,
    tenant_id: str,
    body_format: str = "plain",
    template_id: Optional[str] = None,
) -> EmailResult:
    """Dispatcher mit ENV-Var-Gating (Default-Disabled).

    Default: mock_send_email.
    Real-Mode: nur wenn DF_SENDGRID_REAL_ENABLED='true' UND SENDGRID_API_KEY gesetzt.
    """
    real_enabled = os.environ.get("DF_SENDGRID_REAL_ENABLED", "").lower() == "true"
    if real_enabled:
        return real_send_email(to_email, from_email, subject, body, tenant_id, body_format, template_id)
    return mock_send_email(to_email, from_email, subject, body, tenant_id, body_format, template_id)


def to_audit_record(result: EmailResult) -> dict:
    """Serialize EmailResult fuer audit-log.jsonl. Email-Adressen + Subject klartext (kein PII-Body)."""
    return {
        "ts": result.iso_timestamp,
        "df": "DF-COMMUNICATION-SENDGRID-ADAPTER",
        "message_id": result.message_id,
        "tenant_id": result.tenant_id,
        "to_email": result.to_email,
        "from_email": result.from_email,
        "subject": result.subject,
        "body_format": result.body_format,
        "template_id": result.template_id or "none",
        "status": result.status,
        "source": result.source,
        "phronesis_ticket": result.phronesis_ticket or "none",
    }
