"""Persistencia de NFS-e no banco (contexto loja/CRM)."""
import logging
import re
from decimal import Decimal
from typing import Any
from uuid import uuid4

from django.db.models import Max
from django.utils import timezone

from core.cpf_utils import normalizar_cpf_cnpj

logger = logging.getLogger(__name__)


class EmissaoJaEmAndamento(Exception):
    """Já existe uma emissão igual que ainda não terminou."""

    def __init__(self, numero_rps: int):
        self.numero_rps = int(numero_rps or 0)
        super().__init__(
            f"Esta emissão já está em andamento (DPS {self.numero_rps}). Espere ela aparecer na lista.",
        )


def _travar_config_nfse(config: Any) -> Any:
    """Trava a linha de configuração da loja. Sem pk, devolve o objeto como está."""
    pk = getattr(config, "pk", None)
    manager = getattr(type(config), "objects", None)
    if not pk or manager is None:
        return config
    travada = manager.select_for_update().filter(pk=pk).first()
    return travada or config


def _gravar_ultimo_numero(config: Any, numero: int) -> None:
    meta = getattr(config, "_meta", None)
    if not getattr(config, "pk", None) or meta is None:
        return
    nomes = {campo.name for campo in meta.fields}
    campos = []
    if "issnet_ultimo_rps_conhecido" in nomes:
        config.issnet_ultimo_rps_conhecido = numero
        campos.append("issnet_ultimo_rps_conhecido")
    if "nacional_ultimo_dps" in nomes:
        config.nacional_ultimo_dps = numero
        campos.append("nacional_ultimo_dps")
    if campos:
        config.save(update_fields=campos)


def _calcular_proximo_numero(loja_id: int, config: Any) -> int:
    from nfse_integration.models import NFSe

    mx = NFSe.objects.filter(loja_id=loja_id).aggregate(m=Max("numero_rps"))["m"]
    mx = int(mx or 0)
    portal_ult = int(
        getattr(config, "nacional_ultimo_dps", 0)
        or getattr(config, "issnet_ultimo_rps_conhecido", 0)
        or 0,
    )
    return max(mx + 1, portal_ult + 1)


def gerar_proximo_numero_rps(loja_id: int, config: Any) -> int:
    """Próximo RPS/DPS. Grava o número na configuração antes de devolver."""
    from django.db import transaction

    if not getattr(config, "pk", None):
        nxt = _calcular_proximo_numero(loja_id, config)
    else:
        with transaction.atomic():
            config = _travar_config_nfse(config)
            nxt = _calcular_proximo_numero(loja_id, config)
            _gravar_ultimo_numero(config, nxt)
    logger.info("NFS-e proximo RPS/DPS reservado: %s (loja_id=%s)", nxt, loja_id)
    return nxt


def reservar_emissao_loja(
    loja_id: int,
    config: Any,
    *,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    servico_descricao: str,
    valor_servicos: Decimal,
) -> Any:
    """Cria a linha pendente com o DPS reservado, ou recusa se a mesma já está saindo."""
    from datetime import timedelta

    from django.db import transaction

    from nfse_integration.models import NFSe

    cpf = normalizar_cpf_cnpj(tomador_cpf_cnpj or "")[:18]
    descricao = (servico_descricao or "")[:500]
    valor = Decimal(str(valor_servicos or 0)).quantize(Decimal("0.01"))
    with transaction.atomic():
        config = _travar_config_nfse(config)
        agora = timezone.now()
        limite = agora - timedelta(minutes=3)
        abertas = list(
            NFSe.objects.select_for_update().filter(
                loja_id=loja_id,
                status="pendente",
                tomador_cpf_cnpj=cpf,
                servico_descricao=descricao,
                valor=valor,
            ),
        )
        recente = next((nota for nota in abertas if nota.data_emissao and nota.data_emissao >= limite), None)
        if recente:
            raise EmissaoJaEmAndamento(recente.numero_rps)
        for antiga in abertas:
            antiga.status = "erro"
            antiga.erro = (
                "A emissão anterior não terminou. "
                f"Confira o DPS {antiga.numero_rps} na prefeitura antes de emitir outra igual."
            )[:2000]
            antiga.save(update_fields=["status", "erro", "updated_at"])
        numero = _calcular_proximo_numero(loja_id, config)
        _gravar_ultimo_numero(config, numero)
        provedor = (getattr(config, "provedor_nf", "") or "nacional").strip().lower()[:20]
        return NFSe.objects.create(
            loja_id=loja_id,
            numero_nf=f"PENDENTE-{numero}"[:50],
            numero_rps=numero,
            data_emissao=agora,
            valor=valor,
            tomador_cpf_cnpj=cpf,
            tomador_nome=(tomador_nome or "")[:200],
            tomador_email=tomador_email or "",
            servico_descricao=descricao,
            provedor=provedor or "nacional",
            status="pendente",
        )


