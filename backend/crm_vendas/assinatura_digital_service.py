"""
Serviço de Assinatura Digital para Propostas e Contratos.
Gerencia workflow de assinatura: cliente → vendedor → concluído.
"""
from django.core.signing import dumps, loads, BadSignature
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from datetime import timedelta
from urllib.parse import quote, unquote
import logging

logger = logging.getLogger(__name__)

# Configurações
TOKEN_EXPIRACAO_DIAS = 7  # Token válido por 7 dias


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
    
    logger.info(f'🔑 Token gerado: {token}')
    logger.info(f'   Tamanho: {len(token)}, Contém ":": {(":" in token)}')
    
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
    logger.info(f'   Token salvo no banco: {assinatura.token}')
    
    return assinatura



def verificar_token_assinatura(token):
    """
    Verifica e retorna AssinaturaDigital se token válido.
    
    Args:
        token: string do token (pode estar URL encoded ou não)
    
    Returns:
        tuple: (AssinaturaDigital ou None, mensagem_erro ou None)
    """
    from .models import AssinaturaDigital
    
    logger.info(f'🔍 Verificando token de assinatura - Tamanho: {len(token)}, Primeiros 50 chars: {token[:50]}...')
    
    try:
        # Tentar buscar com o token como está (pode estar URL encoded)
        try:
            logger.info(f'Tentando buscar token direto no banco...')
            assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(token=token)
            logger.info(f'✅ Token encontrado direto - ID: {assinatura.id}')
        except AssinaturaDigital.DoesNotExist:
            # Se não encontrar, tentar com URL decode (para tokens antigos que foram salvos encoded)
            token_decoded = unquote(token)
            logger.info(f'Token não encontrado direto. Tentando com decode... Decoded: {token_decoded[:50]}...')
            if token_decoded != token:  # Só tenta se realmente decodificou algo
                assinatura = AssinaturaDigital.objects.select_related('proposta', 'contrato').get(token=token_decoded)
                logger.info(f'✅ Token encontrado após decode - ID: {assinatura.id}')
            else:
                logger.warning(f'❌ Token não mudou após decode')
                raise AssinaturaDigital.DoesNotExist
        
        # Verificar se já foi assinado
        if assinatura.assinado:
            logger.warning(f'⚠️ Documento já foi assinado - Assinatura ID: {assinatura.id}')
            return None, 'Este documento já foi assinado.'
        
        # Verificar expiração
        if assinatura.is_expirado():
            logger.warning(f'⚠️ Token expirado - Assinatura ID: {assinatura.id}')
            return None, 'Este link de assinatura expirou.'
        
        logger.info(f'✅ Token válido e ativo - Assinatura ID: {assinatura.id}')
        return assinatura, None
    except AssinaturaDigital.DoesNotExist:
        logger.error(f'❌ Token não encontrado no banco de dados')
        return None, 'Link de assinatura inválido.'


def registrar_assinatura(assinatura, ip_address, user_agent=''):
    """
    Registra a assinatura com IP e timestamp.
    Atualiza status do documento e inicia próximo passo do workflow.
    
    Args:
        assinatura: instância de AssinaturaDigital
        ip_address: IP do assinante
        user_agent: User agent do navegador
    
    Returns:
        str: próximo status ('aguardando_vendedor' ou 'concluido')
    """
    # Registrar assinatura
    assinatura.assinado = True
    assinatura.assinado_em = timezone.now()
    assinatura.ip_address = ip_address
    assinatura.user_agent = user_agent[:500]
    assinatura.save()
    
    documento = assinatura.documento
    
    logger.info(
        f'Assinatura registrada: tipo={assinatura.tipo}, documento={documento.__class__.__name__}#{documento.id}, '
        f'assinante={assinatura.nome_assinante}, ip={ip_address}'
    )
    
    if assinatura.tipo == 'cliente':
        # Cliente assinou: próximo passo é vendedor
        documento.status_assinatura = 'aguardando_vendedor'
        documento.save(update_fields=['status_assinatura', 'updated_at'])
        
        return 'aguardando_vendedor'
    else:
        # Vendedor assinou: documento concluído
        documento.status_assinatura = 'concluido'
        documento.save(update_fields=['status_assinatura', 'updated_at'])
        
        return 'concluido'


