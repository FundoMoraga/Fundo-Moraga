"""
Scheduler simple para enviar recordatorios de reservas por email.
Se ejecuta en segundo plano y consulta Cosmos DB cada cierto intervalo.
"""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Optional

import config
from cosmos_client import get_conversation_store
from resend_client import get_resend_client

_scheduler_thread: Optional[threading.Thread] = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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
