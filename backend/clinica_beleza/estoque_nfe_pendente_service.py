"""Fila de NF-e de fornecedor. A entrada no estoque só ocorre na confirmação."""
from __future__ import annotations

import logging
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from core.cpf_utils import eh_cnpj, normalizar_cpf_cnpj

logger = logging.getLogger(__name__)

MSG_JA_IMPORTADA = "Esta nota já entrou no estoque."
MSG_DESTINATARIO = "O destinatário da nota não é o CNPJ desta clínica."
MSG_SEM_XML = "Esta nota ainda não tem o XML completo. Aguarde a próxima consulta à SEFAZ."
MSG_SEM_CERTIFICADO = "Cadastre o certificado A1 nas configurações da nota de serviço da clínica."
MSG_SEM_CNPJ = "A consulta automática exige o CNPJ da loja. CPF não recebe NF-e de produto pela SEFAZ."


def so_digitos(valor: str) -> str:
    return re.sub(r"\D", "", valor or "")


def documento_da_loja(loja_id: int | None) -> str:
    from superadmin.models import Loja

    if not loja_id:
        return ""
    loja = Loja.objects.using("default").filter(id=loja_id).only("cpf_cnpj").first()
    return so_digitos(getattr(loja, "cpf_cnpj", "") or "")


def destinatario_confere(documento_loja: str, documento_nota: str) -> bool:
    loja = so_digitos(documento_loja)
    nota = so_digitos(documento_nota)
    return bool(loja and nota and loja == nota)


def numero_da_chave(chave: str) -> str:
    if len(chave) != 44:
        return ""
    return chave[25:34].lstrip("0") or "0"


def _data(valor: str):
    from clinica_beleza.estoque_xml_import_service import _parse_date

    return _parse_date((valor or "")[:10])


def _decimal(valor: str) -> Decimal | None:
    if not valor:
        return None
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def nota_importada(chave: str) -> bool:
    from .models import NotaEntradaNfe

    if not chave:
        return False
    return NotaEntradaNfe.objects.filter(chave=chave, status=NotaEntradaNfe.STATUS_IMPORTADA).exists()


def listar_abertas():
    from .models import NotaEntradaNfe

    notas = NotaEntradaNfe.objects.filter(
        status__in=[NotaEntradaNfe.STATUS_RESUMO, NotaEntradaNfe.STATUS_PENDENTE],
    ).order_by("-data_emissao", "-id")
    return [serializar_nota(nota) for nota in notas[:50]]


def serializar_nota(nota) -> dict:
    return {
        "id": nota.id,
        "chave": nota.chave,
        "numero": nota.numero,
        "fornecedor": nota.fornecedor_nome,
        "data_emissao": nota.data_emissao.isoformat() if nota.data_emissao else "",
        "status": nota.status,
        "status_display": nota.get_status_display(),
        "origem": nota.origem,
        "tem_xml": bool(nota.xml),
        "ultimo_erro": nota.ultimo_erro,
    }


def guardar_xml(xml_content: bytes, *, loja_id: int | None, origem: str) -> dict:
    """Grava ou atualiza a nota como pendente. Recusa destinatário diferente e nota já importada."""
    from .estoque_xml_import_service import parse_nfe_xml
    from .models import NotaEntradaNfe

    parsed = parse_nfe_xml(xml_content)
    chave = parsed.get("chave") or ""
    if len(chave) != 44:
        raise ValueError("O XML não tem a chave da NF-e.")
    if nota_importada(chave):
        raise ValueError(MSG_JA_IMPORTADA)
    doc_loja = documento_da_loja(loja_id)
    if not destinatario_confere(doc_loja, parsed.get("destinatario_documento") or ""):
        raise ValueError(MSG_DESTINATARIO)
    nota = _salvar_completo(parsed, xml_content, origem=origem, loja_id=loja_id)
    return serializar_nota(nota)


def _salvar_completo(parsed: dict, xml_content: bytes, *, origem: str, loja_id: int | None):
    from .models import NotaEntradaNfe

    chave = parsed["chave"]
    nota = NotaEntradaNfe.objects.filter(chave=chave).first()
    if nota and nota.status == NotaEntradaNfe.STATUS_IGNORADA and origem != NotaEntradaNfe.ORIGEM_ARQUIVO:
        return nota
    if nota is None:
        nota = NotaEntradaNfe(chave=chave, loja_id=loja_id)
    nota.numero = parsed.get("numero_nota") or numero_da_chave(chave)
    nota.fornecedor_nome = (parsed.get("fornecedor") or "")[:200]
    nota.fornecedor_documento = so_digitos(parsed.get("emitente_documento") or "")[:20]
    nota.destinatario_documento = so_digitos(parsed.get("destinatario_documento") or "")[:20]
    nota.data_emissao = _data(parsed.get("data_emissao") or "")
    nota.xml = xml_content.decode("utf-8", errors="replace")
    nota.status = NotaEntradaNfe.STATUS_PENDENTE
    nota.origem = origem
    nota.ultimo_erro = ""
    nota.save()
    return nota


