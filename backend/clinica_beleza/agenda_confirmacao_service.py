"""
Confirmação/cancelamento de agendamento pelo paciente (link WhatsApp ou resposta).
"""
import logging
import re
from dataclasses import dataclass
from datetime import timedelta

from django.conf import settings
from django.core.signing import BadSignature, dumps, loads
from django.utils import timezone

from core.assinatura_service import normalizar_token_url
from .agenda_display import format_agenda_data, format_agenda_hora

logger = logging.getLogger(__name__)

TOKEN_EXPIRACAO_DIAS = 14
ACOES_VALIDAS = frozenset({'confirmar', 'cancelar'})
STATUS_ACIONAVEIS = frozenset({'SCHEDULED', 'PENDING'})


@dataclass
class RespostaConfirmacao:
    ok: bool
    message: str
    status: str | None = None
    appointment_id: int | None = None
    already_done: bool = False


def gerar_token_confirmacao(loja_id: int, appointment_id: int) -> str:
    payload = {
        'doc_type': 'agendamento',
        'doc_id': int(appointment_id),
        'loja_id': int(loja_id),
        'modulo': 'clinica_beleza',
        'exp': int((timezone.now() + timedelta(days=TOKEN_EXPIRACAO_DIAS)).timestamp()),
    }
    return dumps(payload)


def decodificar_token_confirmacao(token: str) -> dict | None:
    token = normalizar_token_url(token)
    if not token:
        return None
    try:
        payload = loads(token)
    except (BadSignature, Exception):
        return None
    if payload.get('doc_type') != 'agendamento':
        return None
    exp = payload.get('exp')
    if exp and int(exp) < int(timezone.now().timestamp()):
        return None
    return payload


def url_confirmacao_frontend(token: str) -> str:
    base = getattr(settings, 'FRONTEND_URL', 'https://lwksistemas.com.br').rstrip('/')
    return f'{base}/confirmar-agendamento/{token}'


def _configurar_tenant(loja_id: int) -> str | None:
    from core.db_config import ensure_loja_database_config
    from superadmin.models import Loja
    from tenants.middleware import set_current_loja_id, set_current_tenant_db

    loja = Loja.objects.using('default').filter(id=loja_id, is_active=True).first()
    if not loja:
        return 'Loja não encontrada.'
    db_name = loja.database_name
    if not ensure_loja_database_config(db_name):
        return 'Banco da loja indisponível.'
    set_current_tenant_db(db_name)
    set_current_loja_id(loja_id)
    return None


def _loja_elegivel_confirmacao_agenda(loja_id: int) -> bool:
    """Só Clínica da Beleza com banco criado processa confirmação de agendamento."""
    from superadmin.models import Loja

    loja = (
        Loja.objects.using('default')
        .select_related('tipo_loja')
        .filter(id=loja_id, is_active=True, database_created=True)
        .first()
    )
    if not loja:
        return False
    tipo = (loja.tipo_loja.nome if loja.tipo_loja else '').strip()
    return tipo == 'Clínica da Beleza'


def _procedure_label(appointment) -> str:
    if appointment.procedures.exists():
        return ', '.join(appointment.procedures.values_list('nome', flat=True))
    if appointment.procedure_id and appointment.procedure:
        return appointment.procedure.nome
    return 'Atendimento'


def serializar_agendamento_publico(appointment, loja_nome: str = '') -> dict:
    return {
        'appointment_id': appointment.id,
        'paciente_nome': getattr(appointment.patient, 'name', '') or getattr(appointment.patient, 'nome', ''),
        'profissional_nome': getattr(appointment.professional, 'nome', '') if appointment.professional else '',
        'procedimento': _procedure_label(appointment),
        'data': format_agenda_data(appointment),
        'hora': format_agenda_hora(appointment),
        'status': appointment.status,
        'status_display': appointment.get_status_display(),
        'clinica_nome': loja_nome,
        'pode_responder': appointment.status in STATUS_ACIONAVEIS,
    }


def obter_dados_confirmacao(token: str) -> tuple[dict | None, str | None, int | None]:
    payload = decodificar_token_confirmacao(token)
    if not payload:
        return None, 'Link inválido ou expirado.', None

    loja_id = payload.get('loja_id')
    appointment_id = payload.get('doc_id')
    if not loja_id or not appointment_id:
        return None, 'Link inválido.', None

    err = _configurar_tenant(loja_id)
    if err:
        return None, err, None

    from .models import Appointment

    appointment = (
        Appointment.objects
        .select_related('patient', 'professional', 'procedure')
        .prefetch_related('procedures')
        .filter(pk=appointment_id)
        .first()
    )
    if not appointment:
        return None, 'Agendamento não encontrado.', loja_id

    from superadmin.models import Loja
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    loja_nome = loja.nome if loja else ''
    return serializar_agendamento_publico(appointment, loja_nome), None, loja_id


