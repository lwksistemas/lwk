"""Configuração de NFS-e do Superadmin (emissão de notas para assinaturas das lojas).
Provedor: Nacional (ADN - Padrão Nacional NFS-e).
"""
from django.db import models


class SuperadminNFSeConfig(models.Model):
    """Configuração de emissão de NFS-e para assinaturas das lojas.
    Singleton — apenas um registro.

    Quando uma loja paga a assinatura, o sistema emite NFS-e usando
    o certificado digital da empresa administradora (ex: LWK Sistemas).
    """

    singleton_key = models.CharField(max_length=10, default="config", unique=True)

    # Provedor de emissão
    PROVEDOR_CHOICES = [
        ("issnet", "ISSNet (WebService Municipal)"),
        ("nacional", "Nacional (ADN - Padrão Nacional NFS-e)"),
        ("desabilitado", "Desabilitado (não emite NFS-e)"),
    ]
    provedor_nfse = models.CharField(
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default="issnet",
        verbose_name="Provedor de NFS-e",
        help_text="ISSNet para municípios sem Emissor Nacional; Nacional para municípios que aderiram ao ADN",
    )

    # Emissão automática após pagamento
    emitir_automaticamente = models.BooleanField(
        default=True,
        verbose_name="Emitir automaticamente",
        help_text="Emitir NFS-e automaticamente quando pagamento é confirmado",
    )

    # === Dados do Prestador (empresa que emite as notas) ===
    prestador_cnpj = models.CharField(
        max_length=18, blank=True,
        verbose_name="CNPJ do Prestador",
        help_text="CNPJ da empresa que emite as notas (ex: LWK Sistemas)",
    )
    prestador_razao_social = models.CharField(
        max_length=200, blank=True,
        verbose_name="Razão Social",
    )
    prestador_inscricao_municipal = models.CharField(
        max_length=20, blank=True,
        verbose_name="Inscrição Municipal",
    )
    prestador_email = models.EmailField(
        blank=True,
        verbose_name="E-mail do Prestador",
        help_text="E-mail para receber notificações de NFS-e emitidas",
    )

    # Regime Especial de Tributação
    REGIME_ESPECIAL_CHOICES = [
        ("", "-"),
        ("1", "Microempresa Municipal"),
        ("2", "Estimativa"),
        ("3", "Sociedade de Profissionais"),
        ("4", "Cooperativa"),
        ("5", "Microempresário Individual (MEI)"),
        ("6", "Microempresário e Empresa de Pequeno Porte (ME EPP)"),
    ]
    regime_especial_tributacao = models.CharField(
        max_length=2, blank=True, default="",
        choices=REGIME_ESPECIAL_CHOICES,
        verbose_name="Regime Especial de Tributação",
        help_text="Identifica o regime de tributação da empresa.",
    )

    # === Campos ISSNet legados (mantidos no banco, não usados) ===
    issnet_usuario = models.CharField(max_length=500, blank=True)
    issnet_senha = models.CharField(max_length=500, blank=True)
    issnet_certificado = models.BinaryField(blank=True, null=True)
    issnet_certificado_nome = models.CharField(max_length=255, blank=True)
    issnet_senha_certificado = models.CharField(max_length=500, blank=True)

    # === Dados fiscais ===
    codigo_servico_municipal = models.CharField(
        max_length=10, default="1401", blank=True,
        verbose_name="Código do Serviço (legado)",
        help_text="Fallback se codigo_tributacao_municipio estiver vazio.",
    )
    item_lista_servico = models.CharField(
        max_length=10, default="14.01", blank=True,
        verbose_name="Item lista serviço (LC 116)",
        help_text="Item LC 116 com ponto (ex.: 14.01, 1.05). Deve ser compatível com o CNAE.",
    )
    codigo_tributacao_municipio = models.CharField(
        max_length=20, blank=True, default="",
        verbose_name="Código tributação municipal",
        help_text="Código cadastrado na prefeitura para este CNPJ/IM (portal ISS / ISSNet).",
    )
    descricao_servico_padrao = models.TextField(
        default="Licenciamento de uso de software SaaS",
        blank=True,
        verbose_name="Descrição Padrão do Serviço",
    )
    aliquota_iss = models.DecimalField(
        max_digits=5, decimal_places=2, default=2.00,
        verbose_name="Alíquota ISS (%)",
    )
    codigo_cnae = models.CharField(
        max_length=20, blank=True,
        verbose_name="Código CNAE",
    )
    optante_simples_nacional = models.BooleanField(
        default=True,
        verbose_name="Optante Simples Nacional",
    )
    incentivador_cultural = models.BooleanField(
        default=False,
        verbose_name="Incentivador Cultural",
    )

    # === Configurações Nacional (ADN) ===
    nacional_certificado = models.BinaryField(
        blank=True, null=True,
        verbose_name="Certificado Digital A1 (.pfx)",
    )
    nacional_certificado_nome = models.CharField(
        max_length=255, blank=True,
        verbose_name="Nome do arquivo .pfx",
    )
    nacional_senha_certificado = models.CharField(
        max_length=500, blank=True,
        verbose_name="Senha do Certificado",
    )
    nacional_ambiente = models.CharField(
        max_length=20, default="homologacao", blank=True,
        choices=[("homologacao", "Homologação"), ("producao", "Produção")],
        verbose_name="Ambiente",
        help_text="Homologação para testes, Produção para emissão real",
    )
    nacional_codigo_municipio = models.CharField(
        max_length=7, blank=True,
        verbose_name="Código IBGE do Município",
        help_text="Código IBGE de 7 dígitos do município do prestador",
    )
    nacional_serie_dps = models.CharField(
        max_length=5, default="1", blank=True,
        verbose_name="Série da DPS",
        help_text="Série da DPS (padrão: 1 = 00001, conforme Portal Contribuinte)",
    )
    nacional_ultimo_dps = models.IntegerField(
        default=0,
        verbose_name="Último nº DPS emitido",
        help_text="Próxima emissão usará este + 1",
    )

    # === Controle de RPS (legado) ===
    serie_rps = models.CharField(max_length=10, default="E", blank=True)
    ultimo_rps = models.IntegerField(default=0)

    # Metadados
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "superadmin_nfse_config"
        verbose_name = "Configuração NFS-e Superadmin"
        verbose_name_plural = "Configurações NFS-e Superadmin"

    def __str__(self):
        return f"NFS-e Config - {self.get_provedor_nfse_display()}"

    @classmethod
    def get_config(cls):
        """Obtém ou cria configuração singleton."""
        obj, _ = cls.objects.using("default").get_or_create(
            singleton_key="config",
            defaults={"provedor_nfse": "nacional"},
        )
        return obj

    def proximo_dps(self) -> int:
        """Retorna e incrementa o próximo número de DPS."""
        self.nacional_ultimo_dps += 1
        self.save(update_fields=["nacional_ultimo_dps", "updated_at"])
        return self.nacional_ultimo_dps

    @property
    def nacional_senha_certificado_decrypted(self) -> str:
        """Retorna senha do certificado Nacional descriptografada."""
        from core.encryption import decrypt_value
        return decrypt_value(self.nacional_senha_certificado)
