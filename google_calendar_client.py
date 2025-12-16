"""
Cliente de Google Calendar para crear eventos de agendamiento.

Uso:
- Configurar `GOOGLE_CALENDAR_ID`
- Proveer credenciales de Service Account vía `GOOGLE_SERVICE_ACCOUNT_JSON` (contenido JSON)
  o `GOOGLE_SERVICE_ACCOUNT_FILE` (ruta a archivo JSON).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import config


@dataclass(frozen=True)
class CalendarEventRequest:
    summary: str
    description: str
    start_iso: str  # RFC3339
    end_iso: str  # RFC3339
    timezone: str
    attendees: List[str]


class GoogleCalendarClient:
    def __init__(self):
        self.calendar_id = config.GOOGLE_CALENDAR_ID
        self.timezone = config.GOOGLE_CALENDAR_TIMEZONE
        self.send_updates = config.GOOGLE_CALENDAR_SEND_UPDATES or "all"

    def _load_credentials(self):
        try:
            from google.oauth2 import service_account
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Faltan dependencias de Google. Agrega `google-api-python-client` y `google-auth`."
            ) from e

        if config.GOOGLE_SERVICE_ACCOUNT_JSON:
            info = json.loads(config.GOOGLE_SERVICE_ACCOUNT_JSON)
            return service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )

        if config.GOOGLE_SERVICE_ACCOUNT_FILE:
            return service_account.Credentials.from_service_account_file(
                config.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=["https://www.googleapis.com/auth/calendar"],
            )

        raise RuntimeError("No hay credenciales: GOOGLE_SERVICE_ACCOUNT_JSON/GOOGLE_SERVICE_ACCOUNT_FILE")

    def create_event(self, req: CalendarEventRequest) -> Dict:
        if not self.calendar_id:
            raise RuntimeError("GOOGLE_CALENDAR_ID no está configurado")

        try:
            from googleapiclient.discovery import build
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Faltan dependencias de Google. Agrega `google-api-python-client`."
            ) from e

        credentials = self._load_credentials()
        service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

        event = {
            "summary": req.summary,
            "description": req.description,
            "start": {"dateTime": req.start_iso, "timeZone": req.timezone},
            "end": {"dateTime": req.end_iso, "timeZone": req.timezone},
            "attendees": [{"email": email} for email in req.attendees],
        }

        created = (
            service.events()
            .insert(calendarId=self.calendar_id, body=event, sendUpdates=self.send_updates)
            .execute()
        )
        return created


_google_calendar_client = None


def get_google_calendar_client() -> GoogleCalendarClient:
    global _google_calendar_client
    if _google_calendar_client is None:
        _google_calendar_client = GoogleCalendarClient()
    return _google_calendar_client

