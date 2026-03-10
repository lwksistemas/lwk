"""
Models para Clínica da Beleza
Sistema completo de gestão de clínica estética
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from core.mixins import LojaIsolationMixin, LojaIsolationManager
from agenda_base.models import ClienteBase, ProfissionalBase, ServicoBase, HorarioTrabalhoProfissionalBase, BloqueioAgendaBase

User = get_user_model()


class Patient(ClienteBase):
    """Pacientes da clínica (herda de ClienteBase)"""
    allow_whatsapp = models.BooleanField(
        default=True,
        verbose_name="Permitir WhatsApp",
        help_text="Se desmarcado, o paciente não recebe mensagens por WhatsApp (LGPD).",
    )
    
    # Aliases para compatibilidade com código existente
    @property
    def name(self):
        return self.nome
    
    @name.setter
    def name(self, value):
        self.nome = value
    
    @property
    def phone(self):
        return self.telefone
    
    @phone.setter
    def phone(self, value):
        self.telefone = value
    
    @property
    def birth_date(self):
        return self.data_nascimento
    
    @birth_date.setter
    def birth_date(self, value):
        self.data_nascimento = value
    
    @property
    def address(self):
        return self.endereco
    
    @address.setter
    def address(self, value):
        self.endereco = value
    
    @property
    def notes(self):
        return self.observacoes
    
    @notes.setter
    def notes(self, value):
        self.observacoes = value
    
    @property
    def active(self):
        return self.is_active
    
    @active.setter
    def active(self, value):
        self.is_active = value

    class Meta(ClienteBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Professional(ProfissionalBase):
    """Profissionais da clínica (herda de ProfissionalBase)"""
    
    # Aliases para compatibilidade com código existente
    @property
    def name(self):
        return self.nome
    
    @name.setter
    def name(self, value):
        self.nome = value
    
    @property
    def specialty(self):
        return self.especialidade
    
    @specialty.setter
    def specialty(self, value):
        self.especialidade = value
    
    @property
    def phone(self):
        return self.telefone
    
    @phone.setter
    def phone(self, value):
        self.telefone = value
    
    @property
    def active(self):
        return self.is_active
    
    @active.setter
    def active(self, value):
        self.is_active = value

    class Meta(ProfissionalBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.especialidade}"


class Procedure(ServicoBase):
    """Procedimentos/Serviços oferecidos (herda de ServicoBase)"""
    
    # Aliases para compatibilidade com código existente
    @property
    def name(self):
        return self.nome
    
    @name.setter
    def name(self, value):
        self.nome = value
    
    @property
    def description(self):
        return self.descricao
    
    @description.setter
    def description(self, value):
        self.descricao = value
    
    @property
    def price(self):
        return self.preco
    
    @price.setter
    def price(self, value):
        self.preco = value
    
    @property
    def duration(self):
        return self.duracao_minutos
    
    @duration.setter
    def duration(self, value):
        self.duracao_minutos = value
    
    @property
    def active(self):
        return self.is_active
    
    @active.setter
    def active(self, value):
        self.is_active = value

    class Meta(ServicoBase.Meta):
        app_label = 'clinica_beleza'
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Appointment(LojaIsolationMixin, models.Model):
    """Agendamentos"""
    STATUS_CHOICES = (
        ('CONFIRMED', 'Confirmado'),
        ('PENDING', 'Pendente'),
        ('SCHEDULED', 'Agendado'),
        ('IN_PROGRESS', 'Em Atendimento'),
        ('COMPLETED', 'Concluído'),
        ('CANCELLED', 'Cancelado'),
        ('NO_SHOW', 'Faltou'),
    )

    date = models.DateTimeField(verbose_name="Data e Hora")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED', verbose_name="Status")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="Paciente")
    professional = models.ForeignKey(Professional, on_delete=models.CASCADE, verbose_name="Profissional")
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, verbose_name="Procedimento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    # Sincronização offline: version para detectar conflitos; updated_by_id = ID do user (schema public)
    version = models.PositiveIntegerField(default=1, verbose_name="Versão")
    updated_by_id = models.PositiveIntegerField(null=True, blank=True, verbose_name="Atualizado por (user id)")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date', 'status']),
            models.Index(fields=['professional', 'date']),
            models.Index(fields=['patient', 'date']),
            models.Index(fields=['loja_id', 'date']),
        ]

    def __str__(self):
        return f"{self.patient.nome} - {self.procedure.nome} - {self.date.strftime('%d/%m/%Y %H:%M')}"


class BloqueioHorario(BloqueioAgendaBase):
    """
    Bloqueio de horário na agenda (herda de BloqueioAgendaBase)
    profissional=None = bloqueio geral (todos os profissionais).
    """
    professional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Profissional",
        help_text="Deixe vazio para bloqueio geral (todos)",
    )
    
    # Campos adicionais específicos (mantém compatibilidade)
    motivo = models.CharField(max_length=100, verbose_name="Motivo")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    # Aliases para compatibilidade
    @property
    def data_inicio_dt(self):
        """Retorna data_inicio como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_inicio:
            return datetime.combine(self.data_inicio, self.horario_inicio)
        return datetime.combine(self.data_inicio, time.min)
    
    @property
    def data_fim_dt(self):
        """Retorna data_fim como datetime para compatibilidade"""
        from datetime import datetime, time
        if self.horario_fim:
            return datetime.combine(self.data_fim, self.horario_fim)
        return datetime.combine(self.data_fim, time.max)

    class Meta(BloqueioAgendaBase.Meta):
        app_label = "clinica_beleza"
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-data_inicio"]
        indexes = [
            models.Index(fields=['data_inicio', 'data_fim']),
            models.Index(fields=['professional', 'data_inicio']),
            models.Index(fields=['loja_id', 'data_inicio']),
        ]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"
    
    def save(self, *args, **kwargs):
        # Sincronizar motivo com titulo
        if not self.titulo:
            self.titulo = self.motivo
        # Definir tipo padrão se não especificado
        if not self.tipo:
            self.tipo = 'outros'
        super().save(*args, **kwargs)


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


