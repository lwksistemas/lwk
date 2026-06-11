"""
Auditoria e correção de schemas PostgreSQL por loja (isolamento por schema).
Usado pelo comando auditar_schema_por_slug e pela API do superadmin.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from django.conf import settings
from django.db import connection, connections

from core.db_config import ensure_loja_database_config
from superadmin.services.database_schema_service import (
    TIPO_LOJA_EXTRA_APPS,
    DatabaseSchemaService,
    get_apps_esperados_para_loja,
)

logger = logging.getLogger(__name__)


def prefixos_tabela_para_app(app_label: str) -> list[str]:
    """
    Prefixos de table_name em information_schema para contar tabelas do app.

    clinica_estetica usa Meta db_table com prefixo clinica_* (legado), não clinica_estetica_*.
    contenttypes usa django_content_type (não contenttypes_*).
    auth usa auth_* (auth_permission, auth_group, etc).
    """
    if app_label == 'clinica_estetica':
        return ['clinica_']
    if app_label == 'contenttypes':
        return ['django_content_type']
    return [f'{app_label}_']


TABELAS_DJANGO_PERMITIDAS = frozenset({'django_migrations', 'django_content_type'})

# Tabelas que migrations/ensure devem criar; ausência = falha na auditoria.
TABELAS_OBRIGATORIAS_POR_TIPO: dict[str, list[str]] = {
    'clinica-beleza': [
        'clinica_beleza_consulta_assinaturas_termo',
        'clinica_beleza_consulta_termo_procedimento',
    ],
}

# Comandos ensure_* executados após migrate (mesma ordem do releaseCommand Railway).
ENSURE_COMANDOS_POR_TIPO: dict[str, list[str]] = {
    'clinica-beleza': [
        'ensure_clinica_beleza_consultas',
        'ensure_appointment_duracao_minutos',
        'ensure_professional_nascimento_sexo',
        'ensure_memed_timbrado_table',
        'ensure_professional_commission_local',
        'ensure_professional_commission_convenio',
        'ensure_convenio_tables',
        'ensure_estoque_produto_fields',
        'ensure_termo_consentimento',
        'ensure_paciente_fotos_table',
    ],
}


# Tabelas com prefixo fora do padrão do app, mas válidas para o tipo.
TABELAS_PERMITIDAS_EXTRA_POR_TIPO: dict[str, frozenset[str]] = {
    'crm-vendas': frozenset({'crm_relatorio_comissao'}),
}


def prefixos_esperados_apps(apps_esperados: list[str]) -> list[str]:
    """Prefixos de table_name considerados válidos para o tipo da loja."""
    out: list[str] = []
    for app in apps_esperados:
        for p in prefixos_tabela_para_app(app):
            if p not in out:
                out.append(p)
    return out


def listar_tabelas_extras_no_schema(
    conn, schema_name: str, apps_esperados: list[str], *, tipo_slug: str = ''
) -> list[str]:
    """
    Tabelas no schema que não pertencem aos apps esperados do tipo da loja.
    Indica legado (ex.: cabeleireiro_* em loja clinica-beleza) — não invalida o OK.
    """
    prefixes = prefixos_esperados_apps(apps_esperados)
    permitidas = TABELAS_PERMITIDAS_EXTRA_POR_TIPO.get(tipo_slug, frozenset())
    extras: list[str] = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            [schema_name],
        )
        for (name,) in cur.fetchall():
            if name in TABELAS_DJANGO_PERMITIDAS or name in permitidas:
                continue
            if any(name.startswith(p) for p in prefixes):
                continue
            extras.append(name)
    return extras


def limpar_tabelas_extras_loja(loja) -> dict[str, Any]:
    """Remove tabelas legado/não esperadas do schema da loja."""
    from django.db import connections

    out: dict[str, Any] = {
        'loja_id': loja.id,
        'slug': loja.slug,
        'removidas': [],
        'sucesso': False,
        'mensagem': '',
    }
    if not loja.database_name or not loja.database_created:
        out['mensagem'] = 'Loja sem schema.'
        return out
    if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
        out['mensagem'] = 'Não foi possível conectar ao schema.'
        return out

    schema = loja.database_name.replace('-', '_')
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
    apps_esperados = get_apps_esperados_para_loja(loja)
    conn = connections[loja.database_name]
    extras = listar_tabelas_extras_no_schema(conn, schema, apps_esperados, tipo_slug=tipo_slug)
    if not extras:
        out['sucesso'] = True
        out['mensagem'] = 'Nenhuma tabela extra.'
        return out

    apps_removidos: set[str] = set()
    for table in extras:
        if table.startswith('cabeleireiro_'):
            apps_removidos.add('cabeleireiro')
        elif table.startswith('asaas_'):
            apps_removidos.add('asaas_integration')
        elif table.startswith('clinica_beleza_'):
            apps_removidos.add('clinica_beleza')
        elif table.startswith('clinica_'):
            apps_removidos.add('clinica_estetica')
        elif table.startswith('crm_vendas_') or table == 'crm_relatorio_comissao':
            apps_removidos.add('crm_vendas')
        elif table.startswith('whatsapp_'):
            apps_removidos.add('whatsapp')
        elif table == 'django_admin_log':
            apps_removidos.add('admin')

    try:
        with conn.cursor() as cur:
            cur.execute('SET search_path TO %s, public', [schema])
            for table in extras:
                cur.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
            for app in sorted(apps_removidos):
                cur.execute('DELETE FROM django_migrations WHERE app = %s', [app])
        out['removidas'] = extras
        out['sucesso'] = True
        out['mensagem'] = f'{len(extras)} tabela(s) legado removida(s).'
        logger.info('limpar_tabelas_extras loja=%s removidas=%s', loja.slug, extras)
    except Exception as exc:
        logger.exception('limpar_tabelas_extras loja=%s', loja.slug)
        out['mensagem'] = str(exc)
    return out


def tabela_existe_no_schema(conn, schema_name: str, table_name: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s AND table_type = 'BASE TABLE'
            """,
            [schema_name, table_name],
        )
        return cur.fetchone() is not None


