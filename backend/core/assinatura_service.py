"""
Serviço genérico de Assinatura Digital.
Reutilizável por qualquer módulo (CRM, Hotel, etc.).

Cada módulo fornece um "adapter" que implementa a interface AssinaturaAdapter
para extrair dados específicos do documento (título, valor, destinatários, PDF).
"""
import logging
from datetime import timedelta
from urllib.parse import quote, unquote

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.signing import dumps, loads, BadSignature
from django.utils import timezone

logger = logging.getLogger(__name__)

TOKEN_EXPIRACAO_DIAS = 7


# ---------------------------------------------------------------------------
# Utilitários de token
# ---------------------------------------------------------------------------

def normalizar_token_url(token: str) -> str:
    """Normaliza token vindo da URL (desfaz encoding duplicado)."""
    if not token:
        return ''
    t = str(token).strip()
    for _ in range(4):
        if '%' not in t:
            break
        prev = t
        t = unquote(t)
        if t == prev:
            break
    return t


def gerar_token(doc_type: str, doc_id: int, tipo: str, loja_id: int, modulo: str = 'crm') -> str:
    """Gera token assinado com payload."""
    payload = {
        'doc_type': doc_type,
        'doc_id': doc_id,
        'tipo': tipo,
        'loja_id': loja_id,
        'modulo': modulo,
        'exp': int((timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS)).timestamp()),
    }
    return dumps(payload)


def decodificar_token(token: str) -> dict | None:
    """Decodifica token e retorna payload ou None."""
    token = normalizar_token_url(token)
    if not token:
        return None
    try:
        return loads(token)
    except (BadSignature, Exception):
        return None


# ---------------------------------------------------------------------------
# Adapter interface (cada módulo implementa)
# ---------------------------------------------------------------------------

class AssinaturaAdapter:
    """
    Interface que cada módulo implementa para fornecer dados específicos.
    Métodos devem ser sobrescritos.
    """

    def get_titulo(self, documento) -> str:
        raise NotImplementedError

    def get_valor_display(self, documento) -> str:
        raise NotImplementedError

    def get_destinatario_parte1(self, documento) -> tuple[str, str]:
        """Retorna (nome, email) da primeira parte (cliente/hóspede)."""
        raise NotImplementedError

    def get_destinatario_parte2(self, documento, loja_id: int) -> tuple[str, str]:
        """Retorna (nome, email) da segunda parte (vendedor/funcionário)."""
        raise NotImplementedError

    def get_tipo_documento_label(self, documento) -> str:
        """Ex: 'Proposta', 'Contrato', 'Confirmação de Reserva'."""
        raise NotImplementedError

    def get_info_extra_email(self, documento) -> dict:
        """Dados extras para o template de email (ex: datas, quarto)."""
        return {}

    def criar_registro_assinatura(self, documento, tipo: str, nome: str, email: str, token: str, loja_id: int):
        """Cria o registro de assinatura no banco (modelo específico do módulo)."""
        raise NotImplementedError

    def buscar_assinatura_por_token(self, token: str):
        """Busca registro de assinatura pelo token."""
        raise NotImplementedError

    def get_documento_da_assinatura(self, assinatura):
        """Retorna o documento a partir do registro de assinatura."""
        raise NotImplementedError

    def atualizar_status_assinatura(self, documento, novo_status: str):
        """Atualiza status_assinatura do documento."""
        raise NotImplementedError

    def get_status_assinatura(self, documento) -> str:
        """Retorna status_assinatura atual do documento."""
        raise NotImplementedError

    def gerar_pdf(self, documento, incluir_assinaturas: bool = False):
        """Gera PDF do documento. Retorna BytesIO."""
        raise NotImplementedError

    def get_todos_destinatarios_pdf_final(self, documento, loja_id: int) -> list[str]:
        """Retorna lista de emails para envio do PDF final."""
        raise NotImplementedError

    def get_label_parte1(self) -> str:
        """Label da parte 1: 'cliente', 'hospede'."""
        return 'cliente'

    def get_label_parte2(self) -> str:
        """Label da parte 2: 'vendedor', 'funcionario'."""
        return 'vendedor'

    def get_modulo(self) -> str:
        """Identificador do módulo: 'crm', 'hotel'."""
        return 'crm'

    def get_pagina_assinatura_path(self) -> str:
        """Path da página pública de assinatura. Ex: '/assinar/', '/assinar-reserva/'."""
        return '/assinar/'

    def deletar_assinaturas_pendentes(self, documento, tipo: str):
        """Remove assinaturas não assinadas do tipo dado para o documento."""
        raise NotImplementedError

    def on_assinatura_concluida(self, documento, loja_id: int):
        """Hook chamado quando ambas as partes assinaram (ex: mudar status da reserva)."""
        pass


