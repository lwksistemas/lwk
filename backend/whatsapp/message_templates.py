"""Templates de mensagem WhatsApp — LWK Sistemas.

Design profissional e seguro para mensagens com links de ação.
Evita aparência de spam/phishing com:
- Identidade visual clara (separadores, ícones consistentes)
- Informações contextuais (loja, tipo de documento, prazo)
- Linha de segurança (verificação LWK)
- Botão de ação em vez de URL nua (quando Evolution disponível)
"""
from __future__ import annotations

SEPARADOR = "━━━━━━━━━━━━━━━━━━━━"
DIAS_EXPIRACAO_PADRAO = 7
_PARTICULAS = frozenset({"de", "da", "do", "das", "dos", "e"})
_SUFIXOS_EMPRESA = {
    "ltda": "Ltda",
    "me": "ME",
    "epp": "EPP",
    "eireli": "Eireli",
    "sa": "S/A",
    "s.a.": "S/A",
    "s/a": "S/A",
}
_MARCAS_PESSOA_JURIDICA = (
    "ltda",
    "eireli",
    "municipio",
    "município",
    "prefeitura",
    "clinica",
    "clínica",
    "hospital",
    "secretaria",
    "laboratório",
    "laboratorio",
)


def _maioria_maiuscula(texto: str) -> bool:
    letras = [c for c in texto if c.isalpha()]
    if not letras:
        return False
    return sum(c.isupper() for c in letras) / len(letras) > 0.6


def nome_legivel(valor: str | None) -> str:
    """Tira a caixa alta do cadastro. Partículas do nome ficam minúsculas."""
    texto = " ".join((valor or "").split())
    if not texto or not _maioria_maiuscula(texto):
        return texto
    partes = []
    for indice, palavra in enumerate(texto.split()):
        chave = palavra.lower().strip(".,")
        if indice and chave in _PARTICULAS:
            partes.append(chave)
        elif chave in _SUFIXOS_EMPRESA:
            partes.append(_SUFIXOS_EMPRESA[chave])
        else:
            partes.append(chave.capitalize())
    return " ".join(partes)


def _primeiro_nome(valor: str | None) -> str:
    legivel = nome_legivel(valor)
    if not legivel:
        return ""
    baixo = legivel.casefold()
    if any(marca in baixo for marca in _MARCAS_PESSOA_JURIDICA):
        return ""
    partes = legivel.split()
    if len(partes) < 2:
        return ""
    return partes[0]


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
    vendedor_nome: str | None = None,
) -> str:
    """Mensagem para o cliente assinar proposta ou contrato.

    O valor fica só na página do link. titulo permanece na assinatura para
    quem já chama a função; o texto não repete o nome do cliente.
    """
    del titulo
    cliente = nome_legivel(nome) or (nome or "").strip() or "cliente"
    saudacao = _primeiro_nome(nome)
    empresa = nome_legivel(loja_nome) or (loja_nome or "").strip() or "a empresa"
    vendedor = nome_legivel(vendedor_nome)
    rotulo = (tipo_doc or "Documento").strip()
    if rotulo.casefold() == "proposta":
        cabecalho = "Proposta comercial"
        frase = "A proposta está pronta para a sua leitura e assinatura."
    elif rotulo.casefold() == "contrato":
        cabecalho = "Contrato"
        frase = "O contrato está pronto para a sua leitura e assinatura."
    else:
        cabecalho = rotulo
        frase = "O documento está pronto para a sua leitura e assinatura."
    prazo = "1 dia" if int(dias) == 1 else f"{int(dias)} dias"
    linhas = [
        f"*{empresa}*",
        cabecalho,
        "",
        f"Olá, {saudacao}." if saudacao else "Olá.",
        "",
        frase,
        "",
        "*Cliente*",
        cliente,
    ]
    if vendedor:
        linhas.extend(["", "*Vendedor*", vendedor])
    linhas.extend([
        "",
        f"Leia e assine pelo link. Ele vale por {prazo} e é exclusivo para você.",
        "",
        link,
    ])
    return "\n".join(linhas)


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
    """Mensagem para o VENDEDOR finalizar assinatura após o cliente já ter assinado.
    """
    subtitulo = f"_{titulo}_" if titulo and titulo.strip() else ""
    cliente_linha = f"👤 *Cliente:* {nome_cliente}" if nome_cliente else ""
    linhas = [
        "✅ *Assinatura do Cliente Concluída*",
        SEPARADOR,
        f"Olá *{nome}*!",
        "",
        f"O cliente assinou o documento de *{loja_nome}*.",
        "Agora é a sua vez de finalizar:",
        "",
        f"📋 *{tipo_doc}*" + (f"\n   {subtitulo}" if subtitulo else ""),
    ]
    if cliente_linha:
        linhas.append(cliente_linha)
    linhas.extend([
        "",
        "👇 *Toque para assinar e concluir:*",
        link,
        "",
        f"⏳ Válido por {dias} dias",
        "🔒 Documento verificado por LWK Sistemas",
        SEPARADOR,
    ])
    return "\n".join(linhas)


