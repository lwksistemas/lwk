from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin


class PropostaTemplate(LojaIsolationMixin, models.Model):
    """Template de proposta para reutilização."""

    nome = models.CharField(max_length=255, help_text="Nome do template (ex: Proposta Padrão, Proposta Premium)")
    conteudo = models.TextField(help_text="Conteúdo do template em texto ou HTML")
    is_padrao = models.BooleanField(default=False, help_text="Template padrão usado ao criar novas propostas")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_proposta_template"
        ordering = ["-is_padrao", "nome"]
        verbose_name = "Template de Proposta"
        verbose_name_plural = "Templates de Propostas"
        indexes = [
            models.Index(fields=["loja_id", "ativo"], name="crm_pt_loja_ativo_idx"),
            models.Index(fields=["loja_id", "is_padrao"], name="crm_pt_loja_padrao_idx"),
        ]

    def __str__(self):
        padrao = " (PADRÃO)" if self.is_padrao else ""
        return f"{self.nome}{padrao}"

    def save(self, *args, **kwargs):
        """Se marcar como padrão, desmarcar outros templates da mesma loja."""
        if self.is_padrao:
            # Desmarcar outros templates como padrão
            PropostaTemplate.objects.filter(loja_id=self.loja_id, is_padrao=True).exclude(id=self.id).update(is_padrao=False)
        super().save(*args, **kwargs)


class ContratoTemplate(LojaIsolationMixin, models.Model):
    """Template de contrato para reutilização."""

    nome = models.CharField(max_length=255, help_text="Nome do template (ex: Contrato Padrão, Contrato Premium)")
    conteudo = models.TextField(help_text="Conteúdo do template em texto ou HTML")
    is_padrao = models.BooleanField(default=False, help_text="Template padrão usado ao criar novos contratos")
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_contrato_template"
        ordering = ["-is_padrao", "nome"]
        verbose_name = "Template de Contrato"
        verbose_name_plural = "Templates de Contratos"
        indexes = [
            models.Index(fields=["loja_id", "ativo"], name="crm_ct_loja_ativo_idx"),
            models.Index(fields=["loja_id", "is_padrao"], name="crm_ct_loja_padrao_idx"),
        ]

    def __str__(self):
        padrao = " (PADRÃO)" if self.is_padrao else ""
        return f"{self.nome}{padrao}"

    def save(self, *args, **kwargs):
        """Se marcar como padrão, desmarcar outros templates da mesma loja."""
        if self.is_padrao:
            # Desmarcar outros templates como padrão
            ContratoTemplate.objects.filter(loja_id=self.loja_id, is_padrao=True).exclude(id=self.id).update(is_padrao=False)
        super().save(*args, **kwargs)


class NfseDescricaoTemplate(LojaIsolationMixin, models.Model):
    """Template de descrição do serviço para emissão de NFS-e."""

    nome = models.CharField(
        max_length=255,
        help_text="Nome do template (ex: Consultoria mensal, Treinamento)",
    )
    conteudo = models.TextField(help_text="Texto da discriminação/descrição do serviço")
    is_padrao = models.BooleanField(
        default=False,
        help_text="Template padrão usado ao emitir novas NFS-e",
    )
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        db_table = "crm_vendas_nfse_descricao_template"
        ordering = ["-is_padrao", "nome"]
        verbose_name = "Template de Descrição NFS-e"
        verbose_name_plural = "Templates de Descrição NFS-e"
        indexes = [
            models.Index(fields=["loja_id", "ativo"], name="crm_ndt_loja_ativo_idx"),
            models.Index(fields=["loja_id", "is_padrao"], name="crm_ndt_loja_padrao_idx"),
        ]

    def __str__(self):
        padrao = " (PADRÃO)" if self.is_padrao else ""
        return f"{self.nome}{padrao}"

    def save(self, *args, **kwargs):
        """Se marcar como padrão, desmarcar outros templates da mesma loja."""
        if self.is_padrao:
            NfseDescricaoTemplate.objects.filter(
                loja_id=self.loja_id, is_padrao=True,
            ).exclude(id=self.id).update(is_padrao=False)
        super().save(*args, **kwargs)