def processar_resposta_confirmacao(token: str, acao: str) -> RespostaConfirmacao:
    acao = (acao or '').strip().lower()
    if acao not in ACOES_VALIDAS:
        return RespostaConfirmacao(False, 'Ação inválida.')

    payload = decodificar_token_confirmacao(token)
    if not payload:
        return RespostaConfirmacao(False, 'Link inválido ou expirado.')

    loja_id = payload.get('loja_id')
    appointment_id = payload.get('doc_id')
    if not loja_id or not appointment_id:
        return RespostaConfirmacao(False, 'Link inválido.')

    err = _configurar_tenant(loja_id)
    if err:
        return RespostaConfirmacao(False, err)

    from .models import Appointment

    appointment = (
        Appointment.objects
        .select_related('patient', 'professional', 'procedure')
        .filter(pk=appointment_id)
        .first()
    )
    if not appointment:
        return RespostaConfirmacao(False, 'Agendamento não encontrado.')

    novo_status = 'CLIENT_CONFIRMED' if acao == 'confirmar' else 'CANCELLED'

    if appointment.status == novo_status:
        label = 'confirmado' if novo_status == 'CLIENT_CONFIRMED' else 'cancelado'
        return RespostaConfirmacao(
            True,
            f'Este agendamento já estava {label}.',
            status=appointment.status,
            appointment_id=appointment.id,
            already_done=True,
        )

    if appointment.status not in STATUS_ACIONAVEIS:
        return RespostaConfirmacao(
            False,
            f'Não é possível alterar: status atual é {appointment.get_status_display()}.',
            status=appointment.status,
            appointment_id=appointment.id,
        )

    from .agenda_service import atualizar_agendamento

    try:
        result = atualizar_agendamento(appointment, new_status=novo_status, user=None, request=None)
    except Exception as exc:
        logger.exception('Erro ao atualizar agendamento %s via confirmação: %s', appointment_id, exc)
        return RespostaConfirmacao(False, 'Erro ao registrar sua resposta. Tente novamente.')

    msg = (
        'Agendamento confirmado! Aguardamos você no horário marcado.'
        if novo_status == 'CLIENT_CONFIRMED'
        else 'Agendamento cancelado. Se precisar remarcar, entre em contato conosco.'
    )
    return RespostaConfirmacao(
        True,
        msg,
        status=result.appointment.status,
        appointment_id=result.appointment.id,
    )


def _normalize_phone_digits(telefone: str) -> str:
    return re.sub(r'\D', '', str(telefone or ''))


def _phones_match(a: str, b: str) -> bool:
    da, db = _normalize_phone_digits(a), _normalize_phone_digits(b)
    if not da or not db:
        return False
    if da == db:
        return True
    # BR: comparar últimos 10–11 dígitos (DDD + número)
    return da[-11:] == db[-11:] or da[-10:] == db[-10:]


def _normalize_reply_text(texto: str) -> str:
    t = re.sub(r'[^\w\sáàâãéèêíìîóòôõúùûç]', '', (texto or '').strip().lower())
    return re.sub(r'\s+', ' ', t).strip()


def _parse_acao_texto(texto: str) -> str | None:
    t = _normalize_reply_text(texto)
    if not t:
        return None
    if t in ('confirmar', 'confirmo', 'sim', '1', 'ok', 'confirmado', 'confirm'):
        return 'confirmar'
    if t in ('cancelar', 'cancelo', 'nao', 'não', '2', 'cancelado', 'cancel'):
        return 'cancelar'
    if t.startswith('confirm') or ' confirm' in f' {t} ':
        return 'confirmar'
    if t.startswith('cancel') or ' cancel' in f' {t} ':
        return 'cancelar'
    return None


def _parse_acao_botao(button_id: str) -> tuple[str | None, int | None]:
    raw = (button_id or '').strip().lower()
    m = re.match(r'^ag_(confirm|cancel)_(\d+)$', raw)
    if m:
        acao = 'confirmar' if m.group(1) == 'confirm' else 'cancelar'
        return acao, int(m.group(2))
    # Fallback: id genérico ou displayText repassado como id
    if raw in ('confirmar', 'confirm', '1'):
        return 'confirmar', None
    if raw in ('cancelar', 'cancel', '2'):
        return 'cancelar', None
    return None, None


def processar_resposta_whatsapp(
    loja_id: int,
    telefone: str,
    *,
    texto: str | None = None,
    button_id: str | None = None,
) -> RespostaConfirmacao | None:
    """
    Processa resposta via WhatsApp (texto ou botão).
    Retorna None se a mensagem não for reconhecida como confirmação de agenda.
    """
    acao = None
    appointment_id = None

    if button_id:
        acao, appointment_id = _parse_acao_botao(button_id)

    if not acao and texto:
        acao = _parse_acao_texto(texto)

    if not acao:
        return None

    if not _loja_elegivel_confirmacao_agenda(loja_id):
        return None

    err = _configurar_tenant(loja_id)
    if err:
        return RespostaConfirmacao(False, err)

    from django.db.utils import ProgrammingError

    from .models import Appointment

    appointment = None
    try:
        if appointment_id:
            appointment = Appointment.objects.filter(pk=appointment_id).first()

        if not appointment:
            phone_digits = _normalize_phone_digits(telefone)
            if not phone_digits:
                return None
            qs = (
                Appointment.objects
                .select_related('patient')
                .filter(status__in=STATUS_ACIONAVEIS, date__gte=timezone.now())
                .order_by('date')
            )
            for ag in qs[:50]:
                pt = getattr(ag.patient, 'telefone', '') or getattr(ag.patient, 'phone', '')
                if _phones_match(phone_digits, pt):
                    appointment = ag
                    break
    except ProgrammingError as exc:
        logger.warning(
            'processar_resposta_whatsapp: erro de schema loja %s: %s',
            loja_id,
            exc,
        )
        return None

    if not appointment:
        return RespostaConfirmacao(
            False,
            'Não encontramos agendamento pendente para confirmar ou cancelar.',
        )

    token = gerar_token_confirmacao(loja_id, appointment.id)
    return processar_resposta_confirmacao(token, acao)