def msg_termo_consentimento(
    *,
    nome: str,
    procedimento: str | None,
    loja_nome: str,
    link: str,
    dias: int = DIAS_EXPIRACAO_PADRAO,
) -> str:
    """Mensagem para o PACIENTE assinar termo de consentimento (Clínica da Beleza).
    """
    proc_linha = f"💉 *Procedimento:* {procedimento}" if procedimento else ""
    linhas = [
        "📋 *Termo de Consentimento*",
        SEPARADOR,
        f"Olá *{nome}*!",
        "",
        f"*{loja_nome}* precisa da sua assinatura no",
        "Termo de Consentimento Livre e Esclarecido (TCLE):",
        "",
    ]
    if proc_linha:
        linhas.append(proc_linha)
        linhas.append("")
    linhas.extend([
        "👇 *Toque para ler e assinar:*",
        link,
        "",
        "⏳ Válido até o fim da consulta",
        "🔒 Documento verificado por LWK Sistemas",
        SEPARADOR,
        "_Sua assinatura confirma que foi informado(a) sobre o procedimento._",
    ])
    return "\n".join(linhas)


def msg_assinatura_recibo(
    *,
    nome: str,
    titulo: str | None,
    loja_nome: str,
    link: str,
    procedimentos: list[str] | None = None,
) -> str:
    """Mensagem para o CLIENTE assinar o recibo de pagamento (Clínica da Beleza)."""
    itens = [item.strip() for item in (procedimentos or []) if (item or "").strip()]
    linhas = [
        "🧾 *Recibo de Pagamento*",
        SEPARADOR,
        f"Olá *{nome}*!",
        "",
        f"*{loja_nome}* enviou o recibo do seu atendimento",
        "para assinatura digital:",
        "",
    ]
    if len(itens) > 1:
        linhas.append("💉 *Procedimentos realizados:*")
        linhas.extend(f"• {item}" for item in itens)
        linhas.append("")
    elif titulo:
        linhas.append(f"🧾 *Procedimento realizado:* {titulo}")
        linhas.append("")
    linhas.extend([
        "👇 *Toque para ler e assinar:*",
        link,
        "",
        "_Link válido por 2 horas._",
        "🔒 Documento verificado por LWK Sistemas",
        SEPARADOR,
        "_Sua assinatura confirma o recebimento do recibo e o reconhecimento do valor a pagar._",
    ])
    return "\n".join(linhas)


