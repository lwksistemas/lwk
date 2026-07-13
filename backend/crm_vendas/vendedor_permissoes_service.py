"""Permissões granulares de vendedores CRM (grupos Django + checkboxes)."""
from __future__ import annotations

import contextlib

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

CRM_GROUP_NAMES = ['Gerente de Vendas', 'Vendedor']

# model (crm_vendas ou superadmin) -> categoria exibida no frontend
CRM_MODEL_CATEGORIAS: dict[tuple[str, str], str] = {
    ('crm_vendas', 'lead'): 'Leads e contas',
    ('crm_vendas', 'conta'): 'Leads e contas',
    ('crm_vendas', 'contato'): 'Leads e contas',
    ('crm_vendas', 'oportunidade'): 'Oportunidades',
    ('crm_vendas', 'oportunidadeitem'): 'Oportunidades',
    ('crm_vendas', 'atividade'): 'Atividades',
    ('crm_vendas', 'proposta'): 'Propostas e contratos',
    ('crm_vendas', 'contrato'): 'Propostas e contratos',
    ('crm_vendas', 'propostatemplate'): 'Propostas e contratos',
    ('crm_vendas', 'contratotemplate'): 'Propostas e contratos',
    ('crm_vendas', 'produtoservico'): 'Produtos e serviços',
    ('crm_vendas', 'categoriaprodutoservico'): 'Produtos e serviços',
    ('crm_vendas', 'crmconfig'): 'Configurações',
    ('superadmin', 'vendedor'): 'Equipe',
    ('superadmin', 'funcionario'): 'Equipe',
}

ACAO_LABELS = {
    'view': 'Visualizar',
    'add': 'Criar',
    'change': 'Editar',
    'delete': 'Excluir',
}


def _format_permission_name(model_label: str, codename: str) -> str:
    acao = codename.split('_', 1)[0] if '_' in codename else codename
    acao_label = ACAO_LABELS.get(acao, acao.capitalize())
    return f'{acao_label} {model_label}'


def _model_label(model: str) -> str:
    labels = {
        'lead': 'leads',
        'conta': 'contas',
        'contato': 'contatos',
        'oportunidade': 'oportunidades',
        'oportunidadeitem': 'itens de oportunidade',
        'atividade': 'atividades',
        'proposta': 'propostas',
        'contrato': 'contratos',
        'propostatemplate': 'templates de proposta',
        'contratotemplate': 'templates de contrato',
        'produtoservico': 'produtos/serviços',
        'categoriaprodutoservico': 'categorias',
        'crmconfig': 'configurações CRM',
        'vendedor': 'vendedores',
        'funcionario': 'funcionários',
    }
    return labels.get(model, model.replace('_', ' '))


def obter_queryset_permissoes_crm():
    filtros = []
    for app_label, model in CRM_MODEL_CATEGORIAS:
        filtros.append((app_label, model))
    q = Permission.objects.none()
    for app_label, model in filtros:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            continue
        q = q | Permission.objects.filter(content_type=ct)
    return q.select_related('content_type').order_by('content_type__model', 'codename')


def listar_permissoes_crm_disponiveis() -> list[dict]:
    """Retorna permissões agrupadas por categoria para o frontend."""
    por_categoria: dict[str, list[dict]] = {}
    for perm in obter_queryset_permissoes_crm():
        chave = (perm.content_type.app_label, perm.content_type.model)
        categoria = CRM_MODEL_CATEGORIAS.get(chave, 'Outros')
        nome = _format_permission_name(_model_label(perm.content_type.model), perm.codename)
        por_categoria.setdefault(categoria, []).append({
            'id': perm.id,
            'codename': perm.codename,
            'nome': nome,
        })

    ordem = [
        'Leads e contas',
        'Oportunidades',
        'Atividades',
        'Propostas e contratos',
        'Produtos e serviços',
        'Relatórios',
        'Configurações',
        'Equipe',
        'Outros',
    ]
    resultado = []
    for cat in ordem:
        if cat in por_categoria:
            resultado.append({'categoria': cat, 'permissoes': por_categoria.pop(cat)})
    for cat, perms in sorted(por_categoria.items()):
        resultado.append({'categoria': cat, 'permissoes': perms})
    return resultado


