"""Notificações e envio de links de assinatura digital (CRM).
"""
import logging
from urllib.parse import quote

from django.conf import settings
from django.utils import timezone

from .assinatura_digital_emails import (
    enviar_email_assinatura_vendedor,
)
from .assinatura_digital_token import criar_token_assinatura

logger = logging.getLogger(__name__)

def _notificar_assinatura_concluida(documento, assinatura):
    """Cria notificação in-app quando assinatura digital é concluída."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import Loja
        loja_id = getattr(documento, "loja_id", None)
        if not loja_id:
            return
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja or not loja.owner_id:
            return
        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, "titulo", "") or f"{tipo_doc} #{documento.id}"
        Notification.objects.using("default").create(
            user_id=loja.owner_id,
            titulo=f"✅ {tipo_doc} assinada digitalmente",
            mensagem=f"{titulo_doc} foi assinada por ambas as partes.",
            tipo="sistema",
            canal="in_app",
            status="pendente",
            metadata={"tipo_documento": tipo_doc.lower(), "documento_id": documento.id, "loja_id": loja_id},
        )
    except Exception as e:
        logger.warning(f"Erro ao criar notificação de assinatura: {e}")


def _notificar_cliente_assinou(documento, assinatura):
    """Cria notificação in-app quando o cliente assina e o vendedor precisa assinar."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import Loja
        loja_id = getattr(documento, "loja_id", None)
        if not loja_id:
            return
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja or not loja.owner_id:
            return
        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, "titulo", "") or f"{tipo_doc} #{documento.id}"
        cliente_nome = assinatura.nome_assinante or "Cliente"
        canal_v = (getattr(documento, "canal_assinatura_vendedor", None) or "email").strip().lower()
        canal_txt = "WhatsApp" if canal_v == "whatsapp" else "e-mail"
        Notification.objects.using("default").create(
            user_id=loja.owner_id,
            titulo=f"📝 {tipo_doc} aguardando sua assinatura",
            mensagem=f"{titulo_doc} foi assinada por {cliente_nome}. Verifique seu {canal_txt} para assinar.",
            tipo="sistema",
            canal="in_app",
            status="pendente",
            metadata={"tipo_documento": tipo_doc.lower(), "documento_id": documento.id, "loja_id": loja_id},
        )
    except Exception as e:
        logger.warning(f"Erro ao criar notificação de assinatura cliente: {e}")


def _telefone_vendedor_documento(documento) -> str:
    oportunidade = getattr(documento, "oportunidade", None)
    vendedor = getattr(oportunidade, "vendedor", None) if oportunidade else None
    return (getattr(vendedor, "telefone", None) or "").strip()


def _email_vendedor_documento(documento) -> str:
    oportunidade = getattr(documento, "oportunidade", None)
    vendedor = getattr(oportunidade, "vendedor", None) if oportunidade else None
    return (getattr(vendedor, "email", None) or "").strip()


def _resolver_email_vendedor(assinatura, documento) -> str:
    email = (getattr(assinatura, "email_assinante", None) or "").strip()
    if email:
        return email
    return _email_vendedor_documento(documento)


def _canais_vendedor_disponiveis(documento):
    canais = []
    if _email_vendedor_documento(documento):
        canais.append("email")
    if _telefone_vendedor_documento(documento):
        canais.append("whatsapp")
    return canais


def _ordenar_canais_vendedor(documento):
    canal_pref = (getattr(documento, "canal_assinatura_vendedor", None) or "email").strip().lower()
    if canal_pref not in ("email", "whatsapp"):
        canal_pref = "email"
    disponiveis = _canais_vendedor_disponiveis(documento)
    ordenados = []
    if canal_pref in disponiveis:
        ordenados.append(canal_pref)
    for canal in ("email", "whatsapp"):
        if canal in disponiveis and canal not in ordenados:
            ordenados.append(canal)
    return ordenados


def _marcar_link_vendedor_enviado(documento, assinatura, canal):
    agora = timezone.now()
    if not assinatura.link_enviado_em:
        assinatura.link_enviado_em = agora
        assinatura.save(update_fields=["link_enviado_em", "updated_at"])
    if getattr(documento, "canal_assinatura_vendedor", None) != canal:
        documento.canal_assinatura_vendedor = canal
        documento.save(update_fields=["canal_assinatura_vendedor", "updated_at"])