def msg_orcamento(
    *,
    nome: str,
    loja_nome: str,
    linhas_itens: list[str],
    total: str,
    validade_dias: int = 30,
) -> str:
    """Orçamento da Clínica da Beleza: resumo curto + foto do PDF.

    Não inclui observações/cadastro/LGPD — esses dados ficam só na foto.
    """
    linhas = [
        "📋 *Orçamento*",
        SEPARADOR,
        f"Olá *{nome}*!",
        "",
        f"Segue o orçamento da *{loja_nome}*:",
        "",
        *linhas_itens,
        "",
        f"💰 *Total: {total}*",
        f"⏳ Válido por {validade_dias} dias",
        SEPARADOR,
        "_A foto do orçamento segue nesta conversa._",
        "_Qualquer dúvida, estamos à disposição._",
    ]
    return "\n".join(linhas)


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
    """Mensagem de confirmação de agendamento — versão texto (fallback ou Meta API).
    Quando Evolution + link disponível, usar junto com send_url_button_or_text.
    """
    linhas = [
        "📅 *Confirmação de Agendamento*",
        SEPARADOR,
        f"Olá *{nome}*! 😊",
        "",
        "Você tem um agendamento confirmado:",
        "",
        f"📆 *Data:* {data}",
        f"⏰ *Hora:* {hora}",
        f"💆 *Procedimento:* {procedimento}",
    ]
    if profissional:
        linhas.append(f"👤 *Profissional:* {profissional}")

    linhas.append("")

    if link:
        linhas.extend([
            "Por favor, confirme ou cancele sua consulta:",
            "",
            "👇 *Abra o link e toque em Confirmar ou Cancelar:*",
            link,
            "",
            "_Ou responda neste chat:_ *CONFIRMAR* ou *CANCELAR*",
            "",
            SEPARADOR,
            "_Qualquer dúvida, entre em contato conosco._",
        ])
    else:
        linhas.extend([
            "Responda *CONFIRMAR* ou *CANCELAR* para este chat.",
            "",
            SEPARADOR,
            "_Qualquer dúvida, entre em contato conosco._",
        ])
    return "\n".join(linhas)


def msg_reagendamento(
    *,
    nome: str,
    data: str,
    hora: str,
    procedimento: str,
    profissional: str | None = None,
    link: str | None = None,
) -> str:
    """Mensagem enviada quando o agendamento é remarcado para outro dia/horário."""
    linhas = [
        "🔄 *Agendamento Remarcado*",
        SEPARADOR,
        f"Olá *{nome}*! 😊",
        "",
        "Seu horário foi *remarcado*. Por favor, desconsidere o horário anterior.",
        "",
        "📆 *Nova data:* {data}",
        "⏰ *Novo horário:* {hora}",
        f"💆 *Procedimento:* {procedimento}",
    ]
    if profissional:
        linhas.append(f"👤 *Profissional:* {profissional}")

    linhas.append("")

    if link:
        linhas.extend([
            "Por favor, confirme ou cancele:",
            "",
            "👇 *Abra o link e toque em Confirmar ou Cancelar:*",
            link,
            "",
            "_Ou responda neste chat:_ *CONFIRMAR* ou *CANCELAR*",
            "",
            SEPARADOR,
            "_Qualquer dúvida, entre em contato conosco._",
        ])
    else:
        linhas.extend([
            "Responda *CONFIRMAR* ou *CANCELAR* para este chat.",
            "",
            SEPARADOR,
            "_Qualquer dúvida, entre em contato conosco._",
        ])
    return "\n".join(linhas).format(data=data, hora=hora)


def msg_lembrete_agendamento(*, nome: str, hora: str, procedimento: str) -> str:
    """Lembrete de agendamento no dia."""
    return "\n".join([
        "⏰ *Lembrete de Agendamento*",
        SEPARADOR,
        f"Olá *{nome}*! 😊",
        "",
        f"Seu agendamento é *hoje às {hora}*.",
        f"💆 *{procedimento}*",
        "",
        "Estamos te aguardando! 🤗",
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
    antecedencia: str = "24h",
) -> str:
    """Lembrete automático de atividade CRM — sem link."""
    quando = "24 horas" if antecedencia == "24h" else "2 horas"
    linhas = [
        f"🔔 *Lembrete — faltam {quando}*",
        SEPARADOR,
        f"📅 *{loja_nome}*",
        "",
        f"*{tipo}:* {titulo}",
        f"*Quando:* {data_hora}",
    ]
    if lead_nome:
        linhas.append(f"*Cliente:* {lead_nome}")
    linhas.extend([
        "",
        SEPARADOR,
        "_Mensagem automática do calendário CRM._",
    ])
    return "\n".join(linhas)