def preview_da_nota(nota_id: int, *, loja_id: int | None) -> dict:
    from .estoque_xml_import_service import importar_produtos_xml
    from .models import NotaEntradaNfe

    nota = NotaEntradaNfe.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if nota.status == NotaEntradaNfe.STATUS_IMPORTADA:
        raise ValueError(MSG_JA_IMPORTADA)
    if not nota.xml:
        raise ValueError(MSG_SEM_XML)
    resultado = importar_produtos_xml(nota.xml.encode("utf-8"), loja_id=loja_id)
    return {"id": nota.id, "preview": True, "status": nota.status, **resultado}


def confirmar_nota(nota_id: int, produtos: list | None, *, loja_id: int | None) -> dict:
    from .estoque_xml_import_service import confirmar_importacao_xml, importar_produtos_xml
    from .models import NotaEntradaNfe

    nota = NotaEntradaNfe.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if nota.status == NotaEntradaNfe.STATUS_IMPORTADA or nota_importada(nota.chave):
        raise ValueError(MSG_JA_IMPORTADA)
    if not nota.xml:
        raise ValueError(MSG_SEM_XML)
    preparados = importar_produtos_xml(nota.xml.encode("utf-8"), loja_id=loja_id)["produtos"]
    if produtos:
        from .views_estoque_xml import _mesclar_overrides_categoria

        _mesclar_overrides_categoria(preparados, produtos, loja_id)
    return _aplicar_estoque(nota, preparados, loja_id)


def confirmar_arquivo(xml_content: bytes, produtos: list, *, loja_id: int | None) -> dict:
    """Confirma um XML enviado na mão e trava a chave para não somar o estoque de novo."""
    from .estoque_xml_import_service import parse_nfe_xml
    from .models import NotaEntradaNfe

    parsed = parse_nfe_xml(xml_content)
    chave = parsed.get("chave") or ""
    if chave and nota_importada(chave):
        raise ValueError(MSG_JA_IMPORTADA)
    nota = None
    if chave and destinatario_confere(documento_da_loja(loja_id), parsed.get("destinatario_documento") or ""):
        nota = _salvar_completo(parsed, xml_content, origem=NotaEntradaNfe.ORIGEM_ARQUIVO, loja_id=loja_id)
    elif chave:
        nota = NotaEntradaNfe.objects.filter(chave=chave).first()
    return _aplicar_estoque(nota, produtos, loja_id, chave=chave)


def _aplicar_estoque(nota, produtos: list, loja_id: int | None, *, chave: str = "") -> dict:
    from .estoque_xml_import_service import confirmar_importacao_xml
    from .models import NotaEntradaNfe

    resultado = confirmar_importacao_xml(produtos, loja_id=loja_id)
    entrou = (resultado["criados"] + resultado["atualizados"]) > 0
    if entrou and nota is not None:
        nota.status = NotaEntradaNfe.STATUS_IMPORTADA
        nota.importada_em = timezone.now()
        nota.ultimo_erro = ""
        nota.save(update_fields=["status", "importada_em", "ultimo_erro", "updated_at"])
    elif entrou and chave and nota is None:
        NotaEntradaNfe.objects.create(
            loja_id=loja_id,
            chave=chave,
            numero=numero_da_chave(chave),
            status=NotaEntradaNfe.STATUS_IMPORTADA,
            origem=NotaEntradaNfe.ORIGEM_ARQUIVO,
            importada_em=timezone.now(),
        )
    return resultado


def ignorar_nota(nota_id: int) -> None:
    from .models import NotaEntradaNfe

    nota = NotaEntradaNfe.objects.filter(pk=nota_id).first()
    if nota is None:
        raise LookupError("Nota não encontrada.")
    if nota.status == NotaEntradaNfe.STATUS_IMPORTADA:
        raise ValueError(MSG_JA_IMPORTADA)
    nota.status = NotaEntradaNfe.STATUS_IGNORADA
    nota.save(update_fields=["status", "updated_at"])


def _credencial_loja(loja):
    from core.encryption import decrypt_value
    from nfse_integration.certificado_armazenado import ler_pfx

    from .estoque_nfe_sefaz import SefazNfeErro, pem_do_pfx
    from .models import ClinicaBelezaNFSeConfig

    cnpj = so_digitos(getattr(loja, "cpf_cnpj", "") or "")
    if not eh_cnpj(normalizar_cpf_cnpj(cnpj)):
        raise SefazNfeErro(MSG_SEM_CNPJ)
    config = ClinicaBelezaNFSeConfig.objects.first()
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
    if estado.ult_nsu != estado.max_nsu:
        return True
    return timezone.now() - estado.consultado_em >= timedelta(hours=1)


