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
    rne = models.CharField(max_length=30, blank=True, default="")
    pais_emissor = models.CharField(max_length=80, blank=True, default="")
    nome_mae = models.CharField(max_length=200, blank=True, default="")
    tipo_sanguineo = models.CharField(max_length=8, blank=True, default="")
    nacionalidade = models.CharField(max_length=80, blank=True, default="Brasileira")
    profissao = models.CharField(max_length=120, blank=True, default="")
    foto_url = models.CharField(max_length=500, blank=True, default="")
    telefone = models.CharField(max_length=30, blank=True, default="")
    telefone_fixo = models.CharField(max_length=30, blank=True, default="")
    quem_indicou = models.CharField(max_length=200, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    cep = models.CharField(max_length=10, blank=True, default="")
    logradouro = models.CharField(max_length=200, blank=True, default="")
    numero = models.CharField(max_length=20, blank=True, default="")
    complemento = models.CharField(max_length=80, blank=True, default="")
    bairro = models.CharField(max_length=100, blank=True, default="")
    cidade = models.CharField(max_length=100, blank=True, default="")
    uf = models.CharField(max_length=2, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")
    alergias = models.TextField(blank=True, default="")
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
        ("checkin", "Check-in"),
        ("recepcionado", "Recepcionado"),
        ("atendido", "Atendido"),
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
    duracao_minutos = models.PositiveSmallIntegerField(default=15)
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tele_sala_url = models.CharField(max_length=400, blank=True, default="")
    tele_token = models.CharField(max_length=64, blank=True, default="", db_index=True)
    tele_minutos = models.PositiveIntegerField(default=0)
    agendado_por = models.CharField(max_length=120, blank=True, default="")
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


class Tarefa(LojaIsolationMixin, models.Model):
    data = models.DateField()
    texto = models.CharField(max_length=240)
    concluida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_tarefa"
        ordering = ["-id"]


class ConfiguracaoConsultorio(LojaIsolationMixin, models.Model):
    hora_inicio = models.TimeField(default="08:00")
    hora_fim = models.TimeField(default="18:00")
    duracao_minutos = models.PositiveSmallIntegerField(default=15)
    endereco = models.CharField(max_length=240, blank=True, default="")
    telefone = models.CharField(max_length=30, blank=True, default="")
    especialidade = models.CharField(max_length=80, blank=True, default="Clínica médica")
    crm = models.CharField(max_length=30, blank=True, default="")
    medico_nome = models.CharField(max_length=200, blank=True, default="")
    teto_tele_minutos = models.PositiveIntegerField(default=600)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_config"


class Evolucao(LojaIsolationMixin, models.Model):
    consulta = models.OneToOneField(Consulta, on_delete=models.CASCADE, related_name="evolucao")
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="evolucoes")
    especialidade = models.CharField(max_length=80, blank=True, default="")
    subjetivo = models.TextField(blank=True, default="")
    objetivo = models.TextField(blank=True, default="")
    avaliacao = models.TextField(blank=True, default="")
    plano = models.TextField(blank=True, default="")
    ficha = models.JSONField(blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_evolucao"
        ordering = ["-id"]


class Prescricao(LojaIsolationMixin, models.Model):
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name="prescricoes")
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="prescricoes")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_prescricao"
        ordering = ["-id"]


class PrescricaoItem(LojaIsolationMixin, models.Model):
    prescricao = models.ForeignKey(Prescricao, on_delete=models.CASCADE, related_name="itens")
    medicamento = models.CharField(max_length=200)
    dosagem = models.CharField(max_length=80, blank=True, default="")
    posologia = models.CharField(max_length=240, blank=True, default="")
    quantidade = models.CharField(max_length=40, blank=True, default="")
    alerta_alergia = models.BooleanField(default=False)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_prescricao_item"


class LoteTiss(LojaIsolationMixin, models.Model):
    STATUS_CHOICES = (
        ("aberto", "Aberto"),
        ("fechado", "Fechado"),
    )
    numero = models.CharField(max_length=30, blank=True, default="")
    competencia = models.CharField(max_length=7, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="aberto")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_lote_tiss"
        ordering = ["-id"]


class GuiaTiss(LojaIsolationMixin, models.Model):
    lote = models.ForeignKey(LoteTiss, on_delete=models.SET_NULL, null=True, blank=True, related_name="guias")
    consulta = models.OneToOneField(Consulta, on_delete=models.CASCADE, related_name="guia_tiss")
    numero_guia = models.CharField(max_length=30, blank=True, default="")
    codigo_procedimento = models.CharField(max_length=20, blank=True, default="10101012")
    valor = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_guia_tiss"
        ordering = ["-id"]


class FechamentoCaixa(LojaIsolationMixin, models.Model):
    data = models.DateField()
    total_particular = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_convenio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_caixa"
        ordering = ["-data"]
        unique_together = ("loja_id", "data")


class PacienteAnexo(LojaIsolationMixin, models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name="anexos")
    nome = models.CharField(max_length=200)
    url = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_geral"
        db_table = "clinica_geral_anexo"
        ordering = ["-id"]
