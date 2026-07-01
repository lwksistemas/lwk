"""
Funções de envio de e-mail para Assinatura Digital de Propostas e Contratos.
Contém templates HTML e lógica de envio para cliente, vendedor e PDF final.
"""
from django.utils import timezone
from django.conf import settings
from urllib.parse import quote
import logging

from .assinatura_digital_token import TOKEN_EXPIRACAO_DIAS

logger = logging.getLogger(__name__)


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
                        <!-- Header (Outlook-compatible: bgcolor + background-color sólido, gradient como enhancement) -->
                        <tr>
                            <td bgcolor="#667eea" style="background-color: #667eea; background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
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
                                
                                <!-- CTA Button (bulletproof Outlook-compatible) -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <!--[if mso]>
                                            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link_assinatura}" style="height:52px;v-text-anchor:middle;width:340px;" arcsize="12%" strokecolor="#667eea" fillcolor="#667eea">
                                                <w:anchorlock/>
                                                <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#9997; Visualizar e Assinar Documento</center>
                                            </v:roundrect>
                                            <![endif]-->
                                            <!--[if !mso]><!-- -->
                                            <a href="{link_assinatura}" style="display: inline-block; background-color: #667eea; background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff !important; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; mso-hide: all;">
                                                ✍️ Visualizar e Assinar Documento
                                            </a>
                                            <!--<![endif]-->
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
        from core.email_delivery import create_email_multipart

        email = create_email_multipart(
            subject=f'📄 Assinatura Digital - {tipo_doc}: {documento.titulo}',
            body=texto_plano,
            to=[lead.email],
            html=html_content,
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
    if not (assinatura.email_assinante or '').strip():
        documento = assinatura.documento
        if documento:
            oportunidade = getattr(documento, 'oportunidade', None)
            vendedor = getattr(oportunidade, 'vendedor', None) if oportunidade else None
            email_doc = (getattr(vendedor, 'email', None) or '').strip()
            if email_doc:
                assinatura.email_assinante = email_doc
    if not (assinatura.email_assinante or '').strip():
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
                        <!-- Header (Outlook-compatible: bgcolor + background-color sólido, gradient como enhancement) -->
                        <tr>
                            <td bgcolor="#10b981" style="background-color: #10b981; background-image: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
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
                                
                                <!-- CTA Button (bulletproof Outlook-compatible) -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <!--[if mso]>
                                            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link_assinatura}" style="height:52px;v-text-anchor:middle;width:340px;" arcsize="12%" strokecolor="#10b981" fillcolor="#10b981">
                                                <w:anchorlock/>
                                                <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#9997; Visualizar e Assinar Documento</center>
                                            </v:roundrect>
                                            <![endif]-->
                                            <!--[if !mso]><!-- -->
                                            <a href="{link_assinatura}" style="display: inline-block; background-color: #10b981; background-image: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #ffffff !important; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; mso-hide: all;">
                                                ✍️ Visualizar e Assinar Documento
                                            </a>
                                            <!--<![endif]-->
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
        from core.email_delivery import create_email_multipart

        email = create_email_multipart(
            subject=f'✅ Cliente Assinou - {tipo_doc}: {documento.titulo}',
            body=texto_plano,
            to=[assinatura.email_assinante],
            html=html_content,
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
                        <!-- Header (Outlook-compatible: bgcolor + background-color sólido, gradient como enhancement) -->
                        <tr>
                            <td bgcolor="#10b981" style="background-color: #10b981; background-image: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
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
        from core.email_delivery import create_email_multipart

        email = create_email_multipart(
            subject=f'🎉 {tipo_doc} Assinado: {documento.titulo}',
            body=texto_plano,
            to=destinatarios,
            html=html_content,
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
