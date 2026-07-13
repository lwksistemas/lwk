"""
Audit Log para ações sensíveis (NFS-e, certificados, configurações).

Registra quem fez o quê, quando e de onde.
Usa o model AuditLog no banco default (superadmin).
"""
import functools
import logging

logger = logging.getLogger(__name__)


def audit_log(acao: str, descricao: str = ''):
    """
    Decorator para registrar ações sensíveis no audit log.

    Uso:
        @audit_log('nfse_emitir_manual', 'Emissão manual de NFS-e')
        def emitir_nfse_manual(request):
            ...

    Registra: usuário, IP, ação, timestamp, sucesso/falha, detalhes.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)
            try:
                _registrar_audit(
                    request=request,
                    acao=acao,
                    descricao=descricao,
                    sucesso=(200 <= response.status_code < 400),
                    status_code=response.status_code,
                )
            except Exception as e:
                logger.warning('Falha ao registrar audit log: %s', e)
            return response
        return wrapper
    return decorator


def registrar_audit_manual(request, acao: str, descricao: str = '', sucesso: bool = True, detalhes: dict = None):
    """
    Registra audit log manualmente (para uso dentro de views sem decorator).
    """
    try:
        _registrar_audit(
            request=request,
            acao=acao,
            descricao=descricao,
            sucesso=sucesso,
            status_code=200 if sucesso else 400,
            detalhes_extra=detalhes,
        )
    except Exception as e:
        logger.warning('Falha ao registrar audit log manual: %s', e)


def _registrar_audit(request, acao, descricao, sucesso, status_code, detalhes_extra=None):
    """Registra no banco de dados."""
    from superadmin.models import AuditLog

    ip = _get_client_ip(request)
    user = request.user if request.user.is_authenticated else None

    detalhes = {
        'method': request.method,
        'path': request.path[:500],
        'status_code': status_code,
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:200],
    }
    if detalhes_extra:
        detalhes.update(detalhes_extra)

    AuditLog.objects.using('default').create(
        user=user,
        usuario_email=user.email if user else '',
        usuario_nome=(user.get_full_name() or user.username) if user else '',
        acao=acao,
        descricao=descricao[:500],
        ip_address=ip,
        sucesso=sucesso,
        detalhes=detalhes,
    )


def _get_client_ip(request):
    """Obtém IP real do cliente."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def registrar_evento_seguranca(
    acao: str,
    descricao: str = '',
    *,
    request=None,
    username: str = '',
    sucesso: bool = False,
    detalhes: dict | None = None,
):
    """
    Registra evento de segurança (login, lockout, violação de isolamento) no AuditLog.
    Não propaga exceção — falha só gera warning no log.
    """
    try:
        from superadmin.models import AuditLog

        user = None
        usuario_email = ''
        usuario_nome = username or ''
        ip = '0.0.0.0'
        det = dict(detalhes or {})

        if request is not None:
            ip = _get_client_ip(request)
            det.setdefault('method', request.method)
            det.setdefault('path', (request.path or '')[:500])
            det.setdefault(
                'user_agent',
                (request.META.get('HTTP_USER_AGENT') or '')[:200],
            )
            if getattr(request, 'user', None) and request.user.is_authenticated:
                user = request.user
                usuario_email = user.email or ''
                usuario_nome = user.get_full_name() or user.username

        if username and not usuario_nome:
            usuario_nome = username

        AuditLog.objects.using('default').create(
            user=user,
            usuario_email=usuario_email,
            usuario_nome=usuario_nome[:255],
            acao=acao[:100],
            descricao=(descricao or '')[:500],
            ip_address=ip,
            sucesso=sucesso,
            detalhes=det,
        )
    except Exception as e:
        logger.warning('Falha ao registrar evento de segurança (%s): %s', acao, e)
