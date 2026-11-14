"""Emissão da NFC-e depois que a venda de produto já foi registrada."""
from __future__ import annotations

import logging
import unicodedata
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

import requests
from lxml import etree

from .chave import (
    TPAG,
    codigo_numerico,
    digitos,
    dinheiro,
    montar_chave,
    url_qrcode,
)
from .sefaz_sp import (
    AUTORIZADAS,
    CANCELADAS,
    DUPLICADAS,
    INUTILIZADA,
    SefazNfceErro,
    certificado_da_clinica,
    consultar_chave,
    enviar_evento,
    enviar_inutilizacao,
    enviar_lote,
)
from .xml_nfce import assinar_raiz, envelopar, montar_nfe, xml_evento_cancelamento, xml_inutilizacao

logger = logging.getLogger(__name__)
FUSO = ZoneInfo("America/Sao_Paulo")


class NfceErro(Exception):
    """A venda permanece. O cupom explica o que falta ou o que a SEFAZ devolveu."""


def emitir_para_resposta(venda) -> dict | None:
    """Não desfaz a venda. Sem a NFC-e ligada, devolve vazio."""
    try:
        resultado = emitir_da_venda(venda)
    except NfceErro as exc:
        return {
            "status": "rejeitada",
            "mensagem": str(exc),
            "venda_id": getattr(venda, "id", None),
            "chave": "",
            "numero": None,
        }
    except Exception:
        logger.exception("Falha ao emitir a NFC-e da venda %s", getattr(venda, "id", None))
        return {
            "status": "pendente",
            "mensagem": "Não foi possível emitir o cupom agora. A venda e o recibo continuam valendo.",
            "venda_id": getattr(venda, "id", None),
            "chave": "",
            "numero": None,
        }
    if resultado.get("status") == "desligada":
        return None
    return resultado


def emitir_da_venda(venda) -> dict:
    from ..estoque_service import tenant_atomic
    from ..models import NfceConfig, VendaBalcao

    config = NfceConfig.objects.filter(loja_id=venda.loja_id).first()
    if config is None or not config.habilitada:
        return {"status": "desligada"}
    cupom = _cupom(venda)
    if cupom is not None and cupom.status in {"autorizada", "cancelada"}:
        return _resumo(cupom)
    if cupom is not None and cupom.status == "pendente" and cupom.xml:
        chave_pem, cert_pem, documento = _certificado(venda.loja_id)
        return _enviar_salvo(cupom, chave_pem, cert_pem, documento)
    contexto = _contexto(venda, config)
    with tenant_atomic():
        config = NfceConfig.objects.select_for_update().get(pk=config.pk)
        venda = VendaBalcao.objects.select_for_update().get(pk=venda.pk)
        cupom = _cupom(venda)
        if cupom is not None and cupom.status == "autorizada":
            return _resumo(cupom)
        if cupom is not None and cupom.status == "pendente" and cupom.xml:
            xml_pronto = cupom
        else:
            xml_pronto = _reservar(venda, config, contexto)
    return _enviar_salvo(xml_pronto, contexto["chave_pem"], contexto["cert_pem"], contexto["documento"])


def cancelar_cupom_da_venda(venda) -> None:
    cupom = _cupom(venda)
    if cupom is None or cupom.status in {"rejeitada", "cancelada"}:
        return
    if cupom.status == "pendente":
        raise NfceErro(
            "O cupom foi enviado e a SEFAZ ainda não confirmou. Tente emitir de novo antes de cancelar a venda.",
        )
    if cupom.status != "autorizada" or not cupom.protocolo:
        return
    chave_pem, cert_pem, documento = _certificado(venda.loja_id)
    evento = xml_evento_cancelamento({
        "chave": cupom.chave,
        "homologacao": cupom.homologacao,
        "documento": documento,
        "quando": _agora(),
        "protocolo": cupom.protocolo,
        "justificativa": "Cancelamento da venda de produto no caixa.",
    })
    assinado = etree.tostring(assinar_raiz(evento, chave_pem, cert_pem), encoding="unicode")
    try:
        resposta = enviar_evento(assinado, homologacao=cupom.homologacao, key_pem=chave_pem, cert_pem=cert_pem)
    except SefazNfceErro as exc:
        raise NfceErro(str(exc)) from exc
    if resposta["cstat"] not in CANCELADAS and resposta["cstat"] != "573":
        raise NfceErro(resposta["motivo"] or "A SEFAZ não cancelou o cupom.")
    cupom.status = "cancelada"
    cupom.motivo = "Cupom fiscal cancelado."
    cupom.save(update_fields=["status", "motivo", "updated_at"])


