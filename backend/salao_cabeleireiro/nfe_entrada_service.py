"""Entrada de produtos pela NF-e do fornecedor. Não emite nota nem lança despesa."""
from __future__ import annotations

import logging
import re
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.utils import timezone

logger = logging.getLogger(__name__)

MSG_JA_IMPORTADA = "Esta nota já entrou no estoque."
MSG_SEM_XML = "Esta nota ainda não tem o XML completo. Busque de novo na SEFAZ."
MSG_SEM_CERTIFICADO = "Cadastre o certificado A1 nas configurações da nota de serviço do salão."
MSG_SEM_CNPJ = "A busca automática exige o CNPJ do salão."
MSG_DESTINATARIO = "O destinatário da nota não é o CNPJ deste salão."


def so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def unidades_da_nota(quantidade: str, fator: str = "1") -> int:
    try:
        total = (Decimal(str(quantidade or "0")) * Decimal(str(fator or "1"))).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    except Exception:
        return 0
    return max(int(total), 0)


def _data(valor: str):
    texto = (valor or "")[:10]
    if len(texto) != 10:
        return None
    try:
        ano, mes, dia = (int(parte) for parte in texto.split("-"))
        return timezone.datetime(ano, mes, dia).date()
    except (TypeError, ValueError):
        return None


def _decimal(valor: str):
    try:
        return Decimal(str(valor or "0").replace(",", "."))
    except Exception:
        return Decimal("0")


def nota_publica(nota) -> dict:
    rotulos = {
        "resumo": "Aguardando XML",
        "pendente": "Pronta para conferir",
        "importada": "Importada",
        "ignorada": "Ignorada",
    }
    return {
        "id": nota.id,
        "chave": nota.chave,
        "numero": nota.numero,
        "fornecedor": nota.fornecedor_nome,
        "data_emissao": nota.data_emissao.isoformat() if nota.data_emissao else "",
        "status": nota.status,
        "status_display": rotulos.get(nota.status, nota.status),
        "origem": nota.origem,
        "tem_xml": bool(nota.xml),
        "ultimo_erro": nota.ultimo_erro,
    }


def listar_abertas():
    from .models import NotaEntradaSalao

    notas = NotaEntradaSalao.objects.filter(
        status__in=[NotaEntradaSalao.STATUS_RESUMO, NotaEntradaSalao.STATUS_PENDENTE],
    ).order_by("-data_emissao", "-id")
    return [nota_publica(nota) for nota in notas[:50]]


def _aviso_destinatario(loja, documento_nota: str) -> str:
    loja_doc = so_digitos(getattr(loja, "cpf_cnpj", "") or "")
    nota_doc = so_digitos(documento_nota)
    if loja_doc and nota_doc and loja_doc != nota_doc:
        return MSG_DESTINATARIO
    return ""


def _linhas_preview(parsed: dict) -> list[dict]:
    from .estoque_service import nome_comercial, nome_fornecedor
    from .models import Produto

    fornecedor = nome_fornecedor(parsed.get("fornecedor") or "")
    linhas = []
    for item in parsed.get("produtos") or []:
        nome = (item.get("nome") or "").strip()[:200]
        if len(nome) < 2:
            continue
        gtin = (item.get("gtin") or "")[:40]
        quantidade = unidades_da_nota(item.get("quantidade") or "0", item.get("fator") or "1")
        comercial = nome_comercial(nome)
        existente = None
        if gtin:
            existente = Produto.objects.filter(codigo_barras=gtin, is_active=True).first()
        if existente is None:
            existente = Produto.objects.filter(nome__iexact=comercial, is_active=True).first()
        linhas.append({
            "nome": nome,
            "nome_comercial": comercial,
            "fornecedor": fornecedor,
            "gtin": gtin,
            "quantidade": quantidade,
            "preco": str(_decimal(item.get("preco_unitario")).quantize(Decimal("0.01"))),
            "produto_id": existente.id if existente else None,
            "acao": "atualizar" if existente else "novo",
        })
    return linhas


def preview_xml(xml_bytes: bytes, loja) -> dict:
    from core.nfe.xml_parser import parse_nfe_xml

    parsed = parse_nfe_xml(xml_bytes)
    return {
        "nota": {
            "chave": parsed.get("chave") or "",
            "numero": parsed.get("numero_nota") or "",
            "fornecedor": parsed.get("fornecedor") or "",
            "data_emissao": parsed.get("data_emissao") or "",
            "valor_total": parsed.get("valor_total") or "",
        },
        "aviso_destinatario": _aviso_destinatario(loja, parsed.get("destinatario_documento") or ""),
        "produtos": _linhas_preview(parsed),
        "parsed": parsed,
    }


