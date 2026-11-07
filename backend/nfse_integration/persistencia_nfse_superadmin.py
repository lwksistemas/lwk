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


JANELA_EMISSAO_MINUTOS = 15


class EmissaoJaEmAndamento(Exception):
    """Já existe uma emissão igual da LWK que ainda não terminou."""

    def __init__(self, numero_rps: int, mensagem: str = ""):
        self.numero_rps = int(numero_rps or 0)
        super().__init__(
            mensagem
            or f"Esta emissão já está em andamento (DPS {self.numero_rps}). Espere ela aparecer na lista.",
        )


def reservar_emissao_superadmin(config: Any, payload: Any) -> Any:
    """Reserva o próximo DPS da LWK e recusa um segundo clique igual."""
    from datetime import timedelta

    from django.db import transaction

    from core.cpf_utils import normalizar_cpf_cnpj
    from superadmin.models import NFSeEmitida

    cpf = normalizar_cpf_cnpj(getattr(payload, "tomador_cpf_cnpj", "") or "")[:18]
    descricao = (getattr(payload, "descricao", "") or "")[:500]
    valor = Decimal(str(getattr(payload, "valor", 0) or 0)).quantize(Decimal("0.01"))
    with transaction.atomic():
        travada = type(config).objects.using("default").select_for_update().get(pk=config.pk)
        agora = timezone.now()
        limite = agora - timedelta(minutes=JANELA_EMISSAO_MINUTOS)
        abertas = list(
            NFSeEmitida.objects.select_for_update().filter(
                status="pendente",
                tomador_cpf_cnpj=cpf,
                descricao_servico=descricao,
                valor=valor,
            ),
        )
        recente = next((nota for nota in abertas if nota.created_at and nota.created_at >= limite), None)
        if recente:
            raise EmissaoJaEmAndamento(recente.numero_rps)
        if abertas:
            for antiga in abertas:
                antiga.status = "erro"
                antiga.erro_mensagem = (
                    "A emissão anterior passou do tempo. "
                    f"Confira o DPS {antiga.numero_rps} na prefeitura antes de emitir outra igual."
                )[:2000]
                antiga.save(update_fields=["status", "erro_mensagem"])
            numero_antigo = abertas[0].numero_rps
            raise EmissaoJaEmAndamento(
                numero_antigo,
                (
                    f"A emissão do DPS {numero_antigo} passou do tempo e foi interrompida. "
                    "Confira na prefeitura. Se a nota não estiver lá, emita de novo."
                ),
            )
        numero = int(travada.nacional_ultimo_dps or 0) + 1
        travada.nacional_ultimo_dps = numero
        travada.ultimo_rps = numero
        travada.save(update_fields=["nacional_ultimo_dps", "ultimo_rps", "updated_at"])
        config.nacional_ultimo_dps = numero
        config.ultimo_rps = numero
        return NFSeEmitida.objects.create(
            loja=getattr(payload, "loja", None),
            numero_nf=f"PENDENTE-{numero}"[:50],
            numero_rps=numero,
            serie_rps=travada.nacional_serie_dps or "1",
            provedor="nacional",
            status="pendente",
            valor=valor,
            aliquota_iss=Decimal(str(getattr(travada, "aliquota_iss", 0) or 0)),
            tomador_nome=(getattr(payload, "tomador_nome", "") or "")[:200],
            tomador_cpf_cnpj=cpf,
            tomador_email=getattr(payload, "tomador_email", "") or "",
            descricao_servico=descricao,
            data_emissao=agora,
        )


def _pendente_do_dps(numero_dps: int) -> Any | None:
    from superadmin.models import NFSeEmitida

    if not numero_dps:
        return None
    base = NFSeEmitida.objects.filter(numero_rps=int(numero_dps))
    return base.filter(status="pendente").first() or base.filter(status="erro").first()


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
    pendente = _pendente_do_dps(numero_dps)
    if pendente:
        pendente.numero_nf = chave[:50]
        pendente.codigo_verificacao = (chave or resultado.get("nsu_recepcao") or "")[:50]
        pendente.serie_rps = config.nacional_serie_dps or "1"
        pendente.provedor = "nacional"
        pendente.status = "emitida"
        pendente.valor = payload.valor
        pendente.aliquota_iss = aliquota
        pendente.valor_iss = valor_iss
        pendente.tomador_nome = payload.tomador_nome
        pendente.tomador_cpf_cnpj = payload.tomador_cpf_cnpj
        pendente.tomador_email = payload.tomador_email
        pendente.descricao_servico = payload.descricao[:500]
        pendente.xml_nfse = resultado.get("xml_nfse") or resultado.get("xml_dps", "")
        pendente.xml_dps_assinado = resultado.get("xml_dps", "")
        pendente.resposta_adn = resultado.get("resposta_adn_raw", "")
        pendente.erro_mensagem = ""
        pendente.data_emissao = timezone.now()
        pendente.save()
        return pendente
    return NFSeEmitida.objects.create(
        loja=payload.loja,
        pagamento=None,
        numero_nf=chave[:50],
        codigo_verificacao=(chave or resultado.get("nsu_recepcao") or "")[:50],
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
        xml_nfse=resultado.get("xml_nfse") or resultado.get("xml_dps", ""),
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
    pendente = _pendente_do_dps(numero_dps)
    if pendente:
        pendente.status = "erro"
        pendente.erro_mensagem = error_msg[:2000]
        pendente.xml_dps_assinado = resultado.get("xml_dps", "") or ""
        pendente.resposta_adn = resultado.get("resposta_adn_raw", "") or ""
        pendente.numero_nf = ""
        pendente.save(update_fields=["status", "erro_mensagem", "xml_dps_assinado", "resposta_adn", "numero_nf"])
        return pendente
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
