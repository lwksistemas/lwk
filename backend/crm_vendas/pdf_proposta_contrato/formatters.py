"""Formatação e utilitários para PDF de proposta/contrato."""
import logging
import re

import pytz

logger = logging.getLogger(__name__)

def _formatar_timestamp_local(assinado_em):
    """Converte timestamp UTC para timezone local (Brasil)."""
    tz_brasil = pytz.timezone('America/Sao_Paulo')
    return assinado_em.astimezone(tz_brasil).strftime('%d/%m/%Y %H:%M:%S')


def _formatar_valor(valor):
    """Formata valor monetário para exibição."""
    if valor is None:
        return '—'
    try:
        v = float(valor)
        return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (TypeError, ValueError):
        return '—'


def _title_case_endereco(texto: str) -> str:
    """Normaliza capitalização de endereço: se tudo maiúsculo, converte para Title Case."""
    if not texto or texto == '—':
        return texto
    # Se mais de 60% das letras são maiúsculas, converter para title case
    letras = [c for c in texto if c.isalpha()]
    if letras and sum(1 for c in letras if c.isupper()) / len(letras) > 0.6:
        # Preservar siglas de estado (SP, PR, RJ, etc.) e CEP
        import re
        def _title_part(part):
            part = part.strip()
            if re.match(r'^[A-Z]{2}$', part):  # UF
                return part
            if re.match(r'^CEP\s', part, re.I):  # CEP XXXXX
                return part
            if re.match(r'^nº\s', part, re.I):  # nº 123
                return part
            return part.title()
        return ', '.join(_title_part(p) for p in texto.split(','))
    return texto


def _formatar_endereco_lead(lead):
    """Monta string de endereço do lead."""
    if not lead:
        return '—'
    parts = [
        getattr(lead, 'logradouro', '') or '',
        f"nº {lead.numero}" if getattr(lead, 'numero', '') else '',
        getattr(lead, 'complemento', '') or '',
        getattr(lead, 'bairro', '') or '',
        (f"{lead.cidade}/{lead.uf}" if (getattr(lead, 'cidade', '') and getattr(lead, 'uf', ''))
         else (getattr(lead, 'cidade', '') or getattr(lead, 'uf', ''))),
        f"CEP {lead.cep}" if getattr(lead, 'cep', '') else '',
    ]
    raw = ', '.join(p for p in parts if p).strip() or '—'
    return _title_case_endereco(raw)


def _formatar_nome_usuario(user):
    """Tenta montar um nome legível para o usuário (vendedor)."""
    if not user:
        return '—'
    first = getattr(user, 'first_name', '') or ''
    last = getattr(user, 'last_name', '') or ''
    full = f'{first} {last}'.strip()
    return full or getattr(user, 'nome', '') or getattr(user, 'username', '') or '—'


def _html_to_paragraphs(html):
    """Converte HTML/texto do conteúdo em lista de parágrafos para o PDF."""
    if not html:
        return ['Conteúdo não informado.']
    text = str(html)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(?:p|div|li|h[1-6])>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'<li[^>]*>', '• ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    lines = text.split('\n')
    paragraphs = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            paragraphs.append(stripped)
        elif paragraphs:
            paragraphs.append('')
    return paragraphs if paragraphs else ['Conteúdo não informado.']


def _obter_dados_loja(loja_id):
    """Obtém dados da loja do superadmin (nome, endereço, CPF/CNPJ, admin, logo, telefone)."""
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
        if not loja:
            return {}
        cidade = getattr(loja, 'cidade', '') or ''
        uf = getattr(loja, 'uf', '') or ''
        cidade_uf = f"{cidade}/{uf}" if (cidade and uf) else (cidade or uf)
        endereco_parts = [
            getattr(loja, 'logradouro', '') or '',
            getattr(loja, 'numero', '') or '',
            getattr(loja, 'complemento', '') or '',
            getattr(loja, 'bairro', '') or '',
            cidade_uf,
            f"CEP {loja.cep}" if getattr(loja, 'cep', '') else '',
        ]
        endereco = ', '.join(p for p in endereco_parts if p).strip() or None
        owner = getattr(loja, 'owner', None)
        admin_nome = None
        admin_email = None
        if owner:
            admin_nome = f"{getattr(owner, 'first_name', '') or ''} {getattr(owner, 'last_name', '') or ''}".strip() or getattr(owner, 'username', '') or None
            admin_email = getattr(owner, 'email', None) or None
        telefone = getattr(loja, 'owner_telefone', '') or getattr(loja, 'telefone', '') or ''
        return {
            'nome': getattr(loja, 'nome', '') or '',
            'endereco': endereco,
            'cpf_cnpj': getattr(loja, 'cpf_cnpj', '') or None,
            'telefone': telefone.strip() or None,
            'admin_nome': admin_nome,
            'admin_email': admin_email,
            'logo': getattr(loja, 'logo', '') or None,
        }
    except Exception:
        return {}