def guardar_xml(xml_bytes: bytes, loja) -> dict:
    from .models import NotaEntradaSalao

    previa = preview_xml(xml_bytes, loja)
    chave = previa["nota"]["chave"]
    if len(chave) != 44:
        raise ValueError("O XML não tem a chave da NF-e.")
    nota = NotaEntradaSalao.objects.filter(chave=chave).first()
    if nota and nota.status == NotaEntradaSalao.STATUS_IMPORTADA:
        raise ValueError(MSG_JA_IMPORTADA)
    if nota is None:
        nota = NotaEntradaSalao(chave=chave, loja_id=loja.id, origem="arquivo")
    parsed = previa.pop("parsed")
    nota.numero = (parsed.get("numero_nota") or "")[:20]
    nota.fornecedor_nome = (parsed.get("fornecedor") or "")[:200]
    nota.fornecedor_documento = so_digitos(parsed.get("emitente_documento") or "")[:20]
    nota.destinatario_documento = so_digitos(parsed.get("destinatario_documento") or "")[:20]
    nota.data_emissao = _data(parsed.get("data_emissao") or "")
    nota.valor = _decimal(parsed.get("valor_total"))
    nota.xml = xml_bytes.decode("utf-8", errors="replace")
    nota.status = NotaEntradaSalao.STATUS_PENDENTE
    nota.origem = "arquivo"
    nota.ultimo_erro = ""
    nota.save()
    return {"id": nota.id, "preview": True, **previa}


def preview_da_nota(nota_id: int, loja) -> dict:
    from .models import NotaEntradaSalao

    nota = NotaEntradaSalao.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if nota.status == NotaEntradaSalao.STATUS_IMPORTADA:
        raise ValueError(MSG_JA_IMPORTADA)
    if not nota.xml:
        raise ValueError(MSG_SEM_XML)
    previa = preview_xml(nota.xml.encode("utf-8"), loja)
    previa.pop("parsed", None)
    return {"id": nota.id, "preview": True, **previa}


def _aplicar(nota, linhas: list[dict]):
    from .caixa_service import quantia
    from .estoque_service import gravar, nome_comercial, nome_fornecedor, tenant_atomic
    from .models import MovimentoEstoque, NotaEntradaSalao, Produto

    criados = atualizados = ignorados = 0
    with tenant_atomic():
        nota = NotaEntradaSalao.objects.select_for_update().get(pk=nota.pk)
        if nota.status == NotaEntradaSalao.STATUS_IMPORTADA:
            raise ValueError(MSG_JA_IMPORTADA)
        for item in linhas:
            if item.get("acao") == "ignorar":
                ignorados += 1
                continue
            quantidade = int(item.get("quantidade") or 0)
            nome = nome_comercial(item.get("nome_comercial") or "") or nome_comercial(item.get("nome") or "")
            if quantidade <= 0 or len(nome) < 2:
                ignorados += 1
                continue
            gtin = (item.get("gtin") or "")[:40]
            produto = None
            if item.get("produto_id"):
                produto = Produto.objects.select_for_update().filter(pk=item["produto_id"], is_active=True).first()
            if produto is None and gtin:
                produto = Produto.objects.select_for_update().filter(codigo_barras=gtin, is_active=True).first()
            if produto is None:
                produto = Produto.objects.select_for_update().filter(nome__iexact=nome, is_active=True).first()
            novo = produto is None
            if novo:
                produto = gravar(
                    Produto,
                    nome=nome,
                    fornecedor=nome_fornecedor(item.get("fornecedor") or ""),
                    codigo_barras=gtin,
                    preco=quantia(item.get("preco") or 0),
                    saldo=0,
                    comissao_percentual=Decimal("0"),
                )
                produto = Produto.objects.select_for_update().get(pk=produto.pk)
            produto.saldo += quantidade
            produto.save(update_fields=["saldo"])
            gravar(
                MovimentoEstoque,
                produto=produto,
                tipo="entrada",
                quantidade=quantidade,
                saldo_depois=produto.saldo,
            )
            if novo:
                criados += 1
            else:
                atualizados += 1
        nota.status = NotaEntradaSalao.STATUS_IMPORTADA
        nota.importada_em = timezone.now()
        nota.ultimo_erro = ""
        nota.save(update_fields=["status", "importada_em", "ultimo_erro", "updated_at"])
    return {"criados": criados, "atualizados": atualizados, "ignorados": ignorados}