# ---------------------------------------------------------------------------
# Funções genéricas de workflow
# ---------------------------------------------------------------------------

def _get_loja_nome(loja_id: int) -> str:
    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    return loja.nome if loja else 'Sistema'


def _build_link_assinatura(token: str, path: str) -> str:
    frontend_url = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br')
    token_encoded = quote(token, safe='')
    return f'{frontend_url}{path}{token_encoded}'


def criar_assinatura(adapter: AssinaturaAdapter, documento, tipo: str, loja_id: int):
    """
    Cria token e registro de assinatura.
    Returns: registro de assinatura criado.
    """
    if tipo == adapter.get_label_parte1():
        nome, email = adapter.get_destinatario_parte1(documento)
    else:
        nome, email = adapter.get_destinatario_parte2(documento, loja_id)

    doc_type = documento.__class__.__name__.lower()
    token = gerar_token(doc_type, documento.id, tipo, loja_id, modulo=adapter.get_modulo())

    assinatura = adapter.criar_registro_assinatura(
        documento, tipo, nome, email, token, loja_id,
    )
    logger.info(f'✅ Assinatura criada: tipo={tipo}, doc={doc_type}#{documento.id}, assinante={nome}')
    return assinatura


def registrar_assinatura(adapter: AssinaturaAdapter, assinatura, ip_address: str, user_agent: str = '') -> str:
    """
    Registra a assinatura (marca como assinado).
    Returns: próximo status ('aguardando_parte2' ou 'concluido').
    """
    assinatura.assinado = True
    assinatura.assinado_em = timezone.now()
    assinatura.ip_address = ip_address
    assinatura.user_agent = (user_agent or '')[:500]
    assinatura.save()

    documento = adapter.get_documento_da_assinatura(assinatura)
    label1 = adapter.get_label_parte1()
    label2 = adapter.get_label_parte2()

    if assinatura.tipo == label1:
        status_map = {
            'cliente': 'aguardando_vendedor',
            'hospede': 'aguardando_funcionario',
        }
        novo_status = status_map.get(label1, f'aguardando_{label2}')
        adapter.atualizar_status_assinatura(documento, novo_status)
        return novo_status
    else:
        adapter.atualizar_status_assinatura(documento, 'concluido')
        adapter.on_assinatura_concluida(documento, assinatura.loja_id)
        return 'concluido'


# ---------------------------------------------------------------------------
# Emails genéricos
# ---------------------------------------------------------------------------

