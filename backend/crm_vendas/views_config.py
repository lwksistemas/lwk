"""
Views de configuração, busca global, dashboard e utilitários do CRM.
Extraído de views.py para melhor organização.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache

from tenants.middleware import get_current_loja_id, get_current_tenant_db, ensure_loja_context
from .utils import get_current_vendedor_id, get_loja_from_context
from .mixins import CRMPermissionMixin
from .cache import CRMCacheManager
from .decorators import require_admin_access

logger = logging.getLogger(__name__)


def _get_crm_config_for_loja(loja_id: int):
    """
    Obtém CRMConfig. Se faltar coluna, aplica patch SQL no tenant.
    """
    from django.db.utils import ProgrammingError
    from .models import CRMConfig

    try:
        return CRMConfig.get_or_create_for_loja(loja_id)
    except ProgrammingError as e:
        err = str(e).lower()
        if 'column' not in err or 'does not exist' not in err:
            raise
        db_name = get_current_tenant_db()
        if not db_name or db_name == 'default':
            raise
        logger.warning(
            'CRMConfig: colunas ausentes no tenant, aplicando patch em %s',
            db_name,
        )
        from .schema_service import patch_crm_vendas_asaas_columns_if_missing
        patch_crm_vendas_asaas_columns_if_missing(db_name)
        return CRMConfig.get_or_create_for_loja(loja_id)

def _empty_dashboard_response():
    """Resposta vazia padrão quando não há contexto de loja."""
    from .services_dashboard import empty_dashboard_response
    return empty_dashboard_response()


ETAPAS_PIPELINE = [
    'prospecting', 'qualification', 'proposal', 'negotiation', 'closed_won', 'closed_lost',
]

# Etapas em andamento (excluindo fechadas)
ETAPAS_EM_ANDAMENTO = [
    'prospecting', 'qualification', 'proposal', 'negotiation',
]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crm_me(request):
    """
    Retorna o contexto do usuário logado no CRM.
    Usado pelo frontend para obter vendedor_id quando o login não o retornou
    (ex: sessão antiga, refresh). Garante que vendedores sempre tenham vendedor_id
    ao criar oportunidades.
    Inclui user_display_name e user_role para exibir no menu (Nayara vs Felix).
    
    IMPORTANTE: Owner NUNCA é marcado como vendedor (is_vendedor=False), mesmo se vinculado.
    Apenas vendedores comuns (não-owners) são marcados como is_vendedor=True.
    """
    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({
            'vendedor_id': None,
            'is_vendedor': False,
            'user_display_name': None,
            'user_role': 'administrador',
        }, status=200)
    
    vendedor_id = get_current_vendedor_id(request)
    user_display_name = None
    user_role = 'administrador'
    is_vendedor = False
    
    try:
        from superadmin.models import Loja
        loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
        
        # Verificar se é proprietário da loja
        is_owner = loja and loja.owner_id == request.user.id
        
        if vendedor_id is not None:
            try:
                from .models import Vendedor as VendedorModel
                vendedor = VendedorModel.objects.filter(id=vendedor_id, loja_id=loja_id).first()
                user_display_name = vendedor.nome if vendedor else request.user.get_full_name() or request.user.username
            except Exception:
                user_display_name = request.user.get_full_name() or request.user.username
            # Owner NUNCA é marcado como vendedor, mesmo se vinculado
            if not is_owner:
                user_role = 'vendedor'
                is_vendedor = True
        
        if is_owner and loja:
            owner = loja.owner
            user_display_name = (owner.get_full_name() or owner.username or '').strip() or owner.username
            user_role = 'administrador'
            is_vendedor = False
            
    except Exception as e:
        logger.warning('crm_me: erro ao obter display_name: %s', e)
    
    return Response({
        'vendedor_id': vendedor_id,
        'is_vendedor': is_vendedor,
        'user_display_name': user_display_name,
        'user_role': user_role,
    }, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    """
    Dados do dashboard CRM. Lógica de negócio delegada para services_dashboard.
    """
    from .services_dashboard import build_dashboard_payload

    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    # Verificar se é owner
    from superadmin.models import Loja
    is_owner_flag = False
    try:
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            is_owner_flag = True
    except Exception:
        pass

    periodo = request.GET.get('periodo', 'mes_atual')
    data_inicio_param = request.GET.get('data_inicio')
    data_fim_param = request.GET.get('data_fim')
    vendedor_id_filtro = request.GET.get('vendedor_id')
    status_filtro = request.GET.get('status', 'todas')

    tem_filtros = (
        periodo != 'mes_atual' or data_inicio_param or data_fim_param
        or vendedor_id_filtro or status_filtro != 'todas'
    )
    vendedor_id = None if is_owner_flag else get_current_vendedor_id(request)

    # Cache
    cache_key = None
    if not tem_filtros:
        cache_key = CRMCacheManager.get_cache_key(CRMCacheManager.DASHBOARD, loja_id, vendedor_id)
        if cache_key:
            from django.core.cache import cache
            cached = cache.get(cache_key)
            if cached:
                return Response(cached)

    for attempt in range(2):
        try:
            payload = build_dashboard_payload(
                loja_id, vendedor_id, periodo, data_inicio_param,
                data_fim_param, vendedor_id_filtro, status_filtro, is_owner_flag,
            )
            if cache_key:
                from django.core.cache import cache
                cache.set(cache_key, payload, 120)
            return Response(payload)
        except Exception as e:
            from django.db.utils import ProgrammingError, OperationalError
            if isinstance(e, (ProgrammingError, OperationalError)) and attempt == 0:
                from .schema_service import configurar_schema_crm_loja
                loja_obj = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
                if loja_obj and configurar_schema_crm_loja(loja_obj):
                    continue
            logger.exception('Erro no dashboard CRM: %s', e)
            if isinstance(e, (ProgrammingError, OperationalError)):
                return Response(
                    {'detail': 'O banco de dados da loja precisa ser configurado.', 'code': 'SCHEMA_NOT_CONFIGURED'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(
                {'detail': 'Erro ao carregar dashboard. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class WhatsAppConfigView(CRMPermissionMixin, APIView):
    """
    Configuração WhatsApp da loja (reutiliza WhatsAppConfig da Clínica da Beleza).
    GET /crm-vendas/whatsapp-config/  → retorna flags
    PATCH /crm-vendas/whatsapp-config/ → atualiza flags
    """
    permission_classes = [IsAuthenticated]

    def _get_config(self, request=None):
        loja = get_loja_from_context(request)
        if not loja:
            logger.warning("WhatsAppConfigView: contexto de loja não encontrado")
            return None
        
        from whatsapp.models import WhatsAppConfig
        try:
            owner_tel = (getattr(loja, 'owner_telefone', None) or '').strip()
            config, created = WhatsAppConfig.objects.get_or_create(
                loja=loja,
                defaults={
                    'enviar_confirmacao': True,
                    'enviar_lembrete_24h': True,
                    'enviar_lembrete_2h': True,
                    'enviar_cobranca': True,
                    'enviar_lembrete_tarefas': True,
                    'whatsapp_numero': owner_tel or '',
                }
            )
            if not created and not (config.whatsapp_numero or '').strip() and owner_tel:
                config.whatsapp_numero = owner_tel
                config.save(update_fields=['whatsapp_numero', 'updated_at'])
            return config
        except Exception as e:
            logger.exception("WhatsAppConfigView._get_config erro: %s", e)
            return None

    def _serialize_config(self, config):
        """Serializa config para response (DRY — usado em get e patch)."""
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return {
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'enviar_lembrete_tarefas': getattr(config, 'enviar_lembrete_tarefas', True),
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (getattr(config, 'whatsapp_phone_id', None) or '').strip(),
            'whatsapp_token_set': bool((getattr(config, 'whatsapp_token', None) or '').strip()),
        }

    @require_admin_access()
    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(self._serialize_config(config))

    @require_admin_access()
    def patch(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        update_fields = ['updated_at']
        for key in ('enviar_confirmacao', 'enviar_lembrete_24h', 'enviar_lembrete_2h', 'enviar_cobranca', 'enviar_lembrete_tarefas'):
            if key in request.data:
                setattr(config, key, bool(request.data[key]))
                update_fields.append(key)
        if 'whatsapp_numero' in request.data:
            config.whatsapp_numero = (request.data.get('whatsapp_numero') or '').strip()[:20]
            update_fields.append('whatsapp_numero')
        if 'whatsapp_ativo' in request.data:
            config.whatsapp_ativo = bool(request.data['whatsapp_ativo'])
            update_fields.append('whatsapp_ativo')
        if 'whatsapp_phone_id' in request.data:
            config.whatsapp_phone_id = (request.data.get('whatsapp_phone_id') or '').strip()[:64]
            update_fields.append('whatsapp_phone_id')
        if 'whatsapp_token' in request.data:
            config.whatsapp_token = (request.data.get('whatsapp_token') or '').strip()[:512]
            update_fields.append('whatsapp_token')
        config.save(update_fields=update_fields)
        return Response(self._serialize_config(config))


class LoginConfigView(CRMPermissionMixin, APIView):
    """
    GET /crm-vendas/login-config/  → retorna logo, cor_primaria, cor_secundaria
    PATCH /crm-vendas/login-config/ → atualiza personalização da tela de login
    """
    permission_classes = [IsAuthenticated]

    @require_admin_access()
    def get(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        tipo = getattr(loja, 'tipo_loja', None)
        cor_default = getattr(tipo, 'cor_primaria', None) if tipo else None
        cor_primaria = (loja.cor_primaria or '').strip() or cor_default or '#10B981'
        cor_secundaria = (loja.cor_secundaria or '').strip() or '#059669'
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': cor_primaria,
            'cor_secundaria': cor_secundaria,
        })

    @require_admin_access()
    def patch(self, request):
        loja = get_loja_from_context(request)
        if loja is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Importar função de deleção do Cloudinary
        from superadmin.cloudinary_utils import delete_cloudinary_image
        
        update_fields = ['updated_at']
        loja_slug = loja.slug  # Slug da loja para validação de propriedade
        
        # Processar logo
        if 'logo' in request.data:
            val = (request.data.get('logo') or '').strip()
            old_logo = (loja.logo or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_logo and old_logo != val and 'cloudinary.com' in old_logo:
                delete_cloudinary_image(old_logo, loja_slug)
            
            loja.logo = val[:200] if val else ''
            update_fields.append('logo')
        
        # Processar login_background
        if 'login_background' in request.data:
            val = (request.data.get('login_background') or '').strip()
            old_background = (loja.login_background or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_background and old_background != val and 'cloudinary.com' in old_background:
                delete_cloudinary_image(old_background, loja_slug)
            
            loja.login_background = val[:200] if val else ''
            update_fields.append('login_background')
        
        # Processar login_logo
        if 'login_logo' in request.data:
            val = (request.data.get('login_logo') or '').strip()
            old_login_logo = (loja.login_logo or '').strip()
            
            # Se mudou e tinha uma imagem antiga, deletar do Cloudinary
            if old_login_logo and old_login_logo != val and 'cloudinary.com' in old_login_logo:
                delete_cloudinary_image(old_login_logo, loja_slug)
            
            loja.login_logo = val[:200] if val else ''
            update_fields.append('login_logo')
        
        # Processar cores
        if 'cor_primaria' in request.data:
            val = (request.data.get('cor_primaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_primaria = val[:7]
                update_fields.append('cor_primaria')
        if 'cor_secundaria' in request.data:
            val = (request.data.get('cor_secundaria') or '').strip()
            if val and val.startswith('#') and len(val) <= 7:
                loja.cor_secundaria = val[:7]
                update_fields.append('cor_secundaria')
        
        loja.save(update_fields=update_fields)
        
        # Limpar cache
        from django.core.cache import cache
        cache_key = f'loja_info_publica:{loja.slug}'
        cache.delete(cache_key)
        
        return Response({
            'logo': (loja.logo or '').strip(),
            'login_background': (loja.login_background or '').strip(),
            'login_logo': (loja.login_logo or '').strip(),
            'cor_primaria': loja.cor_primaria or '#10B981',
            'cor_secundaria': loja.cor_secundaria or '#059669',
        })



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def crm_busca(request):
    """
    Busca global no CRM: Leads, Oportunidades e Contas.
    GET /crm-vendas/busca/?q=termo&limit=5
    Respeita isolamento por loja e filtro por vendedor.
    """
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'leads': [], 'oportunidades': [], 'contas': []})

    q = (request.GET.get('q') or '').strip()
    if len(q) < 2:
        return Response({'leads': [], 'oportunidades': [], 'contas': []})

    limit = min(int(request.GET.get('limit', 5) or 5), 10)
    term = q
    # Versão só com dígitos para buscar CPF/CNPJ sem formatação
    term_digits = ''.join(c for c in q if c.isdigit())
    vendedor_id = get_current_vendedor_id(request)

    from .models import Lead, Oportunidade, Conta

    q_filter = (
        Q(nome__icontains=term) |
        Q(empresa__icontains=term) |
        Q(email__icontains=term) |
        Q(telefone__icontains=term) |
        Q(cpf_cnpj__icontains=term)
    )
    # Buscar CPF/CNPJ sem formatação (dígitos puros)
    if term_digits and len(term_digits) >= 3:
        q_filter |= Q(cpf_cnpj__icontains=term_digits)
    leads_qs = Lead.objects.filter(q_filter)
    if vendedor_id is not None:
        leads_qs = leads_qs.filter(
            Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id)
        ).distinct()
    leads_qs = list(leads_qs.values('id', 'nome', 'empresa', 'status', 'cpf_cnpj')[:limit])

    opp_filter = (
        Q(titulo__icontains=term) |
        Q(lead__nome__icontains=term) |
        Q(lead__empresa__icontains=term) |
        Q(lead__cpf_cnpj__icontains=term) |
        Q(lead__conta__nome__icontains=term) |
        Q(lead__conta__cnpj__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        opp_filter |= Q(lead__cpf_cnpj__icontains=term_digits)
        opp_filter |= Q(lead__conta__cnpj__icontains=term_digits)
    opp_qs = Oportunidade.objects.filter(opp_filter)
    if vendedor_id is not None:
        opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
    opp_qs = list(opp_qs.values('id', 'titulo', 'valor', 'etapa', 'lead__nome', 'lead__empresa')[:limit])

    conta_filter = (
        Q(nome__icontains=term) |
        Q(email__icontains=term) |
        Q(telefone__icontains=term) |
        Q(cnpj__icontains=term) |
        Q(razao_social__icontains=term)
    )
    if term_digits and len(term_digits) >= 3:
        conta_filter |= Q(cnpj__icontains=term_digits)
    contas_qs = Conta.objects.filter(conta_filter)
    if vendedor_id is not None:
        contas_qs = contas_qs.filter(vendedor_id=vendedor_id)
    contas_qs = list(contas_qs.values('id', 'nome', 'segmento', 'cnpj')[:limit])

    def lead_item(r):
        return {'id': r['id'], 'nome': r['nome'], 'empresa': r['empresa'] or '', 'status': r['status'], 'cpf_cnpj': r.get('cpf_cnpj') or ''}

    def opp_item(r):
        return {
            'id': r['id'],
            'titulo': r['titulo'],
            'valor': str(r['valor']),
            'etapa': r['etapa'],
            'lead_nome': r['lead__nome'] or '',
            'lead_empresa': r['lead__empresa'] or '',
        }

    def conta_item(r):
        return {'id': r['id'], 'nome': r['nome'], 'segmento': r['segmento'] or '', 'cnpj': r.get('cnpj') or ''}

    return Response({
        'leads': [lead_item(r) for r in leads_qs],
        'oportunidades': [opp_item(r) for r in opp_qs],
        'contas': [conta_item(r) for r in contas_qs],
    })


@api_view(['GET', 'PATCH'])
def crm_config(request):
    """
    GET: Retorna configurações do CRM da loja
    PATCH: Atualiza configurações do CRM (personalizar: origens, etapas, colunas, módulos)
    Admin e vendedores podem acessar e personalizar.
    """
    from .models import CRMConfig
    from .serializers import CRMConfigSerializer
    
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)
    
    # Buscar ou criar configuração (com auto-recovery se schema não configurado)
    try:
        config = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        from django.db.utils import ProgrammingError, OperationalError
        if isinstance(e, (ProgrammingError, OperationalError)):
            # Auto-recovery: tentar configurar schema e retry
            from superadmin.models import Loja
            from .schema_service import configurar_schema_crm_loja
            loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
            if loja and configurar_schema_crm_loja(loja):
                try:
                    config = _get_crm_config_for_loja(loja_id)
                except Exception as retry_err:
                    logger.exception('Erro ao buscar config CRM após recovery: %s', retry_err)
                    return Response(
                        {
                            'detail': 'O banco de dados da loja precisa ser configurado. Entre em contato com o suporte.',
                            'code': 'SCHEMA_NOT_CONFIGURED',
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                logger.exception('Erro ao buscar config CRM (recovery falhou): %s', e)
                return Response(
                    {
                        'detail': 'O banco de dados da loja precisa ser configurado. Entre em contato com o suporte.',
                        'code': 'SCHEMA_NOT_CONFIGURED',
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            logger.exception('Erro ao buscar config CRM: %s', e)
            raise
    
    if request.method == 'GET':
        serializer = CRMConfigSerializer(config)
        return Response(serializer.data)
    
    elif request.method == 'PATCH':
        serializer = CRMConfigSerializer(config, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # Invalidar cache do dashboard quando configurações mudarem
            CRMCacheManager.invalidate_dashboard(loja_id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crm_config_asaas_test(request):
    """
    Testa a comunicação com a API Asaas usando a chave da loja (NFS-e).

    Body JSON (opcional):
      - api_key: se omitido ou vazio, usa a chave já salva em CRMConfig
      - asaas_sandbox: se omitido, usa o valor salvo na config
    """
    from .models import CRMConfig

    try:
        from asaas_integration.client import AsaasClient
    except ImportError:
        return Response(
            {'success': False, 'detail': 'Cliente Asaas indisponível no servidor.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'success': False, 'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cfg = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        logger.exception('crm_config_asaas_test: config')
        return Response(
            {'success': False, 'detail': f'Erro ao carregar configuração: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    body = request.data if isinstance(request.data, dict) else {}
    api_key = (body.get('api_key') or '').strip()
    if not api_key:
        api_key = (getattr(cfg, 'asaas_api_key', None) or '').strip()

    if body.get('asaas_sandbox') is None:
        sandbox = bool(getattr(cfg, 'asaas_sandbox', False))
    else:
        sb = body.get('asaas_sandbox')
        sandbox = bool(sb) if isinstance(sb, bool) else str(sb).lower() in ('true', '1', 'yes', 'on')

    if not api_key:
        return Response(
            {
                'success': False,
                'detail': 'Informe a API Key acima ou salve uma chave antes de testar.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = AsaasClient(api_key=api_key, sandbox=sandbox)
        client._make_request('GET', 'customers?limit=1')
        environment = 'sandbox (homologação)' if sandbox else 'produção'
        return Response(
            {
                'success': True,
                'message': f'Conexão com o Asaas OK ({environment}).',
                'environment': environment,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.warning('crm_config_asaas_test falhou: %s', e)
        err = str(e)
        if len(err) > 500:
            err = err[:500] + '…'
        return Response(
            {'success': False, 'detail': err or 'Falha ao contactar a API do Asaas.'},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crm_config_issnet_test(request):
    """
    Testa certificado PFX e acesso ao WSDL do ISSNet (Ribeirão Preto), sem emitir NF.

    Body JSON ou multipart/form-data:
      - issnet_usuario, issnet_senha, issnet_senha_certificado (opcionais se já salvos)
      - issnet_certificado: arquivo .pfx (opcional se já salvo)
      - homologacao / issnet_homologacao: true/false (produção = false; padrão false)
    """
    import os
    import tempfile

    from nfse_integration.issnet_client import testar_conexao_issnet

    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'success': False, 'detail': 'Loja não identificada.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        cfg = _get_crm_config_for_loja(loja_id)
    except Exception as e:
        logger.exception('crm_config_issnet_test: config')
        return Response(
            {'success': False, 'detail': f'Erro ao carregar configuração: {e}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    body = request.data

    def _parse_bool(val):
        if val is None:
            return False
        if isinstance(val, bool):
            return val
        return str(val).lower() in ('true', '1', 'yes', 'on')

    homologacao = _parse_bool(body.get('homologacao') or body.get('issnet_homologacao'))

    usuario = (body.get('issnet_usuario') or '').strip() or (getattr(cfg, 'issnet_usuario', None) or '').strip()
    senha = (body.get('issnet_senha') or '').strip() or (getattr(cfg, 'issnet_senha', None) or '').strip()
    senha_cert = (body.get('issnet_senha_certificado') or '').strip() or (
        getattr(cfg, 'issnet_senha_certificado', None) or ''
    ).strip()

    cert_path = None
    cleanup_cert = False
    upload = request.FILES.get('issnet_certificado') if hasattr(request, 'FILES') else None
    if upload:
        # Validação de tamanho (máx 5MB) e extensão
        max_size = 5 * 1024 * 1024  # 5MB
        if upload.size > max_size:
            return Response(
                {'success': False, 'detail': 'Certificado muito grande. Tamanho máximo: 5MB.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ext = os.path.splitext(getattr(upload, 'name', '') or '')[1].lower()
        if ext not in ('.pfx', '.p12'):
            return Response(
                {'success': False, 'detail': 'Formato inválido. Envie um arquivo .pfx ou .p12.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        suf = ext or '.pfx'
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suf)
        try:
            for chunk in upload.chunks():
                tmp.write(chunk)
        finally:
            tmp.close()
        cert_path = tmp.name
        cleanup_cert = True
    elif getattr(cfg, 'issnet_certificado', None) and cfg.issnet_certificado:
        # Certificado salvo como bytes no banco (BinaryField) — gravar em temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.pfx')
        tmp.write(bytes(cfg.issnet_certificado))
        tmp.close()
        cert_path = tmp.name
        cleanup_cert = True
    else:
        return Response(
            {
                'success': False,
                'detail': 'Envie o arquivo .pfx ou salve a configuração com certificado antes de testar.',
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not usuario:
        return Response(
            {'success': False, 'detail': 'Informe o usuário ISSNet.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not senha:
        return Response(
            {'success': False, 'detail': 'Informe a senha ISSNet ou salve antes de testar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not senha_cert:
        return Response(
            {'success': False, 'detail': 'Informe a senha do certificado (.pfx) ou salve antes de testar.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        ambiente = 'homologacao' if homologacao else 'producao'
        resultado = testar_conexao_issnet(
            usuario=usuario,
            senha=senha,
            certificado_path=cert_path,
            senha_certificado=senha_cert,
            ambiente=ambiente,
        )
        if resultado.get('success'):
            payload = {
                'success': True,
                'message': resultado.get('message') or 'Teste ISSNet OK.',
                'ambiente': resultado.get('ambiente'),
            }
            if resultado.get('certificado_subject'):
                payload['certificado_subject'] = resultado['certificado_subject']
            return Response(payload, status=status.HTTP_200_OK)

        detail = resultado.get('detail') or 'Falha no teste do ISSNet.'
        return Response({'success': False, 'detail': detail}, status=status.HTTP_400_BAD_REQUEST)
    finally:
        if cleanup_cert and cert_path:
            try:
                os.unlink(cert_path)
            except OSError:
                pass