class Payment(LojaIsolationMixin, models.Model):
    """Pagamentos"""
    PAYMENT_METHOD_CHOICES = (
        ('CASH', 'Dinheiro'),
        ('CREDIT_CARD', 'Cartão de Crédito'),
        ('DEBIT_CARD', 'Cartão de Débito'),
        ('PIX', 'PIX'),
        ('TRANSFER', 'Transferência'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pendente'),
        ('PAID', 'Pago'),
        ('CANCELLED', 'Cancelado'),
    )

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, verbose_name="Agendamento")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Método de Pagamento")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Status")
    payment_date = models.DateTimeField(blank=True, null=True, verbose_name="Data do Pagamento")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    comissao_percentual = models.PositiveSmallIntegerField(default=0, verbose_name="Comissão %")
    comissao_valor = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Comissão R$")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'payment_date']),
            models.Index(fields=['appointment', 'status']),
            models.Index(fields=['loja_id', 'payment_date']),
        ]

    def save(self, *args, **kwargs):
        if self.amount is not None and self.comissao_percentual is not None:
            self.comissao_valor = (self.amount * self.comissao_percentual / 100).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento {self.id} - R$ {self.amount}"


class CampanhaPromocao(LojaIsolationMixin, models.Model):
    """
    Campanha de promoção: mensagem enviada em massa aos pacientes via WhatsApp.
    Tabela isolada por loja: cada loja tem sua própria tabela no schema (loja_*).
    Router: clinica_beleza está em loja_apps; migrate_all_lojas aplica em cada schema.
    """
    titulo = models.CharField(max_length=200, verbose_name="Título da campanha")
    mensagem = models.TextField(verbose_name="Mensagem (enviada por WhatsApp)")
    data_inicio = models.DateField(blank=True, null=True, verbose_name="Vigência início")
    data_fim = models.DateField(blank=True, null=True, verbose_name="Vigência fim")
    ativa = models.BooleanField(default=True, verbose_name="Ativa")
    enviada_em = models.DateTimeField(blank=True, null=True, verbose_name="Enviada em")
    total_enviados = models.PositiveIntegerField(default=0, verbose_name="Total de mensagens enviadas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")

    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Campanha de promoção"
        verbose_name_plural = "Campanhas de promoções"
        ordering = ['-created_at']

    def __str__(self):
        return self.titulo
