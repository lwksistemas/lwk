"""Aplica catálogo padrão de produtos do estoque (estética + soroterapia)."""
from __future__ import annotations

import logging
from collections.abc import Callable

from clinica_beleza.catalogo_service import is_clinica_beleza_loja, lojas_clinica_beleza_com_schema
from clinica_beleza.estoque_catalogo import ESTOQUE_CATALOGO, estoque_catalogo_defaults
from core.db_config import ensure_loja_database_config
from tenants.middleware import set_current_loja_id, set_current_tenant_db

logger = logging.getLogger(__name__)


def aplicar_estoque_catalogo_padrao(
    loja,
    *,
    log: Callable[[str], None] | None = None,
    adicionar_faltantes: bool = False,
) -> dict | None:
    """Cadastra produtos padrão no estoque da loja.

    Por padrão só executa se não houver nenhum produto ativo (evita sobrescrever cadastro).
    Com adicionar_faltantes=True, faz update_or_create de cada item do catálogo pelo nome.
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

    from clinica_beleza.estoque_categorias import garantir_categorias_estoque_padrao, resolver_categoria
    from clinica_beleza.models import ProdutoEstoque

    garantir_categorias_estoque_padrao(lid)

    existentes = ProdutoEstoque.objects.using(db).filter(loja_id=lid, is_active=True).count()
    if existentes > 0 and not adicionar_faltantes:
        emit(f"  estoque: mantido ({existentes} produto(s) já cadastrado(s))")
        return {"loja_id": lid, "slug": loja.slug, "produtos": 0, "ignorado": True}

    emit(f"Estoque catálogo — {loja.nome} ({loja.slug})")
    criados = 0
    for item in ESTOQUE_CATALOGO:
        cat = resolver_categoria(loja_id=lid, slug=item.categoria)
        defaults = estoque_catalogo_defaults(item, categoria_obj=cat)
        _obj, created = ProdutoEstoque.objects.using(db).update_or_create(
            nome=item.nome,
            loja_id=lid,
            defaults=defaults,
        )
        if created:
            criados += 1

    stats = {
        "loja_id": lid,
        "slug": loja.slug,
        "produtos": len(ESTOQUE_CATALOGO),
        "criados": criados,
        "ignorado": False,
    }
    emit(f'  {stats["produtos"]} itens no catálogo ({criados} novo(s))')
    return stats


__all__ = [
    "aplicar_estoque_catalogo_padrao",
    "lojas_clinica_beleza_com_schema",
]
