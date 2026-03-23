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



def verificar_token_assinatura(token, loja_id=None):
    """
    Verifica e retorna AssinaturaDigital se token válido.
    
    Args:
        token: string do token (pode estar URL encoded ou não)
        loja_id: ID da loja (opcional, será extraído do token se não fornecido)
    
    Returns:
        tuple: (AssinaturaDigital ou None, mensagem_erro ou None, loja_id extraído)
    """
    from .models import AssinaturaDigital
    
    logger.info(f'🔍 Verificando token de assinatura - Tamanho: {len(token)}, Primeiros 50 chars: {token[:50]}...')
    
    # Se loja_id não foi fornecido, extrair do token
    if loja_id is None:
        try:
            # Decodificar token para extrair loja_id
            payload = loads(token)
            loja_id = payload.get('loja_id')
            logger.info(f'📦 Payload decodificado do token: loja_id={loja_id}, doc_type={payload.get("doc_type")}, doc_id={payload.get("doc_id")}')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return None, 'Link de assinatura inválido.', None
    
    try:
        # Tentar buscar com o token como está (pode estar URL encoded)
        try:
            logger.info(f'Tentando buscar token direto no banco (loja_id={loja_id})...')
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
            return None, 'Este documento já foi assinado.', loja_id
        
        # Verificar expiração
        if assinatura.is_expirado():
            logger.warning(f'⚠️ Token expirado - Assinatura ID: {assinatura.id}')
            return None, 'Este link de assinatura expirou.', loja_id
        
        logger.info(f'✅ Token válido e ativo - Assinatura ID: {assinatura.id}')
        return assinatura, None, loja_id
    except AssinaturaDigital.DoesNotExist:
        logger.error(f'❌ Token não encontrado no banco de dados (loja_id={loja_id})')
        return None, 'Link de assinatura inválido.', loja_id


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
    # URL encode do token para evitar problemas com caracteres especiais (:)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    token_encoded = quote(assinatura.token, safe='')
    link_assinatura = f'{frontend_url}/assinar/{token_encoded}'
    
    # Obter dados da loja
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    
    tipo_doc = 'Proposta' if documento.__class__.__name__ == 'Proposta' else 'Contrato'
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    
    # Template HTML profissional
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Assinatura Digital - {tipo_doc}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                    📄 Assinatura Digital
                                </h1>
                                <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                    {tipo_doc} aguardando sua assinatura
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá <strong>{lead.nome}</strong>,
                                </p>
                                
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Você recebeu um(a) <strong>{tipo_doc.lower()}</strong> de <strong>{loja_nome}</strong> para assinatura digital.
                                </p>
                                
                                <!-- Document Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Título:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 16px; font-weight: 600; padding-bottom: 15px;">
                                                        {documento.titulo}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Valor Total:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #10b981; font-size: 20px; font-weight: 700;">
                                                        R$ {documento.valor_total or "0,00"}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <a href="{link_assinatura}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);">
                                                ✍️ Visualizar e Assinar Documento
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff3cd; border-radius: 4px; margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #856404; font-size: 13px; margin: 0; line-height: 1.5;">
                                                ⏰ <strong>Atenção:</strong> Este link é válido por <strong>{TOKEN_EXPIRACAO_DIAS} dias</strong>. Após este período, será necessário solicitar um novo link de assinatura.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Se você tiver alguma dúvida sobre este documento, entre em contato conosco.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; text-align: center; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 15px; font-weight: 600; margin: 0 0 10px 0;">
                                    {loja_nome}
                                </p>
                                <p style="color: #666666; font-size: 13px; margin: 0; line-height: 1.5;">
                                    Este é um email automático. Por favor, não responda.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer Text -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="color: #999999; font-size: 12px; margin: 0;">
                                    © {timezone.now().year} {loja_nome}. Todos os direitos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Texto plano como fallback
    texto_plano = f"""
Olá {lead.nome},

Você recebeu um(a) {tipo_doc.lower()} de {loja_nome} para assinatura digital.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Valor Total: R$ {documento.valor_total or "0,00"}

ASSINAR DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Clique no link abaixo para visualizar e assinar:
{link_assinatura}

⏰ ATENÇÃO: Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.

Se você tiver alguma dúvida sobre este documento, entre em contato conosco.

Atenciosamente,
{loja_nome}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este é um email automático. Por favor, não responda.
© {timezone.now().year} {loja_nome}. Todos os direitos reservados.
    """
    
    try:
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=f'📄 Assinatura Digital - {tipo_doc}: {documento.titulo}',
            body=texto_plano,
            from_email=from_email,
            to=[lead.email],
        )
        
        email.attach_alternative(html_content, "text/html")
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
    # URL encode do token para evitar problemas com caracteres especiais (:)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    token_encoded = quote(assinatura.token, safe='')
    link_assinatura = f'{frontend_url}/assinar/{token_encoded}'
    
    # Obter dados da loja
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=assinatura.loja_id).first()
    loja_nome = loja.nome if loja else 'Sistema'
    
    tipo_doc = 'Proposta' if documento.__class__.__name__ == 'Proposta' else 'Contrato'
    lead = documento.oportunidade.lead
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    
    # Template HTML profissional
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Assinatura Digital - {tipo_doc}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                    ✅ Cliente Assinou!
                                </h1>
                                <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                    Sua assinatura é necessária para finalizar
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá <strong>{assinatura.nome_assinante}</strong>,
                                </p>
                                
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Ótimas notícias! O cliente <strong>{lead.nome}</strong> assinou o(a) {tipo_doc.lower()}. 
                                    Agora é sua vez de assinar digitalmente para finalizar o processo.
                                </p>
                                
                                <!-- Document Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Título:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 16px; font-weight: 600; padding-bottom: 15px;">
                                                        {documento.titulo}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Cliente:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 15px; padding-bottom: 15px;">
                                                        {lead.nome}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Valor Total:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #10b981; font-size: 20px; font-weight: 700;">
                                                        R$ {documento.valor_total or "0,00"}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <a href="{link_assinatura}" style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">
                                                ✍️ Visualizar e Assinar Documento
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff3cd; border-radius: 4px; margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #856404; font-size: 13px; margin: 0; line-height: 1.5;">
                                                ⏰ <strong>Atenção:</strong> Este link é válido por <strong>{TOKEN_EXPIRACAO_DIAS} dias</strong>. Após sua assinatura, o documento será enviado automaticamente para ambas as partes.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Após sua assinatura, o documento finalizado será enviado automaticamente para você e para o cliente.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; text-align: center; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 15px; font-weight: 600; margin: 0 0 10px 0;">
                                    {loja_nome}
                                </p>
                                <p style="color: #666666; font-size: 13px; margin: 0; line-height: 1.5;">
                                    Este é um email automático. Por favor, não responda.
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer Text -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="color: #999999; font-size: 12px; margin: 0;">
                                    © {timezone.now().year} {loja_nome}. Todos os direitos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Texto plano como fallback
    texto_plano = f"""
Olá {assinatura.nome_assinante},

✅ CLIENTE ASSINOU!

O cliente {lead.nome} assinou o(a) {tipo_doc.lower()}.
Agora é sua vez de assinar digitalmente para finalizar o processo.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Cliente: {lead.nome}
Valor Total: R$ {documento.valor_total or "0,00"}

ASSINAR DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Clique no link abaixo para visualizar e assinar:
{link_assinatura}

⏰ ATENÇÃO: Este link é válido por {TOKEN_EXPIRACAO_DIAS} dias.

Após sua assinatura, o documento finalizado será enviado automaticamente 
para você e para o cliente.

Atenciosamente,
{loja_nome}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Este é um email automático. Por favor, não responda.
© {timezone.now().year} {loja_nome}. Todos os direitos reservados.
    """
    
    try:
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=f'✅ Cliente Assinou - {tipo_doc}: {documento.titulo}',
            body=texto_plano,
            from_email=from_email,
            to=[assinatura.email_assinante],
        )
        
        email.attach_alternative(html_content, "text/html")
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
    
    # Template HTML profissional
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{tipo_doc} Assinado</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                    🎉 Documento Assinado!
                                </h1>
                                <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                    Processo de assinatura concluído com sucesso
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá,
                                </p>
                                
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Temos o prazer de informar que o(a) <strong>{tipo_doc.lower()}</strong> foi assinado digitalmente por ambas as partes. 
                                    O documento está anexado a este email.
                                </p>
                                
                                <!-- Success Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f0fdf4; border-left: 4px solid #10b981; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Título:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 16px; font-weight: 600; padding-bottom: 15px;">
                                                        {documento.titulo}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Cliente:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 15px; padding-bottom: 15px;">
                                                        {lead.nome}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 8px;">
                                                        <strong>Valor Total:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #10b981; font-size: 20px; font-weight: 700;">
                                                        R$ {documento.valor_total or "0,00"}
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Info Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #dbeafe; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #1e40af; font-size: 13px; margin: 0; line-height: 1.5;">
                                                📎 <strong>Documento em Anexo:</strong> O PDF assinado digitalmente está anexado a este email. 
                                                Guarde-o em local seguro para referência futura.
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Este documento possui validade jurídica e contém as assinaturas digitais de ambas as partes, 
                                    com registro de data, hora e endereço IP.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; text-align: center; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 15px; font-weight: 600; margin: 0 0 10px 0;">
                                    {loja_nome}
                                </p>
                                <p style="color: #666666; font-size: 13px; margin: 0; line-height: 1.5;">
                                    Obrigado por utilizar nossos serviços!
                                </p>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Footer Text -->
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="color: #999999; font-size: 12px; margin: 0;">
                                    © {timezone.now().year} {loja_nome}. Todos os direitos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Texto plano como fallback
    texto_plano = f"""
🎉 DOCUMENTO ASSINADO COM SUCESSO!

O(A) {tipo_doc.lower()} foi assinado digitalmente por ambas as partes.

DETALHES DO DOCUMENTO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Título: {documento.titulo}
Cliente: {lead.nome}
Valor Total: R$ {documento.valor_total or "0,00"}

DOCUMENTO EM ANEXO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O PDF assinado digitalmente está anexado a este email.
Guarde-o em local seguro para referência futura.

Este documento possui validade jurídica e contém as assinaturas digitais 
de ambas as partes, com registro de data, hora e endereço IP.

Atenciosamente,
{loja_nome}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Obrigado por utilizar nossos serviços!
© {timezone.now().year} {loja_nome}. Todos os direitos reservados.
    """
    
    try:
        from django.core.mail import EmailMultiAlternatives
        
        email = EmailMultiAlternatives(
            subject=f'🎉 {tipo_doc} Assinado: {documento.titulo}',
            body=texto_plano,
            from_email=from_email,
            to=destinatarios,
        )
        
        email.attach_alternative(html_content, "text/html")
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
