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


def queryset_excluir_integracoes(qs):
    """Remove webhooks e integrações automáticas do histórico exibido/rankeado."""
    return qs.exclude(
        Q(recurso__in=RECURSOS_INTEGRACAO)
        | Q(url__contains='/whatsapp/evolution/webhook')
        | Q(usuario_email__endswith='@webhook')
        | Q(usuario_email='api@asaas.sistema')
        | Q(usuario_email='bot@externo')
        | Q(usuario_email='nao-autenticado@sistema')
    )


def url_ignorar_auditoria(path: str) -> bool:
    p = path or ''
    return any(p.startswith(prefix) for prefix in URLS_IGNORAR_AUDITORIA)
