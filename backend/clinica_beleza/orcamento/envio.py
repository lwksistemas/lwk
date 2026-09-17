"""Envio de orçamento por e-mail e WhatsApp."""
import logging
from typing import Any

from django.utils import timezone

from clinica_beleza.models import OrcamentoConsulta
from clinica_beleza.orcamento.pdf import _format_brl, gerar_pdf_orcamento
from superadmin.models import Loja

logger = logging.getLogger(__name__)


def montar_mensagem_whatsapp_orcamento(orcamento: OrcamentoConsulta, loja_nome: str = "") -> str:
    """Resumo profissional para WhatsApp — sem observações/cadastro (vão no PDF)."""
    from whatsapp.message_templates import msg_orcamento

    itens = [
        f"• {item.nome_procedimento} ({item.quantidade}x) — {_format_brl(item.subtotal)}"
        for item in orcamento.itens.all()
    ]
    nome = orcamento.patient.nome if orcamento.patient else "Paciente"
    clinica = (loja_nome or "").strip() or (
        orcamento.professional.nome if orcamento.professional else "Clínica"
    )
    return msg_orcamento(
        nome=nome,
        loja_nome=clinica,
        linhas_itens=itens,
        total=_format_brl(orcamento.valor_total),
        validade_dias=orcamento.validade_dias or 30,
    )


def enviar_orcamento(orcamento_id: int, canais: list[str]) -> dict[str, Any]:
    """Envia orçamento por email e/ou WhatsApp e salva PDF no servidor de mídia."""
    orcamento = OrcamentoConsulta.objects.select_related("patient", "professional").get(id=orcamento_id)
    pdf_bytes = gerar_pdf_orcamento(orcamento_id)
    resultado: dict[str, Any] = {}

    if "email" in canais:
        resultado["email"] = _enviar_email(orcamento, pdf_bytes)

    if "whatsapp" in canais:
        resultado["whatsapp"] = _enviar_whatsapp(orcamento, pdf_bytes)

    try:
        from clinica_beleza.media_docs_service import salvar_orcamento_no_servidor_midia
        salvar_orcamento_no_servidor_midia(orcamento, pdf_bytes)
    except Exception as e:
        logger.warning("Falha ao salvar orçamento no servidor de mídia: %s", e)

    algum_sucesso = any(r.get("sucesso") for r in resultado.values())
    if algum_sucesso:
        orcamento.status = "ENVIADO"
        orcamento.data_envio = timezone.now()
    if resultado.get("email", {}).get("sucesso"):
        orcamento.enviado_email = True
    if resultado.get("whatsapp", {}).get("sucesso"):
        orcamento.enviado_whatsapp = True
    orcamento.save()

    return resultado


def _enviar_email(orcamento: OrcamentoConsulta, pdf_bytes: bytes) -> dict:
    """Envia orçamento por email."""
    email = (getattr(orcamento.patient, "email", "") or "").strip()
    if not email:
        return {"sucesso": False, "erro": "Paciente sem e-mail cadastrado."}

    try:
        from core.email_delivery import create_email_message, send_prepared

        profissional = orcamento.professional.nome if orcamento.professional else "Clínica"
        assunto = f"Orçamento — {profissional}"
        corpo = (
            f"Olá {orcamento.patient.nome},\n\n"
            f"Segue em anexo o orçamento dos procedimentos conversados.\n"
            f"Valor total: {_format_brl(orcamento.valor_total)}\n\n"
            f"Qualquer dúvida, estamos à disposição.\n\n"
            f"Atenciosamente,\n{profissional}"
        )

        msg = create_email_message(subject=assunto, body=corpo, to=[email])
        msg.attach(f"orcamento_{orcamento.id}.pdf", pdf_bytes, "application/pdf")
        send_prepared(msg, fail_silently=False)

        logger.info("Orçamento %d enviado por email para %s", orcamento.id, email)
        return {"sucesso": True}
    except Exception as e:
        logger.warning("Erro ao enviar orçamento por email: %s", e)
        return {"sucesso": False, "erro": str(e)}


def _enviar_whatsapp(orcamento: OrcamentoConsulta, pdf_bytes: bytes) -> dict:
    """Envia orçamento por WhatsApp: mensagem de texto + PDF anexo.
    Mesmo padrão usado no recibo (send_whatsapp + _send_whatsapp_document_evolution).
    """
    telefone = (getattr(orcamento.patient, "telefone", "") or "").strip()
    if not telefone:
        return {"sucesso": False, "erro": "Paciente sem telefone cadastrado."}

    try:
        from django.conf import settings
        from whatsapp.models import WhatsAppConfig
        from whatsapp.services import send_whatsapp, _send_whatsapp_document_evolution

        config = WhatsAppConfig.objects.filter(loja_id=orcamento.loja_id).first()
        if not config or not getattr(config, "whatsapp_ativo", False):
            return {"sucesso": False, "erro": "WhatsApp não está ativo. Configure em Configurações → WhatsApp."}

        loja_nome = "Clínica"
        try:
            loja = Loja.objects.using("default").filter(id=orcamento.loja_id).first()
            if loja and getattr(loja, "nome", ""):
                loja_nome = loja.nome
        except Exception:
            if orcamento.professional:
                loja_nome = orcamento.professional.nome

        mensagem = montar_mensagem_whatsapp_orcamento(orcamento, loja_nome)

        ok, err = send_whatsapp(telefone=telefone, mensagem=mensagem, config=config)
        if not ok:
            return {"sucesso": False, "erro": err or "Erro ao enviar WhatsApp."}

        try:
            from clinica_beleza.public_pdf import PREFIX_ORCAMENTO, gravar_pdf_publico

            token = gravar_pdf_publico(
                PREFIX_ORCAMENTO,
                {"orcamento_id": orcamento.id, "pdf": pdf_bytes},
            )

            api_base = getattr(settings, "API_BASE_URL", "") or "https://api.lwksistemas.com.br"
            pdf_url = f"{api_base}/api/clinica-beleza/orcamentos/{orcamento.id}/pdf-public/{token}/"

            _send_whatsapp_document_evolution(
                telefone, pdf_url, f"orcamento_{orcamento.id}.pdf",
                caption="Orçamento", config=config,
            )
        except Exception as pdf_err:
            logger.warning("PDF via WhatsApp falhou (texto já enviado): %s", pdf_err)

        logger.info("Orçamento %d enviado por WhatsApp para %s", orcamento.id, telefone)
        return {"sucesso": True, "erro": ""}
    except ImportError as e:
        return {"sucesso": False, "erro": f"WhatsApp não configurado: {e}"}
    except Exception as e:
        logger.warning("Erro ao enviar orçamento por WhatsApp: %s", e)
        return {"sucesso": False, "erro": str(e)}