def salvar_nfse_emitida(
    loja_id: int,
    resultado: dict[str, Any],
    tomador_email: str,
    provedor: str = "nacional",
) -> Any | None:
    from nfse_integration.issnet_nacional_xml_builder import extrair_chave_acesso_nfse_nacional
    from nfse_integration.models import NFSe

    try:
        aliquota_iss = Decimal(str(resultado.get("aliquota_iss", 0) or 0))
        valor_iss = Decimal(str(resultado.get("valor_iss", 0) or 0))
        xml_nfse = resultado.get("xml_nfse", "") or ""
        codigo_verificacao = (resultado.get("codigo_verificacao") or "").strip()
        if not codigo_verificacao and xml_nfse:
            codigo_verificacao = (extrair_chave_acesso_nfse_nacional(xml_nfse) or "").strip()
        numero_rps = int(resultado.get("numero_rps") or 0)
        if numero_rps:
            pendente = NFSe.objects.filter(
                loja_id=loja_id, numero_rps=numero_rps, status="pendente",
            ).first()
            if pendente:
                pendente.numero_nf = str(resultado["numero_nf"])[:50]
                pendente.codigo_verificacao = codigo_verificacao[:50]
                pendente.data_emissao = resultado.get("data_emissao", timezone.now())
                pendente.valor = resultado.get("valor", 0)
                pendente.aliquota_iss = aliquota_iss
                pendente.valor_iss = valor_iss
                pendente.tomador_email = tomador_email or pendente.tomador_email
                pendente.tomador_nome = (resultado.get("tomador_nome", "") or pendente.tomador_nome)[:200]
                pendente.tomador_cpf_cnpj = normalizar_cpf_cnpj(
                    resultado.get("tomador_cpf_cnpj", "") or pendente.tomador_cpf_cnpj,
                )[:18]
                pendente.servico_descricao = (resultado.get("servico_descricao") or pendente.servico_descricao or "")[:500]
                pendente.xml_nfse = xml_nfse
                pendente.pdf_url = (resultado.get("pdf_url", "") or "")[:1000]
                pendente.provedor = provedor
                pendente.status = "emitida"
                pendente.erro = ""
                pendente.save()
                logger.info("NFS-e %s concluída da reserva (loja_id=%s)", pendente.numero_nf, loja_id)
                return pendente
        nfse = NFSe.objects.create(
            loja_id=loja_id,
            numero_nf=resultado["numero_nf"],
            numero_rps=int(resultado.get("numero_rps") or 0),
            codigo_verificacao=codigo_verificacao[:50],
            data_emissao=resultado.get("data_emissao", timezone.now()),
            valor=resultado.get("valor", 0),
            aliquota_iss=aliquota_iss,
            valor_iss=valor_iss,
            tomador_email=tomador_email,
            tomador_nome=resultado.get("tomador_nome", ""),
            tomador_cpf_cnpj=normalizar_cpf_cnpj(resultado.get("tomador_cpf_cnpj", "")),
            servico_descricao=(resultado.get("servico_descricao") or "")[:500],
            xml_nfse=xml_nfse,
            pdf_url=(resultado.get("pdf_url", "") or "")[:1000],
            provedor=provedor,
            status="emitida",
        )
        logger.info("NFS-e %s salva (provedor=%s, loja_id=%s)", resultado["numero_nf"], provedor, loja_id)
        return nfse
    except Exception as exc:
        logger.error("Erro ao salvar NFS-e no banco: %s", exc, exc_info=True)
        return None


def registrar_falha_emissao_loja(
    loja_id: int,
    erro_msg: str,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    servico_descricao: str,
    valor_servicos: Decimal,
    numero_rps: int = 0,
    provedor: str = "nacional",
) -> Any | None:
    from nfse_integration.models import NFSe

    numero_nf = f"FALHA-{uuid4().hex[:12]}"
    try:
        if numero_rps:
            pendente = NFSe.objects.filter(
                loja_id=loja_id, numero_rps=int(numero_rps), status="pendente",
            ).first()
            if pendente:
                pendente.status = "erro"
                pendente.erro = (erro_msg or "Erro desconhecido")[:2000]
                pendente.numero_nf = f"FALHA-{int(numero_rps)}"[:50]
                pendente.save(update_fields=["status", "erro", "numero_nf", "updated_at"])
                return pendente
        return NFSe.objects.create(
            loja_id=loja_id,
            numero_nf=numero_nf[:50],
            numero_rps=int(numero_rps or 0),
            codigo_verificacao="",
            data_emissao=timezone.now(),
            valor=valor_servicos,
            tomador_cpf_cnpj=normalizar_cpf_cnpj(tomador_cpf_cnpj or "")[:18],
            tomador_nome=(tomador_nome or "")[:200],
            tomador_email=tomador_email or "",
            servico_descricao=(servico_descricao or "")[:500],
            provedor=provedor,
            status="erro",
            erro=(erro_msg or "Erro desconhecido")[:2000],
        )
    except Exception as exc:
        logger.error("Erro ao registrar falha de NFS-e: %s", exc, exc_info=True)
        return None


