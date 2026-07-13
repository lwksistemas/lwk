"""Resolução de códigos fiscais ISSNet (superadmin / assinaturas)."""
from __future__ import annotations

from typing import Any

from nfse_integration.issnet_xml_builder import normalizar_item_lista_servico_abrasf, somente_digitos


def fiscal_codes_issnet_superadmin(
    config: Any,
    payload: Any | None = None,
) -> tuple[str, str, str | None, str]:
    """Retorna (item_lista_lc116, codigo_tributacao_municipio, codigo_cnae, servico_codigo_legacy).

    item_lista_lc116: ex. 14.01 ou 1.05 (LC 116)
    codigo_tributacao_municipio: código cadastrado na prefeitura para o contribuinte
    """
    cod_cnae_override = ""
    cod_serv_override = ""
    if payload is not None:
        cod_cnae_override = (getattr(payload, "codigo_cnae", None) or "").strip()
        cod_serv_override = (getattr(payload, "codigo_servico", None) or "").strip()

    cod_cnae = cod_cnae_override or (getattr(config, "codigo_cnae", None) or "").strip() or None

    item_cfg = (getattr(config, "item_lista_servico", None) or "").strip()
    trib_cfg = (getattr(config, "codigo_tributacao_municipio", None) or "").strip()
    legado = (getattr(config, "codigo_servico_municipal", None) or "").strip()

    if cod_serv_override:
        digits = somente_digitos(cod_serv_override)
        if len(digits) >= 5:
            codigo_tributacao = digits[:20]
            item_lista = normalizar_item_lista_servico_abrasf(cod_serv_override)
        else:
            item_lista = normalizar_item_lista_servico_abrasf(cod_serv_override)
            codigo_tributacao = trib_cfg or digits or legado
    else:
        item_lista = normalizar_item_lista_servico_abrasf(item_cfg or legado or "14.01")
        codigo_tributacao = trib_cfg or somente_digitos(legado) or somente_digitos(item_lista)

    codigo_tributacao = somente_digitos(codigo_tributacao)[:20]
    if not codigo_tributacao:
        codigo_tributacao = somente_digitos(item_lista)[:4] or "1401"

    servico_codigo = legado or codigo_tributacao
    return item_lista, codigo_tributacao, cod_cnae, servico_codigo
