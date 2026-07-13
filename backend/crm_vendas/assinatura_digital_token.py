"""
Tokens e verificação de links de assinatura digital (CRM).
"""
import logging
from datetime import timedelta
from urllib.parse import unquote

from django.core.signing import BadSignature, dumps, loads
from django.utils import timezone

from core.assinatura_service import normalizar_token_url

logger = logging.getLogger(__name__)

TOKEN_EXPIRACAO_DIAS = 7

MSG_LINK_SUBSTITUIDO = (
    'Este link não é mais válido. Foi enviado um link mais recente '
    'por e-mail ou WhatsApp — abra a última mensagem recebida para assinar.'
)

AVISO_LINK_ANTERIOR = (
    'Você abriu um link anterior. Também enviamos um link mais recente '
    'por e-mail ou WhatsApp; se preferir, pode concluir a assinatura nesta página.'
)

normalizar_token_assinatura_url = normalizar_token_url

def criar_token_assinatura(documento, tipo, loja_id):
    """
    Cria token de assinatura para cliente ou vendedor.
    
    Args:
        documento: instância de Proposta ou Contrato
        tipo: 'cliente' ou 'vendedor'
        loja_id: ID da loja
    
    Returns:
        AssinaturaDigital: instância criada
    """
    from .models import AssinaturaDigital
    
    # Obter dados do assinante
    if tipo == 'cliente':
        lead = documento.oportunidade.lead
        nome = lead.nome
        email = lead.email
    else:  # vendedor
        vendedor = documento.oportunidade.vendedor
        if vendedor:
            nome = vendedor.nome
            email = vendedor.email
        else:
            # Fallback: usar dados da loja (admin)
            from superadmin.models import Loja
            loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
            if loja and loja.owner:
                nome = loja.owner.get_full_name() or loja.owner.username
                email = loja.owner.email
            else:
                nome = 'Vendedor'
                email = ''
    
    # Gerar token único
    payload = {
        'doc_type': documento.__class__.__name__.lower(),
        'doc_id': documento.id,
        'tipo': tipo,
        'loja_id': loja_id,
        'exp': int((timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS)).timestamp()),
    }
    # Gerar token - Django já usa base64 URL-safe
    token = dumps(payload)
    logger.info(
        'Token de assinatura gerado: tipo=%s, documento=%s#%s, loja_id=%s, tamanho=%s',
        tipo,
        documento.__class__.__name__,
        documento.id,
        loja_id,
        len(token),
    )
    
    # Criar registro de assinatura
    # Determinar se é proposta ou contrato
    kwargs = {
        'tipo': tipo,
        'nome_assinante': nome,
        'email_assinante': email,
        'token': token,
        'token_expira_em': timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS),
        'loja_id': loja_id,
        'ip_address': '0.0.0.0',  # Será atualizado ao assinar
    }
    
    if documento.__class__.__name__ == 'Proposta':
        kwargs['proposta'] = documento
    else:
        kwargs['contrato'] = documento

    assinatura = AssinaturaDigital.objects.create(**kwargs)
    
    logger.info(
        f'✅ Token de assinatura criado e salvo no banco: '
        f'tipo={tipo}, documento={documento.__class__.__name__}#{documento.id}, '
        f'assinante={nome}, loja_id={loja_id}, assinatura_id={assinatura.id}'
    )
    
    return assinatura


def _payload_assinatura_de_token(token):
    """Decodifica payload assinado do Django ou retorna None."""
    try:
        return loads(token)
    except (BadSignature, Exception):
        return None


def _buscar_assinatura_pendente_por_payload(payload, loja_id):
    """
    Fallback quando o token exato foi rotacionado (ex.: reenvio por outro canal).
    Aceita qualquer link assinado válido para o mesmo documento/tipo pendente.
    """
    from .models import AssinaturaDigital

    doc_type = (payload.get('doc_type') or '').lower()
    doc_id = payload.get('doc_id')
    tipo = payload.get('tipo')
    if not doc_id or tipo not in ('cliente', 'vendedor'):
        return None

    filt = {'tipo': tipo, 'assinado': False, 'loja_id': loja_id}
    if doc_type == 'proposta':
        filt['proposta_id'] = doc_id
    elif doc_type == 'contrato':
        filt['contrato_id'] = doc_id
    else:
        return None

    assinatura = (
        AssinaturaDigital.objects.select_related('proposta', 'contrato')
        .filter(**filt)
        .order_by('-created_at')
        .first()
    )
    if not assinatura:
        return None
    if assinatura.is_expirado():
        return None
    return assinatura


