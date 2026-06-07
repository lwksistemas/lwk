"""
Adapter de assinatura digital do termo de consentimento — Clínica da Beleza.
Reutiliza core.assinatura_service (mesmo padrão do Hotel).
"""
import logging
from datetime import timedelta

from django.utils import timezone

from core.assinatura_service import AssinaturaAdapter
from .consentimento_service import montar_conteudo_termo_consentimento, nomes_procedimentos_termo

logger = logging.getLogger(__name__)


class ConsultaTermoAssinaturaAdapter(AssinaturaAdapter):

    def get_titulo(self, consulta) -> str:
        return nomes_procedimentos_termo(consulta)

    def get_valor_display(self, consulta) -> str:
        return ''

    def incluir_valor_no_email(self) -> bool:
        return False

    def get_rotulo_titulo_email(self) -> str:
        return 'Procedimento(s)'

    def get_assunto_email_parte1(self, consulta, loja_nome: str) -> str:
        return f'📄 Termo de Consentimento — {nomes_procedimentos_termo(consulta)}'

    def get_assunto_email_parte2(self, consulta, loja_nome: str) -> str:
        paciente = consulta.patient.nome if consulta.patient else 'Paciente'
        return f'✅ Paciente assinou — {nomes_procedimentos_termo(consulta)} ({paciente})'

    def get_destinatario_parte1(self, consulta) -> tuple[str, str]:
        paciente = consulta.patient
        if not paciente:
            return ('', '')
        email = (getattr(paciente, 'email', '') or '').strip()
        return (paciente.nome, email)

    def get_destinatario_parte2(self, consulta, loja_id: int) -> tuple[str, str]:
        prof = consulta.professional
        if prof:
            email = (getattr(prof, 'email', '') or '').strip()
            if email:
                return (prof.nome, email)
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
        if loja and loja.owner and loja.owner.email:
            return (prof.nome if prof else 'Profissional', loja.owner.email)
        return (prof.nome if prof else 'Profissional', '')

    def get_tipo_documento_label(self, consulta) -> str:
        return 'Termo de Consentimento Esclarecido'

    def get_info_extra_email(self, consulta) -> dict:
        """Resumo do e-mail — sem repetir nome do paciente (já está no cumprimento)."""
        info = {}
        if consulta.professional:
            info['Profissional'] = consulta.professional.nome
        if consulta.data_inicio:
            info['Data do atendimento'] = timezone.localtime(consulta.data_inicio).strftime('%d/%m/%Y')
        return info

    def criar_registro_assinatura(self, consulta, tipo, nome, email, token, loja_id):
        from .models import ConsultaAssinaturaTermo
        return ConsultaAssinaturaTermo.objects.create(
            consulta=consulta,
            tipo=tipo,
            nome_assinante=nome,
            email_assinante=email,
            token=token,
            token_expira_em=timezone.now() + timedelta(days=7),
            loja_id=loja_id,
        )

    def buscar_assinatura_por_token(self, token: str):
        from .models import ConsultaAssinaturaTermo
        from core.assinatura_service import normalizar_token_url
        from urllib.parse import unquote

        token = normalizar_token_url(token)
        try:
            return ConsultaAssinaturaTermo.objects.select_related(
                'consulta', 'consulta__patient', 'consulta__professional',
            ).get(token=token)
        except ConsultaAssinaturaTermo.DoesNotExist:
            token_decoded = unquote(token)
            if token_decoded != token:
                try:
                    return ConsultaAssinaturaTermo.objects.select_related(
                        'consulta', 'consulta__patient', 'consulta__professional',
                    ).get(token=token_decoded)
                except ConsultaAssinaturaTermo.DoesNotExist:
                    pass
        return None

    def get_documento_da_assinatura(self, assinatura):
        return assinatura.consulta

    def atualizar_status_assinatura(self, consulta, novo_status: str):
        consulta.status_assinatura_termo = novo_status
        consulta.save(update_fields=['status_assinatura_termo', 'updated_at'])

    def get_status_assinatura(self, consulta) -> str:
        return consulta.status_assinatura_termo or 'rascunho'

    def gerar_pdf(self, consulta, incluir_assinaturas: bool = False):
        from .termo_consentimento_pdf import gerar_pdf_termo_consentimento
        if not consulta.conteudo_termo_consentimento:
            consulta.conteudo_termo_consentimento = montar_conteudo_termo_consentimento(consulta)
            consulta.save(update_fields=['conteudo_termo_consentimento', 'updated_at'])
        return gerar_pdf_termo_consentimento(consulta, incluir_assinaturas=incluir_assinaturas)

    def get_todos_destinatarios_pdf_final(self, consulta, loja_id: int) -> list[str]:
        emails = []
        if consulta.patient and consulta.patient.email:
            emails.append(consulta.patient.email.strip())
        _, email_prof = self.get_destinatario_parte2(consulta, loja_id)
        if email_prof and email_prof not in emails:
            emails.append(email_prof)
        return emails

    def get_label_parte1(self) -> str:
        return 'paciente'

    def get_label_parte2(self) -> str:
        return 'profissional'

    def get_modulo(self) -> str:
        return 'clinica_beleza'

    def get_pagina_assinatura_path(self) -> str:
        return '/assinar-consentimento/'

    def deletar_assinaturas_pendentes(self, consulta, tipo: str):
        from .models import ConsultaAssinaturaTermo
        ConsultaAssinaturaTermo.objects.filter(
            consulta=consulta, tipo=tipo, assinado=False,
        ).delete()

    def on_assinatura_concluida(self, consulta, loja_id: int):
        logger.info('Termo de consentimento assinado — consulta #%s', consulta.id)
