# DF-COMMUNICATION-SENDGRID-ADAPTER [CRUX-MK]

**Welle-53 Real-API-Wave-1 Top-5-Priority Foundation-DF**
**Version:** 0.1.0-SKELETON
**Status:** SKELETON-CONDITIONAL
**Domain:** communication / transactional-email

## Scope

Real-API-Adapter fuer SendGrid Transactional Email API.
ENV-Var-Gated Default-Disabled. **KEIN Live-Send ohne PHRONESIS_TICKET** (Q_0-Schutz).
Test-Keys (SG.test_*) erlaubt ohne Phronesis fuer Dev/Sandbox.

## Operations

- `send_email`: POST /v3/mail/send
- RFC5322-Email-Format-Validation (Pflicht)
- Subject-Length-Limit (255 char)
- Body-Size-Limit (1MB)
- Format: plain | html (Whitelist)
- Template-Support via template_id

## Real-API-Activation-Workflow

1. **SendGrid-Console:** API-Key + Sender-Verification (Single-Sender oder Domain-Auth)
2. **Free-Tier:** 100 emails/day forever
3. **Phronesis-Approval** (nur Live-Mode)
4. **ENV-Vars setzen:**
   ```bash
   export DF_SENDGRID_REAL_ENABLED=true
   export SENDGRID_API_KEY=SG.xxxx...
   export PHRONESIS_TICKET=PT-2026-05-13-W53-003  # nur Live-Mode
   ```
5. **Sandbox-Mode:** mail_settings.sandbox_mode=true erlaubt fuer Dev

## Strict-Conditions-Konformitaet

- KEIN Live-Send ohne PHRONESIS_TICKET (Q_0-Schutz)
- RFC5322-Email-Format Pflicht (K12 non-LLM-validation)
- Subject-Length 255 char Pflicht
- Body-Size 1MB Hard-Cap
- Format-Whitelist [plain, html]
- Tenant-Isolation Pflicht (K11, hotel_id)
- DSGVO: Email-Adressen + Subject klartext OK, kein PII-Body im Audit

## CRUX-Bindung

- **K_0:** indirekt (Review-Request-Pipeline -> Direct-Booking-Lift)
- **Q_0:** Gast-Privacy via RFC5322-Validation + Tenant-Isolation
- **W_0:** Hotel-Front-Desk-Email-Zeit reduziert
- **L_Martin:** Live-Mode explicit Phronesis-Trigger

## rho-Schaetzung

- **Annual:** ~60k EUR (Booking-Confirmation + Pre-Stay + Post-Stay Review-Request)
- **Cost:** Free-Tier 100/day, dann ~$14.95/Mo fuer 40k emails
- **Lambda:** ~1000/Mo = im Free-Tier
- **Validation:** unvalidated bis Pilot 30+ Tage

## Tests

```bash
cd ~/Projects/dark-factories/df-communication-sendgrid-adapter
python -m pytest tests/ -v
```

15 Pflicht-Tests:
1. Default-Mock (no ENV) → mock
2. ENV-True + Test-Key → real-test
3. ENV-True + Live-Key ohne PHRONESIS → mock-fallback
4. ENV-True + Live-Key + PHRONESIS → real-api
5. RFC5322 Email-Validation
6. Invalid to_email Reject
7. Invalid from_email Reject
8. Empty Subject Reject
9. Subject > 255 chars Reject
10. Empty Body Reject
11. Body > 1MB Reject
12. Format-Whitelist
13. Tenant-ID Pflicht
14. HTML-Format erlaubt
15. Template-ID Support
16. Audit-Record-Format

## Promotion-Pfad

- v0.1.0-SKELETON (jetzt): Mock + RFC5322-Validation + Skeleton-Stub
- v0.2.0 (Welle-54): Cross-LLM-Wargame + Real-HTTP-Implementation
- v0.3.0 (Welle-55+): SendGrid-Sandbox-Pilot 30 Tage
- v1.0.0: PRODUCTION-READY-CONDITIONAL (Live-Pilot Year-1)

## Beziehung zu anderen Rules+Skills

- **Verstaerkt** `rules/env-var-gated-real-integration-default.md`
- **Verstaerkt** `rules/df-akzeptanz-kriterien.md` K11-K16 + LC1-LC5
- **Komplementaer zu** `df-pms-opera-adapter` (Booking-Confirmation-Pipeline)
- **Komplementaer zu** `df-communication-twilio-adapter` (Multi-Channel: SMS + Email)
- **Komplementaer zu** `df-reviews-google-adapter` (Post-Stay-Review-Request-Pipeline)

[CRUX-MK]
