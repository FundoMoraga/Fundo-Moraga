"""
Cliente simple para verificar si llegó el correo de transferencia en una casilla (Gmail vía IMAP).

Requiere variables:
- PAYMENT_INBOX_USER (ej: contacto@gmail.com)
- PAYMENT_INBOX_PASSWORD (App Password recomendado)
Opcionales:
- PAYMENT_INBOX_HOST (default: imap.gmail.com)
- PAYMENT_INBOX_FOLDER (default: INBOX)
- PAYMENT_EMAIL_FROM_CONTAINS (default: "Banco")
- PAYMENT_EMAIL_SUBJECT_CONTAINS (default: "transfer")
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import email
import imaplib

import config


@dataclass(frozen=True)
class PaymentCheckResult:
    found: bool
    message_id: Optional[str] = None
    subject: Optional[str] = None
    from_email: Optional[str] = None
    received_at: Optional[str] = None


class PaymentInboxClient:
    def __init__(self):
        self.host = config.PAYMENT_INBOX_HOST
        self.user = config.PAYMENT_INBOX_USER
        self.password = config.PAYMENT_INBOX_PASSWORD
        self.folder = config.PAYMENT_INBOX_FOLDER
        self.from_contains = (config.PAYMENT_EMAIL_FROM_CONTAINS or "").lower()
        self.subject_contains = (config.PAYMENT_EMAIL_SUBJECT_CONTAINS or "").lower()

    def is_configured(self) -> bool:
        return bool(self.user and self.password and self.host and self.folder)

    def find_payment_email(self, since_iso: str, max_scan: int = 20) -> PaymentCheckResult:
        """
        Busca un correo de pago recibido desde `since_iso` (ISO8601).
        """
        if not self.is_configured():
            raise RuntimeError("PAYMENT_INBOX_* no está configurado")

        try:
            since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
        except Exception:
            since_dt = datetime.now(timezone.utc)

        with imaplib.IMAP4_SSL(self.host) as imap:
            imap.login(self.user, self.password)
            imap.select(self.folder)

            # IMAP SINCE usa solo fecha (día), así que filtramos fino por header Date luego.
            since_date = since_dt.strftime("%d-%b-%Y")
            status, data = imap.search(None, "SINCE", since_date)
            if status != "OK" or not data or not data[0]:
                return PaymentCheckResult(found=False)

            ids = data[0].split()
            # Revisar desde los más recientes
            for msg_id in reversed(ids[-max_scan:]):
                status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
                if status != "OK" or not msg_data:
                    continue

                raw = msg_data[0][1]
                msg = email.message_from_bytes(raw)
                subject = (msg.get("Subject") or "").strip()
                from_header = (msg.get("From") or "").strip()
                date_header = (msg.get("Date") or "").strip()

                subject_l = subject.lower()
                from_l = from_header.lower()

                if self.from_contains and self.from_contains not in from_l:
                    continue
                if self.subject_contains and self.subject_contains not in subject_l:
                    continue

                received_iso = None
                try:
                    parsed_date = email.utils.parsedate_to_datetime(date_header)
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    if parsed_date < since_dt:
                        continue
                    received_iso = parsed_date.astimezone(timezone.utc).isoformat()
                except Exception:
                    # Si no podemos parsear Date, igualmente contamos como "encontrado"
                    received_iso = None

                return PaymentCheckResult(
                    found=True,
                    message_id=msg.get("Message-ID"),
                    subject=subject,
                    from_email=from_header,
                    received_at=received_iso,
                )

        return PaymentCheckResult(found=False)


_payment_inbox_client = None


def get_payment_inbox_client() -> PaymentInboxClient:
    global _payment_inbox_client
    if _payment_inbox_client is None:
        _payment_inbox_client = PaymentInboxClient()
    return _payment_inbox_client