def _enviar_salvo(cupom, chave_pem: bytes, cert_pem: bytes, documento: str) -> dict:
    try:
        resposta = enviar_lote(cupom.xml, homologacao=cupom.homologacao, key_pem=chave_pem, cert_pem=cert_pem)
    except SefazNfceErro as exc:
        cupom.motivo = str(exc)
        cupom.save(update_fields=["motivo", "updated_at"])
        return _resumo(cupom)
    return _aplicar(cupom, resposta, chave_pem, cert_pem, documento)


def _aplicar(cupom, resposta: dict, chave_pem: bytes, cert_pem: bytes, documento: str) -> dict:
    from django.utils.timezone import now

    cstat = resposta.get("cstat") or ""
    if cstat in DUPLICADAS and cupom.chave:
        try:
            resposta = consultar_chave(cupom.chave, homologacao=cupom.homologacao, key_pem=chave_pem, cert_pem=cert_pem)
            cstat = resposta.get("cstat") or ""
        except SefazNfceErro as exc:
            cupom.motivo = str(exc)
            cupom.save(update_fields=["motivo", "updated_at"])
            return _resumo(cupom)
    if cstat in AUTORIZADAS:
        cupom.status = "autorizada"
        cupom.protocolo = (resposta.get("protocolo") or "")[:20]
        cupom.motivo = "Cupom fiscal autorizado."
        cupom.emitida_em = now()
        cupom.save(update_fields=["status", "protocolo", "motivo", "emitida_em", "updated_at"])
        return _resumo(cupom)
    cupom.status = "rejeitada"
    cupom.motivo = resposta.get("motivo") or "A SEFAZ rejeitou o cupom."
    cupom.save(update_fields=["status", "motivo", "updated_at"])
    _inutilizar(cupom, chave_pem, cert_pem, documento)
    return _resumo(cupom)


def _inutilizar(cupom, chave_pem: bytes, cert_pem: bytes, documento: str) -> None:
    if len(documento) not in {11, 14}:
        return
    inutil = xml_inutilizacao({
        "ano": _agora()[2:4],
        "serie": cupom.serie,
        "numero": cupom.numero,
        "documento": documento,
        "homologacao": cupom.homologacao,
        "justificativa": "Numero reservado e nao autorizado pela SEFAZ.",
    })
    assinado = etree.tostring(assinar_raiz(inutil, chave_pem, cert_pem), encoding="unicode")
    try:
        resposta = enviar_inutilizacao(
            assinado, homologacao=cupom.homologacao, key_pem=chave_pem, cert_pem=cert_pem,
        )
    except SefazNfceErro:
        logger.warning("NFC-e %s não teve a numeração inutilizada", cupom.chave)
        return
    if resposta.get("cstat") not in {INUTILIZADA, "563"}:
        logger.warning("Inutilização da NFC-e %s devolveu %s", cupom.chave, resposta.get("cstat"))


def _reservar(venda, config, contexto: dict):
    from ..models import NfceCupom

    campo = "proximo_numero_teste" if config.ambiente_homologacao else "proximo_numero"
    numero = int(getattr(config, campo) or 1)
    dados = _dados_xml(contexto, config, numero)
    nfe = assinar_raiz(montar_nfe(dados), contexto["chave_pem"], contexto["cert_pem"])
    xml = envelopar(nfe)
    setattr(config, campo, numero + 1)
    config.save(update_fields=[campo, "updated_at"])
    cupom = _cupom(venda)
    campos = {
        "numero": numero,
        "serie": int(config.serie or 1),
        "homologacao": config.ambiente_homologacao,
        "chave": dados["chave"],
        "qrcode": dados["qrcode"],
        "xml": xml,
        "status": "pendente",
        "motivo": "",
        "protocolo": "",
    }
    if cupom is None:
        cupom = NfceCupom.objects.create(venda=venda, loja_id=venda.loja_id, **campos)
    else:
        for nome, valor in campos.items():
            setattr(cupom, nome, valor)
        cupom.save(update_fields=[*campos.keys(), "updated_at"])
    return cupom


