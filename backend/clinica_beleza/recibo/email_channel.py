"""Envio de recibo por email."""
import logging

from .context import _obter_dados_contexto
from .pdf import _gerar_pdf_recibo

logger = logging.getLogger(__name__)


def _email_somente_foto(ctx: dict, *, assinado: bool = False) -> tuple[str, str, str]:
    """E-mail do recibo: só a foto no corpo. Os dados ficam na imagem."""
    loja = (ctx.get("loja_nome") or "").strip()
    titulo = "Recibo assinado" if assinado else "Recibo de Pagamento"
    assunto = f"{titulo} — {loja}" if loja else titulo
    html = (
        '<div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:12px;">'
        f'<img src="cid:recibo" alt="{titulo}" style="max-width:100%;height:auto;" />'
        "</div>"
    )
    return assunto, html, f"{titulo}."


def _enviar_recibo_email(payment, patient, appointment, *, somente_foto=False) -> tuple[bool, str]:
    """Envia o recibo por e-mail só com a foto no corpo."""
    email = (getattr(patient, "email", "") or "").strip()
    if not email:
        return False, "Paciente não possui email cadastrado."

    try:
        from core.email_delivery import create_email_multipart, send_prepared
        from core.email_sync_context import email_sync_only

        ctx = _obter_dados_contexto(payment, patient, appointment)
        pdf_bytes = _gerar_pdf_recibo(ctx)
        from clinica_beleza.media_docs_service import arquivar_pdf_gerado
        arquivar_pdf_gerado(
            getattr(payment, "loja_id", None),
            patient,
            pdf_bytes,
            f"recibo_{payment.id}.pdf",
        )

        assunto, corpo_html, corpo_texto = _email_somente_foto(ctx, assinado=somente_foto)

        msg = create_email_multipart(
            subject=assunto,
            body=corpo_texto,
            to=[email],
            html=corpo_html,
        )
        jpeg_bytes = None
        try:
            from clinica_beleza.recibo.imagem import pdf_para_jpeg

            jpeg_bytes = pdf_para_jpeg(pdf_bytes)
        except Exception as conv_err:
            logger.warning("Conversão do recibo em foto falhou: %s", conv_err)

        if jpeg_bytes:
            from core.email_delivery import attach_inline_jpeg

            attach_inline_jpeg(
                msg,
                jpeg_bytes,
                cid="recibo",
                filename=f"recibo_{payment.id}.jpg",
            )
        else:
            msg.attach(f"recibo_{payment.id}.pdf", pdf_bytes, "application/pdf")

        token = email_sync_only.set(True)
        try:
            send_prepared(msg, fail_silently=False)
        finally:
            email_sync_only.reset(token)

        logger.info("Recibo PDF enviado por email para %s (payment_id=%s)", email, payment.id)
        return True, f"Recibo enviado para {email}"
    except Exception as e:
        logger.warning("Falha ao enviar recibo email payment_id=%s: %s", payment.id, e)
        return False, "Erro ao enviar email. Tente novamente."
