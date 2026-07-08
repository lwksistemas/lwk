"""Models — consultas, evoluções e Memed."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models

from agenda_base.models import (
    BloqueioAgendaBase,
    ClienteBase,
    HorarioTrabalhoProfissionalBase,
    ProfissionalBase,
    ServicoBase,
)
from core.mixins import LojaIsolationManager, LojaIsolationMixin

User = get_user_model()

from .appointments import Appointment
from .convenios import Convenio, LocalAtendimento
from .patients import Patient
from .procedures import Procedure, ProcedureProtocol
from .professionals import Professional

class Consulta(LojaIsolationMixin, models.Model):
    """Consulta clínica — criada automaticamente ao mudar status do agendamento na agenda."""
    STATUS_CHOICES = (
        ('RECEBER', 'Receber'),
        ('SCHEDULED', 'Agendada'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
    )

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='consulta',
        verbose_name='Agendamento',
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consultas', verbose_name='Cliente')
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, related_name='consultas', verbose_name='Profissional',
    )
    procedure = models.ForeignKey(
        Procedure, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='consultas', verbose_name='Procedimento',
    )
    protocol = models.ForeignKey(
        ProcedureProtocol,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Protocolo aplicado',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name='Status')
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name='Início')
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name='Fim')
    observacoes_gerais = models.TextField(blank=True, default='', verbose_name='Observações gerais')
    protocolo_notas = models.TextField(blank=True, default='', verbose_name='Notas do protocolo')
    valor_consulta = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    retorno_gratuito = models.BooleanField(
        default=False,
        verbose_name='Retorno gratuito',
        help_text='Taxa de consulta isenta por retorno dentro do prazo configurado.',
    )
    RETORNO_TIPO_CHOICES = (
        ('', '—'),
        ('procedimento', 'Por procedimento'),
        ('consulta', 'Por consulta'),
    )
    retorno_tipo = models.CharField(
        max_length=20,
        choices=RETORNO_TIPO_CHOICES,
        blank=True,
        default='',
        verbose_name='Tipo de retorno',
    )
    local_atendimento = models.ForeignKey(
        'LocalAtendimento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Local de atendimento',
    )
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas',
        verbose_name='Convênio',
    )
    STATUS_ASSINATURA_TERMO_CHOICES = (
        ('rascunho', 'Rascunho'),
        ('aguardando_paciente', 'Aguardando Paciente'),
        ('aguardando_profissional', 'Aguardando Profissional'),
        ('concluido', 'Concluído'),
    )
    status_assinatura_termo = models.CharField(
        max_length=30,
        choices=STATUS_ASSINATURA_TERMO_CHOICES,
        default='rascunho',
        verbose_name='Status assinatura termo',
    )
    conteudo_termo_consentimento = models.TextField(
        blank=True, default='', verbose_name='Conteúdo do termo de consentimento',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consultas'
        ordering = ['-data_inicio', '-created_at']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        indexes = [
            models.Index(fields=['patient', 'status']),
            models.Index(fields=['loja_id', 'status']),
        ]

    def __str__(self):
        proc = self.procedure.nome if self.procedure_id and self.procedure else 'Sem procedimento'
        return f'Consulta {self.patient.nome} — {proc}'

    @property
    def duracao_minutos(self):
        if self.data_inicio and self.data_fim:
            return int((self.data_fim - self.data_inicio).total_seconds() / 60)
        return None


class ConsultaTermoProcedimento(LojaIsolationMixin, models.Model):
    """Termo de consentimento de um procedimento específico na consulta — assinatura independente."""

    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE, related_name='termos_procedimentos',
    )
    procedure = models.ForeignKey(
        Procedure, on_delete=models.CASCADE, related_name='termos_consulta',
    )
    conteudo_termo = models.TextField(blank=True, default='', verbose_name='Conteúdo do termo')
    status_assinatura_termo = models.CharField(
        max_length=30,
        choices=Consulta.STATUS_ASSINATURA_TERMO_CHOICES,
        default='rascunho',
        verbose_name='Status assinatura',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consulta_termo_procedimento'
        ordering = ['procedure__nome']
        verbose_name = 'Termo de procedimento'
        verbose_name_plural = 'Termos de procedimentos'
        constraints = [
            models.UniqueConstraint(fields=['consulta', 'procedure'], name='clin_cb_termo_cons_proc_uniq'),
        ]
        indexes = [
            models.Index(fields=['consulta', 'status_assinatura_termo'], name='clin_cb_termo_cons_st_idx'),
        ]

    def __str__(self):
        return f'{self.procedure.nome} — consulta #{self.consulta_id}'


class ConsultaAssinaturaTermo(LojaIsolationMixin, models.Model):
    """Assinatura digital do termo de consentimento esclarecido."""

    TIPO_CHOICES = (
        ('paciente', 'Paciente'),
        ('profissional', 'Profissional'),
    )

    consulta = models.ForeignKey(
        Consulta, on_delete=models.CASCADE, related_name='assinaturas_termo',
    )
    termo_procedimento = models.ForeignKey(
        ConsultaTermoProcedimento,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='assinaturas',
    )
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    nome_assinante = models.CharField(max_length=200)
    email_assinante = models.EmailField()
    ip_address = models.GenericIPAddressField(default='0.0.0.0')
    timestamp = models.DateTimeField(auto_now_add=True)
    user_agent = models.TextField(blank=True, default='')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    token_expira_em = models.DateTimeField()
    assinado = models.BooleanField(default=False)
    assinado_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consulta_assinaturas_termo'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['loja_id', 'token'], name='clin_cb_assin_loja_tok_idx'),
            models.Index(fields=['consulta', 'tipo'], name='clin_cb_assin_cons_tipo_idx'),
            models.Index(fields=['termo_procedimento', 'tipo'], name='clin_cb_assin_termo_tipo_idx'),
        ]

    def __str__(self):
        status = 'Assinado' if self.assinado else 'Pendente'
        return f'{self.get_tipo_display()} — {self.nome_assinante} ({status})'

    @property
    def is_expirado(self):
        from django.utils import timezone
        return timezone.now() > self.token_expira_em


class PrescricaoMemed(LojaIsolationMixin, models.Model):
    """
    Prescrição emitida na Memed (receituário/exames), registrada no histórico do
    paciente a partir do evento `prescricaoImpressa` capturado no frontend.
    """
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prescricoes_memed',
        verbose_name='Consulta',
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='prescricoes_memed', verbose_name='Cliente',
    )
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Profissional',
    )
    prescricao_id = models.CharField(
        max_length=64, blank=True, default='', verbose_name='ID na Memed',
        help_text='Identificador da prescrição retornado pela Memed.',
    )
    resumo = models.TextField(
        blank=True, default='', verbose_name='Resumo',
        help_text='Lista legível dos itens prescritos (medicamentos/exames).',
    )
    itens = models.JSONField(
        default=list, blank=True, verbose_name='Itens',
        help_text='Itens estruturados da prescrição (nome, posologia, tipo, receituário).',
    )
    pdf_url = models.URLField(
        max_length=500, blank=True, default='', verbose_name='URL do PDF',
        help_text='Link para o PDF da prescrição gerado pela Memed.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_prescricoes_memed'
        ordering = ['-created_at']
        verbose_name = 'Prescrição Memed'
        verbose_name_plural = 'Prescrições Memed'

    def __str__(self):
        return f'Prescrição {self.patient.nome} — {self.created_at:%d/%m/%Y %H:%M}'




class ConsultaEvolucao(LojaIsolationMixin, models.Model):
    """Evolução registrada durante ou após a consulta."""
    consulta = models.ForeignKey(
        Consulta,
        on_delete=models.CASCADE,
        related_name='evolucoes',
        verbose_name='Consulta',
    )
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='evolucoes', verbose_name='Cliente')
    professional = models.ForeignKey(
        Professional, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Profissional',
    )
    descricao = models.TextField(blank=True, default='', verbose_name='Evolução')
    procedimento_realizado = models.TextField(blank=True, default='')
    produtos_utilizados = models.TextField(blank=True, default='')
    orientacoes = models.TextField(blank=True, default='')
    protocolo_snapshot = models.TextField(blank=True, default='', help_text='Texto do protocolo aplicado')
    satisfacao = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_consulta_evolucoes'
        ordering = ['-created_at']
        verbose_name = 'Evolução da consulta'
        verbose_name_plural = 'Evoluções das consultas'

    def __str__(self):
        return f'Evolução {self.patient.nome} — {self.created_at:%d/%m/%Y %H:%M}'




class MemedTimbrado(LojaIsolationMixin, models.Model):
    """
    PDF timbrado A4 da clínica (cabeçalho/rodapé) para receituário e exames na Memed.
    Um arquivo por loja; aplicado a cada prescritor via API da Memed ao salvar/upload.
    """
    pdf = models.BinaryField(
        verbose_name='PDF timbrado',
        help_text='Arquivo PDF A4 com papel timbrado da clínica.',
    )
    pdf_nome = models.CharField(max_length=255, blank=True, default='', verbose_name='Nome do arquivo')
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_memed_timbrado'
        verbose_name = 'Timbrado Memed'
        verbose_name_plural = 'Timbrados Memed'

    def __str__(self):
        return self.pdf_nome or f'Timbrado loja {self.loja_id}'

# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTOS CLÍNICOS — Templates reutilizáveis e documentos gerados
# ═══════════════════════════════════════════════════════════════════════════════

