"""Models — profissionais, horários e comissões."""
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


class Professional(ProfissionalBase):
    """Profissionais da clínica (herda de ProfissionalBase)"""

    CONSELHO_CHOICES = (
        ('CRM', 'CRM - Medicina'),
        ('CRO', 'CRO - Odontologia'),
        ('COREN', 'COREN - Enfermagem'),
        ('CRF', 'CRF - Farmácia'),
        ('CRP', 'CRP - Psicologia'),
        ('CRN', 'CRN - Nutrição'),
        ('CREFITO', 'CREFITO - Fisioterapia/TO'),
        ('CRBM', 'CRBM - Biomedicina'),
        ('CRMV', 'CRMV - Veterinária'),
        ('CRFa', 'CRFa - Fonoaudiologia'),
    )

    # Dados do prescritor para integração com a Memed (receituário/exames).
    conselho = models.CharField(
        max_length=10, blank=True, null=True,
        choices=CONSELHO_CHOICES, verbose_name="Conselho",
        help_text="Conselho de classe (CRM, COREN, CRF, etc.)",
    )
    conselho_uf = models.CharField(
        max_length=2, blank=True, null=True, verbose_name="UF do conselho",
    )
    cpf = models.CharField(
        max_length=14, blank=True, null=True, verbose_name="CPF",
        help_text="CPF do prescritor (usado para assinar na Memed).",
    )
    SEXO_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    )
    data_nascimento = models.DateField(
        blank=True, null=True, verbose_name="Data de nascimento",
        help_text="Data de nascimento do prescritor (usada no cadastro da Memed).",
    )
    sexo = models.CharField(
        max_length=1, blank=True, null=True, choices=SEXO_CHOICES,
        verbose_name="Sexo", help_text="Sexo do prescritor (usado no cadastro da Memed).",
    )

    class Meta(ProfissionalBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ['nome']

    def formatar_conselho(self) -> str:
        """Conselho com UF e número de registro — ex.: COREN-SP 123456."""
        conselho = (self.conselho or '').strip().upper()
        registro = (self.registro_profissional or '').strip()
        uf = (self.conselho_uf or '').strip().upper()
        if not conselho and not registro:
            return ''
        label = f'{conselho}-{uf}' if conselho and uf else conselho
        if label and registro:
            return f'{label} {registro}'
        return label or registro

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"




class ProfessionalCommission(LojaIsolationMixin, models.Model):
    """
    Configuração de comissão por profissional.
    Permite comissão por consulta (atendimento) e por procedimento específico.
    Cada tipo pode ser valor fixo (R$) ou percentual (%).
    """
    TIPO_CHOICES = (
        ('consulta', 'Por consulta (atendimento)'),
        ('procedimento', 'Por procedimento'),
    )
    MODO_CHOICES = (
        ('percentual', 'Percentual (%)'),
        ('fixo', 'Valor fixo (R$)'),
    )

    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='comissoes',
        verbose_name='Profissional',
    )
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES,
        verbose_name='Tipo de comissão',
    )
    modo = models.CharField(
        max_length=15, choices=MODO_CHOICES, default='percentual',
        verbose_name='Modo de cálculo',
    )
    valor = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name='Valor',
        help_text='Percentual (ex: 30.00 = 30%) ou valor fixo em R$.',
    )
    procedure = models.ForeignKey(
        'Procedure',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='comissoes',
        verbose_name='Procedimento',
        help_text='Obrigatório quando tipo = procedimento. Vazio em consulta.',
    )
    convenio = models.ForeignKey(
        'Convenio',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='comissoes_profissionais',
        verbose_name='Convênio',
        help_text='Opcional em procedimento: regra específica por convênio. Vazio = regra geral.',
    )
    local_atendimento = models.ForeignKey(
        'LocalAtendimento',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='comissoes',
        verbose_name='Local de atendimento',
        help_text='Obrigatório quando tipo = consulta: comissão para este local de atendimento.',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        db_table = 'clinica_beleza_professional_commissions'
        ordering = ['professional', 'tipo', 'procedure']
        verbose_name = 'Comissão do profissional'
        verbose_name_plural = 'Comissões dos profissionais'

    def __str__(self):
        if self.tipo == 'procedimento' and self.procedure:
            conv = f" ({self.convenio.nome})" if self.convenio_id else ''
            return f"{self.professional.nome} — {self.procedure.nome}{conv}: {self.valor_display}"
        if self.local_atendimento_id:
            return f"{self.professional.nome} — Consulta ({self.local_atendimento.nome}): {self.valor_display}"
        return f"{self.professional.nome} — Consulta (geral): {self.valor_display}"

    @property
    def valor_display(self):
        if self.modo == 'percentual':
            return f"{self.valor}%"
        return f"R$ {self.valor}"




class HorarioTrabalhoProfissional(HorarioTrabalhoProfissionalBase):
    """
    Dias e horários de trabalho por profissional (herda de HorarioTrabalhoProfissionalBase)
    Um registro por dia da semana em que o profissional trabalha (ex.: Seg 08:00-18:00).
    """
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='horarios_trabalho',
        verbose_name="Profissional",
    )

    class Meta(HorarioTrabalhoProfissionalBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Horário de trabalho (profissional)"
        verbose_name_plural = "Horários de trabalho (profissionais)"
        ordering = ['professional', 'dia_semana']
        unique_together = [['professional', 'dia_semana']]
        indexes = [
            models.Index(fields=['professional', 'dia_semana']),
            models.Index(fields=['loja_id', 'professional']),
        ]

    def __str__(self):
        return f"{self.professional.nome} - {self.get_dia_semana_display()}: {self.hora_entrada}-{self.hora_saida}"


