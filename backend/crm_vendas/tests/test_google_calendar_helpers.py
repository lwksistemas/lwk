"""Testes de helpers do Google Calendar (parse de eventos e normalização de token)."""
from datetime import datetime, timezone as dt_timezone

from django.test import SimpleTestCase
from django.utils import timezone

from crm_vendas.google_calendar_helpers import (
    SYNC_DIRECTION_BOTH,
    SYNC_DIRECTION_PULL,
    SYNC_DIRECTION_PUSH_ONLY,
    VALID_SYNC_DIRECTIONS,
    normalize_token_expiry,
    parse_google_event_start,
)


class GoogleCalendarHelpersTest(SimpleTestCase):
    def test_parse_event_start_datetime(self):
        ev = {'start': {'dateTime': '2026-06-15T14:30:00+00:00'}}
        dt = parse_google_event_start(ev)
        self.assertIsNotNone(dt)
        self.assertTrue(timezone.is_aware(dt))

    def test_parse_event_start_all_day(self):
        ev = {'start': {'date': '2026-06-15'}}
        dt = parse_google_event_start(ev)
        self.assertIsNotNone(dt)
        self.assertEqual(dt.hour, 9)

    def test_parse_event_start_vazio(self):
        self.assertIsNone(parse_google_event_start({}))
        self.assertIsNone(parse_google_event_start({'start': {}}))

    def test_normalize_token_expiry_naive(self):
        naive = datetime(2026, 6, 1, 12, 0, 0)
        aware = normalize_token_expiry(naive)
        self.assertTrue(timezone.is_aware(aware))
        self.assertEqual(aware.tzinfo, dt_timezone.utc)

    def test_valid_sync_directions(self):
        self.assertIn(SYNC_DIRECTION_PUSH_ONLY, VALID_SYNC_DIRECTIONS)
        self.assertIn(SYNC_DIRECTION_PULL, VALID_SYNC_DIRECTIONS)
        self.assertIn(SYNC_DIRECTION_BOTH, VALID_SYNC_DIRECTIONS)
