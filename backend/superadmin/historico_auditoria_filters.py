"""Filtros compartilhados para auditoria / histórico global."""
from django.db.models import Q

# URLs que não representam ação humana (webhooks, bots)
URLS_IGNORAR_AUDITORIA = (
    '/api/whatsapp/evolution/webhook/',
    '/api/asaas/',
)

RECURSOS_INTEGRACAO = (
    'Webhook Evolution',
)

NOMES_USUARIO_IGNORAR_RANKING = (
    'Anônimo',
    '',
)

EMAILS_USUARIO_IGNORAR_RANKING = (
    'nao-autenticado@sistema',
    'bot@externo',
    'api@asaas.sistema',
    'Anônimo',
)


def _slugs_lojas_ativas():
    from superadmin.models import Loja

    return set(Loja.objects.using('default').values_list('slug', flat=True))


def _ids_lojas_ativas():
    from superadmin.models import Loja

    return set(Loja.objects.using('default').values_list('id', flat=True))


def queryset_excluir_integracoes(qs):
    """Remove webhooks e integrações automáticas do histórico exibido/rankeado."""
    return qs.exclude(
        Q(recurso__in=RECURSOS_INTEGRACAO)
        | Q(url__contains='/whatsapp/evolution/webhook')
        | Q(usuario_email__endswith='@webhook')
        | Q(usuario_email__in=EMAILS_USUARIO_IGNORAR_RANKING)
        | Q(usuario_nome__in=NOMES_USUARIO_IGNORAR_RANKING)
    )


def queryset_excluir_lojas_removidas(qs):
    """Remove histórico de lojas que não existem mais no cadastro."""
    slugs_ativos = _slugs_lojas_ativas()
    ids_ativos = _ids_lojas_ativas()

    # Slug preenchido de loja excluída (FK já foi anulada)
    qs = qs.exclude(Q(loja_slug__gt='') & ~Q(loja_slug__in=slugs_ativos))

    # FK órfã (não deveria ocorrer, mas protege ranking)
    if ids_ativos:
        qs = qs.exclude(Q(loja_id__isnull=False) & ~Q(loja_id__in=ids_ativos))
    else:
        qs = qs.exclude(loja_id__isnull=False)

    return qs


def queryset_auditoria_visivel(qs, *, incluir_integracoes=False, incluir_lojas_removidas=False):
    if not incluir_integracoes:
        qs = queryset_excluir_integracoes(qs)
    if not incluir_lojas_removidas:
        qs = queryset_excluir_lojas_removidas(qs)
    return qs


def queryset_ranking_lojas(qs):
    """Ranking/gráficos por loja: só lojas ativas com FK válida."""
    ids_ativos = _ids_lojas_ativas()
    qs = queryset_auditoria_visivel(qs)
    if not ids_ativos:
        return qs.none()
    return qs.filter(loja_id__in=ids_ativos)


def queryset_ranking_usuarios(qs):
    """Ranking de usuários humanos (sem bots, anônimos ou integrações)."""
    return queryset_auditoria_visivel(qs).exclude(
        Q(usuario_nome__in=NOMES_USUARIO_IGNORAR_RANKING)
        | Q(usuario_email__in=EMAILS_USUARIO_IGNORAR_RANKING)
        | Q(usuario_email__endswith='@webhook')
        | Q(usuario_nome__startswith='Paciente:')
        | Q(usuario_nome__startswith='Cliente:')
        | Q(usuario_nome__startswith='WhatsApp Evolution')
    )


def url_ignorar_auditoria(path: str) -> bool:
    p = path or ''
    return any(p.startswith(prefix) for prefix in URLS_IGNORAR_AUDITORIA)
