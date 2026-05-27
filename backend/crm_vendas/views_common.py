"""Utilitários compartilhados entre ViewSets do CRM."""
from rest_framework.pagination import PageNumberPagination


class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
