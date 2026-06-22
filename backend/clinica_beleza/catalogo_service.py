"""
Catálogo padrão (locais + procedimentos) — Clínica da Beleza.

Idempotente: update_or_create por nome, sem apagar cadastros personalizados.
"""
from __future__ import annotations

import logging
from typing import Callable

from clinica_beleza.procedimentos_catalogo import (
    CONVENIO_PARTICULAR_CATALOGO,
    LOCAIS_CATALOGO,
    LOCAIS_CATALOGO_LEGADO,
    NOMES_AGENDA_CATALOGO,
    PROCEDIMENTOS_CATALOGO,
    procedimento_catalogo_defaults,
)
from core.db_config import ensure_loja_database_config
from tenants.middleware import set_current_loja_id, set_current_tenant_db

logger = logging.getLogger(__name__)

TIPO_CLINICA_BELEZA_NOME = 'Clínica da Beleza'


def _normalizar_nome_local(nome: str) -> str:
    return (nome or '').strip().upper()


def _desativar_locais_catalogo_duplicados(db, lid) -> int:
    """
    Desativa cópias automáticas do catálogo (ex.: Consultório R$ 0) quando já existe
    local ativo com o mesmo nome (ignorando maiúsculas/minúsculas).
    """
    from clinica_beleza.models import LocalAtendimento

    catalog_defaults = {
        _normalizar_nome_local(nome): valor
        for nome, valor, _tempo in LOCAIS_CATALOGO
    }
    locais = list(
        LocalAtendimento.objects.using(db).filter(loja_id=lid, is_active=True)
    )
    by_norm: dict[str, list] = {}
    for loc in locais:
        by_norm.setdefault(_normalizar_nome_local(loc.nome), []).append(loc)

    desativados = 0
    for nome_norm, grupo in by_norm.items():
        if len(grupo) <= 1 or nome_norm not in catalog_defaults:
            continue
        valor_cat = catalog_defaults[nome_norm]
        fantasmas = [loc for loc in grupo if loc.valor_consulta == valor_cat]
        if not fantasmas or len(fantasmas) >= len(grupo):
            continue
        for loc in fantasmas:
            loc.is_active = False
            loc.save(update_fields=['is_active', 'updated_at'])
            desativados += 1
    return desativados


def _aplicar_locais_catalogo(db, lid, emit) -> int:
    """Só cria locais padrão se a loja ainda não tiver nenhum ativo."""
    from clinica_beleza.models import LocalAtendimento

    if LocalAtendimento.objects.using(db).filter(loja_id=lid, is_active=True).exists():
        emit('  locais: mantidos (já cadastrados)')
        return 0

    for nome, valor, _tempo in LOCAIS_CATALOGO:
        LocalAtendimento.objects.using(db).update_or_create(
            nome=_normalizar_nome_local(nome),
            loja_id=lid,
            defaults={
                'valor_consulta': valor,
                'is_active': True,
            },
        )
    return len(LOCAIS_CATALOGO)
TIPO_CLINICA_BELEZA_SLUG = 'clinica-beleza'


def is_clinica_beleza_loja(loja) -> bool:
    tipo = getattr(loja, 'tipo_loja', None)
    if not tipo:
        return False
    nome = (getattr(tipo, 'nome', '') or '').strip()
    slug = (getattr(tipo, 'slug', '') or '').strip()
    return nome == TIPO_CLINICA_BELEZA_NOME or slug == TIPO_CLINICA_BELEZA_SLUG


def lojas_clinica_beleza_com_schema(*, apenas_ativas: bool = True):
    from django.db.models import Q
    from superadmin.models import Loja

    qs = Loja.objects.using('default').filter(
        database_created=True,
    ).filter(
        Q(tipo_loja__nome=TIPO_CLINICA_BELEZA_NOME)
        | Q(tipo_loja__slug=TIPO_CLINICA_BELEZA_SLUG)
    ).select_related('tipo_loja').order_by('slug')
    if apenas_ativas:
        qs = qs.filter(is_active=True)
    return qs


