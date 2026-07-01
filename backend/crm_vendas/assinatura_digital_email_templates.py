"""
Templates HTML/texto para e-mails de assinatura digital (CRM).
"""
from django.utils import timezone

from .assinatura_digital_token import TOKEN_EXPIRACAO_DIAS


def montar_email_cliente_assinatura(*, lead, documento, loja_nome, link_assinatura, tipo_doc):
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
    return html_content, texto_plano


def montar_email_vendedor_assinatura(*, assinatura, lead, documento, loja_nome, link_assinatura, tipo_doc):
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
    return html_content, texto_plano


def montar_email_pdf_final(*, documento, lead, loja_nome, tipo_doc):
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
    return html_content, texto_plano
