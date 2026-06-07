"""
Adapter de assinatura digital do termo de consentimento — Clínica da Beleza.
Cada procedimento tem termo e fluxo de assinatura independentes.
"""
import logging
from datetime import timedelta

from django.utils import timezone

from core.assinatura_service import AssinaturaAdapter
from .consentimento_service import sincronizar_status_consulta

logger = logging.getLogger(__name__)


class ConsultaTermoAssinaturaAdapter(AssinaturaAdapter):

    def _consulta(self, termo_proc):
        return termo_proc.consulta

    def _nome_procedimento(self, termo_proc) -> str:
        return termo_proc.procedure.nome if termo_proc.procedure_id else 'Procedimento clínico'

    def get_titulo(self, termo_proc) -> str:
        return self._nome_procedimento(termo_proc)

    def get_valor_display(self, termo_proc) -> str:
        return ''

    def incluir_valor_no_email(self) -> bool:
        return False

    def get_rotulo_titulo_email(self) -> str:
        return 'Procedimento'

    def get_assunto_email_parte1(self, termo_proc, loja_nome: str) -> str:
        return f'📄 Termo de Consentimento — {self._nome_procedimento(termo_proc)}'

    def get_assunto_email_parte2(self, termo_proc, loja_nome: str) -> str:
        consulta = self._consulta(termo_proc)
        paciente = consulta.patient.nome if consulta.patient else 'Paciente'
        return f'✅ Paciente assinou — {self._nome_procedimento(termo_proc)} ({paciente})'

    def get_destinatario_parte1(self, termo_proc) -> tuple[str, str]:
        consulta = self._consulta(termo_proc)
        paciente = consulta.patient
        if not paciente:
            return ('', '')
        email = (getattr(paciente, 'email', '') or '').strip()
        return (paciente.nome, email)

    def get_destinatario_parte2(self, termo_proc, loja_id: int) -> tuple[str, str]:
        consulta = self._consulta(termo_proc)
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

    def get_tipo_documento_label(self, termo_proc) -> str:
        return 'Termo de Consentimento Esclarecido'

    def get_info_extra_email(self, termo_proc) -> dict:
        consulta = self._consulta(termo_proc)
        info = {}
        if consulta.professional:
            info['Profissional'] = consulta.professional.nome
        if consulta.data_inicio:
            info['Data do atendimento'] = timezone.localtime(consulta.data_inicio).strftime('%d/%m/%Y')
        return info

    def criar_registro_assinatura(self, termo_proc, tipo, nome, email, token, loja_id):
        from .models import ConsultaAssinaturaTermo
        return ConsultaAssinaturaTermo.objects.create(
            consulta=termo_proc.consulta,
            termo_procedimento=termo_proc,
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
        qs = ConsultaAssinaturaTermo.objects.select_related(
            'consulta', 'consulta__patient', 'consulta__professional',
            'termo_procedimento', 'termo_procedimento__procedure',
        )
        try:
            return qs.get(token=token)
        except ConsultaAssinaturaTermo.DoesNotExist:
            token_decoded = unquote(token)
            if token_decoded != token:
                try:
                    return qs.get(token=token_decoded)
                except ConsultaAssinaturaTermo.DoesNotExist:
                    pass
        return None

    def get_documento_da_assinatura(self, assinatura):
        if assinatura.termo_procedimento_id:
            return assinatura.termo_procedimento
        from .consentimento_service import garantir_termos_procedimento
        termos = garantir_termos_procedimento(assinatura.consulta)
        if len(termos) == 1:
            return termos[0]
        raise ValueError('Assinatura legada sem procedimento vinculado.')

    def atualizar_status_assinatura(self, termo_proc, novo_status: str):
        termo_proc.status_assinatura_termo = novo_status
        termo_proc.save(update_fields=['status_assinatura_termo', 'updated_at'])
        sincronizar_status_consulta(termo_proc.consulta)

    def get_status_assinatura(self, termo_proc) -> str:
        return termo_proc.status_assinatura_termo or 'rascunho'

    def gerar_pdf(self, termo_proc, incluir_assinaturas: bool = False):
        from .termo_consentimento_pdf import gerar_pdf_termo_consentimento
        return gerar_pdf_termo_consentimento(termo_proc, incluir_assinaturas=incluir_assinaturas)

    def get_todos_destinatarios_pdf_final(self, termo_proc, loja_id: int) -> list[str]:
        consulta = self._consulta(termo_proc)
        emails = []
        if consulta.patient and consulta.patient.email:
            emails.append(consulta.patient.email.strip())
        _, email_prof = self.get_destinatario_parte2(termo_proc, loja_id)
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

    def deletar_assinaturas_pendentes(self, termo_proc, tipo: str):
        from .models import ConsultaAssinaturaTermo
        ConsultaAssinaturaTermo.objects.filter(
            termo_procedimento=termo_proc, tipo=tipo, assinado=False,
        ).delete()

    def on_assinatura_concluida(self, termo_proc, loja_id: int):
        logger.info(
            'Termo de consentimento assinado — consulta #%s, procedimento %s',
            termo_proc.consulta_id,
            self._nome_procedimento(termo_proc),
        )
