"""Modelos Super Admin."""

from django.db import models

from .financeiro import PagamentoLoja
from .loja import Loja


class NFSeEmitida(models.Model):
    """Registro de NFS-e emitidas pela LWK para as lojas (assinaturas).
    Armazena notas emitidas via ISSNet direto ou via Asaas.
    """

    loja = models.ForeignKey(Loja, on_delete=models.SET_NULL, related_name="nfse_emitidas", null=True, blank=True)
    pagamento = models.ForeignKey(PagamentoLoja, on_delete=models.SET_NULL, null=True, blank=True, related_name="nfse")

    # Dados da NFS-e
    numero_nf = models.CharField(max_length=50, blank=True, verbose_name="Número da NFS-e")
    codigo_verificacao = models.CharField(max_length=50, blank=True, verbose_name="Código de Verificação")
    numero_rps = models.IntegerField(default=0, verbose_name="Número do RPS")
    serie_rps = models.CharField(max_length=10, blank=True, verbose_name="Série do RPS")

    # Provedor
    PROVEDOR_CHOICES = [
        ("issnet", "ISSNet (Direto)"),
        ("asaas", "Asaas (Intermediário)"),
        ("nacional", "Nacional (ADN)"),
    ]
    provedor = models.CharField(max_length=20, choices=PROVEDOR_CHOICES, default="issnet")

    # Status
    STATUS_CHOICES = [
        ("emitida", "Emitida"),
        ("cancelada", "Cancelada"),
        ("erro", "Erro"),
        ("pendente", "Pendente"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="emitida")

    # Valores
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=2.00)
    valor_iss = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Tomador
    tomador_nome = models.CharField(max_length=200, blank=True)
    tomador_cpf_cnpj = models.CharField(max_length=18, blank=True)
    tomador_email = models.EmailField(blank=True)

    # Descrição do serviço
    descricao_servico = models.TextField(blank=True)

    # XML e PDF
    xml_nfse = models.TextField(blank=True, verbose_name="XML da NFS-e")
    xml_dps_assinado = models.TextField(
        blank=True,
        verbose_name="XML DPS Assinado (debug)",
        help_text="XML completo assinado enviado ao ADN — para validação manual",
    )
    resposta_adn = models.TextField(
        blank=True,
        verbose_name="Resposta ADN (debug)",
        help_text="Resposta JSON completa retornada pelo ADN — para diagnóstico",
    )
    pdf_url = models.TextField(blank=True, verbose_name="URL do PDF")

    # Asaas (quando emitido via Asaas)
    asaas_invoice_id = models.CharField(max_length=100, blank=True)
    asaas_payment_id = models.CharField(max_length=100, blank=True)

    # Erro (quando falha)
    erro_mensagem = models.TextField(blank=True)

    # Datas
    data_emissao = models.DateTimeField(null=True, blank=True)
    data_cancelamento = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "NFS-e Emitida"
        verbose_name_plural = "NFS-e Emitidas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["loja", "-created_at"], name="nfse_loja_created_idx"),
            models.Index(fields=["status", "-created_at"], name="nfse_status_created_idx"),
            models.Index(fields=["asaas_payment_id"], name="nfse_asaas_pay_idx"),
        ]

    def __str__(self):
        return f"NF {self.numero_nf} - {self.tomador_nome} - R$ {self.valor}"