def confirmar_nota(nota_id: int, produtos: list | None, loja) -> dict:
    from .models import NotaEntradaSalao

    nota = NotaEntradaSalao.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if not nota.xml:
        raise ValueError(MSG_SEM_XML)
    previa = preview_xml(nota.xml.encode("utf-8"), loja)
    linhas = previa["produtos"]
    if produtos:
        por_indice = {indice: item for indice, item in enumerate(produtos) if isinstance(item, dict)}
        for indice, linha in enumerate(linhas):
            escolhido = por_indice.get(indice)
            if not escolhido:
                continue
            if "quantidade" in escolhido:
                linha["quantidade"] = int(escolhido.get("quantidade") or 0)
            if escolhido.get("acao") in {"novo", "atualizar", "ignorar"}:
                linha["acao"] = escolhido["acao"]
            if "nome_comercial" in escolhido:
                linha["nome_comercial"] = str(escolhido.get("nome_comercial") or "")[:200]
            if escolhido.get("preco") not in (None, ""):
                linha["preco"] = str(escolhido["preco"])
    return _aplicar(nota, linhas)


def ignorar_nota(nota_id: int) -> None:
    from .models import NotaEntradaSalao

    nota = NotaEntradaSalao.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if nota.status == NotaEntradaSalao.STATUS_IMPORTADA:
        raise ValueError(MSG_JA_IMPORTADA)
    nota.status = NotaEntradaSalao.STATUS_IGNORADA
    nota.save(update_fields=["status", "updated_at"])


def _credencial(loja):
    from core.cpf_utils import eh_cnpj, normalizar_cpf_cnpj
    from core.encryption import decrypt_value
    from core.nfe.sefaz import SefazNfeErro, pem_do_pfx
    from nfse_integration.certificado_armazenado import ler_pfx

    from .models_fiscal import SalaoNFSeConfig

    cnpj = so_digitos(getattr(loja, "cpf_cnpj", "") or "")
    if not eh_cnpj(normalizar_cpf_cnpj(cnpj)):
        raise SefazNfeErro(MSG_SEM_CNPJ)
    config = SalaoNFSeConfig.objects.first()
    pfx = ler_pfx(getattr(config, "issnet_certificado", None) if config else None)
    senha = decrypt_value(getattr(config, "issnet_senha_certificado", "") or "") if config else ""
    if not pfx or not senha:
        raise SefazNfeErro(MSG_SEM_CERTIFICADO)
    key_pem, cert_pem = pem_do_pfx(pfx, senha)
    return {
        "cnpj": cnpj,
        "uf": (getattr(loja, "uf", "") or "").upper(),
        "homologacao": bool(getattr(config, "issnet_ambiente_homologacao", False)),
        "key_pem": key_pem,
        "cert_pem": cert_pem,
    }


def _pode_consultar(estado) -> bool:
    if estado.consultado_em is None:
        return True
    passou = timezone.now() - estado.consultado_em >= timedelta(hours=1)
    if "consumo indevido" in (estado.ultimo_erro or "").lower():
        return passou
    if estado.ult_nsu != estado.max_nsu:
        return True
    return passou


def sincronizar_loja(loja) -> dict:
    from core.nfe.sefaz import (
        SefazNfeErro,
        classificar_documento,
        consultar_distribuicao,
        enviar_ciencia,
    )

    from .models import NfeDistribuicaoSalao, NotaEntradaSalao

    try:
        cred = _credencial(loja)
    except SefazNfeErro as exc:
        return {"ok": False, "detail": str(exc), "novas": 0, "pendentes": listar_abertas()}

    estado, _criado = NfeDistribuicaoSalao.objects.get_or_create(
        loja_id=loja.id,
        defaults={"ult_nsu": "000000000000000", "max_nsu": "000000000000000"},
    )
    if not _pode_consultar(estado):
        hora = timezone.localtime((estado.consultado_em or timezone.now()) + timedelta(hours=1)).strftime("%H:%M")
        return {
            "ok": False,
            "detail": f"A SEFAZ pediu para aguardar. Tente de novo após {hora}.",
            "novas": 0,
            "pendentes": listar_abertas(),
        }

    novas = 0
    try:
        novas += _puxar_lote(loja, cred, estado, consultar_distribuicao, classificar_documento)
    except SefazNfeErro as exc:
        estado.ultimo_erro = str(exc)[:500]
        estado.consultado_em = timezone.now()
        estado.save(update_fields=["ultimo_erro", "consultado_em"])
        return {"ok": False, "detail": estado.ultimo_erro, "novas": novas, "pendentes": listar_abertas()}

    resumos = list(NotaEntradaSalao.objects.filter(status=NotaEntradaSalao.STATUS_RESUMO).order_by("id")[:20])
    for nota in resumos:
        try:
            ok = enviar_ciencia(
                cnpj=cred["cnpj"],
                chave=nota.chave,
                homologacao=cred["homologacao"],
                key_pem=cred["key_pem"],
                cert_pem=cred["cert_pem"],
            )
        except SefazNfeErro as exc:
            nota.ultimo_erro = str(exc)[:500]
            nota.save(update_fields=["ultimo_erro", "updated_at"])
            continue
        if not ok:
            nota.ultimo_erro = "A SEFAZ não registrou a ciência desta nota."
            nota.save(update_fields=["ultimo_erro", "updated_at"])
    estado.refresh_from_db()
    if resumos and _pode_consultar(estado):
        try:
            novas += _puxar_lote(loja, cred, estado, consultar_distribuicao, classificar_documento)
        except SefazNfeErro as exc:
            estado.ultimo_erro = str(exc)[:500]
            estado.consultado_em = timezone.now()
            estado.save(update_fields=["ultimo_erro", "consultado_em"])
            return {"ok": False, "detail": estado.ultimo_erro, "novas": novas, "pendentes": listar_abertas()}
    return {"ok": True, "detail": "Consulta concluída.", "novas": novas, "pendentes": listar_abertas()}


