"""Registro de leitura clínica.

O middleware global não grava GET. Estas leituras anotam usuário, paciente e hora
no histórico que já existe, sem mudar quem pode ver.
"""
import logging

logger = logging.getLogger(__name__)


def _ip_do_pedido(request) -> str:
    """Último salto do proxy. O primeiro pode ser inventado pelo cliente."""
    forwarded = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if forwarded:
        return forwarded.split(",")[-1].strip() or "0.0.0.0"
    return (request.META.get("REMOTE_ADDR") or "0.0.0.0").strip() or "0.0.0.0"


def registrar_leitura_clinica(request, paciente_id, recurso: str) -> None:
    """Grava a abertura. Uma falha aqui não impede a tela de responder."""
    if not paciente_id:
        return
    try:
        paciente_id = int(paciente_id)
    except (TypeError, ValueError):
        return
    try:
        from superadmin.historico_usuario import resolver_identidade_historico
        from superadmin.models import HistoricoAcessoGlobal, Loja
        from tenants.middleware import get_current_loja_id

        user, email, nome, loja_sugerida = resolver_identidade_historico(request)
        if user is not None and not getattr(user, "pk", None):
            user = None
        loja_id = get_current_loja_id() or loja_sugerida
        loja = Loja.objects.using("default").filter(pk=loja_id).first() if loja_id else None
        HistoricoAcessoGlobal.objects.using("default").create(
            user=user,
            usuario_email=(email or "")[:254],
            usuario_nome=(nome or "Usuário")[:200],
            loja=loja,
            loja_nome=(getattr(loja, "nome", "") or "")[:200],
            loja_slug=(getattr(loja, "slug", "") or "")[:100],
            acao="visualizar",
            recurso=(recurso or "")[:100],
            recurso_id=paciente_id,
            detalhes="",
            ip_address=_ip_do_pedido(request)[:45],
            user_agent=(request.META.get("HTTP_USER_AGENT") or "")[:500],
            metodo_http=(getattr(request, "method", "") or "")[:10],
            url=(getattr(request, "path", "") or "")[:500],
            sucesso=True,
        )
    except Exception:
        logger.exception(
            "leitura clinica paciente=%s recurso=%s", paciente_id, recurso,
        )
