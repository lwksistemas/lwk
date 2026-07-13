"""Testes unitários para paginate_queryset."""
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from clinica_beleza.pagination import paginate_queryset


class FakeQuerySet(list):
    """QuerySet mínimo para testes de paginação."""

    def count(self):
        return len(self)


class PaginationTests(SimpleTestCase):
    def _request(self, page=None, page_size=None):
        request = MagicMock()
        request.query_params.get.side_effect = lambda key, default=None: {
            "page": page,
            "page_size": page_size,
        }.get(key, default)
        return request

    def test_sem_page_retorna_lista_completa(self):
        qs = FakeQuerySet([{"id": 1}, {"id": 2}])
        response = paginate_queryset(
            qs,
            self._request(),
            to_representation=lambda item: {"id": item["id"], "label": f'#{item["id"]}'},
        )
        self.assertEqual(
            response.data,
            [{"id": 1, "label": "#1"}, {"id": 2, "label": "#2"}],
        )

    def test_com_page_retorna_envelope_paginado(self):
        items = [{"id": i} for i in range(1, 6)]
        qs = FakeQuerySet(items)
        response = paginate_queryset(
            qs,
            self._request(page="2", page_size="2"),
            to_representation=lambda item: item,
        )
        self.assertEqual(response.data["count"], 5)
        self.assertEqual(response.data["page"], 2)
        self.assertEqual(response.data["page_size"], 2)
        self.assertEqual(response.data["total_pages"], 3)
        self.assertEqual(response.data["results"], [{"id": 3}, {"id": 4}])
