"""Templates HTML profissionais para emails do sistema.
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
    nome_sistema: str = "LWK Sistemas",
) -> tuple[str, str]:
    """Gera email HTML profissional para envio de senha provisória.

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
                                                        <strong>Entre com o usuário:</strong>
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

Entre com o usuário: {usuario}
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


def email_boleto_assinatura_html(
    *,
    nome_loja: str,
    valor: str,
    vencimento: str,
    url_boleto: str,
    pix_copia_cola: str = "",
    avisar_senha: bool = False,
    nome_sistema: str = "LWK Sistemas",
) -> tuple[str, str]:
    """E-mail do boleto da assinatura. O PDF vai anexo; o link fica só de reserva."""
    import html

    loja = html.escape(nome_loja or "sua loja")
    valor_html = html.escape(valor or "—")
    vencimento_html = html.escape(vencimento or "—")
    url = (url_boleto or "").strip()
    url_html = html.escape(url, quote=True)
    pix = (pix_copia_cola or "").strip()
    pix_html = html.escape(pix)

    aviso_senha_html = ""
    aviso_senha_texto = ""
    if avisar_senha:
        aviso_senha_html = """
                                <p style="color: #555555; font-size: 14px; line-height: 1.6; margin: 24px 0 0 0;">
                                    A senha de acesso é enviada para este e-mail depois que o pagamento for confirmado.
                                </p>
        """
        aviso_senha_texto = (
            "\nA senha de acesso é enviada para este e-mail depois que o pagamento for confirmado.\n"
        )

    pix_bloco_html = ""
    pix_bloco_texto = ""
    if pix:
        pix_bloco_html = f"""
                                <p style="color: #666666; font-size: 13px; margin: 24px 0 8px 0;">
                                    PIX copia e cola
                                </p>
                                <p style="color: #333333; font-size: 13px; line-height: 1.5; font-family: 'Courier New', monospace; background-color: #f8f9fa; padding: 12px; border-radius: 4px; word-break: break-all; margin: 0;">
                                    {pix_html}
                                </p>
        """
        pix_bloco_texto = f"\nPIX copia e cola:\n{pix}\n"

    link_html = ""
    link_texto = ""
    if url:
        link_html = f"""
                                <p style="color: #888888; font-size: 13px; line-height: 1.5; margin: 24px 0 0 0;">
                                    Se o anexo não aparecer, o mesmo boleto está neste link:<br>
                                    <a href="{url_html}" style="color: #667eea; word-break: break-all;">{url_html}</a>
                                </p>
        """
        link_texto = f"\nSe o anexo não aparecer, use este link:\n{url}\n"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Boleto da assinatura</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px 0;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px;">
                        <tr>
                            <td bgcolor="#667eea" style="background-color: #667eea; padding: 32px 30px; border-radius: 8px 8px 0 0;">
                                <p style="color: #ffffff; margin: 0; font-size: 13px; letter-spacing: 0.4px;">LWK SISTEMAS</p>
                                <h1 style="color: #ffffff; margin: 8px 0 0 0; font-size: 24px; font-weight: 600;">Boleto da assinatura</h1>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 32px 30px;">
                                <p style="color: #333333; font-size: 16px; line-height: 1.6; margin: 0 0 16px 0;">
                                    Olá,
                                </p>
                                <p style="color: #555555; font-size: 15px; line-height: 1.6; margin: 0 0 24px 0;">
                                    O boleto da loja <strong>{loja}</strong> está em anexo neste e-mail, em PDF.
                                    Abra o arquivo para pagar pelo código de barras ou pelo PIX impresso no boleto.
                                </p>
                                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8f9fa; border-left: 4px solid #667eea; border-radius: 4px;">
                                    <tr>
                                        <td style="padding: 16px 20px; color: #666666; font-size: 13px;">Valor</td>
                                        <td style="padding: 16px 20px; color: #333333; font-size: 16px; font-weight: 600;" align="right">{valor_html}</td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 0 20px 16px 20px; color: #666666; font-size: 13px;">Vencimento</td>
                                        <td style="padding: 0 20px 16px 20px; color: #333333; font-size: 16px; font-weight: 600;" align="right">{vencimento_html}</td>
                                    </tr>
                                </table>
                                {pix_bloco_html}
                                {aviso_senha_html}
                                {link_html}
                            </td>
                        </tr>
                        <tr>
                            <td style="background-color: #f8f9fa; padding: 24px 30px; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                                <p style="color: #333333; font-size: 14px; font-weight: 600; margin: 0 0 6px 0;">{html.escape(nome_sistema)}</p>
                                <p style="color: #666666; font-size: 13px; margin: 0;">suporte@lwksistemas.com.br</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    texto = (
        f"Olá,\n\n"
        f"O boleto da loja {nome_loja or 'sua loja'} está em anexo neste e-mail, em PDF.\n"
        f"Abra o arquivo para pagar pelo código de barras ou pelo PIX impresso no boleto.\n\n"
        f"Valor: {valor or '—'}\n"
        f"Vencimento: {vencimento or '—'}\n"
        f"{pix_bloco_texto}"
        f"{aviso_senha_texto}"
        f"{link_texto}\n"
        f"Atenciosamente,\n{nome_sistema}\n"
        f"suporte@lwksistemas.com.br\n"
    )
    return html_content, texto
