"""Bloqueio por inadimplência de assinatura (boleto da loja na LWK)."""
from __future__ import annotations

import logging
from datetime import date, timedelta

from django.utils import timezone

logger = logging.getLogger(__name__)

DAYS_TO_WARN_BOLETO = 10
DAYS_TO_WARN_UI = 5
DAYS_TO_BLOCK = 5


def dias_atraso_assinatura(loja) -> int:
    """Dias corridos após o vencimento da cobrança em aberto (0 = em dia ou adiantado)."""
    from superadmin.models import PagamentoLoja

    hoje = date.today()
    dias = 0

    try:
        financeiro = loja.financeiro
    except Exception:
        financeiro = None

    if financeiro and financeiro.data_proxima_cobranca and hoje > financeiro.data_proxima_cobranca:
        dias = max(dias, (hoje - financeiro.data_proxima_cobranca).days)

    pag_atrasado = (
        PagamentoLoja.objects.filter(
            loja=loja,
            status__in=['pendente', 'atrasado'],
            data_vencimento__lt=hoje,
        )
        .order_by('data_vencimento')
        .first()
    )
    if pag_atrasado:
        dias = max(dias, (hoje - pag_atrasado.data_vencimento).days)

    return dias


def loja_deve_estar_bloqueada(loja) -> bool:
    return dias_atraso_assinatura(loja) >= DAYS_TO_BLOCK


def situacao_aviso_assinatura(loja) -> dict | None:
    """
    Aviso para exibir na abertura do sistema (5 dias antes do vencimento até o bloqueio).
    Retorna None se não houver aviso a mostrar.
    """
    if getattr(loja, 'is_blocked', False):
        return None

    try:
        financeiro = loja.financeiro
    except Exception:
        return None

    if not financeiro or not financeiro.data_proxima_cobranca:
        return None

    hoje = date.today()
    dias_para = (financeiro.data_proxima_cobranca - hoje).days
    dias_atraso = dias_atraso_assinatura(loja)
    data_venc = financeiro.data_proxima_cobranca.isoformat()

    if dias_para > DAYS_TO_WARN_UI:
        return None

    if dias_para >= 1:
        dia_label = 'dia' if dias_para == 1 else 'dias'
        return {
            'nivel': 'aviso',
            'dias_restantes': dias_para,
            'data_vencimento': data_venc,
            'mensagem': (
                f'Faltam {dias_para} {dia_label} para vencer a assinatura. '
                'Efetue o pagamento para evitar o bloqueio do sistema.'
            ),
        }

    if dias_para == 0:
        return {
            'nivel': 'urgente',
            'dias_restantes': 0,
            'data_vencimento': data_venc,
            'mensagem': (
                'Sua assinatura vence hoje. Efetue o pagamento para evitar o bloqueio do sistema.'
            ),
        }

    if dias_atraso > 0 and dias_atraso < DAYS_TO_BLOCK:
        dias_ate_bloqueio = DAYS_TO_BLOCK - dias_atraso
        bloqueio_label = 'dia' if dias_ate_bloqueio == 1 else 'dias'
        atraso_label = 'dia' if dias_atraso == 1 else 'dias'
        return {
            'nivel': 'critico',
            'dias_atraso': dias_atraso,
            'dias_ate_bloqueio': dias_ate_bloqueio,
            'data_vencimento': data_venc,
            'mensagem': (
                f'Assinatura vencida há {dias_atraso} {atraso_label}. '
                f'O sistema será bloqueado em {dias_ate_bloqueio} {bloqueio_label} '
                'se o pagamento não for efetuado.'
            ),
        }

    return None