def nfse_importacao_incompleta(nfse: Any, loja: Any | None = None) -> bool:
    """True quando a nota foi importada só com número/URL (sem tomador, valor ou XML)."""
    if not nfse:
        return False
    valor = Decimal(str(getattr(nfse, "valor", 0) or 0))
    tomador = (getattr(nfse, "tomador_nome", "") or "").strip()
    prest_cnpj = re.sub(r"\D", "", getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    tom_doc = re.sub(r"\D", "", getattr(nfse, "tomador_cpf_cnpj", "") or "")
    if prest_cnpj and tom_doc == prest_cnpj:
        return True
    if valor <= 0 or not tomador:
        return True
    from nfse_integration.xml_nfse_loja import nfse_precisa_buscar_xml

    return bool(nfse_precisa_buscar_xml(nfse))


_CAMPOS_NFSE_SCALARES: list[tuple] = [
    ("numero_rps",      lambda r: int(r["numero_rps"]),                              "numero_rps"),
    ("codigo_verificacao", lambda r: str(r["codigo_verificacao"])[:50],               "codigo_verificacao"),
    ("data_emissao",    lambda r: r["data_emissao"],                                  "data_emissao"),
    ("servico_descricao", lambda r: str(r["servico_descricao"])[:500],                "servico_descricao"),
    ("xml_nfse",        lambda r: r["xml_nfse"],                                      "xml_nfse"),
    ("pdf_url",         lambda r: str(r["pdf_url"])[:500],                            "pdf_url"),
    ("tomador_email",   lambda r: str(r["tomador_email"])[:254],                      "tomador_email"),
    ("tomador_nome",    lambda r: str(r["tomador_nome"])[:200],                       "tomador_nome"),
]


def _aplicar_campos_scalares_nfse(nfse, resultado: dict) -> list[str]:
    """Aplica campos escalares de resultado a nfse. Retorna lista de update_fields."""
    update_fields: list[str] = []
    for chave, conversor, attr in _CAMPOS_NFSE_SCALARES:
        if resultado.get(chave):
            setattr(nfse, attr, conversor(resultado))
            update_fields.append(attr)
    valor = resultado.get("valor")
    if valor is not None and Decimal(str(valor or 0)) > 0:
        nfse.valor = valor
        update_fields.append("valor")
    if resultado.get("aliquota_iss") is not None:
        nfse.aliquota_iss = Decimal(str(resultado.get("aliquota_iss") or 0))
        update_fields.append("aliquota_iss")
    if resultado.get("valor_iss") is not None:
        nfse.valor_iss = Decimal(str(resultado.get("valor_iss") or 0))
        update_fields.append("valor_iss")
    return update_fields


def _aplicar_campo_tomador_cpf_cnpj(nfse, resultado: dict, loja) -> list[str]:
    """Aplica campo tomador_cpf_cnpj respeitando regra de não sobrescrever com CNPJ próprio."""
    if "tomador_cpf_cnpj" not in resultado:
        return []
    novo_doc = normalizar_cpf_cnpj(str(resultado.get("tomador_cpf_cnpj") or ""))[:18]
    prest = re.sub(r"\D", "", getattr(loja, "cpf_cnpj", "") or "") if loja else ""
    if not (prest and novo_doc == prest):
        nfse.tomador_cpf_cnpj = novo_doc
    elif nfse.tomador_cpf_cnpj:
        nfse.tomador_cpf_cnpj = ""
    return ["tomador_cpf_cnpj"]


def atualizar_nfse_recuperada(
    nfse: Any,
    resultado: dict[str, Any],
    *,
    loja: Any | None = None,
) -> Any | None:
    """Atualiza NFS-e incompleta com dados obtidos na recuperação."""
    if not nfse:
        return None
    try:
        update_fields = _aplicar_campos_scalares_nfse(nfse, resultado)
        update_fields += _aplicar_campo_tomador_cpf_cnpj(nfse, resultado, loja)
        if not update_fields:
            return nfse
        nfse.save(update_fields=list(dict.fromkeys(update_fields)))
        return nfse
    except Exception as exc:
        logger.error("Erro ao atualizar NFS-e recuperada id=%s: %s", getattr(nfse, "id", None), exc)
        return None
