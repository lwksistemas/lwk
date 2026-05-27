"""Persistencia de NFS-e no banco (contexto loja/CRM)."""
import logging
from decimal import Decimal
from typing import Any
from uuid import uuid4

from django.db.models import Max
from django.utils import timezone

logger = logging.getLogger(__name__)


def gerar_proximo_numero_rps(loja_id: int, config: Any) -> int:
    """Proximo numero RPS/DPS baseado no maior ja gravado."""
    from nfse_integration.models import NFSe

    mx = NFSe.objects.filter(loja_id=loja_id).aggregate(m=Max('numero_rps'))['m']
    mx = int(mx or 0)
    portal_ult = int(
        getattr(config, 'nacional_ultimo_dps', 0)
        or getattr(config, 'issnet_ultimo_rps_conhecido', 0)
        or 0
    )
    nxt = max(mx + 1, portal_ult + 1)
    logger.info('NFS-e proximo RPS/DPS: max_BD=%s, portal=%s -> %s', mx, portal_ult, nxt)
    return nxt


def salvar_nfse_emitida(
    loja_id: int,
    resultado: dict[str, Any],
    tomador_email: str,
    provedor: str = 'nacional',
) -> None:
    from nfse_integration.models import NFSe

    try:
        aliquota_iss = Decimal(str(resultado.get('aliquota_iss', 0) or 0))
        valor_iss = Decimal(str(resultado.get('valor_iss', 0) or 0))
        NFSe.objects.create(
            loja_id=loja_id,
            numero_nf=resultado['numero_nf'],
            numero_rps=int(resultado.get('numero_rps') or 0),
            codigo_verificacao=resultado.get('codigo_verificacao', ''),
            data_emissao=resultado.get('data_emissao', timezone.now()),
            valor=resultado.get('valor', 0),
            aliquota_iss=aliquota_iss,
            valor_iss=valor_iss,
            tomador_email=tomador_email,
            tomador_nome=resultado.get('tomador_nome', ''),
            tomador_cpf_cnpj=resultado.get('tomador_cpf_cnpj', ''),
            servico_descricao=(resultado.get('servico_descricao') or '')[:500],
            xml_nfse=resultado.get('xml_nfse', ''),
            pdf_url=(resultado.get('pdf_url', '') or '')[:500],
            provedor=provedor,
            status='emitida',
        )
        logger.info('NFS-e %s salva (provedor=%s, loja_id=%s)', resultado['numero_nf'], provedor, loja_id)
    except Exception as exc:
        logger.error('Erro ao salvar NFS-e no banco: %s', exc)


def registrar_falha_emissao_loja(
    loja_id: int,
    erro_msg: str,
    tomador_cpf_cnpj: str,
    tomador_nome: str,
    tomador_email: str,
    servico_descricao: str,
    valor_servicos: Decimal,
    numero_rps: int = 0,
    provedor: str = 'nacional',
) -> Any | None:
    from nfse_integration.models import NFSe

    numero_nf = f'FALHA-{uuid4().hex[:12]}'
    try:
        return NFSe.objects.create(
            loja_id=loja_id,
            numero_nf=numero_nf[:50],
            numero_rps=int(numero_rps or 0),
            codigo_verificacao='',
            data_emissao=timezone.now(),
            valor=valor_servicos,
            tomador_cpf_cnpj=(tomador_cpf_cnpj or '')[:18],
            tomador_nome=(tomador_nome or '')[:200],
            tomador_email=tomador_email or '',
            servico_descricao=(servico_descricao or '')[:500],
            provedor=provedor,
            status='erro',
            erro=(erro_msg or 'Erro desconhecido')[:2000],
        )
    except Exception as exc:
        logger.error('Erro ao registrar falha de NFS-e: %s', exc, exc_info=True)
        return None