def tentar_enviar_link_vendedor(documento, assinatura, request=None, user=None):
    """Tenta enviar link ao vendedor por todos os canais disponíveis (preferência da proposta primeiro).
    Retorna (sucesso, canal_usado, erro).
    """
    if assinatura.link_enviado_em:
        return True, getattr(documento, "canal_assinatura_vendedor", None), None

    email = _resolver_email_vendedor(assinatura, documento)
    if email and email != (assinatura.email_assinante or "").strip():
        assinatura.email_assinante = email
        assinatura.save(update_fields=["email_assinante", "updated_at"])

    canais = _ordenar_canais_vendedor(documento)
    if not canais:
        return False, None, "Vendedor sem e-mail e sem telefone cadastrados."

    user = user or getattr(request, "user", None)
    ultimo_erro = None
    for canal in canais:
        ok, err = enviar_link_assinatura_vendedor(
            documento,
            assinatura,
            request,
            canal=canal,
            user=user,
        )
        if ok:
            _marcar_link_vendedor_enviado(documento, assinatura, canal)
            logger.info(
                "Link vendedor enviado (%s): documento=%s#%s",
                canal,
                documento.__class__.__name__,
                documento.id,
            )
            return True, canal, None
        ultimo_erro = err

    return False, None, ultimo_erro