def _contexto(venda, config) -> dict:
    from superadmin.models import Loja

    from ..models import ClinicaBelezaNFSeConfig

    loja = Loja.objects.using("default").filter(id=venda.loja_id).first()
    if loja is None:
        raise NfceErro("Clínica não encontrada para emitir o cupom.")
    documento = digitos(loja.cpf_cnpj)
    if len(documento) not in {11, 14}:
        raise NfceErro("Informe o CNPJ ou o CPF da clínica para emitir o cupom.")
    uf = (loja.uf or "").strip().upper()
    if uf != "SP":
        raise NfceErro("O cupom fiscal emite NFC-e na SEFAZ-SP. Complete a UF da clínica com SP.")
    endereco = {
        "logradouro": (loja.logradouro or "").strip(),
        "numero_endereco": (loja.numero or "").strip(),
        "bairro": (loja.bairro or "").strip(),
        "cidade": (loja.cidade or "").strip(),
        "cep": digitos(loja.cep),
    }
    faltando = [nome for nome, valor in (
        ("logradouro", endereco["logradouro"]),
        ("número", endereco["numero_endereco"]),
        ("bairro", endereco["bairro"]),
        ("cidade", endereco["cidade"]),
        ("CEP", endereco["cep"]),
    ) if not valor]
    if len(endereco["cep"]) != 8:
        if "CEP" not in faltando:
            faltando.append("CEP")
    if faltando:
        raise NfceErro(f"Complete o endereço da clínica ({', '.join(faltando)}) antes de emitir o cupom.")
    ie = digitos(config.inscricao_estadual)
    if len(ie) < 2:
        raise NfceErro("Informe a inscrição estadual em Cupom fiscal.")
    nfse = ClinicaBelezaNFSeConfig.objects.filter(loja_id=venda.loja_id).first()
    municipio = _municipio(config, nfse, loja.cidade)
    chave_pem, cert_pem = _pem(nfse)
    csc = _csc(config)
    itens = _itens(venda, config)
    pagamento = getattr(venda, "payment", None)
    metodo = (getattr(pagamento, "payment_method", "") or "CASH").upper()
    if metodo not in TPAG:
        raise NfceErro("Esta forma de pagamento ainda não entra no cupom fiscal.")
    paciente = getattr(venda, "paciente", None)
    cpf = digitos(getattr(paciente, "cpf", "") or "")
    return {
        "loja": loja,
        "documento": documento,
        "ie": ie,
        "municipio": municipio,
        "endereco": endereco,
        "itens": itens,
        "tpag": TPAG[metodo],
        "cpf": cpf if len(cpf) == 11 else "",
        "nome_cliente": (getattr(paciente, "nome", "") or venda.nome_cliente or "").strip(),
        "csc": csc,
        "id_csc": config.id_csc,
        "chave_pem": chave_pem,
        "cert_pem": cert_pem,
        "simples": config.regime == "simples",
        "aliquota_icms": dinheiro(config.aliquota_icms or 0),
        "homologacao": bool(config.ambiente_homologacao),
        "serie": int(config.serie or 1),
        "venda_id": venda.id,
    }