def _documento_aguarda_assinatura(payload, loja_id):
    """True se proposta/contrato ainda está aguardando assinatura."""
    doc_type = (payload.get('doc_type') or '').lower()
    doc_id = payload.get('doc_id')
    if not doc_id:
        return False
    if doc_type == 'proposta':
        from .models import Proposta
        doc = Proposta.objects.filter(pk=doc_id, loja_id=loja_id).first()
    elif doc_type == 'contrato':
        from .models import Contrato
        doc = Contrato.objects.filter(pk=doc_id, loja_id=loja_id).first()
    else:
        return False
    if not doc:
        return False
    return getattr(doc, 'status_assinatura', '') in ('aguardando_cliente', 'aguardando_vendedor')


def verificar_token_assinatura(token, loja_id=None):
    """
    Verifica e retorna AssinaturaDigital se token válido.
    
    Args:
        token: string do token (pode estar URL encoded ou não)
        loja_id: ID da loja (opcional, será extraído do token se não fornecido)
    
    Returns:
        tuple: (AssinaturaDigital ou None, mensagem_erro ou None, loja_id, meta dict)
    """
    from .models import AssinaturaDigital

    meta: dict = {}
    token = normalizar_token_assinatura_url(token)
    if not token:
        return None, 'Link de assinatura inválido.', loja_id, {'error_code': 'invalido'}

    payload = _payload_assinatura_de_token(token)
    if payload is None:
        logger.error('❌ Erro ao decodificar token de assinatura')
        return None, 'Link de assinatura inválido.', loja_id, {'error_code': 'invalido'}

    exp = payload.get('exp')
    if exp and timezone.now().timestamp() > exp:
        return None, 'Este link de assinatura expirou.', loja_id, {'error_code': 'expirado'}

    if loja_id is None:
        loja_id = payload.get('loja_id')
    elif payload.get('loja_id') and int(payload.get('loja_id')) != int(loja_id):
        return None, 'Link de assinatura inválido.', loja_id, {'error_code': 'invalido'}

    logger.info(
        'Verificando token de assinatura: tamanho=%s, loja_id=%s, doc_type=%s, doc_id=%s',
        len(token),
        loja_id,
        payload.get('doc_type'),
        payload.get('doc_id'),
    )

    assinatura = None
    try:
        try:
            assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(token=token)
            logger.info('✅ Token encontrado direto - ID: %s', assinatura.id)
        except AssinaturaDigital.DoesNotExist:
            token_decoded = unquote(token)
            if token_decoded != token:
                assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(
                    token=token_decoded,
                )
                logger.info('✅ Token encontrado após decode - ID: %s', assinatura.id)
            else:
                raise AssinaturaDigital.DoesNotExist
    except AssinaturaDigital.DoesNotExist:
        assinatura = _buscar_assinatura_pendente_por_payload(payload, loja_id)
        if assinatura:
            meta['link_anterior'] = True
            logger.info(
                '✅ Token rotacionado — usando assinatura pendente ID=%s (doc=%s#%s)',
                assinatura.id,
                payload.get('doc_type'),
                payload.get('doc_id'),
            )
        elif _documento_aguarda_assinatura(payload, loja_id):
            logger.warning(
                'Link substituído: token válido mas ausente no banco (loja_id=%s, doc=%s#%s)',
                loja_id,
                payload.get('doc_type'),
                payload.get('doc_id'),
            )
            return None, MSG_LINK_SUBSTITUIDO, loja_id, {'error_code': 'link_substituido'}
        else:
            logger.error('❌ Token não encontrado no banco de dados (loja_id=%s)', loja_id)
            return None, 'Link de assinatura inválido.', loja_id, {'error_code': 'invalido'}

    if assinatura.assinado:
        logger.warning('⚠️ Documento já foi assinado - Assinatura ID: %s', assinatura.id)
        return None, 'Este documento já foi assinado.', loja_id, {'error_code': 'ja_assinado'}

    doc = assinatura.proposta or assinatura.contrato
    if doc is not None and getattr(doc, 'status_assinatura', '') == 'concluido':
        logger.warning(
            '⚠️ Documento já concluído (assinatura manual) - Assinatura ID: %s',
            assinatura.id,
        )
        return None, 'Este documento já foi assinado.', loja_id, {'error_code': 'ja_assinado'}

    if assinatura.is_expirado():
        logger.warning('⚠️ Token expirado - Assinatura ID: %s', assinatura.id)
        return None, 'Este link de assinatura expirou.', loja_id, {'error_code': 'expirado'}

    if meta.get('link_anterior'):
        meta['aviso'] = AVISO_LINK_ANTERIOR

    logger.info('✅ Token válido e ativo - Assinatura ID: %s', assinatura.id)
    return assinatura, None, loja_id, meta
