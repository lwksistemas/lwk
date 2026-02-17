"""
Models para Clínica da Beleza
Sistema completo de gestão de clínica estética
"""
from decimal import Decimal
from django.db import models
from django.contrib.auth import get_user_model
from core.mixins import LojaIsolationMixin, LojaIsolationManager

User = get_user_model()


class Patient(LojaIsolationMixin, models.Model):
    """Pacientes da clínica"""
    name = models.CharField(max_length=150, verbose_name="Nome")
    phone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    birth_date = models.DateField(blank=True, null=True, verbose_name="Data de Nascimento")
    address = models.TextField(blank=True, null=True, verbose_name="Endereço")
    notes = models.TextField(blank=True, null=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    allow_whatsapp = models.BooleanField(
        default=True,
        verbose_name="Permitir WhatsApp",
        help_text="Se desmarcado, o paciente não recebe mensagens por WhatsApp (LGPD).",
    )
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['name']

    def __str__(self):
        return self.name


class Professional(LojaIsolationMixin, models.Model):
    """Profissionais da clínica"""
    name = models.CharField(max_length=150, verbose_name="Nome")
    specialty = models.CharField(max_length=150, verbose_name="Especialidade")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.specialty}"


class Procedure(LojaIsolationMixin, models.Model):
    """Procedimentos/Serviços oferecidos"""
    name = models.CharField(max_length=150, verbose_name="Nome")
    description = models.TextField(blank=True, null=True, verbose_name="Descrição")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço")
    duration = models.IntegerField(help_text="Duração em minutos", verbose_name="Duração")
    active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = 'clinica_beleza'
        verbose_name = "Procedimento"
        verbose_name_plural = "Procedimentos"
        ordering = ['name']

    def __str__(self):
        return self.name


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

    def __str__(self):
        return f"{self.patient.name} - {self.procedure.name} - {self.date.strftime('%d/%m/%Y %H:%M')}"


class BloqueioHorario(LojaIsolationMixin, models.Model):
    """
    Bloqueio de horário na agenda (almoço, férias, manutenção, evento).
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
    data_inicio = models.DateTimeField(verbose_name="Início")
    data_fim = models.DateTimeField(verbose_name="Fim")
    motivo = models.CharField(max_length=100, verbose_name="Motivo")
    observacoes = models.TextField(blank=True, null=True, verbose_name="Observações")
    criado_em = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        verbose_name = "Bloqueio de Horário"
        verbose_name_plural = "Bloqueios de Horário"
        ordering = ["-data_inicio"]

    def __str__(self):
        return f"{self.motivo} ({self.data_inicio} - {self.data_fim})"


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

    def save(self, *args, **kwargs):
        if self.amount is not None and self.comissao_percentual is not None:
            self.comissao_valor = (self.amount * self.comissao_percentual / 100).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento {self.id} - R$ {self.amount}"