def _notificar_vendedor_usuario_in_app(documento, assinatura, loja_id):
    """Notifica o usuário do vendedor no CRM com o link direto de assinatura."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import VendedorUsuario

        oportunidade = getattr(documento, "oportunidade", None)
        vendedor = getattr(oportunidade, "vendedor", None) if oportunidade else None
        if not vendedor:
            return

        vu = (
            VendedorUsuario.objects.using("default")
            .filter(loja_id=loja_id, vendedor_id=vendedor.id)
            .select_related("user")
            .first()
        )
        if not vu or not vu.user_id:
            return

        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, "titulo", "") or f'{tipo_doc} #{getattr(documento, "numero", None) or documento.id}'
        frontend_url = getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")
        link = f'{frontend_url}/assinar/{quote(assinatura.token, safe="")}'

        Notification.objects.using("default").create(
            user_id=vu.user_id,
            titulo=f"📝 Assinar {tipo_doc}",
            mensagem=(
                f"{titulo_doc}: o cliente já assinou. "
                f"Finalize com sua assinatura: {link}"
            ),
            tipo="sistema",
            canal="in_app",
            status="pendente",
            metadata={
                "tipo_documento": tipo_doc.lower(),
                "documento_id": documento.id,
                "loja_id": loja_id,
                "assinatura_token": assinatura.token,
            },
        )
    except Exception as exc:
        logger.warning("Erro ao notificar vendedor in-app: %s", exc)


def enviar_whatsapp_assinatura_vendedor(documento, assinatura, request, user=None):
    """Envia link de assinatura digital ao vendedor por WhatsApp.
    Returns: (sucesso, erro)
    """
    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    telefone = _telefone_vendedor_documento(documento)
    if not telefone:
        return False, "Vendedor não possui telefone cadastrado."

    is_proposta = documento.__class__.__name__ == "Proposta"
    config = WhatsAppConfig.objects.filter(loja_id=assinatura.loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(
        config,
        proposta=is_proposta,
        contrato=not is_proposta,
    )
    if not ok_cfg:
        return False, err_cfg

    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else "Sistema"
    tipo_doc = "Proposta" if is_proposta else "Contrato"
    titulo = (getattr(documento, "titulo", None) or getattr(documento, "numero", None) or tipo_doc).strip()
    nome_vendedor = (assinatura.nome_assinante or "Vendedor").strip()

    # Nome do cliente para contexto
    lead = documento.oportunidade.lead if hasattr(documento, "oportunidade") else None
    nome_cliente = getattr(lead, "nome", None) if lead else None

    frontend_url = getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")
    full_link = f'{frontend_url}/assinar/{quote(assinatura.token, safe="")}'
    try:
        from core.short_link import build_short_url
        link = build_short_url(full_link)
    except Exception:
        link = full_link

    from whatsapp.message_templates import msg_assinatura_vendedor
    mensagem = msg_assinatura_vendedor(
        nome=nome_vendedor,
        tipo_doc=tipo_doc,
        titulo=titulo,
        loja_nome=loja_nome,
        link=link,
        nome_cliente=nome_cliente,
    )

    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    if ok:
        logger.info(
            "WhatsApp assinatura vendedor CRM: %s#%s vendedor=%s",
            documento.__class__.__name__,
            documento.id,
            nome_vendedor,
        )
    return ok, err


def enviar_link_assinatura_vendedor(documento, assinatura, request, canal="email", user=None):
    """Envia link de assinatura ao vendedor por e-mail ou WhatsApp."""
    canal = (canal or "email").strip().lower()
    if canal == "whatsapp":
        return enviar_whatsapp_assinatura_vendedor(documento, assinatura, request, user=user)
    if not _resolver_email_vendedor(assinatura, documento):
        return False, "Vendedor não possui e-mail cadastrado."
    return enviar_email_assinatura_vendedor(documento, assinatura, request)


def _notificar_falha_envio_vendedor(documento, erro):
    """Alerta o dono da loja quando o link automático ao vendedor falha após assinatura do cliente."""
    try:
        from notificacoes.models import Notification
        from superadmin.models import Loja

        loja_id = getattr(documento, "loja_id", None)
        if not loja_id:
            return
        loja = Loja.objects.using("default").filter(id=loja_id).first()
        if not loja or not loja.owner_id:
            return
        tipo_doc = documento.__class__.__name__
        titulo_doc = getattr(documento, "titulo", "") or f"{tipo_doc} #{documento.numero or documento.id}"
        detalhe = (erro or "erro desconhecido")[:300]
        Notification.objects.using("default").create(
            user_id=loja.owner_id,
            titulo="⚠️ Vendedor não recebeu link de assinatura",
            mensagem=(
                f"{titulo_doc}: o cliente assinou, mas o envio automático ao vendedor falhou ({detalhe}). "
                "Abra a proposta/contrato e use os ícones de e-mail ou WhatsApp na coluna Assinatura para reenviar."
            ),
            tipo="sistema",
            canal="in_app",
            status="pendente",
            metadata={"tipo_documento": tipo_doc.lower(), "documento_id": documento.id, "loja_id": loja_id},
        )
    except Exception as e:
        logger.warning("Erro ao notificar falha de envio ao vendedor: %s", e)


def notificar_vendedor_apos_assinatura_cliente(documento, loja_id, request):
    """Cria token do vendedor, notifica in-app e envia por todos os canais disponíveis."""
    from .assinatura_vendedor_retry import agendar_retry_envio_vendedor

    assinatura_vendedor = criar_token_assinatura(documento, "vendedor", loja_id)
    _notificar_vendedor_usuario_in_app(documento, assinatura_vendedor, loja_id)

    ok, canal, err = tentar_enviar_link_vendedor(
        documento,
        assinatura_vendedor,
        request,
        user=getattr(request, "user", None),
    )
    if ok:
        return True, None

    agendar_retry_envio_vendedor(assinatura_vendedor.id, loja_id)
    _notificar_falha_envio_vendedor(documento, err)
    logger.warning(
        "Envio imediato ao vendedor falhou; retries agendados: documento=%s#%s err=%s",
        documento.__class__.__name__,
        documento.id,
        err,
    )
    return False, err or "Erro ao enviar link ao vendedor."


def enviar_whatsapp_assinatura_cliente(documento, assinatura, request, user=None):
    """Envia link de assinatura digital ao cliente por WhatsApp.
    Returns: (sucesso, erro)
    """
    from urllib.parse import quote

    from whatsapp.assinatura_whatsapp import whatsapp_envio_permitido
    from whatsapp.models import WhatsAppConfig
    from whatsapp.services import send_whatsapp

    lead = documento.oportunidade.lead
    telefone = (getattr(lead, "telefone", None) or "").strip()
    if not telefone:
        return False, "Lead não possui telefone cadastrado."

    is_proposta = documento.__class__.__name__ == "Proposta"
    config = WhatsAppConfig.objects.filter(loja_id=assinatura.loja_id).first()
    ok_cfg, err_cfg = whatsapp_envio_permitido(
        config,
        proposta=is_proposta,
        contrato=not is_proposta,
    )
    if not ok_cfg:
        return False, err_cfg

    from superadmin.models import Loja
    loja = Loja.objects.using("default").filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else "Sistema"
    tipo_doc = "Proposta" if is_proposta else "Contrato"
    titulo = (getattr(documento, "titulo", None) or getattr(documento, "numero", None) or tipo_doc).strip()

    frontend_url = getattr(settings, "FRONTEND_URL", "https://lwksistemas.com.br")
    full_link = f'{frontend_url}/assinar/{quote(assinatura.token, safe="")}'
    try:
        from core.short_link import build_short_url
        link = build_short_url(full_link)
    except Exception:
        link = full_link

    from whatsapp.message_templates import msg_assinatura_cliente
    mensagem = msg_assinatura_cliente(
        nome=lead.nome,
        tipo_doc=tipo_doc,
        titulo=titulo,
        loja_nome=loja_nome,
        link=link,
    )

    ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, user=user, config=config)
    if ok:
        logger.info(
            "WhatsApp assinatura CRM enviado: %s#%s lead=%s",
            documento.__class__.__name__,
            documento.id,
            lead.nome,
        )
    return ok, err


