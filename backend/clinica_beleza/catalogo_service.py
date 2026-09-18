"""Catálogo padrão (locais + procedimentos) — Clínica da Beleza.

Loja nova (sem cadastro): cria locais e procedimentos do seed.
Loja que já tem cadastro: não recria, não reativa e não reescreve o que a clínica
editou ou excluiu. O ensure_all do deploy não pode desfazer o catálogo da loja.
"""
from __future__ import annotations

import logging
from collections.abc import Callable

from clinica_beleza.procedimentos_catalogo import (
    CONVENIO_PARTICULAR_CATALOGO,
    LOCAIS_CATALOGO,
    LOCAIS_CATALOGO_LEGADO,
    NOMES_AGENDA_CATALOGO,
    PROCEDIMENTOS_CATALOGO,
    nomes_agenda_faltando,
    procedimento_catalogo_defaults,
)
from core.db_config import ensure_loja_database_config
from tenants.middleware import set_current_loja_id, set_current_tenant_db

logger = logging.getLogger(__name__)

TIPO_CLINICA_BELEZA_NOME = "Clínica da Beleza"


def _normalizar_nome_local(nome: str) -> str:
    return (nome or "").strip().upper()


def _normalizar_nome_procedimento(nome: str) -> str:
    """Alinha ao TextNormalizationMixin da API (maiúsculas)."""
    return (nome or "").strip().upper()


def _procedimento_catalogo_existente(db, lid, item):
    """Encontra procedimento do catálogo pelo nome (inclui inativos e nome legado)."""
    from clinica_beleza.models import Procedure

    nome_norm = _normalizar_nome_procedimento(item.nome)
    cat_prefix = (item.categoria or "").strip().upper()
    nome_legado = f"{cat_prefix} — {nome_norm}" if cat_prefix and not nome_norm.startswith(cat_prefix) else ""
    existente = (
        Procedure.objects.using(db)
        .filter(loja_id=lid, nome__iexact=nome_norm)
        .order_by("id")
        .first()
    )
    if existente or not nome_legado:
        return existente
    return (
        Procedure.objects.using(db)
        .filter(loja_id=lid, nome__iexact=nome_legado)
        .order_by("id")
        .first()
    )


def _upsert_procedimento_catalogo(db, lid, item) -> None:
    """Cria procedimento do seed só se ainda não existir (mesmo inativo).

    Não reescreve preço, descrição, termo nem reativa exclusão (is_active=False).
    """
    from clinica_beleza.models import Procedure

    if _procedimento_catalogo_existente(db, lid, item):
        return
    defaults = procedimento_catalogo_defaults(item)
    defaults["nome"] = _normalizar_nome_procedimento(item.nome)
    Procedure.objects.using(db).create(loja_id=lid, **defaults)


def _aplicar_procedimentos_catalogo(db, lid, emit) -> tuple[int, int]:
    """Só semeia o catálogo se a loja ainda não tiver nenhum procedimento.

    Exclusão na tela é soft-delete (is_active=False). Se já há linhas, o deploy
    não reativa nem recria o padrão.
    """
    from clinica_beleza.models import Procedure

    if Procedure.objects.using(db).filter(loja_id=lid).exists():
        emit("  procedimentos: mantidos (já cadastrados)")
        return 0, 0

    com_termo = 0
    for item in PROCEDIMENTOS_CATALOGO:
        defaults = procedimento_catalogo_defaults(item)
        if defaults["termo_consentimento_ativo"]:
            com_termo += 1
        _upsert_procedimento_catalogo(db, lid, item)
    return len(PROCEDIMENTOS_CATALOGO), com_termo


