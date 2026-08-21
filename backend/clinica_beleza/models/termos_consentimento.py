"""Templates de Termo de Consentimento — simples ou TCLE Interativo."""
from django.db import models

from core.mixins import LojaIsolationManager, LojaIsolationMixin

TIPO_SIMPLES = "simples"
TIPO_INTERATIVO = "interativo"
TIPO_CHOICES = (
    (TIPO_SIMPLES, "Termo simples"),
    (TIPO_INTERATIVO, "TCLE Interativo"),
)

PDF_CABECALHO_LOGO = "logo"
PDF_CABECALHO_TIMBRADO = "timbrado"
PDF_CABECALHO_CHOICES = (
    (PDF_CABECALHO_LOGO, "Logomarca da clínica"),
    (PDF_CABECALHO_TIMBRADO, "Papel timbrado"),
)

SECAO_SIM_NAO = "sim_nao"
SECAO_ASSINATURA = "assinatura"
SECAO_GRAVIDEZ = "gravidez"
SECAO_FOTOS = "fotos"
SECAO_CONSINTO = "consinto"
SECAO_PROFISSIONAL = "profissional"
SECAO_TIPO_CHOICES = (
    (SECAO_SIM_NAO, "Leitura + SIM/NÃO + dúvidas"),
    (SECAO_ASSINATURA, "Somente ciência"),
    (SECAO_GRAVIDEZ, "Risco de gravidez"),
    (SECAO_FOTOS, "Fotos, som e imagem"),
    (SECAO_CONSINTO, "Consentimento ou recusa"),
    (SECAO_PROFISSIONAL, "Declaração do profissional"),
)


def secao_vazia() -> dict:
    return {
        "id": "",
        "codigo": "",
        "titulo": "",
        "texto": "",
        "tipo": SECAO_SIM_NAO,
    }


class TermoConsentimentoTemplate(LojaIsolationMixin, models.Model):
    """Biblioteca de termos da clínica. Cada procedimento escolhe um template."""

    nome = models.CharField(max_length=200, verbose_name="Nome")
    tipo = models.CharField(
        max_length=20, choices=TIPO_CHOICES, default=TIPO_SIMPLES, verbose_name="Tipo",
    )
    introducao = models.TextField(
        blank=True, default="",
        verbose_name="Introdução",
        help_text="Texto inicial. Não inclua dados de paciente/profissional — o sistema preenche.",
    )
    conteudo = models.TextField(
        blank=True, default="",
        verbose_name="Texto do termo simples",
        help_text="Use {paciente_nome}, {paciente_cpf}, {profissional_nome}, {profissional_conselho}, "
                  "{clinica_nome}, {procedimentos}, {data}.",
    )
    secoes = models.JSONField(
        default=list, blank=True, verbose_name="Seções do TCLE Interativo",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_termo_template"
        ordering = ["nome"]
        verbose_name = "Template de termo de consentimento"
        verbose_name_plural = "Templates de termo de consentimento"

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    @property
    def is_interativo(self) -> bool:
        return self.tipo == TIPO_INTERATIVO


class TermoConsentimentoConfig(LojaIsolationMixin, models.Model):
    """Opções da clínica para PDF de termo (uma linha por loja)."""

    pdf_cabecalho = models.CharField(
        max_length=20,
        choices=PDF_CABECALHO_CHOICES,
        default=PDF_CABECALHO_LOGO,
        verbose_name="Cabeçalho do PDF",
    )
    updated_at = models.DateTimeField(auto_now=True)

    objects = LojaIsolationManager()

    class Meta:
        app_label = "clinica_beleza"
        db_table = "clinica_beleza_termo_config"
        verbose_name = "Configuração de termo de consentimento"
        verbose_name_plural = "Configurações de termo de consentimento"

    def __str__(self):
        return self.get_pdf_cabecalho_display()
