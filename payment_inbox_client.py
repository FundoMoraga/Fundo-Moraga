"""
Cliente simple para verificar si llegó el correo de transferencia en una casilla (Gmail vía IMAP).
Requiere variables:
- PAYMENT_INBOX_USER (ej: contacto@gmail.com)
- PAYMENT_INBOX_PASSWORD (App Password recomendado)
Opcionales:
- PAYMENT_INBOX_HOST (default: imap.gmail.com)
- PAYMENT_INBOX_FOLDER (default: INBOX)
- PAYMENT_EMAIL_FROM_CONTAINS (default: "Banco")  # acepta múltiples keywords separadas por | o ,
- PAYMENT_EMAIL_SUBJECT_CONTAINS (default: "transferencia")  # acepta múltiples keywords separadas por | o ,
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List
import email
from email.header import decode_header
import imaplib
import re
import unicodedata

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
        self.max_scan = config.PAYMENT_INBOX_MAX_SCAN
        self.from_keywords = self._split_keywords(config.PAYMENT_EMAIL_FROM_CONTAINS)
        self.subject_keywords = self._split_keywords(config.PAYMENT_EMAIL_SUBJECT_CONTAINS)

    def _normalize_text(self, text: str) -> str:
        if not text:
            return ""
        lowered = text.lower()
        normalized = unicodedata.normalize("NFKD", lowered)
        return "".join(ch for ch in normalized if not unicodedata.combining(ch))

    def _decode_header_value(self, value: Optional[str]) -> str:
        if not value:
            return ""
        decoded_parts = []
        for part, enc in decode_header(value):
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(enc or "utf-8", errors="ignore"))
                except Exception:
                    decoded_parts.append(part.decode("utf-8", errors="ignore"))
            else:
                decoded_parts.append(str(part))
        return "".join(decoded_parts)

    def _split_keywords(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        parts = re.split(r"[|,]", raw)
        return [self._normalize_text(p.strip()) for p in parts if p and p.strip()]

    def _split_folders(self, raw: Optional[str]) -> List[str]:
        if not raw:
            return []
        parts = re.split(r"[|,]", raw)
        return [p.strip() for p in parts if p and p.strip()]

    def _folders_to_check(self) -> List[str]:
        folders = self._split_folders(self.folder) or ["INBOX"]
        fallback = []
        if len(folders) == 1 and folders[0].upper() == "INBOX":
            fallback = [
                "[Gmail]/All Mail",
                "[Google Mail]/All Mail",
                "[Gmail]/Todos",
                "[Gmail]/Todos los mensajes",
            ]
        # Dedup preservando orden
        seen = set()
        ordered: List[str] = []
        for f in folders + fallback:
            key = f.lower()
            if key in seen:
                continue
            seen.add(key)
            ordered.append(f)
        return ordered

    def is_configured(self) -> bool:
        return bool(self.user and self.password and self.host and self.folder)

    def find_payment_email(
        self, since_iso: str, max_scan: Optional[int] = None, expected_from: Optional[str] = None
    ) -> PaymentCheckResult:
        """
        Busca un correo de pago recibido desde `since_iso` (ISO8601).
        El match se cumple si el asunto contiene una keyword configurada
        o si el remitente contiene el email esperado/configurado.
        """
        if not self.is_configured():
            raise RuntimeError("PAYMENT_INBOX_* no está configurado")

        try:
            since_dt = datetime.fromisoformat(since_iso.replace("Z", "+00:00"))
        except Exception:
            since_dt = datetime.now(timezone.utc)

        if max_scan is None:
            max_scan = int(self.max_scan or 20)

        with imaplib.IMAP4_SSL(self.host) as imap:
            imap.login(self.user, self.password)

            # IMAP SINCE usa solo fecha (día), así que filtramos fino por header Date luego.
            since_date = since_dt.strftime("%d-%b-%Y")
            for folder in self._folders_to_check():
                status, _ = imap.select(folder)
                if status != "OK":
                    continue
                status, data = imap.search(None, "SINCE", since_date)
                if status != "OK" or not data or not data[0]:
                    continue

                ids = data[0].split()
                # Revisar desde los más recientes
                for msg_id in reversed(ids[-max_scan:]):
                    status, msg_data = imap.fetch(msg_id, "(RFC822.HEADER)")
                    if status != "OK" or not msg_data:
                        continue

                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    subject = self._decode_header_value(msg.get("Subject")).strip()
                    from_header = self._decode_header_value(msg.get("From")).strip()
                    date_header = (msg.get("Date") or "").strip()

                    subject_l = self._normalize_text(subject)
                    from_l = self._normalize_text(from_header)
                    expected_from_l = self._normalize_text((expected_from or "").strip())

                    subject_match = (
                        any(k in subject_l for k in self.subject_keywords) if self.subject_keywords else False
                    )
                    from_match = False
                    if expected_from_l:
                        from_match = expected_from_l in from_l
                    if not from_match and self.from_keywords:
                        from_match = any(k in from_l for k in self.from_keywords)

                    if not (subject_match or from_match):
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
