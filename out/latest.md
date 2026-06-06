# df-communication-sendgrid-adapter — Output [CRUX-MK]
*Autonom aktiviert 2026-06-05T13:01:56.580127+00:00 | ollama-local/qwen2.5:14b-instruct*

# DF-COMMUNICATION-SENDGRID-ADAPTER [CRUX-MK]

## Ziel

Dieser Dark Factory Adapter integriert SendGrids Transactional Email API in
in das Hotelmanagement System, um sicherzustellen, dass alle E-Mail-Kommuni
E-Mail-Kommunikationen für Buchungen und andere Transaktionen ordnungsgemäß
ordnungsgemäß versendet werden. Die Implementierung ist standardmäßig deakt
deaktiviert und erfordert eine spezielle Genehmigung für den Live-Betrieb.

## API Endpunkte

- **send_email**: POST /v3/mail/send
  - Diese Funktion sendet E-Mails an die angegebenen Empfänger basierend au
auf dem SendGrid Transactional Email API.
  
## Validierung und Limitierungen

### Formatvalidierung
- RFC5322: Alle E-Mail-Adressen und Headerfelder müssen das RFC5322 Format 
erfüllen.
- Betreffzeile: Länge maximal 255 Zeichen.
- Inhalt (Body): Größe maximal 1 MB.
- Formate: Nur plain oder html sind zulässig.

### Sandbox-Modus
Um während der Entwicklung und Tests sicherzustellen, dass keine E-Mails an
an echte Empfänger gesendet werden, kann ein Sandbox-Modus aktiviert werden
werden. Dies ist durch die Setzung von `mail_settings.sandbox_mode=true` mö
möglich.

## Aktivierung des Live-Betriebs

Für den Betrieb im Live-Modus sind mehrere Schritte notwendig:

1. **SendGrid-Konsole**: Ein API-Schlüssel wird generiert und der Sender mu
muss verifiziert werden.
2. **Free-Tier**: Maximal 100 E-Mails pro Tag kostenlos, dann können Kosten
Kosten für zusätzliche Mails entstehen.
3. **Phronesis-Approval** (nur Live-Modus): Ein spezieller Phronesis Ticket
Ticket ist erforderlich.
4. **Umgebungsvariablen setzen:**
   ```bash
   export DF_SENDGRID_REAL_ENABLED=true
   export SENDGRID_API_KEY=SG.xxxx...
   export PHRONESIS_TICKET=PT-2026-05-13-W53-003  # nur Live-Modus
   ```
5. **Sandbox-Modus**: Für Entwicklungszwecke ist der Sandbox-Modus aktivier
aktivierbar.

## Sicherheitsaspekte

### Datenschutz und Isolation
- Keine E-Mails ohne Phronesis-Ticket im Live-Modus.
- PII-Datenschutz: Die Body-Inhalte dürfen keine personenbezogene Informati
Informationen (PII) enthalten, welche im Audit vermerkt sind. Betreffzeilen
Betreffzeilen und E-Mailadressen können klar textig übermittelt werden.

### Rho-Schätzung
- **Jährliche Nutzung:** ~60k EUR für Booking-Bestätigungen, Pre-Stay Kommu
Kommunikation sowie Post-Stay Review-Anfragen.
- **Kosten:** Im Free-Tier sind 100 E-Mails pro Tag möglich. Über diese Gre
Grenze hinweg beträgt der Preis etwa $14.95/Monat für 40k E-Mails.
- **Lambda:** Bei durchschnittlich ~1000 E-Mails pro Monat bleibt die Anwen
Anwendung im Free-Tier.
- **Validierung:** Die Validierung wird erst nach einem Pilotprojekt von mi
mindestens 30 Tagen aktiv.

## Tests

```bash
cd ~/Projects/dark-factories/df-communication-sendgrid-adapter
python -m pytest tests/ -v
```

### Testfälle (15 Pflichttests)
1. Default-Mock: Ohne Umgebungsvariablen wird ein Mock ausgeführt.
2. ENV-True + Test-Key: Bei aktivierter Umgebung und Test-Schlüssel wird ei
eine echte Überprüfung durchgeführt.
3. ENV-True + Live-Key ohne PHRONESIS: Fällt auf Mock-Fallback zurück, wenn
wenn kein Phronesis-Ticket vorliegt.
4. ENV-True + Live-Key + PHRONESIS: Sendet die E-Mail an den SendGrid API.
5. RFC5322 Email-Validation
6. Verwerfung bei ungültiger Empfänger-E-Mail-Adresse
7. Verwerfung bei ungültigem Absender
8. Ablehnung eines leeren Betreffs
9. Ablehnung von Betreff-Zeichen über 255 Zeichen
10. Ablehnung leerer Inhalte
11. Ablehnung größer als 1MB Inhalte
12. Whitelist der Formate (nur plain oder html)
13. Pflicht von Tenant-ID zur Isolierung
14. Abstimmung mit DSGVO Richtlinien für E-Mail-Kommunikation