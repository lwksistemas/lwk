"""Modelos do RIS Radiologia LWK (multi-tenant)."""
from __future__ import annotations

import uuid

from django.db import models
from django.utils import timezone

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class PacienteRadiologia(LojaIsolationMixin, models.Model):
    """Paciente do fluxo de exames de imagem."""

    nome = models.CharField(max_length=200)
    cpf = models.CharField(max_length=14, blank=True, default="")
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(
        max_length=1,
        blank=True,
        default="",
        choices=(("M", "Masculino"), ("F", "Feminino"), ("O", "Outro")),
    )
    telefone = models.CharField(max_length=20, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_paciente"
        ordering = ["nome"]
        indexes = [
            models.Index(fields=["loja_id", "cpf"], name="rad_pac_loja_cpf_idx"),
            models.Index(fields=["loja_id", "is_active"], name="rad_pac_loja_ativo_idx"),
        ]

    def __str__(self) -> str:
        return self.nome


class Equipamento(LojaIsolationMixin, models.Model):
    """Modalidade / aparelho (AE Title único por clínica)."""

    nome = models.CharField(max_length=120)
    ae_title = models.CharField(max_length=16, help_text="Calling AE Title do aparelho (ex: LWK_US_0001)")
    modality = models.CharField(
        max_length=8,
        default="US",
        help_text="Código DICOM: US, CR, DX, MG, CT, MR…",
    )
    fabricante = models.CharField(max_length=80, blank=True, default="")
    modelo = models.CharField(max_length=80, blank=True, default="")
    numero_serie = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Serial do ultrassom — vincula aparelho à clínica (CPF/CNPJ da loja)",
    )
    codigo_vinculo = models.CharField(
        max_length=16,
        blank=True,
        default="",
        db_index=True,
        help_text="Código aleatório LWK para parear/enviar exames deste aparelho",
    )
    vinculado_em = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Quando o exame de vínculo DICOM confirmou o serial do aparelho",
    )
    orthanc_study_id_vinculo = models.CharField(max_length=64, blank=True, default="")
    station_name = models.CharField(max_length=64, blank=True, default="")
    suporte_dicom_storage = models.BooleanField(default=True)
    suporte_mwl = models.BooleanField(default=True)
    suporte_sr = models.BooleanField(default=False)
    cobranca_mensal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_equipamento"
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "ae_title"],
                name="rad_equip_loja_aet_uniq",
            ),
            models.UniqueConstraint(
                fields=["loja_id", "numero_serie"],
                condition=~models.Q(numero_serie=""),
                name="rad_equip_loja_serial_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ae_title})"


class Procedimento(LojaIsolationMixin, models.Model):
    """Catálogo de procedimentos / protocolos."""

    codigo = models.CharField(max_length=32, blank=True, default="")
    nome = models.CharField(max_length=200)
    modality = models.CharField(max_length=8, default="US")
    descricao = models.TextField(blank=True, default="")
    template_laudo = models.TextField(
        blank=True,
        default="",
        help_text="Texto-base do laudo (placeholders opcionais)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_procedimento"
        ordering = ["nome"]

    def __str__(self) -> str:
        return self.nome


class PedidoExame(LojaIsolationMixin, models.Model):
    """Pedido RIS → gera AccessionNumber / Study UID e item MWL."""

    class Status(models.TextChoices):
        AGENDADO = "agendado", "Agendado"
        NA_WORKLIST = "na_worklist", "Na worklist"
        EM_AQUISICAO = "em_aquisicao", "Em aquisição"
        IMAGENS_RECEBIDAS = "imagens_recebidas", "Imagens recebidas"
        EM_LAUDO = "em_laudo", "Em laudo"
        LAUDADO = "laudado", "Laudado"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"
        ORFAO = "orfao", "Estudo órfão"

    paciente = models.ForeignKey(
        PacienteRadiologia,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    procedimento = models.ForeignKey(
        Procedimento,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    equipamento = models.ForeignKey(
        Equipamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pedidos",
    )
    medico_solicitante = models.CharField(max_length=200, blank=True, default="")
    crm_solicitante = models.CharField(max_length=32, blank=True, default="")
    indicacao_clinica = models.TextField(blank=True, default="")
    agendado_para = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.AGENDADO,
        db_index=True,
    )
    accession_number = models.CharField(max_length=64, blank=True, default="", db_index=True)
    study_instance_uid = models.CharField(max_length=128, blank=True, default="", db_index=True)
    orthanc_study_id = models.CharField(max_length=64, blank=True, default="")
    dicom_media_url = models.TextField(
        blank=True,
        default="",
        help_text="ZIP DICOM arquivado no media server (pasta dicom/{paciente}/)",
    )
    dicom_instance_count = models.PositiveIntegerField(default=0)
    dicom_synced_at = models.DateTimeField(null=True, blank=True)
    mwl_synced_at = models.DateTimeField(null=True, blank=True)
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_pedido_exame"
        ordering = ["-agendado_para", "-id"]
        indexes = [
            models.Index(fields=["loja_id", "status"], name="rad_ped_loja_status_idx"),
            models.Index(fields=["loja_id", "accession_number"], name="rad_ped_loja_acc_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["loja_id", "study_instance_uid"],
                condition=~models.Q(study_instance_uid=""),
                name="rad_ped_loja_study_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.accession_number or self.id} — {self.paciente}"


class Laudo(LojaIsolationMixin, models.Model):
    """Laudo estruturado (fonte da verdade no Postgres)."""

    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        FINALIZADO = "finalizado", "Finalizado"
        ASSINADO = "assinado", "Assinado"
        ENTREGUE = "entregue", "Entregue"

    pedido = models.OneToOneField(
        PedidoExame,
        on_delete=models.CASCADE,
        related_name="laudo",
    )
    medico_laudador = models.CharField(max_length=200, blank=True, default="")
    crm_laudador = models.CharField(max_length=32, blank=True, default="")
    texto = models.TextField(blank=True, default="")
    conclusao = models.TextField(blank=True, default="")
    bi_rads = models.CharField(max_length=8, blank=True, default="", help_text="Categoria BI-RADS (mamografia)")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RASCUNHO,
    )
    pdf_url = models.TextField(blank=True, default="")
    assinado_em = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_laudo"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Laudo {self.pedido_id} ({self.status})"


class AuditoriaAcessoEstudo(LojaIsolationMixin, models.Model):
    """Auditoria LGPD: quem acessou qual estudo."""

    pedido = models.ForeignKey(
        PedidoExame,
        on_delete=models.CASCADE,
        related_name="acessos",
        null=True,
        blank=True,
    )
    study_instance_uid = models.CharField(max_length=128, blank=True, default="")
    usuario_id = models.IntegerField(null=True, blank=True)
    usuario_nome = models.CharField(max_length=200, blank=True, default="")
    acao = models.CharField(max_length=64, default="visualizar")
    ip = models.GenericIPAddressField(null=True, blank=True)
    detalhe = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "radiologia_auditoria_acesso"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["loja_id", "created_at"], name="rad_aud_loja_dt_idx"),
        ]


def novo_uuid_hex() -> str:
    return uuid.uuid4().hex
