"""
Scheduler simple para enviar recordatorios de reservas por email.
Se ejecuta en segundo plano y consulta Cosmos DB cada cierto intervalo.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

import config
from cosmos_client import get_conversation_store
from resend_client import get_resend_client

_scheduler_thread: Optional[threading.Thread] = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _next_attempt_iso(attempts: int) -> str:
    base = max(1, config.PENDING_EMAIL_RETRY_MINUTES)
    cap = max(base, config.PENDING_EMAIL_RETRY_MAX_MINUTES)
    delay = min(cap, base * max(1, attempts + 1))
    return (datetime.now(timezone.utc) + timedelta(minutes=delay)).isoformat().replace("+00:00", "Z")


def _run_once() -> None:
    store = get_conversation_store()
    resend_client = get_resend_client()
    if not resend_client.is_configured():
        return

    now_iso = _utc_now_iso()
    reminders = store.fetch_due_reminders(now_iso=now_iso, limit=30)
    for reminder in reminders:
        metadata = reminder.get("metadata") or {}
        email = (metadata.get("email") or "").strip()
        booking = metadata.get("booking") or {}
        if not email:
            store.update_reminder_status(reminder, status="error", error="missing_email")
            continue

        send_result = resend_client.send_booking_reminder_to_user(
            to_email=email,
            full_name=booking.get("full_name") or "Cliente",
            visit_date=str(booking.get("visit_date") or ""),
            visit_day=str(booking.get("visit_day") or ""),
            arrival_time=str(booking.get("arrival_time") or ""),
            cars_count=int(booking.get("cars_count") or 0),
            motos_count=int(booking.get("motos_count") or 0),
            people_count=int(booking.get("people_count") or 0),
            price_clp=int(booking.get("price_clp") or 0),
        )

        if send_result.get("success"):
            store.update_reminder_status(reminder, status="sent")
        else:
            store.update_reminder_status(
                reminder, status="error", error=send_result.get("error") or "send_failed"
            )

    pending_emails = store.fetch_due_pending_emails(now_iso=now_iso, limit=30)
    for pending in pending_emails:
        metadata = pending.get("metadata") or {}
        email_type = metadata.get("email_type") or ""
        payload = metadata.get("payload") or {}
        attempts = int(metadata.get("attempts") or 0)

        if email_type == "booking_request":
            send_result = resend_client.send_booking_request(**payload)
        elif email_type == "booking_confirmation":
            send_result = resend_client.send_booking_confirmation_to_user(**payload)
        elif email_type == "lead_summary":
            send_result = resend_client.send_conversation_summary(**payload)
        elif email_type == "conversation_summary":
            send_result = resend_client.send_conversation_end_summary(**payload)
        elif email_type == "contact_sheet":
            send_result = resend_client.send_contact_sheet(**payload)
        else:
            send_result = {"success": False, "error": "unknown_email_type"}

        if send_result.get("success"):
            store.update_pending_email_status(pending, status="sent")
        else:
            store.update_pending_email_status(
                pending,
                status="pending",
                error=send_result.get("error") or "send_failed",
                next_attempt_at=_next_attempt_iso(attempts),
                attempts=attempts + 1,
            )


def _loop() -> None:
    while True:
        try:
            _run_once()
        except Exception as exc:
            print(f"❌ Error en scheduler de recordatorios: {exc}")
        time.sleep(config.REMINDER_POLL_SECONDS)


def start_reminder_scheduler() -> None:
    global _scheduler_thread
    if not config.REMINDER_SCHEDULER_ENABLED:
        return
    if _scheduler_thread and _scheduler_thread.is_alive():
        return
    _scheduler_thread = threading.Thread(target=_loop, daemon=True)
    _scheduler_thread.start()
