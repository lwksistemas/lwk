"""
Smoke tests de integração Clínica da Beleza — reutilizável em testes locais e CLI (schema real).

Uso CLI (PostgreSQL / schema loja_*):
  python manage.py smoke_test_clinica_integracao --slug novaimagem
  railway run --service lwks-backend-staging python manage.py smoke_test_clinica_integracao --slug novaimagem --write
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable

from django.contrib.auth.models import User
from django.db import connections, transaction
from django.utils import timezone

from clinica_beleza.consulta_service import finalizar_consulta
from clinica_beleza.models import (
    Appointment,
    Consulta,
    LocalAtendimento,
    Patient,
    PatientAnamnese,
    Professional,
    ProfessionalCommission,
)
from clinica_beleza.retorno_service import get_agenda_retorno_config
from superadmin.authentication import invalidate_session_cache
from superadmin.session_manager import SessionManager
from tenants.middleware import set_current_loja_id, set_current_tenant_db


@dataclass
class SmokeContext:
    loja_id: int
    loja_slug: str
    tenant_db: str
    owner: User
    loja_b_id: int | None = None
    loja_b_slug: str | None = None
    loja_b_tenant_db: str | None = None


CheckFn = Callable[[SmokeContext], None]


def activate_loja(ctx: SmokeContext, *, loja_id: int, tenant_db: str) -> None:
    set_current_tenant_db(tenant_db)
    set_current_loja_id(loja_id)


def _required_tables(tenant_db: str) -> list[str]:
    return [
        'clinica_beleza_patient',
        'clinica_beleza_agenda_retorno_config',
        'clinica_beleza_consultas',
    ]


def check_schema_tenant(ctx: SmokeContext) -> None:
    tables = set(connections[ctx.tenant_db].introspection.table_names())
    missing = [t for t in _required_tables(ctx.tenant_db) if t not in tables]
    if missing:
        raise AssertionError(f'Tabelas ausentes no schema {ctx.tenant_db}: {", ".join(missing)}')


def check_retorno_service_config(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    config = get_agenda_retorno_config(ctx.loja_id)
    if config is None:
        raise AssertionError('get_agenda_retorno_config retornou None')
    if config.loja_id != ctx.loja_id:
        raise AssertionError(f'config.loja_id={config.loja_id} != {ctx.loja_id}')


def _api_host() -> str:
    from django.conf import settings

    for host in settings.ALLOWED_HOSTS:
        if host and host not in ('*', 'testserver', 'localhost', '127.0.0.1'):
            return host
    return 'api.lwksistemas.com.br'


def _authenticated_api_client(owner: User):
    from rest_framework.test import APIClient

    invalidate_session_cache(owner.id)
    client = APIClient()
    token = _owner_token(owner)
    sid = SessionManager.create_session(owner.id, token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}', HTTP_X_SESSION_ID=sid)
    return client


def _tenant_api_headers(ctx: SmokeContext) -> dict[str, str]:
    return {
        'HTTP_X_LOJA_ID': str(ctx.loja_id),
        'HTTP_X_TENANT_SLUG': ctx.loja_slug,
        'HTTP_HOST': _api_host(),
    }


def check_api_retorno_config_get(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    client = _authenticated_api_client(ctx.owner)
    response = client.get(
        '/api/clinica-beleza/retorno/config/',
        **_tenant_api_headers(ctx),
    )
    if response.status_code != 200:
        raise AssertionError(f'GET retorno/config → {response.status_code}: {response.content!r}')
    if 'retorno_consulta_ativo' not in response.json():
        raise AssertionError('Resposta sem retorno_consulta_ativo')


def check_cria_paciente_com_contexto_loja(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    patient = Patient.objects.create(nome='[SMOKE] Maria Integração', loja_id=ctx.loja_id)
    if Patient.objects.filter(pk=patient.pk).count() != 1:
        raise AssertionError('Paciente não visível no contexto da loja A')

    if ctx.loja_b_tenant_db and ctx.loja_b_tenant_db != ctx.tenant_db:
        activate_loja(ctx, loja_id=ctx.loja_b_id or ctx.loja_id, tenant_db=ctx.loja_b_tenant_db)
        if Patient.objects.filter(pk=patient.pk).exists():
            raise AssertionError('Paciente da loja A visível no schema da loja B')
    else:
        fake_loja_id = ctx.loja_b_id or (ctx.loja_id + 1_000_000)
        activate_loja(ctx, loja_id=fake_loja_id, tenant_db=ctx.tenant_db)
        if Patient.objects.filter(pk=patient.pk).exists():
            raise AssertionError('Paciente visível com contexto loja_id incorreto')


def check_api_post_paciente(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    client = _authenticated_api_client(ctx.owner)
    response = client.post(
        '/api/clinica-beleza/patients/',
        {
            'name': '[SMOKE] João API Tenant',
            'phone': '16999998888',
            'active': True,
        },
        format='json',
        **_tenant_api_headers(ctx),
    )
    if response.status_code != 201:
        raise AssertionError(f'POST patients → {response.status_code}: {response.content!r}')


def check_api_anamnese_put(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    patient = Patient.objects.create(nome='[SMOKE] Paciente Anamnese', loja_id=ctx.loja_id)
    client = _authenticated_api_client(ctx.owner)
    response = client.put(
        f'/api/clinica-beleza/patients/{patient.id}/anamnese/',
        {'queixa_principal': '[SMOKE] Melasma'},
        format='json',
        **_tenant_api_headers(ctx),
    )
    if response.status_code != 200:
        raise AssertionError(f'PUT anamnese → {response.status_code}: {response.content!r}')
    if not PatientAnamnese.objects.filter(patient_id=patient.id).exists():
        raise AssertionError('PatientAnamnese não criada')


def check_finalizar_consulta_somente_taxa_comissao(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    patient = Patient.objects.create(nome='[SMOKE] Paciente Taxa', loja_id=ctx.loja_id)
    professional = Professional.objects.create(nome='[SMOKE] Dra. Taxa', loja_id=ctx.loja_id)
    local = LocalAtendimento.objects.create(
        nome='[SMOKE] Sala 1',
        valor_consulta=Decimal('150.00'),
        loja_id=ctx.loja_id,
    )
    ProfessionalCommission.objects.create(
        professional=professional,
        tipo='consulta',
        modo='percentual',
        valor=Decimal('30.00'),
        local_atendimento=local,
        loja_id=ctx.loja_id,
    )
    appt = Appointment.objects.create(
        date=timezone.now(),
        status='IN_PROGRESS',
        patient=patient,
        professional=professional,
        local_atendimento=local,
        loja_id=ctx.loja_id,
    )
    consulta = Consulta.objects.create(
        appointment=appt,
        patient=patient,
        professional=professional,
        status='IN_PROGRESS',
        data_inicio=timezone.now(),
        valor_consulta=Decimal('150.00'),
        local_atendimento=local,
        loja_id=ctx.loja_id,
    )
    finalizar_consulta(
        consulta,
        payment_method='CASH',
        mark_as_paid=True,
        amount=Decimal('150.00'),
    )
    consulta.refresh_from_db()
    payment = consulta.appointment.payment_set.first()
    if payment is None:
        raise AssertionError('Pagamento não criado ao finalizar consulta')
    if payment.status != 'PAID':
        raise AssertionError(f'Pagamento status={payment.status!r}, esperado PAID')
    if (payment.comissao_valor or Decimal('0')) <= Decimal('0'):
        raise AssertionError('Comissão zerada em pagamento só taxa de consulta')
    if payment.comissao_valor != Decimal('45.00'):
        raise AssertionError(f'Comissão={payment.comissao_valor}, esperado 45.00')


def check_isolamento_loja_id(ctx: SmokeContext) -> None:
    activate_loja(ctx, loja_id=ctx.loja_id, tenant_db=ctx.tenant_db)
    Patient.objects.create(nome='[SMOKE] Só Loja A', loja_id=ctx.loja_id)
    if Patient.objects.filter(loja_id=ctx.loja_id).count() < 1:
        raise AssertionError('Nenhum paciente visível para loja A')

    other_id = ctx.loja_b_id or (ctx.loja_id + 1_000_000)
    other_db = ctx.loja_b_tenant_db or ctx.tenant_db
    activate_loja(ctx, loja_id=other_id, tenant_db=other_db)
    if Patient.objects.filter(loja_id=ctx.loja_id).count() != 0:
        raise AssertionError('Isolamento por loja_id falhou no contexto alternativo')


READONLY_CHECKS: list[tuple[str, CheckFn]] = [
    ('schema_tenant', check_schema_tenant),
    ('retorno_service_config', check_retorno_service_config),
    ('api_retorno_config_get', check_api_retorno_config_get),
]

WRITE_CHECKS: list[tuple[str, CheckFn]] = [
    ('cria_paciente_contexto_loja', check_cria_paciente_com_contexto_loja),
    ('api_post_paciente', check_api_post_paciente),
    ('api_anamnese_put', check_api_anamnese_put),
    ('finalizar_consulta_comissao_taxa', check_finalizar_consulta_somente_taxa_comissao),
    ('isolamento_loja_id', check_isolamento_loja_id),
]


def _owner_token(owner: User) -> str:
    from rest_framework_simplejwt.tokens import RefreshToken

    return str(RefreshToken.for_user(owner).access_token)


def run_smoke_checks(
    ctx: SmokeContext,
    *,
    include_write: bool = False,
    rollback_write: bool = True,
) -> list[tuple[str, str | None]]:
    """
    Executa checks. Retorna lista de (nome, erro ou None).
    Com rollback_write=True, checks de escrita rodam em atomic no tenant_db.
    """
    results: list[tuple[str, str | None]] = []
    checks = list(READONLY_CHECKS)
    if include_write:
        checks.extend(WRITE_CHECKS)

    write_names = {name for name, _ in WRITE_CHECKS}

    for name, fn in checks:
        try:
            if include_write and rollback_write and name in write_names:
                with transaction.atomic(using=ctx.tenant_db):
                    fn(ctx)
                    transaction.set_rollback(True, using=ctx.tenant_db)
            else:
                fn(ctx)
            results.append((name, None))
        except Exception as exc:
            results.append((name, str(exc)))
        finally:
            set_current_tenant_db('default')
            set_current_loja_id(None)

    return results