def permissoes_ids_grupo(grupo_id: int | None) -> list[int]:
    if not grupo_id:
        return []
    try:
        grupo = Group.objects.using('default').get(id=grupo_id, name__in=CRM_GROUP_NAMES)
    except Group.DoesNotExist:
        return []
    crm_ids = set(obter_queryset_permissoes_crm().values_list('id', flat=True))
    return list(grupo.permissions.filter(id__in=crm_ids).values_list('id', flat=True))


def normalizar_config_acesso(config: dict | None) -> dict:
    cfg = dict(config or {})
    grupo_id = cfg.get('grupo_id')
    permissoes_ids = cfg.get('permissoes_ids') or []
    try:
        grupo_id = int(grupo_id) if grupo_id is not None else None
    except (TypeError, ValueError):
        grupo_id = None
    ids_norm = []
    for pid in permissoes_ids:
        try:
            ids_norm.append(int(pid))
        except (TypeError, ValueError):
            continue
    return {'grupo_id': grupo_id, 'permissoes_ids': ids_norm}


def aplicar_permissoes_usuario_crm(user, grupo_id: int | None, permissoes_ids: list[int]) -> None:
    """Aplica grupo (metadado) e permissões diretas exatas ao usuário."""
    crm_qs = obter_queryset_permissoes_crm()
    crm_ids = set(crm_qs.values_list('id', flat=True))
    selected = [pid for pid in permissoes_ids if pid in crm_ids]

    user.groups.remove(*Group.objects.using('default').filter(name__in=CRM_GROUP_NAMES))
    if grupo_id:
        with contextlib.suppress(Group.DoesNotExist):
            user.groups.add(Group.objects.using('default').get(id=grupo_id, name__in=CRM_GROUP_NAMES))

    atuais = user.user_permissions.filter(id__in=crm_ids)
    user.user_permissions.remove(*atuais)
    if selected:
        user.user_permissions.add(*Permission.objects.filter(id__in=selected))


def permissoes_codenames_usuario_crm(user) -> list[str]:
    """Codenames Django efetivos (diretas + via grupo) no escopo CRM."""
    crm_ids = set(obter_queryset_permissoes_crm().values_list('id', flat=True))
    codenames: set[str] = set()
    for codename in user.user_permissions.filter(id__in=crm_ids).values_list('codename', flat=True):
        codenames.add(codename)
    for codename in Permission.objects.filter(group__user=user, id__in=crm_ids).values_list(
        'codename', flat=True
    ):
        codenames.add(codename)
    return sorted(codenames)


def todas_permissoes_codenames_crm() -> list[str]:
    return sorted(obter_queryset_permissoes_crm().values_list('codename', flat=True))


def _map_drf_action_para_permissao(action: str) -> str:
    if action in ('list', 'retrieve'):
        return 'view'
    if action == 'create':
        return 'add'
    if action in ('update', 'partial_update', 'destroy'):
        return 'change' if action != 'destroy' else 'delete'
    return 'change'


def verificar_permissao_crm_action(request, model: str, action: str):
    """Retorna Response 403 ou None se permitido."""
    from rest_framework import status as http_status
    from rest_framework.response import Response

    from .utils import is_owner

    if is_owner(request):
        return None

    user = request.user
    codenames = permissoes_codenames_usuario_crm(user)
    if not codenames:
        return None

    acao = _map_drf_action_para_permissao(action)
    needed = f'{acao}_{model}'
    for app_label in ('crm_vendas', 'superadmin'):
        if user.has_perm(f'{app_label}.{needed}'):
            return None

    return Response(
        {'detail': 'Você não tem permissão para esta ação.'},
        status=http_status.HTTP_403_FORBIDDEN,
    )


def permissoes_ids_usuario_crm(user) -> list[int]:
    crm_qs = obter_queryset_permissoes_crm()
    crm_ids = set(crm_qs.values_list('id', flat=True))
    diretas = set(user.user_permissions.filter(id__in=crm_ids).values_list('id', flat=True))
    if diretas:
        return sorted(diretas)
    via_grupo = set(
        Permission.objects.filter(group__user=user, id__in=crm_ids).values_list('id', flat=True)
    )
    return sorted(via_grupo)


def listar_grupos_crm_com_permissoes() -> list[dict]:
    grupos = []
    for row in Group.objects.using('default').filter(name__in=CRM_GROUP_NAMES).values('id', 'name').order_by('name'):
        grupos.append({
            **row,
            'permissoes_ids': permissoes_ids_grupo(row['id']),
        })
    return grupos