def situacao_geracao_boleto_assinatura(loja, financeiro) -> dict:
    """
    Regras para o proprietário gerar boleto manualmente na página Assinatura.
    Alinhado ao cron criar_boletos_proximos: só dentro de DAYS_TO_WARN_BOLETO dias do vencimento.
    """
    from superadmin.models import PagamentoLoja

    hoje = date.today()
    venc = financeiro.data_proxima_cobranca

    if not venc:
        return {
            'pode_gerar': False,
            'motivo': 'Próximo vencimento não definido.',
            'data_liberacao': None,
            'dias_ate_liberacao': None,
        }

    data_liberacao = venc - timedelta(days=DAYS_TO_WARN_BOLETO)

    tem_pendente = PagamentoLoja.objects.filter(
        loja=loja,
        status__in=['pendente', 'atrasado'],
    ).exists()
    if tem_pendente:
        return {
            'pode_gerar': False,
            'motivo': (
                'Já existe um boleto em aberto. Efetue o pagamento ou aguarde a confirmação '
                'antes de gerar outro.'
            ),
            'data_liberacao': data_liberacao.isoformat(),
            'dias_ate_liberacao': None,
        }

    dias_ate_vencimento = (venc - hoje).days
    if dias_ate_vencimento > DAYS_TO_WARN_BOLETO:
        dias_ate_liberacao = (data_liberacao - hoje).days
        return {
            'pode_gerar': False,
            'motivo': (
                f'O boleto só pode ser gerado a partir de {data_liberacao.strftime("%d/%m/%Y")} '
                f'({DAYS_TO_WARN_BOLETO} dias antes do vencimento).'
            ),
            'data_liberacao': data_liberacao.isoformat(),
            'dias_ate_liberacao': max(dias_ate_liberacao, 0),
        }

    return {
        'pode_gerar': True,
        'motivo': None,
        'data_liberacao': data_liberacao.isoformat(),
        'dias_ate_liberacao': 0,
    }


def aplicar_bloqueio_inadimplencia_loja(loja, *, persistir: bool = True) -> dict:
    """
    Atualiza status financeiro e is_blocked conforme dias de atraso.
    Bloqueio após DAYS_TO_BLOCK; antes disso marca atrasado se vencido.
    """
    from superadmin.models import FinanceiroLoja

    try:
        financeiro = loja.financeiro
    except FinanceiroLoja.DoesNotExist:
        return {'loja_id': loja.id, 'skipped': True, 'reason': 'sem_financeiro'}

    dias = dias_atraso_assinatura(loja)
    blocked_before = bool(getattr(loja, 'is_blocked', False))
    status_before = financeiro.status_pagamento
    changed = False

    if dias >= DAYS_TO_BLOCK:
        if not loja.is_blocked:
            loja.is_blocked = True
            loja.blocked_at = timezone.now()
            loja.blocked_reason = f'Assinatura vencida há {dias} dias'
            loja.days_overdue = dias
            changed = True
        elif loja.days_overdue != dias:
            loja.days_overdue = dias
            changed = True
        if financeiro.status_pagamento != 'suspenso':
            financeiro.status_pagamento = 'suspenso'
            changed = True
    elif dias > 0:
        if loja.is_blocked:
            loja.is_blocked = False
            loja.blocked_at = None
            loja.blocked_reason = ''
            loja.days_overdue = dias
            changed = True
        elif loja.days_overdue != dias:
            loja.days_overdue = dias
            changed = True
        if financeiro.status_pagamento not in ('ativo', 'pendente'):
            financeiro.status_pagamento = 'atrasado'
            changed = True
        elif financeiro.status_pagamento == 'suspenso':
            financeiro.status_pagamento = 'atrasado'
            changed = True
    else:
        if loja.days_overdue:
            loja.days_overdue = 0
            changed = True
        if loja.is_blocked and financeiro.status_pagamento == 'ativo':
            loja.is_blocked = False
            loja.blocked_at = None
            loja.blocked_reason = ''
            changed = True

    if persistir and changed:
        update_loja = ['is_blocked', 'blocked_at', 'blocked_reason', 'days_overdue']
        loja.save(update_fields=[f for f in update_loja if hasattr(loja, f)])
        financeiro.save(update_fields=['status_pagamento'])
        if blocked_before != loja.is_blocked:
            if loja.is_blocked:
                logger.warning('Loja %s bloqueada (%s dias de atraso)', loja.slug, dias)
            else:
                logger.info('Loja %s desbloqueada (atraso=%s dias)', loja.slug, dias)
            from superadmin.loja_utils import invalidate_loja_info_publica_cache
            invalidate_loja_info_publica_cache(loja)

    return {
        'loja_id': loja.id,
        'slug': loja.slug,
        'dias_atraso': dias,
        'blocked': bool(loja.is_blocked),
        'status': financeiro.status_pagamento,
        'changed': changed,
        'status_before': status_before,
    }