def contar_tabelas_app_no_schema(conn, schema_name: str, app_label: str) -> int:
    """Quantas tabelas do app existem no schema (por prefixo(s) real(is))."""
    prefixes = prefixos_tabela_para_app(app_label)
    or_parts = ' OR '.join(['table_name LIKE %s'] * len(prefixes))
    params: list[Any] = [schema_name] + [p + '%' for p in prefixes]
    with conn.cursor() as cur:
        cur.execute(
            f"""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
              AND ({or_parts})
            """,
            params,
        )
        return cur.fetchone()[0]


def _usando_postgresql() -> bool:
    eng = (settings.DATABASES.get('default') or {}).get('ENGINE', '')
    return 'postgresql' in eng


def auditar_loja(loja) -> dict[str, Any]:
    """
    Retorna dict com status do schema e de cada app esperado para o tipo da loja.
    """
    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip() or 'unknown'
    nome_tipo = loja.tipo_loja.nome if loja.tipo_loja else '—'
    schema_name = (loja.database_name or '').replace('-', '_')
    apps_esperados = get_apps_esperados_para_loja(loja)

    base: dict[str, Any] = {
        'loja_id': loja.id,
        'slug': loja.slug,
        'nome': loja.nome,
        'database_name': loja.database_name,
        'database_created': bool(loja.database_created),
        'tipo_slug': tipo_slug,
        'tipo_nome': nome_tipo,
        'schema_nome': schema_name,
        'tipo_mapeado': tipo_slug in TIPO_LOJA_EXTRA_APPS or tipo_slug == 'unknown',
        'apps_esperados': apps_esperados,
        'schema_existe': None,
        'conexao_ok': False,
        'tabelas_total': 0,
        'tabelas_negocio': 0,
        'tabelas_extras': [],
        'tabelas_extras_count': 0,
        'apps_detalhe': [],
        'tabelas_faltando': [],
        'ok': False,
        'erro': None,
    }

    if not loja.database_name:
        base['erro'] = 'database_name vazio'
        return base

    if not _usando_postgresql():
        base['erro'] = 'Ambiente não usa PostgreSQL no default; schema por loja não se aplica.'
        return base

    if not os.environ.get('DATABASE_URL'):
        base['erro'] = 'DATABASE_URL não configurada.'
        return base

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                [schema_name],
            )
            base['schema_existe'] = cursor.fetchone() is not None
    except Exception as e:
        base['erro'] = f'Erro ao verificar schema: {e}'
        return base

    if not base['schema_existe']:
        base['erro'] = f'Schema "{schema_name}" não existe.'
        return base

    if not ensure_loja_database_config(loja.database_name, conn_max_age=0):
        base['erro'] = f'Não foi possível configurar conexão para "{loja.database_name}".'
        return base

    conn = connections[loja.database_name]
    try:
        conn.ensure_connection()
        base['conexao_ok'] = True
    except Exception as e:
        base['erro'] = f'Erro ao conectar: {e}'
        return base

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            """,
            [schema_name],
        )
        base['tabelas_total'] = cur.fetchone()[0]
        cur.execute(
            """
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
              AND table_name NOT LIKE 'django_%%'
            """,
            [schema_name],
        )
        base['tabelas_negocio'] = cur.fetchone()[0]

    if base['tabelas_negocio'] == 0:
        base['erro'] = 'Nenhuma tabela de negócio no schema.'
        return base

    tudo_ok = True
    # Apps de infraestrutura Django que não criam tabelas com prefixo próprio nos schemas tenant
    APPS_INFRA_SKIP_TABELA = {'contenttypes', 'auth'}

    for app in apps_esperados:
        # Pular verificação de tabela para apps de infra (só verificar migration)
        if app in APPS_INFRA_SKIP_TABELA:
            with conn.cursor() as cur:
                cur.execute('SET search_path TO %s, public', [schema_name])
                cur.execute(
                    'SELECT COUNT(*) FROM django_migrations WHERE app = %s',
                    [app],
                )
                n_mig = cur.fetchone()[0]
            ok_app = n_mig > 0
            if not ok_app:
                tudo_ok = False
            base['apps_detalhe'].append(
                {
                    'app': app,
                    'prefixos_tabela': [],
                    'tabelas_prefixo': 0,
                    'migrations_registradas': n_mig,
                    'ok': ok_app,
                    'infra': True,
                }
            )
            continue

        pfx_list = prefixos_tabela_para_app(app)
        n_tab = contar_tabelas_app_no_schema(conn, schema_name, app)
        with conn.cursor() as cur:
            cur.execute('SET search_path TO %s, public', [schema_name])
            cur.execute(
                'SELECT COUNT(*) FROM django_migrations WHERE app = %s',
                [app],
            )
            n_mig = cur.fetchone()[0]

        ok_app = n_tab > 0 and n_mig > 0
        if not ok_app:
            tudo_ok = False
        base['apps_detalhe'].append(
            {
                'app': app,
                'prefixos_tabela': pfx_list,
                'tabelas_prefixo': n_tab,
                'migrations_registradas': n_mig,
                'ok': ok_app,
            }
        )

    tabelas_obrigatorias = TABELAS_OBRIGATORIAS_POR_TIPO.get(tipo_slug, [])
    tabelas_faltando = [
        tbl
        for tbl in tabelas_obrigatorias
        if not tabela_existe_no_schema(conn, schema_name, tbl)
    ]
    base['tabelas_faltando'] = tabelas_faltando
    if tabelas_faltando:
        tudo_ok = False
        faltando_txt = ', '.join(tabelas_faltando)
        base['erro'] = base.get('erro') or f'Tabelas obrigatórias faltando: {faltando_txt}'

    base['ok'] = tudo_ok

    extras = listar_tabelas_extras_no_schema(conn, schema_name, apps_esperados, tipo_slug=tipo_slug)
    base['tabelas_extras'] = extras
    base['tabelas_extras_count'] = len(extras)
    if extras:
        amostra = ', '.join(extras[:5])
        sufixo = f' (+{len(extras) - 5} mais)' if len(extras) > 5 else ''
        base['aviso_tabelas_extras'] = (
            f'{len(extras)} tabela(s) legado/não esperada(s) para {tipo_slug}: '
            f'{amostra}{sufixo}'
        )

    if loja.database_name in connections:
        try:
            connections[loja.database_name].close()
        except Exception:
            pass

    return base


def _loja_identificador_ensure(loja) -> str:
    return (loja.slug or getattr(loja, 'atalho', None) or '').strip()


def _aplicar_ensure_comandos_por_tipo(loja) -> list[str]:
    """Executa ensure_* do tipo da loja (idempotente). Retorna mensagens de erro."""
    from django.core.management import call_command

    tipo_slug = (loja.tipo_loja.slug if loja.tipo_loja else '').strip()
    comandos = ENSURE_COMANDOS_POR_TIPO.get(tipo_slug, [])
    if not comandos:
        return []

    slug = _loja_identificador_ensure(loja)
    erros: list[str] = []
    for cmd in comandos:
        try:
            if slug:
                call_command(cmd, slug=slug)
            else:
                call_command(cmd)
        except Exception as e:
            logger.warning('ensure %s loja %s: %s', cmd, slug or loja.id, e)
            erros.append(f'{cmd}: {e}')
    return erros


def corrigir_loja(loja) -> dict[str, Any]:
    """
    Garante schema, aplica migrations e comandos ensure_* do tipo da loja.
    """
    out: dict[str, Any] = {'loja_id': loja.id, 'slug': loja.slug, 'sucesso': False, 'mensagem': ''}
    if not _usando_postgresql() or not os.environ.get('DATABASE_URL'):
        out['mensagem'] = 'PostgreSQL/DATABASE_URL necessários.'
        return out
    try:
        schema_name = loja.database_name.replace('-', '_')
        if not DatabaseSchemaService.verificar_schema_existe(schema_name):
            DatabaseSchemaService.criar_schema(loja)
            out['mensagem'] = 'Schema criado. '
        if not loja.database_created:
            loja.database_created = True
            loja.save(update_fields=['database_created'])
        ok_mig = DatabaseSchemaService.aplicar_migrations(loja)
        if ok_mig:
            out['mensagem'] += 'Migrations aplicadas. '
        else:
            out['mensagem'] += 'Falha parcial ao aplicar migrations. '

        ensure_erros = _aplicar_ensure_comandos_por_tipo(loja)
        if ensure_erros:
            out['mensagem'] += 'Ensure: ' + '; '.join(ensure_erros)
        elif ENSURE_COMANDOS_POR_TIPO.get((loja.tipo_loja.slug if loja.tipo_loja else '').strip()):
            out['mensagem'] += 'Ensure commands executados.'

        limpeza = limpar_tabelas_extras_loja(loja)
        if limpeza.get('removidas'):
            out['mensagem'] += ' ' + limpeza['mensagem']

        out['sucesso'] = bool(ok_mig) and not ensure_erros
    except Exception as e:
        logger.exception('corrigir_loja')
        out['mensagem'] = str(e)
    return out


def auditar_e_opcionalmente_corrigir(
    lojas,
    aplicar_correcao: bool,
) -> dict[str, Any]:
    """
    lojas: queryset ou lista de Loja.
    """
    if not _usando_postgresql():
        return {
            'postgresql': False,
            'mensagem': 'Auditoria de schema por loja requer PostgreSQL (ex.: Heroku).',
            'resultados': [],
            'resumo': {'total': 0, 'ok': 0, 'falhas': 0, 'corrigidos': 0},
        }

    resultados: list[dict[str, Any]] = []
    resumo = {'total': 0, 'ok': 0, 'falhas': 0, 'corrigidos': 0}

    # Adicionar schemas especiais (public/default e suporte) no início
    schemas_especiais = [
        {
            'schema_nome': 'public',
            'slug': 'default',
            'nome': 'Schema Público (Default)',
            'tipo_nome': 'Sistema',
            'tipo_slug': 'sistema',
            'especial': True,
        },
        {
            'schema_nome': 'suporte',
            'slug': 'suporte',
            'nome': 'Schema de Suporte',
            'tipo_nome': 'Suporte',
            'tipo_slug': 'suporte',
            'especial': True,
        },
    ]

    for schema_esp in schemas_especiais:
        resumo['total'] += 1
        audit = {
            'loja_id': None,
            'slug': schema_esp['slug'],
            'nome': schema_esp['nome'],
            'database_name': schema_esp['schema_nome'],
            'database_created': True,
            'tipo_slug': schema_esp['tipo_slug'],
            'tipo_nome': schema_esp['tipo_nome'],
            'schema_nome': schema_esp['schema_nome'],
            'tipo_mapeado': True,
            'apps_esperados': [],
            'schema_existe': None,
            'conexao_ok': False,
            'tabelas_total': 0,
            'tabelas_negocio': 0,
            'apps_detalhe': [],
            'ok': False,
            'erro': None,
            'especial': True,
        }

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                    [schema_esp['schema_nome']],
                )
                audit['schema_existe'] = cursor.fetchone() is not None

            if audit['schema_existe']:
                audit['conexao_ok'] = True
                with connection.cursor() as cur:
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                        """,
                        [schema_esp['schema_nome']],
                    )
                    audit['tabelas_total'] = cur.fetchone()[0]
                    cur.execute(
                        """
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_schema = %s AND table_type = 'BASE TABLE'
                          AND table_name NOT LIKE 'django_%%'
                        """,
                        [schema_esp['schema_nome']],
                    )
                    audit['tabelas_negocio'] = cur.fetchone()[0]

                audit['ok'] = audit['tabelas_total'] > 0
            else:
                audit['erro'] = f'Schema "{schema_esp["schema_nome"]}" não existe.'

        except Exception as e:
            audit['erro'] = f'Erro ao verificar schema: {e}'

        # Aplicar correção se solicitado e schema não existe
        correcao: dict[str, Any] | None = None
        audit_pos: dict[str, Any] | None = None
        ok_final = bool(audit.get('ok'))

        if aplicar_correcao and not ok_final and not audit['schema_existe']:
            # Criar schema especial se não existir
            correcao = {
                'slug': schema_esp['slug'],
                'sucesso': False,
                'mensagem': '',
            }
            try:
                with connection.cursor() as cursor:
                    cursor.execute(f'CREATE SCHEMA IF NOT EXISTS {schema_esp["schema_nome"]}')
                    logger.info(f'Schema {schema_esp["schema_nome"]} criado com sucesso.')
                correcao['sucesso'] = True
                correcao['mensagem'] = f'Schema {schema_esp["schema_nome"]} criado.'
                resumo['corrigidos'] += 1

                # Re-auditar após correção
                audit_pos = audit.copy()
                with connection.cursor() as cursor:
                    cursor.execute(
                        'SELECT 1 FROM information_schema.schemata WHERE schema_name = %s',
                        [schema_esp['schema_nome']],
                    )
                    audit_pos['schema_existe'] = cursor.fetchone() is not None
                    audit_pos['ok'] = audit_pos['schema_existe']
                    audit_pos['erro'] = None if audit_pos['schema_existe'] else audit_pos['erro']
                ok_final = bool(audit_pos.get('ok'))
            except Exception as e:
                logger.exception(f'Erro ao criar schema {schema_esp["schema_nome"]}')
                correcao['mensagem'] = f'Erro ao criar schema: {e}'

        resultados.append({
            'audit': audit,
            'correcao': correcao,
            'audit_pos': audit_pos,
            'ok_final': ok_final,
        })

        if ok_final:
            resumo['ok'] += 1
        else:
            resumo['falhas'] += 1

    # Processar lojas normais
    for loja in lojas:
        resumo['total'] += 1
        audit = auditar_loja(loja)
        correcao: dict[str, Any] | None = None
        audit_pos: dict[str, Any] | None = None
        ok_final = bool(audit.get('ok'))

        if aplicar_correcao:
            if not ok_final:
                correcao = corrigir_loja(loja)
                if correcao.get('sucesso'):
                    resumo['corrigidos'] += 1
                audit_pos = auditar_loja(loja)
                ok_final = bool(audit_pos.get('ok'))
            elif audit.get('tabelas_extras_count', 0) > 0:
                correcao = limpar_tabelas_extras_loja(loja)
                if correcao.get('sucesso') and correcao.get('removidas'):
                    resumo['corrigidos'] += 1
                audit_pos = auditar_loja(loja)
                ok_final = bool(audit_pos.get('ok'))

        resultados.append(
            {
                'audit': audit,
                'correcao': correcao,
                'audit_pos': audit_pos,
                'ok_final': ok_final,
            }
        )
        if ok_final:
            resumo['ok'] += 1
        else:
            resumo['falhas'] += 1

    return {
        'postgresql': True,
        'resultados': resultados,
        'resumo': resumo,
    }
