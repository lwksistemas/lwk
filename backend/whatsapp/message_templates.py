"""
Templates de mensagem WhatsApp — LWK Sistemas.

Design profissional e seguro para mensagens com links de ação.
Evita aparência de spam/phishing com:
- Identidade visual clara (separadores, ícones consistentes)
- Informações contextuais (loja, tipo de documento, prazo)
- Linha de segurança (verificação LWK)
- Botão de ação em vez de URL nua (quando Evolution disponível)
"""
from __future__ import annotations

SEPARADOR = '━━━━━━━━━━━━━━━━━━━━'
DIAS_EXPIRACAO_PADRAO = 7

# ---------------------------------------------------------------------------
# Templates de assinatura digital (CRM: proposta/contrato; Clínica: termo)
# ---------------------------------------------------------------------------

def msg_assinatura_cliente(
    *,
    nome: str,
    tipo_doc: str,
    titulo: str | None,
    loja_nome: str,
    link: str,
    dias: int = DIAS_EXPIRACAO_PADRAO,
) -> str:
    """
    Mensagem para o CLIENTE assinar proposta, contrato ou termo de consentimento.
    Aparência profissional — evita parecer spam/phishing.
    """
    subtitulo = f'_{titulo}_' if titulo and titulo.strip() else ''
    linhas = [
        f'🔐 *Documento para Assinatura Digital*',
        SEPARADOR,
        f'Olá *{nome}*!',
        '',
        f'*{loja_nome}* enviou um documento que precisa da sua assinatura:',
        '',
        f'📋 *{tipo_doc}*' + (f'\n   {subtitulo}' if subtitulo else ''),
        '',
        f'👇 *Toque no link abaixo para ler e assinar:*',
        link,
        '',
        f'⏳ Válido por {dias} dias',
        f'🔒 Documento verificado por LWK Sistemas',
        SEPARADOR,
        '_Este link é exclusivo para você. Não compartilhe._',
    ]
    return '\n'.join(l for l in linhas)


def msg_assinatura_vendedor(
    *,
    nome: str,
    tipo_doc: str,
    titulo: str | None,
    loja_nome: str,
    link: str,
    nome_cliente: str | None = None,
    dias: int = DIAS_EXPIRACAO_PADRAO,
) -> str:
    """
    Mensagem para o VENDEDOR finalizar assinatura após o cliente já ter assinado.
    """
    subtitulo = f'_{titulo}_' if titulo and titulo.strip() else ''
    cliente_linha = f'👤 *Cliente:* {nome_cliente}' if nome_cliente else ''
    linhas = [
        f'✅ *Assinatura do Cliente Concluída*',
        SEPARADOR,
        f'Olá *{nome}*!',
        '',
        f'O cliente assinou o documento de *{loja_nome}*.',
        f'Agora é a sua vez de finalizar:',
        '',
        f'📋 *{tipo_doc}*' + (f'\n   {subtitulo}' if subtitulo else ''),
    ]
    if cliente_linha:
        linhas.append(cliente_linha)
    linhas.extend([
        '',
        f'👇 *Toque para assinar e concluir:*',
        link,
        '',
        f'⏳ Válido por {dias} dias',
        f'🔒 Documento verificado por LWK Sistemas',
        SEPARADOR,
    ])
    return '\n'.join(l for l in linhas)


def msg_termo_consentimento(
    *,
    nome: str,
    procedimento: str | None,
    loja_nome: str,
    link: str,
    dias: int = DIAS_EXPIRACAO_PADRAO,
) -> str:
    """
    Mensagem para o PACIENTE assinar termo de consentimento (Clínica da Beleza).
    """
    proc_linha = f'💉 *Procedimento:* {procedimento}' if procedimento else ''
    linhas = [
        f'📋 *Termo de Consentimento*',
        SEPARADOR,
        f'Olá *{nome}*!',
        '',
        f'*{loja_nome}* precisa da sua assinatura no',
        f'Termo de Consentimento Livre e Esclarecido (TCLE):',
        '',
    ]
    if proc_linha:
        linhas.append(proc_linha)
        linhas.append('')
    linhas.extend([
        f'👇 *Toque para ler e assinar:*',
        link,
        '',
        f'⏳ Válido por {dias} dias',
        f'🔒 Documento verificado por LWK Sistemas',
        SEPARADOR,
        '_Sua assinatura confirma que foi informado(a) sobre o procedimento._',
    ])
    return '\n'.join(l for l in linhas)


# ---------------------------------------------------------------------------
# Templates de confirmação de agendamento (Clínica da Beleza)
# ---------------------------------------------------------------------------

def msg_confirmacao_agendamento(
    *,
    nome: str,
    data: str,
    hora: str,
    procedimento: str,
    profissional: str | None = None,
    link: str | None = None,
) -> str:
    """
    Mensagem de confirmação de agendamento — versão texto (fallback ou Meta API).
    Quando Evolution + link disponível, usar junto com send_url_button_or_text.
    """
    linhas = [
        f'📅 *Confirmação de Agendamento*',
        SEPARADOR,
        f'Olá *{nome}*! 😊',
        '',
        f'Você tem um agendamento confirmado:',
        '',
        f'📆 *Data:* {data}',
        f'⏰ *Hora:* {hora}',
        f'💆 *Procedimento:* {procedimento}',
    ]
    if profissional:
        linhas.append(f'👤 *Profissional:* {profissional}')

    linhas.append('')

    if link:
        linhas.extend([
            f'Por favor, confirme ou cancele sua consulta:',
            '',
            f'👇 *Abra o link e toque em Confirmar ou Cancelar:*',
            link,
            '',
            f'_Ou responda neste chat:_ *CONFIRMAR* ou *CANCELAR*',
            '',
            SEPARADOR,
            '_Qualquer dúvida, entre em contato conosco._',
        ])
    else:
        linhas.extend([
            f'Responda *CONFIRMAR* ou *CANCELAR* para este chat.',
            '',
            SEPARADOR,
            '_Qualquer dúvida, entre em contato conosco._',
        ])
    return '\n'.join(linhas)


def msg_lembrete_agendamento(*, nome: str, hora: str, procedimento: str) -> str:
    """Lembrete de agendamento no dia."""
    return '\n'.join([
        f'⏰ *Lembrete de Agendamento*',
        SEPARADOR,
        f'Olá *{nome}*! 😊',
        '',
        f'Seu agendamento é *hoje às {hora}*.',
        f'💆 *{procedimento}*',
        '',
        f'Estamos te aguardando! 🤗',
        SEPARADOR,
    ])


# ---------------------------------------------------------------------------
# Templates lembrete de tarefas CRM
# ---------------------------------------------------------------------------

def msg_lembrete_tarefa(
    *,
    tipo: str,
    titulo: str,
    data_hora: str,
    loja_nome: str,
    lead_nome: str | None = None,
    antecedencia: str = '24h',
) -> str:
    """Lembrete automático de atividade CRM — sem link."""
    quando = '24 horas' if antecedencia == '24h' else '2 horas'
    linhas = [
        f'🔔 *Lembrete — faltam {quando}*',
        SEPARADOR,
        f'📅 *{loja_nome}*',
        '',
        f'*{tipo}:* {titulo}',
        f'*Quando:* {data_hora}',
    ]
    if lead_nome:
        linhas.append(f'*Cliente:* {lead_nome}')
    linhas.extend([
        '',
        SEPARADOR,
        '_Mensagem automática do calendário CRM._',
    ])
    return '\n'.join(linhas)