def verificar_bloqueio_todas_lojas(*, apenas_ativas: bool = True) -> dict:
    from superadmin.models import Loja

    qs = Loja.objects.filter(is_active=True) if apenas_ativas else Loja.objects.all()
    qs = qs.select_related('financeiro')

    bloqueadas = 0
    desbloqueadas = 0
    alteradas = 0

    for loja in qs.iterator(chunk_size=100):
        before = bool(loja.is_blocked)
        out = aplicar_bloqueio_inadimplencia_loja(loja)
        if out.get('changed'):
            alteradas += 1
        if not before and loja.is_blocked:
            bloqueadas += 1
        if before and not loja.is_blocked:
            desbloqueadas += 1

    return {
        'alteradas': alteradas,
        'bloqueadas_agora': bloqueadas,
        'desbloqueadas_agora': desbloqueadas,
        'total': qs.count(),
    }


BLOCKED_ALLOWED_PATH_FRAGMENTS = (
    '/alterar_senha_primeiro_acesso/',
    '/reenviar_senha/',
    '/verificar_senha_provisoria/',
    '/info_publica/',
    '/registrar-erro-frontend/',
    '/financeiro/',
    '/loja-financeiro/',
    '/loja-pagamentos/',
)


def path_allowed_when_store_blocked(path: str) -> bool:
    if path.rstrip('/').endswith('/heartbeat') or '/lojas/heartbeat' in path:
        return True
    return any(fragment in path for fragment in BLOCKED_ALLOWED_PATH_FRAGMENTS)


def check_inadimplencia_block(request):
    """
    Retorna JsonResponse 403 se usuário de loja bloqueada tentar acessar rota não permitida.
  """
    from django.http import JsonResponse

    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'is_authenticated', False):
        return None
    if getattr(user, 'is_superuser', False):
        return None

    path = request.path or ''
    if path.startswith('/api/auth/'):
        return None
    if path_allowed_when_store_blocked(path):
        return None

    slug = _extract_slug_from_request(request)
    from core.store_membership import resolve_loja_for_user, user_belongs_to_store

    if slug and not user_belongs_to_store(user, slug):
        return None

    loja = resolve_loja_for_user(user, slug)
    if not loja or not getattr(loja, 'is_blocked', False):
        return None

    logger.warning(
        'Bloqueio inadimplência: user=%s loja=%s path=%s',
        getattr(user, 'username', '?'),
        loja.slug,
        path,
    )
    return JsonResponse(
        {
            'error': 'Assinatura em atraso. Regularize o pagamento para continuar usando o sistema.',
            'code': 'STORE_BLOCKED_INADIMPLENCIA',
            'redirect': f'/loja/{loja.slug}/assinatura',
            'loja_slug': loja.slug,
        },
        status=403,
    )


def _extract_slug_from_request(request) -> str | None:
    slug = (
        request.headers.get('X-Store-Slug')
        or request.headers.get('X-Tenant-Slug')
    )
    if slug:
        return slug.strip()
    loja_id = request.headers.get('X-Loja-ID')
    if loja_id:
        try:
            from superadmin.models import Loja

            loja = Loja.objects.filter(id=int(loja_id), is_active=True).first()
            if loja:
                return loja.slug
        except (ValueError, TypeError):
            pass
    slug = request.GET.get('store') or request.GET.get('tenant')
    if slug:
        return slug.strip()
    path_parts = (request.path or '').split('/')
    if 'loja' in path_parts:
        idx = path_parts.index('loja')
        if idx + 1 < len(path_parts):
            return path_parts[idx + 1]
    return None
