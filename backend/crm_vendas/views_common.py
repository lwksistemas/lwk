"""Utilitários compartilhados entre ViewSets do CRM."""
import logging
import re

from rest_framework.pagination import PageNumberPagination

from tenants.middleware import ensure_loja_context, get_current_loja_id

logger = logging.getLogger(__name__)


class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 500


def aplicar_cache_control_sem_store(response):
    """Evita cache de listagens CRM no navegador (dados por loja/vendedor)."""
    response["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def filtrar_queryset_por_query_params(queryset, request, param_field_map: dict[str, str]):
    """Aplica filtros opcionais ?param=valor como queryset.filter(field=valor)."""
    for param, field in param_field_map.items():
        value = request.query_params.get(param)
        if value:
            queryset = queryset.filter(**{field: value})
    return queryset


def filtrar_queryset_busca_texto(queryset, request, q_filter_builder):
    """Filtra ?q=termo (mín. 2 caracteres) usando builder que recebe (term, term_digits).
    """
    term = (request.query_params.get("q") or "").strip()
    if len(term) < 2:
        return queryset
    term_digits = "".join(c for c in term if c.isdigit())
    return queryset.filter(q_filter_builder(term, term_digits))


def _build_q_lead_busca(term: str, term_digits: str):
    from django.db.models import Q

    from core.text_search import q_icontains_sem_acento

    q_filter = (
        q_icontains_sem_acento(term, "nome", "empresa", "email")
        | Q(telefone__icontains=term)
        | Q(cpf_cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        q_filter |= Q(cpf_cnpj__icontains=term_digits)
    return q_filter


def _build_q_conta_busca(term: str, term_digits: str):
    from django.db.models import Q

    from core.text_search import q_icontains_sem_acento

    q_filter = (
        q_icontains_sem_acento(term, "nome", "razao_social", "email", "segmento")
        | Q(telefone__icontains=term)
        | Q(cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        q_filter |= Q(cnpj__icontains=term_digits)
    return q_filter


def filtrar_leads_busca_lista(queryset, request):
    return filtrar_queryset_busca_texto(queryset, request, _build_q_lead_busca)


def filtrar_contas_busca_lista(queryset, request):
    return filtrar_queryset_busca_texto(queryset, request, _build_q_conta_busca)


def _documento_digitos_match(stored: str | None, documento: str) -> bool:
    a = re.sub(r"\D", "", stored or "")
    if not a:
        return False
    if a == documento:
        return True
    if len(a) in (11, 14) and len(documento) in (11, 14):
        pad = 14 if max(len(a), len(documento)) == 14 else 11
        return a.zfill(pad) == documento.zfill(pad)
    return False


def filtrar_queryset_por_documento(queryset, request, campo_documento: str):
    """Filtra ?documento= (CPF/CNPJ só dígitos) comparando o campo após remover formatação.
    Usado na emissão NFS-e para localizar tomador sem carregar toda a lista paginada.
    """
    documento = re.sub(r"\D", "", request.query_params.get("documento") or "")
    if not documento or len(documento) not in (11, 14):
        return queryset

    suffix = documento[-4:]
    candidatos = queryset.filter(**{f"{campo_documento}__icontains": suffix}).values("pk", campo_documento)
    matching_ids = [
        row["pk"]
        for row in candidatos
        if _documento_digitos_match(row.get(campo_documento), documento)
    ]
    if matching_ids:
        return queryset.filter(pk__in=matching_ids)

    # Fallback: varredura completa — limitada a 1000 para evitar full scan em lojas grandes
    matching_ids = [
        row["pk"]
        for row in queryset.exclude(**{f"{campo_documento}__isnull": True}).values("pk", campo_documento)[:1000]
        if _documento_digitos_match(row.get(campo_documento), documento)
    ]
    return queryset.filter(pk__in=matching_ids) if matching_ids else queryset.none()


def filtrar_leads_por_documento(queryset, request):
    """Filtra leads por ?documento= no cpf_cnpj do lead ou CNPJ da conta vinculada."""
    from django.db.models import Q

    documento = re.sub(r"\D", "", request.query_params.get("documento") or "")
    if not documento or len(documento) not in (11, 14):
        return queryset

    qs = queryset.select_related("conta")
    suffix = documento[-4:]
    candidatos = qs.filter(
        Q(cpf_cnpj__icontains=suffix) | Q(conta__cnpj__icontains=suffix),
    ).distinct()

    matching_ids: list[int] = []
    for lead in candidatos.iterator():
        if _documento_digitos_match(lead.cpf_cnpj, documento) or (lead.conta_id and lead.conta and _documento_digitos_match(lead.conta.cnpj, documento)):
            matching_ids.append(lead.pk)

    if matching_ids:
        return queryset.filter(pk__in=matching_ids)

    for lead in qs.iterator():
        if _documento_digitos_match(lead.cpf_cnpj, documento) or (lead.conta_id and lead.conta and _documento_digitos_match(lead.conta.cnpj, documento)):
            matching_ids.append(lead.pk)

    return queryset.filter(pk__in=matching_ids) if matching_ids else queryset.none()


class CRMNoCacheListMixin:
    """Mixin para list() sem cache HTTP (padrão cadastros CRM)."""

    def list(self, request, *args, **kwargs):
        return aplicar_cache_control_sem_store(super().list(request, *args, **kwargs))


def filtrar_ativo_query_param(queryset, request, param="ativo", field="ativo"):
    """Filtra ?ativo=true|false quando o parâmetro está presente."""
    ativo = request.query_params.get(param)
    if ativo is not None:
        return queryset.filter(**{field: ativo.lower() == "true"})
    return queryset


class LojaScopedCatalogMixin:
    """Catálogo por loja (CategoriaProdutoServico, ProdutoServico).
    perform_create com loja_id e queryset base filtrado por loja.
    """

    loja_catalog_model = None
    loja_catalog_label = "LojaScopedCatalogMixin"

    def _ensure_loja_context(self):
        if hasattr(self, "request") and self.request:
            ensure_loja_context(self.request)

    def perform_create(self, serializer):
        self._ensure_loja_context()
        loja_id = get_current_loja_id()
        if loja_id:
            serializer.save(loja_id=loja_id)
        else:
            serializer.save()

    def get_loja_catalog_base_qs(self):
        self._ensure_loja_context()
        loja_id = get_current_loja_id()
        if not loja_id:
            logger.warning("[%s] Acesso sem loja_id no contexto", self.loja_catalog_label)
            return self.loja_catalog_model.objects.none()
        return self.loja_catalog_model.objects.filter(loja_id=loja_id)
