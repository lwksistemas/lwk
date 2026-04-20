"""
Templates HTML profissionais para emails do sistema.
"""
from datetime import datetime


def email_senha_provisoria_html(
    nome_destinatario: str,
    usuario: str,
    senha: str,
    url_login: str,
    titulo_principal: str,
    subtitulo: str,
    info_adicional: dict,
    nome_sistema: str = "LWK Sistemas"
) -> tuple[str, str]:
    """
    Gera email HTML profissional para envio de senha provisória.
    
    Args:
        nome_destinatario: Nome da pessoa que receberá o email
        usuario: Nome de usuário para login
        senha: Senha provisória
        url_login: URL completa para fazer login
        titulo_principal: Título do email (ex: "Bem-vindo ao Sistema")
        subtitulo: Subtítulo explicativo
        info_adicional: Dict com informações adicionais (ex: {"Loja": "Nome da Loja", "Plano": "Premium"})
        nome_sistema: Nome do sistema/loja
    
    Returns:
        tuple: (html_content, texto_plano)
    """
    
    # Construir linhas de informações adicionais
    info_lines_html = ""
    info_lines_text = ""
    
    for chave, valor in info_adicional.items():
        info_lines_html += f"""
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 5px;">
                                                        <strong>{chave}:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 15px; padding-bottom: 12px;">
                                                        {valor}
                                                    </td>
                                                </tr>
        """
        info_lines_text += f"{chave}: {valor}\n"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{titulo_principal}</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <!-- Header (Outlook-compatible: bgcolor + background-color sólido) -->
                        <tr>
                            <td bgcolor="#667eea" style="background-color: #667eea; background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; border-radius: 8px 8px 0 0; text-align: center;">
                                <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                    🔐 {titulo_principal}
                                </h1>
                                <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                    {subtitulo}
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Body -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Olá <strong>{nome_destinatario}</strong>,
                                </p>
                                
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Seus dados de acesso ao sistema foram gerados com sucesso!
                                </p>
                                
                                <!-- Credentials Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 5px;">
                                                        <strong>👤 Usuário:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 16px; font-weight: 600; padding-bottom: 15px;">
                                                        {usuario}
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #666666; font-size: 13px; padding-bottom: 5px;">
                                                        <strong>🔑 Senha Provisória:</strong>
                                                    </td>
                                                </tr>
                                                <tr>
                                                    <td style="color: #333333; font-size: 18px; font-weight: 700; font-family: 'Courier New', monospace; background-color: #ffffff; padding: 12px; border-radius: 4px; margin-bottom: 15px; display: inline-block;">
                                                        {senha}
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
                                            <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{url_login}" style="height:52px;v-text-anchor:middle;width:280px;" arcsize="12%" strokecolor="#667eea" fillcolor="#667eea">
                                                <w:anchorlock/>
                                                <center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#128640; Acessar Sistema</center>
                                            </v:roundrect>
                                            <![endif]-->
                                            <!--[if !mso]><!-- -->
                                            <a href="{url_login}" style="display: inline-block; background-color: #667eea; background-image: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff !important; text-decoration: none; padding: 16px 40px; border-radius: 6px; font-size: 16px; font-weight: 600; mso-hide: all;">
                                                🚀 Acessar Sistema
                                            </a>
                                            <!--<![endif]-->
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Warning Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff3cd; border-radius: 4px; margin-bottom: 30px;">
                                    <tr>
                                        <td style="padding: 15px;">
                                            <p style="color: #856404; font-size: 13px; margin: 0 0 8px 0; font-weight: 600;">
                                                ⚠️ IMPORTANTE - SEGURANÇA
                                            </p>
                                            <p style="color: #856404; font-size: 13px; margin: 0; line-height: 1.5;">
                                                • Esta é uma senha provisória gerada automaticamente<br>
                                                • Recomendamos <strong>ALTERAR A SENHA</strong> no primeiro acesso<br>
                                                • Mantenha seus dados de acesso em segurança<br>
                                                • Nunca compartilhe sua senha com terceiros
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Additional Info -->
                                {f'''
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #e7f3ff; border-left: 4px solid #2196F3; border-radius: 4px; margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 20px;">
                                            <p style="color: #0d47a1; font-size: 14px; margin: 0 0 12px 0; font-weight: 600;">
                                                📋 INFORMAÇÕES
                                            </p>
                                            <table width="100%" cellpadding="0" cellspacing="0">
                                                {info_lines_html}
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                ''' if info_adicional else ''}
                                
                                <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 0;">
                                    Se você tiver alguma dúvida, entre em contato com nosso suporte.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; text-align: center; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 15px; font-weight: 600; margin: 0 0 10px 0;">
                                    {nome_sistema}
                                </p>
                                <p style="color: #666666; font-size: 13px; margin: 0 0 10px 0;">
                                    📧 suporte@lwksistemas.com.br | 📱 WhatsApp: (11) 99999-9999
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
                                    © {datetime.now().year} {nome_sistema}. Todos os direitos reservados.
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
═══════════════════════════════════════════════════════════════
                    {titulo_principal}
═══════════════════════════════════════════════════════════════

Olá {nome_destinatario},

{subtitulo}

═══════════════════════════════════════════════════════════════
                    🔐 DADOS DE ACESSO
═══════════════════════════════════════════════════════════════

👤 Usuário: {usuario}
🔑 Senha Provisória: {senha}

🚀 ACESSAR SISTEMA:
{url_login}

═══════════════════════════════════════════════════════════════
                    ⚠️ IMPORTANTE - SEGURANÇA
═══════════════════════════════════════════════════════════════

• Esta é uma senha provisória gerada automaticamente
• Recomendamos ALTERAR A SENHA no primeiro acesso
• Mantenha seus dados de acesso em segurança
• Nunca compartilhe sua senha com terceiros

{f'''═══════════════════════════════════════════════════════════════
                    📋 INFORMAÇÕES
═══════════════════════════════════════════════════════════════

{info_lines_text}''' if info_adicional else ''}

═══════════════════════════════════════════════════════════════
                    📞 SUPORTE
═══════════════════════════════════════════════════════════════

Em caso de dúvidas ou problemas, entre em contato:
• Email: suporte@lwksistemas.com.br
• WhatsApp: (11) 99999-9999

═══════════════════════════════════════════════════════════════

Atenciosamente,
{nome_sistema}
https://lwksistemas.com.br

Este é um email automático. Por favor, não responda.
© {datetime.now().year} {nome_sistema}. Todos os direitos reservados.

═══════════════════════════════════════════════════════════════
    """
    
    return html_content, texto_plano
