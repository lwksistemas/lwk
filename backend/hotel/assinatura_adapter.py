"""
Adapter de assinatura digital para Reservas de Hotel.
Implementa a interface AssinaturaAdapter do core.
"""
import logging
from datetime import timedelta
from django.utils import timezone

from core.assinatura_service import AssinaturaAdapter

logger = logging.getLogger(__name__)


class ReservaAssinaturaAdapter(AssinaturaAdapter):

    def get_titulo(self, reserva) -> str:
        hospede = reserva.hospede.nome if reserva.hospede else 'Hóspede'
        quarto = reserva.quarto.numero if reserva.quarto else '?'
        return f'Reserva {hospede} - Quarto {quarto}'

    def get_valor_display(self, reserva) -> str:
        return f'R$ {reserva.valor_total or "0,00"}'

    def get_destinatario_parte1(self, reserva) -> tuple[str, str]:
        """Hóspede é a parte 1."""
        hospede = reserva.hospede
        return (hospede.nome, hospede.email) if hospede else ('', '')

    def get_destinatario_parte2(self, reserva, loja_id: int) -> tuple[str, str]:
        """Funcionário logado ou admin da loja é a parte 2."""
        # Tentar pegar do request (será passado via contexto)
        nome = reserva.nome_funcionario_assinatura or ''
        if nome:
            # Buscar email do funcionário pelo nome
            from .models import Funcionario
            func = Funcionario.objects.filter(loja_id=loja_id, nome__icontains=nome, is_active=True).first()
            if func and func.email:
                return (func.nome, func.email)

        # Fallback: admin da loja
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
        if loja and loja.owner:
            return (loja.owner.get_full_name() or loja.owner.username, loja.owner.email)
        return ('Funcionário', '')

    def get_tipo_documento_label(self, reserva) -> str:
        return 'Confirmação de Reserva'

    def get_info_extra_email(self, reserva) -> dict:
        info = {}
        if reserva.quarto:
            info['Quarto'] = f'{reserva.quarto.numero} - {reserva.quarto.nome or reserva.quarto.tipo or ""}'.strip(' -')
        if reserva.data_checkin:
            info['Check-in'] = reserva.data_checkin.strftime('%d/%m/%Y')
        if reserva.data_checkout:
            info['Check-out'] = reserva.data_checkout.strftime('%d/%m/%Y')
        if reserva.adultos:
            info['Hóspedes'] = f'{reserva.adultos} adulto(s)'
            if reserva.criancas:
                info['Hóspedes'] += f', {reserva.criancas} criança(s)'
        return info

    def criar_registro_assinatura(self, reserva, tipo, nome, email, token, loja_id):
        from .models import ReservaAssinatura
        return ReservaAssinatura.objects.create(
            reserva=reserva,
            tipo=tipo,
            nome_assinante=nome,
            email_assinante=email,
            token=token,
            token_expira_em=timezone.now() + timedelta(days=7),
            loja_id=loja_id,
        )

    def buscar_assinatura_por_token(self, token: str):
        from .models import ReservaAssinatura
        from core.assinatura_service import normalizar_token_url
        from urllib.parse import unquote

        token = normalizar_token_url(token)
        try:
            return ReservaAssinatura.objects.select_related('reserva', 'reserva__hospede', 'reserva__quarto').get(token=token)
        except ReservaAssinatura.DoesNotExist:
            token_decoded = unquote(token)
            if token_decoded != token:
                try:
                    return ReservaAssinatura.objects.select_related('reserva', 'reserva__hospede', 'reserva__quarto').get(token=token_decoded)
                except ReservaAssinatura.DoesNotExist:
                    pass
        return None

    def get_documento_da_assinatura(self, assinatura):
        return assinatura.reserva

    def atualizar_status_assinatura(self, reserva, novo_status: str):
        reserva.status_assinatura = novo_status
        reserva.save(update_fields=['status_assinatura', 'updated_at'])

    def get_status_assinatura(self, reserva) -> str:
        return reserva.status_assinatura

    def gerar_pdf(self, reserva, incluir_assinaturas: bool = False):
        from .pdf_reserva import gerar_pdf_reserva
        return gerar_pdf_reserva(reserva, incluir_assinaturas=incluir_assinaturas)

    def get_todos_destinatarios_pdf_final(self, reserva, loja_id: int) -> list[str]:
        emails = []
        if reserva.hospede and reserva.hospede.email:
            emails.append(reserva.hospede.email)
        # Funcionário ou admin
        _, email_func = self.get_destinatario_parte2(reserva, loja_id)
        if email_func and email_func not in emails:
            emails.append(email_func)
        return emails

    def get_label_parte1(self) -> str:
        return 'hospede'

    def get_label_parte2(self) -> str:
        return 'funcionario'

    def get_modulo(self) -> str:
        return 'hotel'

    def get_pagina_assinatura_path(self) -> str:
        return '/assinar-reserva/'

    def deletar_assinaturas_pendentes(self, reserva, tipo: str):
        from .models import ReservaAssinatura
        ReservaAssinatura.objects.filter(reserva=reserva, tipo=tipo, assinado=False).delete()

    def on_assinatura_concluida(self, reserva, loja_id: int):
        """Quando ambas as partes assinaram, muda status da reserva para Confirmada."""
        from .models import Reserva
        if reserva.status not in (Reserva.STATUS_CANCELADA, Reserva.STATUS_CHECKOUT, Reserva.STATUS_CHECKIN):
            reserva.status = Reserva.STATUS_CONFIRMADA
            reserva.save(update_fields=['status', 'updated_at'])
            logger.info(f'Reserva #{reserva.id} confirmada automaticamente após assinatura digital.')
