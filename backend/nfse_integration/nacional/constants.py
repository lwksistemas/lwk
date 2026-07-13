"""Constantes do provedor NFS-e Nacional (ADN).
URLs, namespaces XML, enumerações.
"""

# === Endpoints ADN ===
ADN_URLS = {
    "producao": "https://adn.nfse.gov.br/adn/DFe",
    "homologacao": "https://adn.nfse.gov.br/adn/DFe",  # Produção restrita não processa DPS
}

# === Namespaces XML ===
# Namespace principal da DPS (NFS-e Nacional) - conforme XSD oficial
NS_NFSE = "http://www.sped.fazenda.gov.br/nfse"
# Namespace da assinatura digital
NS_DS = "http://www.w3.org/2000/09/xmldsig#"

# === Versão do layout ===
VERSAO_DPS = "1.00"

# === Ambiente ===
AMBIENTE_PRODUCAO = 1
AMBIENTE_HOMOLOGACAO = 2

# === Tipo de DPS ===
# 1 = NFS-e (Normal)
# 2 = NFS-e substituída
# 3 = NFS-e de ajuste
TIPO_DPS_NORMAL = 1

# === Natureza da Tributação ===
NATUREZA_TRIBUTACAO = {
    "tributacao_municipio": 1,       # Tributação no Município
    "tributacao_fora_municipio": 2,  # Tributação fora do Município
    "isencao": 3,                    # Isenção
    "imune": 4,                      # Imune
    "exigibilidade_suspensa_decisao_judicial": 5,
    "exigibilidade_suspensa_procedimento_administrativo": 6,
    "exportacao": 7,                 # Exportação de serviço
    "tributacao_simples_nacional": 8,  # Simples Nacional (MEI)
}

# === Tipo de Recolhimento do ISS ===
TIPO_RECOLHIMENTO = {
    "retido": 1,       # ISS retido
    "nao_retido": 2,   # ISS não retido (a recolher pelo prestador)
}

# === Regime Especial de Tributação ===
REGIME_ESPECIAL = {
    "nenhum": 0,
    "microempresa_municipal": 1,
    "estimativa": 2,
    "sociedade_profissionais": 3,
    "cooperativa": 4,
    "mei": 5,
    "me_epp": 6,
}

# === Código do País (Brasil) ===
CODIGO_PAIS_BRASIL = "01058"
