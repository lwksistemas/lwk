"""Models — Clínica Geral (consultório). Sem lógica de estética."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class Paciente(LojaIsolationMixin, models.Model):
    SEXO_CHOICES = (
        ("", "Não informado"),
        ("M", "Masculino"),
        ("F", "Feminino"),
        ("I", "Indefinido"),
    )

    numero_prontuario = models.CharField(max_length=30, blank=True, default="")
    medico_referencia = models.CharField(max_length=200, blank=True, default="")
    nome = models.CharField(max_length=200)
    nome_social = models.CharField(max_length=200, blank=True, default="")
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, blank=True, default="", choices=SEXO_CHOICES)
    estado_civil = models.CharField(max_length=40, blank=True, default="")
    cpf = models.CharField(max_length=14, blank=True, default="")
    rg = models.CharField(max_length=20, blank=True, default="")
    passaporte = models.CharField(max_length=30, blank=True, default="")
    nome_mae = models.CharField(max_length=200, blank=True, default="")
    tipo_sanguineo = models.CharField(max_length=8, blank=True, default="")
    telefone = models.CharField(max_length=30, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    cep = models.CharField(max_length=10, blank=True, default="")
    logradouro = models.CharField(max_length=200, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    complemento = models.CharField(max_length=80, blank=True, default="")
    bairro = models.CharField(max_length=100, blank=True, default="")
    cidade = models.CharField(max_length=100, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_paciente"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["loja_id", "is_active"], name="cg_pac_loja_act_idx"),
            models.Index(fields=["loja_id", "nome"], name="cg_pac_loja_nome_idx"),
        ]

    def __str__(self):
        return self.nome_social or self.nome


class Responsavel(LojaIsolationMixin, models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="responsaveis")
    nome = models.CharField(max_length=200)
    profissao = models.CharField(max_length=120, blank=True, default="")
    parentesco = models.CharField(max_length=80, blank=True, default="")
    telefone = models.CharField(max_length=30, blank=True, default="")

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_responsavel"


class ConvenioPaciente(LojaIsolationMixin, models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="convenios")
    convenio = models.CharField(max_length=120)
    plano = models.CharField(max_length=120, blank=True, default="")
    carteirinha = models.CharField(max_length=60, blank=True, default="")
    validade = models.DateField(null=True, blank=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_convenio"


class Consulta(LojaIsolationMixin, models.Model):
    TIPO_CHOICES = (
        ("consulta", "Consulta"),
        ("primeira", "Primeira consulta"),
        ("retorno", "Retorno"),
    )
    MODALIDADE_CHOICES = (
        ("presencial", "Consulta presencial"),
        ("tele", "Teleconsulta"),
    )
    STATUS_CHOICES = (
        ("agendado", "Agendado"),
        ("confirmado", "Confirmado"),
        ("recepcionado", "Recepcionado"),
        ("desmarcado", "Desmarcado"),
        ("faltou", "Faltou"),
    )

    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="consultas")
    data = models.DateField()
    hora = models.TimeField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="consulta")
    modalidade = models.CharField(max_length=20, choices=MODALIDADE_CHOICES, default="presencial")
    convenio = models.CharField(max_length=80, blank=True, default="PARTICULAR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="agendado")
    observacoes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_consulta"
        ordering = ["data", "hora"]
        indexes = [
            models.Index(fields=["loja_id", "data"], name="cg_cons_loja_data_idx"),
        ]
