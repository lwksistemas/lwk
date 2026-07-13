"""Persistencia de NFSeEmitida (superadmin)."""
import logging
from decimal import Decimal
from typing import Any

from django.db.models import Max
from django.utils import timezone

logger = logging.getLogger(__name__)


def gerar_proximo_numero_rps_superadmin(config: Any) -> int:
    """Próximo RPS para assinatura/superadmin: maior entre BD, config (tela) e legado.
    """
    from superadmin.models import NFSeEmitida

    mx = NFSeEmitida.objects.aggregate(m=Max("numero_rps"))["m"]
    mx = int(mx or 0)
    portal_ult = max(
        int(getattr(config, "nacional_ultimo_dps", 0) or 0),
        int(getattr(config, "ultimo_rps", 0) or 0),
    )
    nxt = max(mx, portal_ult) + 1
    logger.info("NFS-e superadmin próximo RPS: max_BD=%s config=%s -> %s", mx, portal_ult, nxt)
    return nxt


def sincronizar_contadores_rps_superadmin(config: Any, numero_rps: int) -> None:
    """Mantém nacional_ultimo_dps (tela) e ultimo_rps (legado) alinhados após emissão."""
    n = int(numero_rps)
    config.nacional_ultimo_dps = n
    config.ultimo_rps = n
    config.save(update_fields=["nacional_ultimo_dps", "ultimo_rps", "updated_at"])


def salvar_nfse_emitida_issnet_superadmin(
    payload: Any,
    config: Any,
    resultado: dict,
    *,
    numero_rps: int,
    serie_rps: str,
) -> Any:
    from superadmin.models import NFSeEmitida

    aliquota = Decimal(str(config.aliquota_iss))
    valor_iss = (payload.valor * aliquota / 100).quantize(Decimal("0.01"))
    return NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf=resultado.get("numero_nf", ""),
        codigo_verificacao=resultado.get("codigo_verificacao", ""),
        numero_rps=numero_rps,
        serie_rps=serie_rps,
        provedor="issnet",
        status="emitida",
        valor=payload.valor,
        aliquota_iss=aliquota,
        valor_iss=valor_iss,
        tomador_nome=payload.tomador_nome,
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_email=payload.tomador_email,
        descricao_servico=payload.descricao[:500],
        xml_nfse=resultado.get("xml_nfse", ""),
        data_emissao=timezone.now(),
    )


def salvar_nfse_erro_issnet_superadmin(
    payload: Any,
    config: Any,
    error_msg: str,
    *,
    numero_rps: int,
    serie_rps: str,
) -> None:
    from superadmin.models import NFSeEmitida

    aliquota = Decimal(str(config.aliquota_iss))
    NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf="",
        numero_rps=numero_rps,
        serie_rps=serie_rps,
        provedor="issnet",
        status="erro",
        valor=payload.valor,
        aliquota_iss=aliquota,
        valor_iss=Decimal(0),
        tomador_nome=payload.tomador_nome,
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_email=payload.tomador_email,
        descricao_servico=payload.descricao[:500],
        erro_mensagem=error_msg[:2000],
    )


def salvar_nfse_emitida_nacional_superadmin(
    payload: Any,
    config: Any,
    resultado: dict,
    *,
    numero_dps: int,
) -> Any:
    from superadmin.models import NFSeEmitida

    aliquota = Decimal(str(config.aliquota_iss))
    valor_iss = (payload.valor * aliquota / 100).quantize(Decimal("0.01"))
    chave = resultado.get("chave_acesso", "")
    return NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf=chave,
        codigo_verificacao=resultado.get("nsu_recepcao", ""),
        numero_rps=numero_dps,
        serie_rps=config.nacional_serie_dps or "1",
        provedor="nacional",
        status="emitida",
        valor=payload.valor,
        aliquota_iss=aliquota,
        valor_iss=valor_iss,
        tomador_nome=payload.tomador_nome,
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_email=payload.tomador_email,
        descricao_servico=payload.descricao[:500],
        xml_nfse=resultado.get("xml_dps", ""),
        xml_dps_assinado=resultado.get("xml_dps", ""),
        resposta_adn=resultado.get("resposta_adn_raw", ""),
        data_emissao=timezone.now(),
    )


def salvar_nfse_erro_nacional_superadmin(
    payload: Any,
    config: Any,
    resultado: dict,
    error_msg: str,
    *,
    numero_dps: int,
) -> Any:
    from superadmin.models import NFSeEmitida

    aliquota = Decimal(str(config.aliquota_iss))
    return NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf="",
        numero_rps=numero_dps,
        serie_rps=config.nacional_serie_dps or "1",
        provedor="nacional",
        status="erro",
        valor=payload.valor,
        aliquota_iss=aliquota,
        valor_iss=Decimal(0),
        tomador_nome=payload.tomador_nome,
        tomador_cpf_cnpj=payload.tomador_cpf_cnpj,
        tomador_email=payload.tomador_email,
        descricao_servico=payload.descricao[:500],
        xml_dps_assinado=resultado.get("xml_dps", "") or "",
        resposta_adn=resultado.get("resposta_adn_raw", "") or "",
        erro_mensagem=error_msg[:2000],
    )
