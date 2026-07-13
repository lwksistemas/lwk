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
) -> Any | None:
    from nfse_integration.models import NFSe

    try:
        aliquota_iss = Decimal(str(resultado.get('aliquota_iss', 0) or 0))
        valor_iss = Decimal(str(resultado.get('valor_iss', 0) or 0))
        nfse = NFSe.objects.create(
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
            tomador_cpf_cnpj=normalizar_cpf_cnpj(resultado.get('tomador_cpf_cnpj', '')),
            servico_descricao=(resultado.get('servico_descricao') or '')[:500],
            xml_nfse=resultado.get('xml_nfse', ''),
            pdf_url=(resultado.get('pdf_url', '') or '')[:500],
            provedor=provedor,
            status='emitida',
        )
        logger.info('NFS-e %s salva (provedor=%s, loja_id=%s)', resultado['numero_nf'], provedor, loja_id)
        return nfse
    except Exception as exc:
        logger.error('Erro ao salvar NFS-e no banco: %s', exc, exc_info=True)
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
            tomador_cpf_cnpj=normalizar_cpf_cnpj(tomador_cpf_cnpj or '')[:18],
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


def nfse_importacao_incompleta(nfse: Any, loja: Any | None = None) -> bool:
    """True quando a nota foi importada só com número/URL (sem tomador, valor ou XML)."""
    if not nfse:
        return False
    valor = Decimal(str(getattr(nfse, 'valor', 0) or 0))
    tomador = (getattr(nfse, 'tomador_nome', '') or '').strip()
    prest_cnpj = re.sub(r'\D', '', getattr(loja, 'cpf_cnpj', '') or '') if loja else ''
    tom_doc = re.sub(r'\D', '', getattr(nfse, 'tomador_cpf_cnpj', '') or '')
    if prest_cnpj and tom_doc == prest_cnpj:
        return True
    if valor <= 0 or not tomador:
        return True
    from nfse_integration.xml_nfse_loja import nfse_precisa_buscar_xml

    return bool(nfse_precisa_buscar_xml(nfse))


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
        update_fields: list[str] = []
        if resultado.get('numero_rps'):
            nfse.numero_rps = int(resultado['numero_rps'])
            update_fields.append('numero_rps')
        if resultado.get('codigo_verificacao'):
            nfse.codigo_verificacao = str(resultado['codigo_verificacao'])[:50]
            update_fields.append('codigo_verificacao')
        if resultado.get('data_emissao'):
            nfse.data_emissao = resultado['data_emissao']
            update_fields.append('data_emissao')
        valor = resultado.get('valor')
        if valor is not None and Decimal(str(valor or 0)) > 0:
            nfse.valor = valor
            update_fields.append('valor')
        if resultado.get('aliquota_iss') is not None:
            nfse.aliquota_iss = Decimal(str(resultado.get('aliquota_iss') or 0))
            update_fields.append('aliquota_iss')
        if resultado.get('valor_iss') is not None:
            nfse.valor_iss = Decimal(str(resultado.get('valor_iss') or 0))
            update_fields.append('valor_iss')
        if resultado.get('tomador_nome'):
            nfse.tomador_nome = str(resultado['tomador_nome'])[:200]
            update_fields.append('tomador_nome')
        if 'tomador_cpf_cnpj' in resultado:
            novo_doc = normalizar_cpf_cnpj(str(resultado.get('tomador_cpf_cnpj') or ''))[:18]
            prest = re.sub(r'\D', '', getattr(loja, 'cpf_cnpj', '') or '') if loja else ''
            if not (prest and novo_doc == prest):
                nfse.tomador_cpf_cnpj = novo_doc
                update_fields.append('tomador_cpf_cnpj')
            elif nfse.tomador_cpf_cnpj:
                nfse.tomador_cpf_cnpj = ''
                update_fields.append('tomador_cpf_cnpj')
        if resultado.get('servico_descricao'):
            nfse.servico_descricao = str(resultado['servico_descricao'])[:500]
            update_fields.append('servico_descricao')
        if resultado.get('xml_nfse'):
            nfse.xml_nfse = resultado['xml_nfse']
            update_fields.append('xml_nfse')
        if resultado.get('pdf_url'):
            nfse.pdf_url = str(resultado['pdf_url'])[:500]
            update_fields.append('pdf_url')
        if resultado.get('tomador_email'):
            nfse.tomador_email = str(resultado['tomador_email'])[:254]
            update_fields.append('tomador_email')
        if not update_fields:
            return nfse
        nfse.save(update_fields=update_fields)
        return nfse
    except Exception as exc:
        logger.error('Erro ao atualizar NFS-e recuperada id=%s: %s', getattr(nfse, 'id', None), exc)
        return None