def _desativar_procedimentos_duplicados(db, lid) -> int:
    """Desativa procedimentos com o mesmo nome (ignorando caixa), mantendo o de menor id.

    Reaponta comissões e preços de convênio dos duplicados para o registro mantido.
    """
    from clinica_beleza.models import ConvenioProcedimentoPreco, Procedure, ProfessionalCommission

    ativos = list(
        Procedure.objects.using(db).filter(loja_id=lid, is_active=True).order_by("id"),
    )
    by_norm: dict[str, list] = {}
    for proc in ativos:
        by_norm.setdefault(_normalizar_nome_procedimento(proc.nome), []).append(proc)

    desativados = 0
    for grupo in by_norm.values():
        if len(grupo) <= 1:
            continue
        keeper = grupo[0]
        if keeper.nome != _normalizar_nome_procedimento(keeper.nome):
            keeper.nome = _normalizar_nome_procedimento(keeper.nome)
            keeper.save(update_fields=["nome", "updated_at"])
        for dup in grupo[1:]:
            ProfessionalCommission.objects.using(db).filter(
                loja_id=lid, procedure_id=dup.id,
            ).update(procedure_id=keeper.id)
            for preco in ConvenioProcedimentoPreco.objects.using(db).filter(
                loja_id=lid, procedure_id=dup.id,
            ):
                conflito = (
                    ConvenioProcedimentoPreco.objects.using(db)
                    .filter(
                        loja_id=lid,
                        procedure_id=keeper.id,
                        convenio_id=preco.convenio_id,
                    )
                    .exists()
                )
                if conflito:
                    preco.is_active = False
                    preco.save(update_fields=["is_active", "updated_at"])
                else:
                    preco.procedure_id = keeper.id
                    preco.save(update_fields=["procedure_id", "updated_at"])
            dup.is_active = False
            dup.save(update_fields=["is_active", "updated_at"])
            desativados += 1
    return desativados