def enviar_email_assinatura_cliente(documento, assinatura, request):
    """
    Envia email para cliente com link de assinatura.
    
    Args:
        documento: instância de Proposta ou Contrato
        assinatura: instância de AssinaturaDigital
        request: HttpRequest para construir URL absoluta
    
    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    lead = documento.oportunidade.lead
    
    if not lead.email:
        return False, 'Lead não possui email cadastrado.'
    
    # Construir link de assinatura (usar URL do frontend)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    link_assinatura = f'{frontend_url}/assinar/{assinatura.token}'
    
    # Obter dados da loja
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    
    tipo_doc = 'Proposta' if documento.__class__.__name__ == 'Proposta' else 'Contrato'
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    
    try:
        email = EmailMessage(
            subject=f'Assinatura de {tipo_doc}: {documento.titulo}',
            body=(
                f'Olá {lead.nome},\n\n'
                f'Você recebeu um(a) {tipo_doc.lower()} para assinatura digital.\n\n'
                f'Título: {documento.titulo}\n'
                f'Valor: R$ {documento.valor_total or "0,00"}\n\n'
                f'Clique no link abaixo para visualizar e assinar:\n'
                f'{link_assinatura}\n\n'
                f'Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.\n\n'
                f'Atenciosamente,\n'
                f'{loja_nome}'
            ),
            from_email=from_email,
            to=[lead.email],
        )
        
        email.send(fail_silently=False)
        
        logger.info(
            f'Email de assinatura enviado para cliente: {lead.email}, '
            f'documento={documento.__class__.__name__}#{documento.id}'
        )
        
        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar email de assinatura para cliente: {e}')
        return False, str(e)



def enviar_email_assinatura_vendedor(documento, assinatura, request):
    """
    Envia email para vendedor com link de assinatura.
    
    Args:
        documento: instância de Proposta ou Contrato
        assinatura: instância de AssinaturaDigital
        request: HttpRequest para construir URL absoluta
    
    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    if not assinatura.email_assinante:
        return False, 'Vendedor não possui email cadastrado.'
    
    # Construir link de assinatura (usar URL do frontend)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    link_assinatura = f'{frontend_url}/assinar/{assinatura.token}'
    
    # Obter dados da loja
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    
    tipo_doc = 'Proposta' if documento.__class__.__name__ == 'Proposta' else 'Contrato'
    lead = documento.oportunidade.lead
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    
    try:
        email = EmailMessage(
            subject=f'Assinatura de {tipo_doc}: {documento.titulo}',
            body=(
                f'Olá {assinatura.nome_assinante},\n\n'
                f'O cliente {lead.nome} assinou o(a) {tipo_doc.lower()}.\n'
                f'Agora é sua vez de assinar digitalmente.\n\n'
                f'Título: {documento.titulo}\n'
                f'Cliente: {lead.nome}\n'
                f'Valor: R$ {documento.valor_total or "0,00"}\n\n'
                f'Clique no link abaixo para visualizar e assinar:\n'
                f'{link_assinatura}\n\n'
                f'Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.\n\n'
                f'Atenciosamente,\n'
                f'{loja_nome}'
            ),
            from_email=from_email,
            to=[assinatura.email_assinante],
        )
        
        email.send(fail_silently=False)
        
        logger.info(
            f'Email de assinatura enviado para vendedor: {assinatura.email_assinante}, '
            f'documento={documento.__class__.__name__}#{documento.id}'
        )
        
        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar email de assinatura para vendedor: {e}')
        return False, str(e)


def enviar_pdf_final(documento, loja_id):
    """
    Envia PDF final com ambas assinaturas para cliente e vendedor.
    
    Args:
        documento: instância de Proposta ou Contrato
        loja_id: ID da loja
    
    Returns:
        tuple: (sucesso: bool, erro: str ou None)
    """
    from .pdf_proposta_contrato import gerar_pdf_proposta, gerar_pdf_contrato
    from superadmin.models import Loja
    
    # Gerar PDF com assinaturas
    if documento.__class__.__name__ == 'Proposta':
        pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=True)
        tipo_doc = 'Proposta'
    else:
        pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=True)
        tipo_doc = 'Contrato'
    
    pdf_buffer.seek(0)
    pdf_bytes = pdf_buffer.read()
    
    # Obter dados
    lead = documento.oportunidade.lead
    vendedor = documento.oportunidade.vendedor
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    
    # Preparar lista de destinatários
    destinatarios = []
    if lead.email:
        destinatarios.append(lead.email)
    if vendedor and vendedor.email:
        destinatarios.append(vendedor.email)
    elif loja and loja.owner and loja.owner.email:
        destinatarios.append(loja.owner.email)
    
    if not destinatarios:
        return False, 'Nenhum destinatário com email cadastrado.'
    
    filename = f'{tipo_doc.lower()}_{documento.titulo or documento.id}_assinado.pdf'
    
    try:
        email = EmailMessage(
            subject=f'{tipo_doc} Assinado: {documento.titulo}',
            body=(
                f'Olá,\n\n'
                f'O(A) {tipo_doc.lower()} foi assinado por ambas as partes.\n\n'
                f'Título: {documento.titulo}\n'
                f'Cliente: {lead.nome}\n'
                f'Valor: R$ {documento.valor_total or "0,00"}\n\n'
                f'Segue em anexo o documento assinado digitalmente.\n\n'
                f'Atenciosamente,\n'
                f'{loja_nome}'
            ),
            from_email=from_email,
            to=destinatarios,
        )
        
        email.attach(filename, pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
        
        logger.info(
            f'PDF final enviado: documento={documento.__class__.__name__}#{documento.id}, '
            f'destinatarios={destinatarios}'
        )
        
        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar PDF final: {e}')
        return False, str(e)
