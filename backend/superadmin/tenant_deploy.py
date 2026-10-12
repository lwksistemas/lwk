"""Filtro de apps/ensures para migrate e deploy pontual por módulo.

Uso típico (bug na agenda da clínica, sem mexer em CRM/Felix):

    python manage.py migrate_all_lojas --apps clinica_beleza
    python manage.py ensure_all --apps clinica_beleza

Ou o atalho:

    python manage.py deploy_app clinica_beleza
"""
from __future__ import annotations

from superadmin.services.database_schema_service import get_apps_esperados_para_loja

# Ensures ligados a um app Django. Com --apps, só estes rodam.
ENSURE_POR_APP: dict[str, tuple[str, ...]] = {
    "clinica_beleza": (
        "ensure_clinica_beleza_consultas",
        "ensure_appointment_duracao_minutos",
        "ensure_professional_nascimento_sexo",
        "ensure_professional_tempo_consulta",
        "ensure_memed_timbrado_table",
        "ensure_memed_prescricao_table",
        "ensure_professional_memed_fields",
        "ensure_professional_commission_local",
        "ensure_professional_commission_convenio",
        "ensure_convenio_tables",
        "ensure_nomes_agenda_table",
        "ensure_retorno_gratuito_tables",
        "ensure_protocolo_comercial",
        "ensure_appointment_local_atendimento",
        "ensure_local_tempo_consulta",
        "ensure_local_nomeagenda_is_padrao",
        "normalizar_status_agenda",
        "ensure_estoque_produto_fields",
        "ensure_categoria_estoque",
        "ensure_despesas_tables",
        "ensure_orcamento_tables",
        "ensure_document_templates_tables",
        "ensure_termo_consentimento",
        "ensure_procedimentos_catalogo",
        "ensure_paciente_fotos_table",
        "ensure_patient_foto_url",
        "ensure_payment_draft_nao_finalizadas",
        "ensure_consulta_numero",
        "ensure_auto_finalizar_consultas_schedule",
    ),
    "crm_vendas": (
        "ensure_relatorio_comissao_table",
        "ensure_crm_config_colunas",
        "ensure_crm_atividade_colunas",
        "ensure_crm_financeiro_tabelas",
        "ensure_crm_emitente_documento_colunas",
        "ensure_crm_negociacao_historico",
        "ensure_canal_assinatura_vendedor",
        "ensure_vendedor_config_acesso",
        "ensure_assinatura_link_enviado_em",
    ),
    "whatsapp": ("ensure_whatsapp_evolution_fields",),
    "nfse_integration": ("ensure_nfse_tenant_clinica_beleza",),
    "suporte": ("ensure_suporte_schema",),
}

# Só no deploy completo (sem --apps).
ENSURES_SO_DEPLOY_COMPLETO: tuple[str, ...] = (
    "ensure_financeiro_lojas",
    "verificar_storage_lojas",
    "setup_security_schedules",
)

FIX_COLUMNS_CRM: tuple[str, ...] = (
    "fix_google_event_id_column",
    "fix_duracao_minutos_column",
    "fix_vendedor_column",
)


def parse_apps_option(values: list[str] | None) -> list[str]:
    """Aceita --apps clinica_beleza,whatsapp ou várias flags --apps."""
    if not values:
        return []
    out: list[str] = []
    for raw in values:
        for part in (raw or "").split(","):
            name = part.strip()
            if name and name not in out:
                out.append(name)
    return out


def slugs_tipo_que_usam_app(app_label: str) -> list[str]:
    """Slugs de TipoLoja que têm este app. Hotel não entra no CRM."""
    from superadmin.services.database_schema_service import TIPO_LOJA_EXTRA_APPS

    return [slug for slug, apps in TIPO_LOJA_EXTRA_APPS.items() if app_label in apps]


def slugs_tipo_que_usam_algum(app_labels: list[str]) -> list[str]:
    from superadmin.services.database_schema_service import TIPO_LOJA_EXTRA_APPS

    wanted = set(app_labels)
    return [slug for slug, apps in TIPO_LOJA_EXTRA_APPS.items() if wanted.intersection(apps)]


def queryset_lojas_do_app(app_label: str):
    """Lojas ativas com banco, só dos tipos que usam o app. Não abre as outras."""
    from superadmin.models import Loja

    return (
        Loja.objects.using("default")
        .filter(
            is_active=True,
            database_created=True,
            tipo_loja__slug__in=slugs_tipo_que_usam_app(app_label),
        )
        .select_related("tipo_loja")
    )


def filtrar_apps_loja(loja, filtro_apps: list[str] | None) -> list[str]:
    """Apps a migrar nesta loja. Vazio = esta loja não usa o app pedido (não cria tabela)."""
    esperados = get_apps_esperados_para_loja(loja)
    if not filtro_apps:
        return list(esperados)
    wanted = set(filtro_apps)
    return [app for app in esperados if app in wanted]


def ensures_para_apps(filtro_apps: list[str] | None, all_ensures: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """Filtra a lista ENSURES do ensure_all pelo(s) app(s). Sem filtro = lista original."""
    if not filtro_apps:
        return list(all_ensures)
    allowed: set[str] = set()
    for app in filtro_apps:
        allowed.update(ENSURE_POR_APP.get(app, ()))
    return [(name, kwargs) for name, kwargs in all_ensures if name in allowed]


def deve_rodar_fix_colunas_crm(filtro_apps: list[str] | None) -> bool:
    if not filtro_apps:
        return True
    return "crm_vendas" in filtro_apps
