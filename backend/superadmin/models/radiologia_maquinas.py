"""Catálogo Super Admin: máquinas de imagem + contrato PACS/Worklist por clínica."""
from decimal import Decimal

from django.db import models

from .loja import Loja


class ContratoPacsLoja(models.Model):
    """Contrato do servidor DICOM + Worklist da clínica (cobrado pelo Super Admin)."""

    loja = models.OneToOneField(Loja, on_delete=models.CASCADE, related_name="contrato_pacs")
    dicom_contratado = models.BooleanField(default=False)
    worklist_contratado = models.BooleanField(default=False)
    cobranca_dicom_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    cobranca_worklist_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_contrato_pacs_loja"
        verbose_name = "Contrato PACS da loja"
        verbose_name_plural = "Contratos PACS"

    def valor_mensal(self) -> Decimal:
        if not self.is_active:
            return Decimal("0.00")
        total = Decimal("0.00")
        if self.dicom_contratado:
            total += self.cobranca_dicom_mensal or Decimal("0.00")
        if self.worklist_contratado:
            total += self.cobranca_worklist_mensal or Decimal("0.00")
        return total

    def __str__(self) -> str:
        return f"PACS {self.loja_id} dicom={self.dicom_contratado} mwl={self.worklist_contratado}"


class MaquinaRadiologia(models.Model):
    """Máquina cadastrada pelo Super Admin e liberada no tenant da clínica."""

    class Tipo(models.TextChoices):
        US = "US", "Ultrassom"
        RX = "DX", "Raio-X"
        MG = "MG", "Mamógrafo"
        CR = "CR", "CR / Digitalizador"
        CT = "CT", "Tomógrafo"
        MR = "MR", "Ressonância"

    class Status(models.TextChoices):
        CADASTRADA = "cadastrada", "Cadastrada"
        LIBERADA = "liberada", "Liberada no cliente"
        SUSPENSA = "suspensa", "Suspensa"

    loja = models.ForeignKey(Loja, on_delete=models.CASCADE, related_name="maquinas_radiologia")
    tipo = models.CharField(max_length=8, choices=Tipo.choices, default=Tipo.US)
    nome = models.CharField(max_length=120)
    ae_title = models.CharField(max_length=16)
    fabricante = models.CharField(max_length=80, blank=True, default="")
    modelo = models.CharField(max_length=80, blank=True, default="")
    cobranca_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CADASTRADA, db_index=True)
    codigo_vinculo = models.CharField(max_length=16, blank=True, default="")
    equipamento_tenant_id = models.IntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    liberada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "superadmin_maquina_radiologia"
        ordering = ["-id"]
        constraints = [
            models.UniqueConstraint(fields=["loja", "ae_title"], name="sa_maq_loja_aet_uniq"),
        ]
        indexes = [
            models.Index(fields=["loja", "status"], name="sa_maq_loja_status_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.nome} ({self.ae_title}) loja={self.loja_id}"