def _desativar_locais_catalogo_duplicados(db, lid) -> int:
    """Desativa cópias automáticas do catálogo (ex.: Consultório R$ 0) quando já existe
    local ativo com o mesmo nome (ignorando maiúsculas/minúsculas).
    """
    from clinica_beleza.models import LocalAtendimento

    catalog_defaults = {
        _normalizar_nome_local(nome): valor
        for nome, valor, _tempo in LOCAIS_CATALOGO
    }
    locais = list(
        LocalAtendimento.objects.using(db).filter(loja_id=lid, is_active=True),
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
            loc.save(update_fields=["is_active", "updated_at"])
            desativados += 1
    return desativados


def _aplicar_locais_catalogo(db, lid, emit) -> int:
    """Só cria locais padrão se a loja ainda não tiver nenhum ativo."""
    from clinica_beleza.models import LocalAtendimento

    if LocalAtendimento.objects.using(db).filter(loja_id=lid, is_active=True).exists():
        emit("  locais: mantidos (já cadastrados)")
        return 0

    for nome, valor, _tempo in LOCAIS_CATALOGO:
        LocalAtendimento.objects.using(db).update_or_create(
            nome=_normalizar_nome_local(nome),
            loja_id=lid,
            defaults={
                "valor_consulta": valor,
                "is_active": True,
            },
        )
    return len(LOCAIS_CATALOGO)
TIPO_CLINICA_BELEZA_SLUG = "clinica-beleza"
TIPO_CLINICA_BELEZA_SLUGS = frozenset(
    {
        "clinica-beleza",
        "clinica-da-beleza",
        "clinica-estetica",
        "clinica-de-estetica",
    },
)


def is_clinica_beleza_loja(loja) -> bool:
    tipo = getattr(loja, "tipo_loja", None)
    if not tipo:
        return False
    nome = (getattr(tipo, "nome", "") or "").strip()
    slug = (getattr(tipo, "slug", "") or "").strip()
    return nome == TIPO_CLINICA_BELEZA_NOME or slug in TIPO_CLINICA_BELEZA_SLUGS


def garantir_nomes_agenda_padrao(db: str, lid: int) -> int:
    """Garante Consulta e Retorno sem duplicar se já existirem com outra caixa."""
    from clinica_beleza.models import NomeAgenda

    existentes = list(NomeAgenda.objects.using(db).filter(loja_id=lid))
    sistema_keys = {n.strip().casefold() for n in NOMES_AGENDA_CATALOGO}
    alterados = 0
    for obj in existentes:
        if (obj.nome or "").strip().casefold() in sistema_keys and not obj.is_active:
            obj.is_active = True
            obj.save(update_fields=["is_active", "updated_at"])
            alterados += 1

    faltando = nomes_agenda_faltando([n.nome for n in existentes])
    tem_padrao = any(n.is_padrao for n in existentes)
    for i, nome in enumerate(NOMES_AGENDA_CATALOGO):
        if nome not in faltando:
            continue
        NomeAgenda.objects.using(db).create(
            nome=nome,
            loja_id=lid,
            is_active=True,
            is_padrao=(i == 0 and not tem_padrao),
        )
        if i == 0:
            tem_padrao = True
        alterados += 1
    return alterados


def lojas_clinica_beleza_com_schema(*, apenas_ativas: bool = True):
    from django.db.models import Q

    from superadmin.models import Loja

    qs = Loja.objects.using("default").filter(
        database_created=True,
    ).filter(
        Q(tipo_loja__nome=TIPO_CLINICA_BELEZA_NOME)
        | Q(tipo_loja__slug__in=TIPO_CLINICA_BELEZA_SLUGS),
    ).select_related("tipo_loja").order_by("slug")
    if apenas_ativas:
        qs = qs.filter(is_active=True)
    return qs


def aplicar_catalogo_padrao(loja, *, log: Callable[[str], None] | None = None) -> dict | None:
    """Garante locais e procedimentos padrão na loja.
    Retorna estatísticas ou None se a loja foi ignorada.
    """
    emit = log or (lambda msg: logger.info(msg))

    if not is_clinica_beleza_loja(loja):
        emit(f'skip {getattr(loja, "slug", "?")}: não é Clínica da Beleza')
        return None

    if not loja.database_created or not loja.database_name:
        emit(f"skip {loja.slug}: schema não criado")
        return None

    db = loja.database_name
    lid = loja.id
    if not ensure_loja_database_config(db, conn_max_age=0):
        emit(f"skip {loja.slug}: banco inacessível")
        return None

    set_current_loja_id(lid)
    set_current_tenant_db(db)

    from clinica_beleza.models import (
        Convenio,
        ConvenioProcedimentoPreco,
        LocalAtendimento,
        Patient,
        Procedure,
    )

    emit(f"Catálogo padrão — {loja.nome} ({loja.slug})")

    garantir_nomes_agenda_padrao(db, lid)

    locais_aplicados = _aplicar_locais_catalogo(db, lid, emit)
    duplicados = _desativar_locais_catalogo_duplicados(db, lid)
    if duplicados:
        emit(f"  {duplicados} local(is) duplicado(s) do catálogo desativado(s)")

    if LOCAIS_CATALOGO_LEGADO:
        desativados = (
            LocalAtendimento.objects.using(db)
            .filter(loja_id=lid, nome__in=LOCAIS_CATALOGO_LEGADO, is_active=True)
            .update(is_active=False)
        )
        if desativados:
            emit(f"  {desativados} local(is) de demonstração desativado(s)")

    n_proc, com_termo = _aplicar_procedimentos_catalogo(db, lid, emit)
    if n_proc:
        proc_dups = _desativar_procedimentos_duplicados(db, lid)
        if proc_dups:
            emit(f"  {proc_dups} procedimento(s) duplicado(s) desativado(s)")

    nome_particular, codigo_particular = CONVENIO_PARTICULAR_CATALOGO
    particular, _ = Convenio.objects.using(db).get_or_create(
        nome=nome_particular,
        loja_id=lid,
        defaults={"codigo": codigo_particular, "is_active": True},
    )
    precos_particular = 0
    if n_proc:
        for proc in Procedure.objects.using(db).filter(loja_id=lid, is_active=True):
            ConvenioProcedimentoPreco.objects.using(db).update_or_create(
                convenio=particular,
                procedure=proc,
                loja_id=lid,
                defaults={"modo": "fixo", "preco": proc.preco, "is_active": True},
            )
            precos_particular += 1
    else:
        precos_particular = ConvenioProcedimentoPreco.objects.using(db).filter(
            convenio=particular, loja_id=lid,
        ).count()

    vinculados = (
        Patient.objects.using(db)
        .filter(loja_id=lid, convenio_id__isnull=True)
        .update(convenio_id=particular.id)
    )
    if vinculados:
        emit(f"  {vinculados} paciente(s) vinculado(s) ao convênio Particular")

    stats = {
        "loja_id": lid,
        "slug": loja.slug,
        "locais": locais_aplicados,
        "procedimentos": n_proc if n_proc else Procedure.objects.using(db).filter(loja_id=lid).count(),
        "com_termo": com_termo,
        "convenio_particular_id": particular.id,
        "precos_particular": precos_particular,
    }
    emit(
        f'  {stats["locais"]} locais, {stats["procedimentos"]} procedimentos '
        f'({stats["com_termo"]} com TCLE), convênio Particular ({precos_particular} preços)',
    )
    return stats