def _render_email_html(titulo_header: str, cor_gradient: str, corpo_html: str, loja_nome: str) -> str:
    ano = timezone.now().year
    cor_solida = cor_gradient.split(' ')[0].strip()
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;background:#f4f4f4;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:20px 0;"><tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1);">
<tr><td bgcolor="{cor_solida}" style="background-color:{cor_solida};background-image:linear-gradient(135deg,{cor_gradient});padding:40px 30px;border-radius:8px 8px 0 0;text-align:center;">
<h1 style="color:#fff;margin:0;font-size:28px;font-weight:600;">{titulo_header}</h1>
</td></tr>
<tr><td style="padding:40px 30px;">{corpo_html}</td></tr>
<tr><td style="background:#f8f9fa;padding:30px;border-radius:0 0 8px 8px;text-align:center;border-top:1px solid #e9ecef;">
<p style="color:#333;font-size:15px;font-weight:600;margin:0 0 10px 0;">{loja_nome}</p>
<p style="color:#666;font-size:13px;margin:0;">Email automático. Não responda.</p>
</td></tr></table>
<table width="600" style="margin-top:20px;"><tr><td align="center">
<p style="color:#999;font-size:12px;margin:0;">© {ano} {loja_nome}</p>
</td></tr></table>
</td></tr></table></body></html>"""


def enviar_email_parte1(adapter: AssinaturaAdapter, documento, assinatura, loja_id: int) -> tuple[bool, str | None]:
    """Envia email para a primeira parte (cliente/hóspede) com link de assinatura."""
    nome, email = adapter.get_destinatario_parte1(documento)
    if not email:
        return False, f'{adapter.get_label_parte1().title()} não possui email cadastrado.'

    loja_nome = _get_loja_nome(loja_id)
    link = _build_link_assinatura(assinatura.token, adapter.get_pagina_assinatura_path())
    tipo_doc = adapter.get_tipo_documento_label(documento)
    titulo = adapter.get_titulo(documento)
    valor = adapter.get_valor_display(documento)
    info = adapter.get_info_extra_email(documento)

    info_extra_html = ''
    for label, val in info.items():
        info_extra_html += f'<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>{label}:</strong></td></tr><tr><td style="color:#333;font-size:15px;padding-bottom:12px;">{val}</td></tr>'

    corpo = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 20px;">Olá <strong>{nome}</strong>,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 30px;">Você recebeu um(a) <strong>{tipo_doc.lower()}</strong> de <strong>{loja_nome}</strong> para assinatura digital.</p>
<table width="100%" style="background:#f8f9fa;border-left:4px solid #667eea;border-radius:4px;margin-bottom:30px;"><tr><td style="padding:20px;">
<table width="100%">
<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>Título:</strong></td></tr>
<tr><td style="color:#333;font-size:16px;font-weight:600;padding-bottom:12px;">{titulo}</td></tr>
{info_extra_html}
<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>Valor:</strong></td></tr>
<tr><td style="color:#10b981;font-size:20px;font-weight:700;">{valor}</td></tr>
</table></td></tr></table>
<table width="100%" style="margin-bottom:30px;"><tr><td align="center">
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link}" style="height:52px;v-text-anchor:middle;width:300px;" arcsize="12%" strokecolor="#667eea" fillcolor="#667eea">
<w:anchorlock/><center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#9997; Visualizar e Assinar</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
<a href="{link}" style="display:inline-block;background-color:#667eea;background-image:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#ffffff !important;text-decoration:none;padding:16px 40px;border-radius:6px;font-size:16px;font-weight:600;mso-hide:all;">✍️ Visualizar e Assinar</a>
<!--<![endif]-->
</td></tr></table>
<table width="100%" style="background:#fff3cd;border-radius:4px;margin-bottom:20px;"><tr><td style="padding:15px;">
<p style="color:#856404;font-size:13px;margin:0;">⏰ Link válido por <strong>{TOKEN_EXPIRACAO_DIAS} dias</strong>.</p>
</td></tr></table>"""

    html = _render_email_html(f'📄 Assinatura Digital', '#667eea 0%, #764ba2 100%', corpo, loja_nome)
    subject = f'📄 Assinatura Digital - {tipo_doc}: {titulo}'

    return _enviar_email(subject, html, f'Assinatura digital: {titulo}', email, loja_nome)


def enviar_email_parte2(adapter: AssinaturaAdapter, documento, assinatura, loja_id: int) -> tuple[bool, str | None]:
    """Envia email para a segunda parte (vendedor/funcionário) após parte 1 assinar."""
    if not assinatura.email_assinante:
        return False, f'{adapter.get_label_parte2().title()} não possui email cadastrado.'

    nome_parte1, _ = adapter.get_destinatario_parte1(documento)
    loja_nome = _get_loja_nome(loja_id)
    link = _build_link_assinatura(assinatura.token, adapter.get_pagina_assinatura_path())
    tipo_doc = adapter.get_tipo_documento_label(documento)
    titulo = adapter.get_titulo(documento)
    valor = adapter.get_valor_display(documento)
    label1 = adapter.get_label_parte1().title()

    corpo = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 20px;">Olá <strong>{assinatura.nome_assinante}</strong>,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 30px;">O(a) {label1.lower()} <strong>{nome_parte1}</strong> assinou o(a) {tipo_doc.lower()}. Agora é sua vez.</p>
<table width="100%" style="background:#f0fdf4;border-left:4px solid #10b981;border-radius:4px;margin-bottom:30px;"><tr><td style="padding:20px;">
<table width="100%">
<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>Título:</strong></td></tr>
<tr><td style="color:#333;font-size:16px;font-weight:600;padding-bottom:12px;">{titulo}</td></tr>
<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>{label1}:</strong></td></tr>
<tr><td style="color:#333;font-size:15px;padding-bottom:12px;">{nome_parte1}</td></tr>
<tr><td style="color:#666;font-size:13px;padding-bottom:4px;"><strong>Valor:</strong></td></tr>
<tr><td style="color:#10b981;font-size:20px;font-weight:700;">{valor}</td></tr>
</table></td></tr></table>
<table width="100%" style="margin-bottom:30px;"><tr><td align="center">
<!--[if mso]>
<v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{link}" style="height:52px;v-text-anchor:middle;width:300px;" arcsize="12%" strokecolor="#10b981" fillcolor="#10b981">
<w:anchorlock/><center style="color:#ffffff;font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">&#9997; Visualizar e Assinar</center>
</v:roundrect>
<![endif]-->
<!--[if !mso]><!-- -->
<a href="{link}" style="display:inline-block;background-color:#10b981;background-image:linear-gradient(135deg,#10b981 0%,#059669 100%);color:#ffffff !important;text-decoration:none;padding:16px 40px;border-radius:6px;font-size:16px;font-weight:600;mso-hide:all;">✍️ Visualizar e Assinar</a>
<!--<![endif]-->
</td></tr></table>"""

    html = _render_email_html(f'✅ {label1} Assinou!', '#10b981 0%, #059669 100%', corpo, loja_nome)
    subject = f'✅ {label1} Assinou - {tipo_doc}: {titulo}'

    return _enviar_email(subject, html, f'{label1} assinou: {titulo}', assinatura.email_assinante, loja_nome)


def enviar_pdf_final(adapter: AssinaturaAdapter, documento, loja_id: int) -> tuple[bool, str | None]:
    """Gera PDF com assinaturas e envia para ambas as partes."""
    loja_nome = _get_loja_nome(loja_id)
    tipo_doc = adapter.get_tipo_documento_label(documento)
    titulo = adapter.get_titulo(documento)
    destinatarios = adapter.get_todos_destinatarios_pdf_final(documento, loja_id)

    if not destinatarios:
        return False, 'Nenhum destinatário com email.'

    try:
        pdf_buffer = adapter.gerar_pdf(documento, incluir_assinaturas=True)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()
    except Exception as e:
        logger.exception(f'Erro ao gerar PDF final: {e}')
        return False, f'Erro ao gerar PDF: {e}'

    filename = f'{tipo_doc.lower().replace(" ", "_")}_{titulo or documento.id}_assinado.pdf'

    corpo = f"""