def _puxar_lote(loja, cred, estado, consultar, classificar) -> int:
    novas = 0
    for _ in range(3):
        ret = consultar(
            cnpj=cred["cnpj"],
            uf=cred["uf"],
            ult_nsu=estado.ult_nsu,
            homologacao=cred["homologacao"],
            key_pem=cred["key_pem"],
            cert_pem=cred["cert_pem"],
        )
        estado.ult_nsu = ret["ult_nsu"]
        estado.max_nsu = ret["max_nsu"]
        estado.consultado_em = timezone.now()
        estado.ultimo_erro = ""
        estado.save()
        for doc in ret["documentos"]:
            if _absorver(doc, classificar, cred["cnpj"], loja.id):
                novas += 1
        if ret["vazio"] or estado.ult_nsu >= estado.max_nsu:
            break
    return novas


def _absorver(doc: dict, classificar, cnpj_loja: str, loja_id: int) -> bool:
    from .models import NotaEntradaSalao

    try:
        info = classificar(doc["xml"])
    except Exception:
        logger.warning("Documento NSU %s ignorado", doc.get("nsu"))
        return False
    if not info:
        return False
    if info["tipo"] == "resumo":
        if so_digitos(info.get("emitente_documento") or "") == cnpj_loja:
            return False
        return _guardar_resumo(info, doc.get("nsu") or "", loja_id)
    parsed = info["parsed"]
    if so_digitos(parsed.get("destinatario_documento") or "") != cnpj_loja:
        return False
    if NotaEntradaSalao.objects.filter(chave=parsed["chave"], status=NotaEntradaSalao.STATUS_IMPORTADA).exists():
        return False
    antes = NotaEntradaSalao.objects.filter(chave=parsed["chave"], status=NotaEntradaSalao.STATUS_PENDENTE).exists()
    _salvar_completo(parsed, info["xml"], loja_id)
    return not antes


def _guardar_resumo(info: dict, nsu: str, loja_id: int) -> bool:
    from .models import NotaEntradaSalao

    if NotaEntradaSalao.objects.filter(chave=info["chave"]).exists():
        return False
    NotaEntradaSalao.objects.create(
        loja_id=loja_id,
        chave=info["chave"],
        numero=(info.get("chave") or "")[25:34].lstrip("0") or "0",
        fornecedor_nome=(info.get("fornecedor_nome") or "")[:200],
        fornecedor_documento=so_digitos(info.get("emitente_documento") or "")[:20],
        data_emissao=_data(info.get("data_emissao") or ""),
        status=NotaEntradaSalao.STATUS_RESUMO,
        origem="sefaz",
        nsu=(nsu or "")[:20],
    )
    return True


def _salvar_completo(parsed: dict, xml_doc: bytes, loja_id: int):
    from .models import NotaEntradaSalao

    nota = NotaEntradaSalao.objects.filter(chave=parsed["chave"]).first()
    if nota is None:
        nota = NotaEntradaSalao(chave=parsed["chave"], loja_id=loja_id)
    nota.numero = (parsed.get("numero_nota") or "")[:20]
    nota.fornecedor_nome = (parsed.get("fornecedor") or "")[:200]
    nota.fornecedor_documento = so_digitos(parsed.get("emitente_documento") or "")[:20]
    nota.destinatario_documento = so_digitos(parsed.get("destinatario_documento") or "")[:20]
    nota.data_emissao = _data(parsed.get("data_emissao") or "")
    nota.valor = _decimal(parsed.get("valor_total"))
    nota.xml = xml_doc.decode("utf-8", errors="replace") if isinstance(xml_doc, bytes) else str(xml_doc)
    nota.status = NotaEntradaSalao.STATUS_PENDENTE
    nota.origem = "sefaz"
    nota.ultimo_erro = ""
    nota.save()
    return nota
