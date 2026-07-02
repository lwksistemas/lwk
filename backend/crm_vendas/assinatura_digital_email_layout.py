"""Fragmentos HTML compartilhados entre templates de e-mail de assinatura."""
from django.utils import timezone

from .assinatura_digital_token import TOKEN_EXPIRACAO_DIAS

__all__ = [
    'TOKEN_EXPIRACAO_DIAS',
    'ano_corrente',
    'rodape_html_tabela',
    'rodape_texto_padrao',
]


def ano_corrente() -> int:
    return timezone.now().year


def rodape_html_tabela(loja_nome: str) -> str:
    year = ano_corrente()
    return f"""
                    <table width="600" cellpadding="0" cellspacing="0" style="margin-top: 20px;">
                        <tr>
                            <td align="center">
                                <p style="color: #999999; font-size: 12px; margin: 0;">
                                    © {year} {loja_nome}. Todos os direitos reservados.
                                </p>
                            </td>
                        </tr>
                    </table>"""


def rodape_texto_padrao(loja_nome: str, *, tagline: str = 'Este é um email automático. Por favor, não responda.') -> str:
    year = ano_corrente()
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tagline}
© {year} {loja_nome}. Todos os direitos reservados."""
