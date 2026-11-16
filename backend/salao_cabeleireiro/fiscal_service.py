"""Gravação da nota de serviço e do cupom de produto. Não envia documento à SEFAZ."""
from clinica_beleza.nfce.chave import digitos, dinheiro
from core.encryption import encrypt_value

from .models_fiscal import SalaoNFSeConfig, SalaoNfceConfig


class SalaoFiscalErro(Exception):
    pass


def obter_nfse(loja_id: int) -> SalaoNFSeConfig:
    config = SalaoNFSeConfig.objects.filter(loja_id=loja_id).first()
    if config is None:
        config = SalaoNFSeConfig(loja_id=loja_id)
        config.save()
    return config


def obter_nfce(loja_id: int) -> SalaoNfceConfig:
    config, _criada = SalaoNfceConfig.objects.get_or_create(loja_id=loja_id)
    return config


def gravar_nfce(config: SalaoNfceConfig, data) -> None:
    ligar = data.get("habilitada") is True
    regime = str(data.get("regime") or config.regime or "").strip()
    identificador = digitos(data.get("id_csc") or config.id_csc)[:6]
    csc = str(data.get("csc") or "").strip()
    ie = digitos(data.get("inscricao_estadual") if "inscricao_estadual" in data else config.inscricao_estadual)
    ncm = digitos(data.get("ncm_padrao") if "ncm_padrao" in data else config.ncm_padrao)
    ibge = digitos(data.get("codigo_municipio") if "codigo_municipio" in data else config.codigo_municipio)
    if ligar:
        if regime not in {"simples", "normal"}:
            raise SalaoFiscalErro("Escolha o regime: Simples Nacional ou regime normal.")
        if not identificador:
            raise SalaoFiscalErro("Informe o ID do CSC.")
        if not csc and not config.csc:
            raise SalaoFiscalErro("Informe o CSC.")
        if len(ie) < 2:
            raise SalaoFiscalErro("Informe a inscrição estadual.")
    if regime and regime not in {"simples", "normal"}:
        raise SalaoFiscalErro("Escolha o regime: Simples Nacional ou regime normal.")
    if ncm and len(ncm) != 8:
        raise SalaoFiscalErro("O NCM padrão tem 8 dígitos.")
    if ibge and len(ibge) != 7:
        raise SalaoFiscalErro("O código IBGE do município tem 7 dígitos.")
    try:
        serie = int(data.get("serie") or config.serie or 1)
    except (TypeError, ValueError) as exc:
        raise SalaoFiscalErro("A série da NFC-e fica entre 1 e 999.") from exc
    if serie < 1 or serie > 999:
        raise SalaoFiscalErro("A série da NFC-e fica entre 1 e 999.")
    if regime:
        config.regime = regime
    if identificador:
        config.id_csc = identificador
    if csc:
        config.csc = encrypt_value(csc)
    config.inscricao_estadual = ie
    config.ncm_padrao = ncm
    config.codigo_municipio = ibge
    config.serie = serie
    if "ambiente_homologacao" in data:
        config.ambiente_homologacao = data.get("ambiente_homologacao") is not False
    if regime == "normal" and data.get("aliquota_icms") not in (None, ""):
        config.aliquota_icms = dinheiro(data.get("aliquota_icms"))
    config.habilitada = ligar
    config.save()


def publico_nfce(config: SalaoNfceConfig) -> dict:
    nfse = SalaoNFSeConfig.objects.filter(loja_id=config.loja_id).first()
    return {
        "habilitada": config.habilitada,
        "regime": config.regime,
        "id_csc": config.id_csc,
        "csc_informado": bool(config.csc),
        "inscricao_estadual": config.inscricao_estadual,
        "serie": config.serie,
        "ambiente_homologacao": config.ambiente_homologacao,
        "ncm_padrao": config.ncm_padrao,
        "codigo_municipio": config.codigo_municipio,
        "aliquota_icms": str(config.aliquota_icms),
        "certificado_a1": bool(getattr(nfse, "issnet_certificado", None)),
        "proximo_numero": config.proximo_numero_teste if config.ambiente_homologacao else config.proximo_numero,
    }

