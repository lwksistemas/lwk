"""Adapter de assinatura digital do RECIBO de pagamento — Clínica da Beleza.

Reusa o motor genérico core.assinatura_service. Diferente do termo de consentimento
(duas partes), o recibo é assinado APENAS pelo paciente (parte1) e conclui logo após.
O valor jurídico vem do token assinado + IP + user_agent + data/hora do aceite.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from core.assinatura_service import AssinaturaAdapter

logger = logging.getLogger(__name__)


class ReciboAssinaturaAdapter(AssinaturaAdapter):
    """Assinatura do recibo de um Payment. Só o paciente assina."""

    # ------------------------------------------------------------------
    # Documento e destinatários
    # ------------------------------------------------------------------
    def _appointment(self, payment):
        return getattr(payment, "appointment", None)

    def _patient(self, payment):
        appointment = self._appointment(payment)
        return getattr(appointment, "patient", None) if appointment else None

    def get_procedimentos(self, payment) -> list[dict]:
        appointment = self._appointment(payment)
        if appointment is None:
            return []
        from .recibo.context import _buscar_procedimentos_recibo

        return _buscar_procedimentos_recibo(appointment)

    def get_titulo(self, payment) -> str:
        nomes = [
            (p.get("nome") or "").strip()
            for p in self.get_procedimentos(payment)
            if (p.get("nome") or "").strip()
        ]
        if nomes:
            return " · ".join(nomes)
        return f"Recibo #{payment.id}"

    def get_itens_titulo(self, payment) -> list[str]:
        linhas = []
        for proc in self.get_procedimentos(payment):
            nome = (proc.get("nome") or "").strip()
            if not nome:
                continue
            try:
                valor = float(proc.get("valor") or 0)
            except (TypeError, ValueError):
                valor = 0.0
            linhas.append(f"{nome} — R$ {valor:.2f}")
        return linhas

    def get_valor_display(self, payment) -> str:
        try:
            return f"R$ {float(payment.valor_total_efetivo):.2f}"
        except Exception:
            return ""

    def incluir_valor_no_email(self) -> bool:
        return True

    def get_rotulo_titulo_email(self) -> str:
        return "Procedimentos realizados"

    def get_tipo_documento_label(self, payment) -> str:
        return "Recibo de Pagamento"

    def get_assunto_email_parte1(self, payment, loja_nome: str) -> str:
        return f"🧾 Recibo para assinatura — {self.get_titulo(payment)}"

    def get_destinatario_parte1(self, payment) -> tuple[str, str]:
        patient = self._patient(payment)
        if not patient:
            return ("", "")
        email = (getattr(patient, "email", "") or "").strip()
        return (getattr(patient, "nome", "Cliente"), email)

    def get_telefone_parte1(self, payment) -> str:
        patient = self._patient(payment)
        if not patient:
            return ""
        return (getattr(patient, "telefone", "") or getattr(patient, "phone", "") or "").strip()

    def get_info_extra_email(self, payment) -> dict:
        appointment = self._appointment(payment)
        info = {}
        prof = getattr(appointment, "professional", None) if appointment else None
        if prof and getattr(prof, "nome", ""):
            info["Profissional"] = prof.nome
        return info

    # ------------------------------------------------------------------
    # Registro de assinatura
    # ------------------------------------------------------------------
    def criar_registro_assinatura(self, payment, tipo, nome, email, token, loja_id):
        from .models import ReciboAssinatura
        return ReciboAssinatura.objects.create(
            payment=payment,
            tipo=tipo,
            nome_assinante=nome,
            email_assinante=email or "",
            token=token,
            token_expira_em=timezone.now() + self.prazo_token(),
            loja_id=loja_id,
        )

    def buscar_assinatura_por_token(self, token: str):
        from urllib.parse import unquote

        from core.assinatura_service import normalizar_token_url

        from .models import ReciboAssinatura

        token = normalizar_token_url(token)
        qs = ReciboAssinatura.objects.select_related(
            "payment", "payment__appointment", "payment__appointment__patient",
            "payment__appointment__professional",
        )
        try:
            return qs.get(token=token)
        except ReciboAssinatura.DoesNotExist:
            token_decoded = unquote(token)
            if token_decoded != token:
                try:
                    return qs.get(token=token_decoded)
                except ReciboAssinatura.DoesNotExist:
                    pass
        return None

    def buscar_assinatura_pendente(self, doc_id: int, tipo: str):
        from .models import ReciboAssinatura

        if not doc_id or not tipo:
            return None
        return (
            ReciboAssinatura.objects.select_related(
                "payment", "payment__appointment", "payment__appointment__patient",
                "payment__appointment__professional",
            )
            .filter(payment_id=doc_id, tipo=tipo, assinado=False)
            .order_by("-id")
            .first()
        )

    def get_documento_da_assinatura(self, assinatura):
        return assinatura.payment

    def atualizar_status_assinatura(self, payment, novo_status: str):
        payment.status_assinatura_recibo = novo_status
        payment.save(update_fields=["status_assinatura_recibo", "updated_at"])

    def get_status_assinatura(self, payment) -> str:
        return payment.status_assinatura_recibo or "rascunho"

    def deletar_assinaturas_pendentes(self, payment, tipo: str):
        from .models import ReciboAssinatura
        ReciboAssinatura.objects.filter(payment=payment, tipo=tipo, assinado=False).delete()

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def gerar_pdf(self, payment, incluir_assinaturas: bool = False):
        """Gera o PDF do recibo. Retorna BytesIO (contrato do core)."""
        import io

        from .recibo.context import _obter_dados_contexto
        from .recibo.pdf import _gerar_pdf_recibo

        appointment = self._appointment(payment)
        patient = self._patient(payment)
        ctx = _obter_dados_contexto(payment, patient, appointment)

        # O contexto já injeta 'assinatura_recibo' quando o recibo foi assinado.
        # No PDF "para ler antes de assinar" (incluir_assinaturas=False), remove a seção.
        if not incluir_assinaturas:
            ctx.pop("assinatura_recibo", None)

        pdf_bytes = _gerar_pdf_recibo(ctx)
        return io.BytesIO(pdf_bytes)

    def get_todos_destinatarios_pdf_final(self, payment, loja_id: int) -> list[str]:
        _, email = self.get_destinatario_parte1(payment)
        return [email] if email else []

    # ------------------------------------------------------------------
    # Rótulos / configuração
    # ------------------------------------------------------------------
    def get_label_parte1(self) -> str:
        return "paciente"

    def get_label_parte2(self) -> str:
        # Não há parte 2; mantém rótulo distinto por segurança.
        return "clinica"

    def get_modulo(self) -> str:
        return "clinica_beleza"

    def aviso_validade_link(self) -> str:
        return "Link válido por <strong>2 horas</strong>."

    def prazo_token(self) -> timedelta:
        return timedelta(hours=2)

    def get_pagina_assinatura_path(self) -> str:
        return "/assinar-recibo/"

    def on_assinatura_concluida(self, payment, loja_id: int):
        logger.info("Recibo assinado — payment #%s (loja %s)", payment.id, loja_id)
