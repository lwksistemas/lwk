"""Rate limit público usa contagem atômica."""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from clinica_beleza.throttles import check_rate_limit


class CheckRateLimitAtomicoTest(SimpleTestCase):
    @patch("django.core.cache.cache")
    def test_usa_add_e_incr(self, cache):
        cache.add.return_value = True
        cache.incr.return_value = 1
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "203.0.113.10"}
        self.assertTrue(check_rate_limit(request, "public_foto", "10/min"))
        cache.add.assert_called_once()
        cache.incr.assert_called_once()
        self.assertFalse(cache.set.called)

    @patch("django.core.cache.cache")
    def test_estoura_quando_passa_do_teto(self, cache):
        cache.add.return_value = True
        cache.incr.return_value = 11
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "203.0.113.10"}
        self.assertFalse(check_rate_limit(request, "public_foto", "10/min"))