def _dados_xml(contexto: dict, config, numero: int) -> dict:
    quando = _agora()
    codigo = codigo_numerico(contexto["venda_id"], numero)
    chave = montar_chave(
        cnpj=contexto["documento"],
        ano_mes=quando[2:4] + quando[5:7],
        serie=contexto["serie"],
        numero=numero,
        codigo=codigo,
    )
    bruto = Decimal("0")
    desconto = Decimal("0")
    icms = Decimal("0")
    pis = Decimal("0")
    cofins = Decimal("0")
    base = Decimal("0")
    itens = []
    for item in contexto["itens"]:
        liquido = item["bruto"] - item["desconto"]
        item_icms = Decimal("0")
        item_pis = Decimal("0")
        item_cofins = Decimal("0")
        if not contexto["simples"]:
            item_icms = (liquido * contexto["aliquota_icms"] / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            item_pis = (liquido * Decimal("0.65") / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            item_cofins = (liquido * Decimal("3") / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            base += liquido
        bruto += item["bruto"]
        desconto += item["desconto"]
        icms += item_icms
        pis += item_pis
        cofins += item_cofins
        itens.append({**item, "liquido": liquido, "icms": item_icms, "pis": item_pis, "cofins": item_cofins})
    dados = {
        **contexto,
        "quando": quando,
        "numero": numero,
        "codigo": codigo,
        "chave": chave,
        "itens": itens,
        "bruto": bruto,
        "desconto": desconto,
        "liquido": bruto - desconto,
        "base_icms": base,
        "icms": icms,
        "pis": pis,
        "cofins": cofins,
        "nome": contexto["loja"].nome,
        "logradouro": contexto["endereco"]["logradouro"],
        "numero_endereco": contexto["endereco"]["numero_endereco"],
        "bairro": contexto["endereco"]["bairro"],
        "cidade": contexto["endereco"]["cidade"],
        "cep": contexto["endereco"]["cep"],
    }
    dados["qrcode"] = url_qrcode(
        chave=chave,
        homologacao=contexto["homologacao"],
        id_csc=config.id_csc,
        csc=contexto["csc"],
    )
    return dados


def _itens(venda, config) -> list[dict]:
    linhas = []
    for item in venda.itens.select_related("produto").all():
        if item.estornado:
            continue
        ncm = digitos(item.produto.ncm) or digitos(config.ncm_padrao)
        if len(ncm) != 8:
            raise NfceErro(
                f"Informe o NCM de {item.produto.nome} no estoque, ou um NCM padrão em Cupom fiscal.",
            )
        bruto = (
            Decimal(str(item.quantidade or 0)) * Decimal(str(item.preco_unitario or 0))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        desconto = dinheiro(item.desconto)
        if desconto > bruto:
            desconto = bruto
        linhas.append({
            "codigo": item.produto_id,
            "nome": item.produto.nome,
            "ncm": ncm,
            "unidade": item.produto.unidade_medida,
            "quantidade": item.quantidade,
            "preco": item.preco_unitario,
            "bruto": bruto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "desconto": desconto,
        })
    if not linhas:
        raise NfceErro("A venda não tem produto para o cupom.")
    return linhas


def _municipio(config, nfse, cidade: str) -> str:
    codigo = digitos(config.codigo_municipio)
    if len(codigo) == 7:
        return codigo
    codigo = digitos(getattr(nfse, "nacional_codigo_municipio", "") or "")
    if len(codigo) != 7:
        codigo = buscar_codigo_ibge(cidade)
    if len(codigo) == 7 and codigo != digitos(config.codigo_municipio):
        config.codigo_municipio = codigo
        config.save(update_fields=["codigo_municipio", "updated_at"])
        return codigo
    if len(codigo) == 7:
        return codigo
    raise NfceErro("Informe o código IBGE do município em Cupom fiscal.")


def buscar_codigo_ibge(cidade: str) -> str:
    nome = _normalizar(cidade)
    if not nome:
        return ""
    try:
        resposta = requests.get(
            "https://brasilapi.com.br/api/ibge/municipios/v1/SP",
            timeout=8,
        )
        resposta.raise_for_status()
        lista = resposta.json()
    except Exception:
        logger.warning("Não foi possível consultar o código IBGE de %s", cidade)
        return ""
    if not isinstance(lista, list):
        return ""
    for item in lista:
        if _normalizar(item.get("nome") or "") == nome:
            return digitos(item.get("codigo_ibge"))
    return ""


def _pem(nfse):
    from core.encryption import decrypt_value

    pfx = getattr(nfse, "issnet_certificado", None) if nfse is not None else None
    if not pfx:
        raise NfceErro("Envie o certificado A1 em Nota Fiscal. O cupom usa o mesmo certificado da nota de serviço.")
    senha = decrypt_value(getattr(nfse, "issnet_senha_certificado", "") or "")
    try:
        return certificado_da_clinica(bytes(pfx), senha)
    except SefazNfceErro as exc:
        raise NfceErro(str(exc)) from exc


def _certificado(loja_id: int):
    from ..models import ClinicaBelezaNFSeConfig
    from superadmin.models import Loja

    nfse = ClinicaBelezaNFSeConfig.objects.filter(loja_id=loja_id).first()
    loja = Loja.objects.using("default").filter(id=loja_id).only("cpf_cnpj").first()
    documento = digitos(getattr(loja, "cpf_cnpj", "") or "")
    chave_pem, cert_pem = _pem(nfse)
    return chave_pem, cert_pem, documento


def _csc(config) -> str:
    from core.encryption import decrypt_value

    csc = decrypt_value(config.csc or "").strip()
    if not csc:
        raise NfceErro("Informe o CSC em Cupom fiscal.")
    return csc


def _cupom(venda):
    from django.core.exceptions import ObjectDoesNotExist

    try:
        return venda.cupom_nfce
    except ObjectDoesNotExist:
        return None


def _resumo(cupom) -> dict:
    textos = {
        "autorizada": "Cupom fiscal autorizado.",
        "pendente": "O cupom foi enviado e a SEFAZ ainda não confirmou.",
        "rejeitada": "A SEFAZ rejeitou o cupom.",
        "cancelada": "Cupom fiscal cancelado.",
    }
    return {
        "status": cupom.status,
        "mensagem": cupom.motivo or textos.get(cupom.status, ""),
        "chave": cupom.chave,
        "numero": cupom.numero,
        "protocolo": cupom.protocolo,
        "venda_id": cupom.venda_id,
    }


def _agora() -> str:
    momento = datetime.now(FUSO).strftime("%Y-%m-%dT%H:%M:%S%z")
    return f"{momento[:-2]}:{momento[-2:]}"


def _normalizar(valor: str) -> str:
    base = unicodedata.normalize("NFKD", str(valor or ""))
    sem = "".join(ch for ch in base if not unicodedata.combining(ch))
    return " ".join(sem.casefold().split())