def sincronizar_loja(loja) -> dict:
    """Busca notas novas da loja e pede o XML das que ainda estão em resumo."""
    from .estoque_nfe_sefaz import (
        SefazNfeErro,
        classificar_documento,
        consultar_distribuicao,
        enviar_ciencia,
    )
    from .models import NfeDistribuicaoEstado, NotaEntradaNfe

    try:
        cred = _credencial_loja(loja)
    except SefazNfeErro as exc:
        return {"ok": False, "detail": str(exc), "novas": 0}

    estado, _criado = NfeDistribuicaoEstado.objects.get_or_create(
        loja_id=loja.id,
        defaults={"ult_nsu": "000000000000000", "max_nsu": "000000000000000"},
    )
    novas = 0
    if _pode_consultar(estado):
        try:
            novas += _puxar_lote(loja, cred, estado, consultar_distribuicao, classificar_documento)
        except SefazNfeErro as exc:
            estado.ultimo_erro = str(exc)[:500]
            estado.consultado_em = timezone.now()
            estado.save(update_fields=["ultimo_erro", "consultado_em"])
            return {"ok": False, "detail": str(exc), "novas": novas}

    resumos = list(
        NotaEntradaNfe.objects.filter(status=NotaEntradaNfe.STATUS_RESUMO).order_by("id")[:20]
    )
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
    if resumos and _pode_consultar(estado):
        try:
            novas += _puxar_lote(loja, cred, estado, consultar_distribuicao, classificar_documento)
        except SefazNfeErro as exc:
            estado.ultimo_erro = str(exc)[:500]
            estado.consultado_em = timezone.now()
            estado.save(update_fields=["ultimo_erro", "consultado_em"])
            return {"ok": False, "detail": str(exc), "novas": novas}
    return {"ok": True, "detail": "Consulta concluída.", "novas": novas}


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
            if _absorver_documento(doc, classificar, cred["cnpj"], loja.id):
                novas += 1
        if ret["vazio"] or estado.ult_nsu >= estado.max_nsu:
            break
    return novas


def _absorver_documento(doc: dict, classificar, cnpj_loja: str, loja_id: int) -> bool:
    from .models import NotaEntradaNfe

    try:
        info = classificar(doc["xml"])
    except Exception:
        logger.warning("Documento NSU %s ignorado", doc.get("nsu"))
        return False
    if not info:
        return False
    if info["tipo"] == "resumo":
        if so_digitos(info["emitente_documento"]) == cnpj_loja:
            return False
        return _guardar_resumo(info, doc.get("nsu") or "", loja_id)
    parsed = info["parsed"]
    if not destinatario_confere(cnpj_loja, parsed.get("destinatario_documento") or ""):
        return False
    if nota_importada(parsed["chave"]):
        return False
    antes = NotaEntradaNfe.objects.filter(chave=parsed["chave"], status=NotaEntradaNfe.STATUS_PENDENTE).exists()
    _salvar_completo(parsed, info["xml"], origem=NotaEntradaNfe.ORIGEM_SEFAZ, loja_id=loja_id)
    return not antes


def _guardar_resumo(info: dict, nsu: str, loja_id: int) -> bool:
    from .models import NotaEntradaNfe

    nota = NotaEntradaNfe.objects.filter(chave=info["chave"]).first()
    if nota is not None:
        return False
    NotaEntradaNfe.objects.create(
        loja_id=loja_id,
        chave=info["chave"],
        numero=numero_da_chave(info["chave"]),
        fornecedor_nome=(info.get("fornecedor_nome") or "")[:200],
        fornecedor_documento=so_digitos(info.get("emitente_documento") or "")[:20],
        data_emissao=_data(info.get("data_emissao") or ""),
        valor=_decimal(info.get("valor") or ""),
        status=NotaEntradaNfe.STATUS_RESUMO,
        origem=NotaEntradaNfe.ORIGEM_SEFAZ,
        nsu=nsu[:20],
    )
    return True


def sincronizar_nfe_fornecedores() -> int:
    """Job do worker: consulta a SEFAZ em cada loja da clínica."""
    from core.db_config import ensure_loja_database_config
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    from .catalogo_service import lojas_clinica_beleza_com_schema

    total = 0
    for loja in lojas_clinica_beleza_com_schema(apenas_ativas=True):
        if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
            continue
        try:
            set_current_loja_id(loja.id)
            set_current_tenant_db(loja.database_name)
            resultado = sincronizar_loja(loja)
            total += int(resultado.get("novas") or 0)
            if not resultado.get("ok"):
                logger.info("NF-e entrada loja %s: %s", loja.id, resultado.get("detail"))
        except Exception:
            logger.exception("NF-e entrada loja %s", loja.id)
        finally:
            set_current_loja_id(None)
            set_current_tenant_db("default")
    return total