<p style="color:#333;font-size:16px;line-height:1.6;margin:0 0 20px;">Olá,</p>
<p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 30px;">O(a) <strong>{tipo_doc.lower()}</strong> &quot;{titulo}&quot; foi assinado digitalmente por ambas as partes. O documento está anexado.</p>
<table width="100%" style="background:#dbeafe;border-radius:4px;margin-bottom:30px;"><tr><td style="padding:15px;">
<p style="color:#1e40af;font-size:13px;margin:0;">📎 O PDF assinado está anexado. Guarde-o em local seguro.</p>
</td></tr></table>
<p style="color:#666;font-size:14px;">Este documento possui validade jurídica com assinaturas digitais, registro de data, hora e IP.</p>"""

    html = _render_email_html('🎉 Documento Assinado!', '#10b981 0%, #059669 100%', corpo, loja_nome)
    subject = f'🎉 {tipo_doc} Assinado: {titulo}'

    return _enviar_email(subject, html, f'Documento assinado: {titulo}', destinatarios, loja_nome, pdf_bytes, filename)


def _enviar_email(subject, html, texto_fallback, to, loja_nome, pdf_bytes=None, pdf_filename=None) -> tuple[bool, str | None]:
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@lwksistemas.com.br')
    if isinstance(to, str):
        to = [to]
    try:
        email = EmailMultiAlternatives(subject=subject, body=texto_fallback, from_email=from_email, to=to)
        email.attach_alternative(html, 'text/html')
        if pdf_bytes and pdf_filename:
            email.attach(pdf_filename, pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
        logger.info(f'Email enviado: subject="{subject}", to={to}')
        return True, None
    except Exception as e:
        logger.exception(f'Erro ao enviar email: {e}')
        return False, str(e)


# ---------------------------------------------------------------------------
# Reenvio genérico
# ---------------------------------------------------------------------------

def reenviar_link(adapter: AssinaturaAdapter, documento, loja_id: int) -> tuple[bool, str | None, str | None]:
    """
    Reenvia link de assinatura para o passo atual.
    Returns: (sucesso, mensagem_sucesso, erro)
    """
    status_atual = adapter.get_status_assinatura(documento)
    label1 = adapter.get_label_parte1()
    label2 = adapter.get_label_parte2()

    if status_atual == f'aguardando_{label1}':
        _, email = adapter.get_destinatario_parte1(documento)
        if not email:
            return False, None, f'{label1.title()} não possui email.'
        adapter.deletar_assinaturas_pendentes(documento, label1)
        assinatura = criar_assinatura(adapter, documento, label1, loja_id)
        ok, err = enviar_email_parte1(adapter, documento, assinatura, loja_id)
        if ok:
            return True, f'Novo link enviado para {email}', None
        assinatura.delete()
        return False, None, err

    if status_atual == f'aguardando_{label2}':
        adapter.deletar_assinaturas_pendentes(documento, label2)
        assinatura = criar_assinatura(adapter, documento, label2, loja_id)
        ok, err = enviar_email_parte2(adapter, documento, assinatura, loja_id)
        if ok:
            return True, 'Novo link enviado.', None
        assinatura.delete()
        return False, None, err

    return False, None, 'Reenvio só é possível quando aguardando assinatura.'