def aplicar_catalogo_padrao(loja, *, log: Callable[[str], None] | None = None) -> dict | None:
    """
    Garante locais e procedimentos padrão na loja.
    Retorna estatísticas ou None se a loja foi ignorada.
    """
    emit = log or (lambda msg: logger.info(msg))

    if not is_clinica_beleza_loja(loja):
        emit(f'skip {getattr(loja, "slug", "?")}: não é Clínica da Beleza')
        return None

    if not loja.database_created or not loja.database_name:
        emit(f'skip {loja.slug}: schema não criado')
        return None

    db = loja.database_name
    lid = loja.id
    if not ensure_loja_database_config(db, conn_max_age=0):
        emit(f'skip {loja.slug}: banco inacessível')
        return None

    set_current_loja_id(lid)
    set_current_tenant_db(db)

    from clinica_beleza.models import Convenio, ConvenioProcedimentoPreco, LocalAtendimento, NomeAgenda, Patient, Procedure

    emit(f'Catálogo padrão — {loja.nome} ({loja.slug})')

    # Nomes de agenda padrão
    for nome_agenda in NOMES_AGENDA_CATALOGO:
        NomeAgenda.objects.using(db).update_or_create(
            nome=nome_agenda,
            loja_id=lid,
            defaults={'is_active': True},
        )

    locais_aplicados = _aplicar_locais_catalogo(db, lid, emit)
    duplicados = _desativar_locais_catalogo_duplicados(db, lid)
    if duplicados:
        emit(f'  {duplicados} local(is) duplicado(s) do catálogo desativado(s)')

    if LOCAIS_CATALOGO_LEGADO:
        desativados = (
            LocalAtendimento.objects.using(db)
            .filter(loja_id=lid, nome__in=LOCAIS_CATALOGO_LEGADO, is_active=True)
            .update(is_active=False)
        )
        if desativados:
            emit(f'  {desativados} local(is) de demonstração desativado(s)')

    com_termo = 0
    for item in PROCEDIMENTOS_CATALOGO:
        defaults = procedimento_catalogo_defaults(item)
        if defaults['termo_consentimento_ativo']:
            com_termo += 1
        Procedure.objects.using(db).update_or_create(
            nome=item.nome,
            loja_id=lid,
            defaults=defaults,
        )

    nome_particular, codigo_particular = CONVENIO_PARTICULAR_CATALOGO
    particular, _ = Convenio.objects.using(db).update_or_create(
        nome=nome_particular,
        loja_id=lid,
        defaults={'codigo': codigo_particular, 'is_active': True},
    )
    precos_particular = 0
    for proc in Procedure.objects.using(db).filter(loja_id=lid, is_active=True):
        ConvenioProcedimentoPreco.objects.using(db).update_or_create(
            convenio=particular,
            procedure=proc,
            loja_id=lid,
            defaults={'modo': 'fixo', 'preco': proc.preco, 'is_active': True},
        )
        precos_particular += 1

    vinculados = (
        Patient.objects.using(db)
        .filter(loja_id=lid, convenio_id__isnull=True)
        .update(convenio_id=particular.id)
    )
    if vinculados:
        emit(f'  {vinculados} paciente(s) vinculado(s) ao convênio Particular')

    stats = {
        'loja_id': lid,
        'slug': loja.slug,
        'locais': locais_aplicados,
        'procedimentos': len(PROCEDIMENTOS_CATALOGO),
        'com_termo': com_termo,
        'convenio_particular_id': particular.id,
        'precos_particular': precos_particular,
    }
    emit(
        f'  {stats["locais"]} locais, {stats["procedimentos"]} procedimentos '
        f'({stats["com_termo"]} com TCLE), convênio Particular ({precos_particular} preços)'
    )
    return stats
