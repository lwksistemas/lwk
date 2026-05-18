from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.db.models import Sum, Count, Q, Exists, OuterRef
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.auth.models import Group
from datetime import timedelta
import logging

from core.views import BaseModelViewSet
from .models import (
    Vendedor, Conta, Lead, Contato, Oportunidade, Atividade,
    ProdutoServico, CategoriaProdutoServico, OportunidadeItem, Proposta, Contrato,
    PropostaTemplate, ContratoTemplate,
)
from .serializers import (
    VendedorSerializer,
    ContaSerializer,
    LeadSerializer,
    LeadListSerializer,
    ContatoSerializer,
    OportunidadeSerializer,
    AtividadeSerializer,
    AtividadeListSerializer,
    ProdutoServicoSerializer,
    CategoriaProdutoServicoSerializer,
    OportunidadeItemSerializer,
    PropostaSerializer,
    PropostaTemplateSerializer,
    ContratoTemplateSerializer,
    ContratoSerializer,
)
from tenants.middleware import get_current_loja_id, get_current_tenant_db, ensure_loja_context
from .utils import get_current_vendedor_id, get_loja_from_context
from .mixins import CRMPermissionMixin, VendedorFilterMixin, CacheInvalidationMixin
from .cache import CRMCacheManager
from .decorators import cache_list_response, require_admin_access, invalidate_cache_on_change
from .activities_google_sync import sync_atividade_create, sync_atividade_update, sync_atividade_delete
from .mixins_assinatura import AssinaturaDigitalMixin
from .mixins_documento import DocumentoQuerysetMixin, EnviarClienteMixin, TemplateViewSetMixin
from .services import (
    OportunidadeService,
    PropostaService,
    ContratoService,
    ProdutoServicoService,
)

logger = logging.getLogger(__name__)


def _get_crm_config_for_loja(loja_id: int):
    """
    Obtém CRMConfig. Se faltar coluna (ex.: 0045 asaas_api_key), aplica patch SQL no tenant.
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
            'CRMConfig: colunas ausentes no tenant, aplicando patch 0045 em %s',
            db_name,
        )
        from .schema_service import patch_crm_vendas_asaas_columns_if_missing
        patch_crm_vendas_asaas_columns_if_missing(db_name)
        return CRMConfig.get_or_create_for_loja(loja_id)


# ✅ OTIMIZAÇÃO: Paginação para reduzir tempo de resposta
class CRMPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class VendedorViewSet(CRMPermissionMixin, BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação

    def _obter_funcionario_administrador_da_loja(self, loja):
        """
        Obtém o funcionário que representa o administrador da loja.
        
        Args:
            loja: Instância da Loja
        
        Returns:
            dict: Dados do funcionário administrador
        """
        owner = loja.owner
        nome = owner.get_full_name() or owner.username or (owner.email or '').split('@')[0]
        return {
            'id': 'admin',
            'nome': nome,
            'email': owner.email or '',
            'telefone': getattr(loja, 'owner_telefone', '') or '',
            'cargo': 'Administrador',
            'is_admin': True,
            'is_active': True,
            'tem_acesso': True,
        }

    def get_queryset(self):
        """✅ OTIMIZAÇÃO: Anotar tem_acesso para evitar N+1 queries"""
        qs = super().get_queryset()
        
        # Anotar se vendedor tem acesso (evita N+1)
        # IMPORTANTE: VendedorUsuario está no banco 'default', não no schema isolado
        # Não podemos usar Exists() cross-database, então removemos a anotação aqui
        # e fazemos a verificação no serializer ou no método list()
        
        if hasattr(Vendedor, 'is_active'):
            return qs.filter(is_active=True)
        return qs

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def list(self, request, *args, **kwargs):
        import logging
        logger = logging.getLogger(__name__)
        
        loja_id = get_current_loja_id()
        logger.debug(
            "[VendedorViewSet.list] loja_id=%s, user=%s",
            loja_id,
            request.user.id if request.user else None,
        )
        
        for attempt in range(2):
            try:
                response = super().list(request, *args, **kwargs)
                
                logger.debug(
                    "[VendedorViewSet.list] response count=%s",
                    response.data.get('count')
                    if isinstance(response.data, dict)
                    else len(response.data),
                )
                
                # Prepend admin (owner) como primeiro item APENAS se não tiver vendedor vinculado
                loja_id = get_current_loja_id()
                if loja_id:
                    from superadmin.models import Loja, VendedorUsuario
                    try:
                        loja = Loja.objects.select_related('owner').get(id=loja_id)
                        owner_email_lower = (loja.owner.email or '').strip().lower()
                        
                        # Verificar se owner tem VendedorUsuario vinculado
                        owner_tem_vendedor = VendedorUsuario.objects.using('default').filter(
                            user=loja.owner,
                            loja_id=loja_id,
                        ).exists()
                        
                        logger.debug(
                            "[VendedorViewSet.list] owner_tem_vendedor=%s, owner_email=%s",
                            owner_tem_vendedor,
                            owner_email_lower,
                        )
                        
                        data = response.data
                        results = list(data.get('results', []) if isinstance(data, dict) else (data or []))
                        
                        logger.debug("[VendedorViewSet.list] results ANTES de filtrar: %s", len(results))
                        
                        # Filtrar vendedores legacy (is_admin) que eram owner — só quando o admin
                        # virtual será inserido (owner sem VendedorUsuario). Se o owner já tem
                        # VendedorUsuario, o registro na lista é a representação dele; filtrar aqui
                        # remove o administrador da UI por completo.
                        if owner_email_lower and not owner_tem_vendedor:
                            results = [r for r in results if not (
                                r.get('is_admin') and
                                (r.get('email') or '').strip().lower() == owner_email_lower
                            )]
                        
                        logger.debug("[VendedorViewSet.list] results DEPOIS de filtrar: %s", len(results))
                        
                        # Verificar se owner já existe como vendedor comum (mesmo email)
                        owner_ja_existe_como_vendedor = False
                        for r in results:
                            if (r.get('email') or '').strip().lower() == owner_email_lower:
                                owner_ja_existe_como_vendedor = True
                                # Marcar este vendedor como administrador
                                r['is_admin'] = True
                                r['cargo'] = 'Administrador'
                                break
                        
                        logger.debug(
                            "[VendedorViewSet.list] owner_ja_existe_como_vendedor=%s",
                            owner_ja_existe_como_vendedor,
                        )
                        
                        # Adicionar admin virtual APENAS se:
                        # 1. Owner NÃO tem VendedorUsuario vinculado E
                        # 2. Owner NÃO existe como vendedor comum na lista
                        if not owner_tem_vendedor and not owner_ja_existe_como_vendedor:
                            admin_item = self._obter_funcionario_administrador_da_loja(loja)
                            results.insert(0, admin_item)
                            logger.debug("[VendedorViewSet.list] Admin virtual adicionado")
                        
                        # Lista vazia com VendedorUsuario: vínculo no public sem linha ativa no tenant
                        # (órfão, inativo ou loja_id divergente) — recuperar por vendedor_id ou fallback.
                        if not results and owner_tem_vendedor:
                            vu = VendedorUsuario.objects.using('default').filter(
                                user=loja.owner,
                                loja_id=loja_id,
                            ).first()
                            recovered = False
                            if vu:
                                tenant_db = get_current_tenant_db()
                                qs = Vendedor.objects.all_without_filter()
                                if tenant_db and tenant_db != 'default':
                                    qs = qs.using(tenant_db)
                                vend = qs.filter(pk=vu.vendedor_id).first()
                                if vend and vend.loja_id == loja_id and vend.is_active:
                                    row = self.get_serializer(vend).data
                                    if owner_email_lower and (row.get('email') or '').strip().lower() == owner_email_lower:
                                        row['is_admin'] = True
                                        row['cargo'] = 'Administrador'
                                    results = [row]
                                    recovered = True
                                    logger.debug(
                                        "[VendedorViewSet.list] Recuperado Vendedor pk=%s (lista estava vazia)",
                                        vu.vendedor_id,
                                    )
                                elif vend:
                                    logger.warning(
                                        "[VendedorViewSet.list] Vendedor %s inconsistente "
                                        "(loja_id=%s, is_active=%s, contexto=%s)",
                                        vu.vendedor_id,
                                        vend.loja_id,
                                        vend.is_active,
                                        loja_id,
                                    )
                                else:
                                    logger.warning(
                                        "[VendedorViewSet.list] VendedorUsuario órfão: vendedor_id=%s",
                                        vu.vendedor_id,
                                    )
                            if not recovered:
                                admin_item = self._obter_funcionario_administrador_da_loja(loja)
                                results.insert(0, admin_item)
                                logger.debug(
                                    "[VendedorViewSet.list] Admin virtual (fallback lista vazia + VU)"
                                )
                        
                        logger.debug("[VendedorViewSet.list] results FINAL: %s", len(results))
                        
                        if isinstance(data, dict):
                            response.data['results'] = results
                            response.data['count'] = len(results)
                        else:
                            response.data = results
                    except Loja.DoesNotExist:
                        pass
                
                # Adicionar headers para evitar cache
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
            except Exception as e:
                from django.db.utils import ProgrammingError, OperationalError
                if isinstance(e, (ProgrammingError, OperationalError)) and attempt == 0:
                    from superadmin.models import Loja
                    from .schema_service import configurar_schema_crm_loja
                    loja_id = get_current_loja_id()
                    loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
                    if loja and configurar_schema_crm_loja(loja):
                        continue
                raise

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def destroy(self, request, *args, **kwargs):
        # Impedir exclusão de vendedor admin (legacy: is_admin=True)
        instance = self.get_object()
        if instance.is_admin:
            return Response(
                {'detail': 'O vendedor administrador não pode ser excluído.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna informações do vendedor logado."""
        from superadmin.models import VendedorUsuario
        
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Verificar se é o owner (admin)
        from superadmin.models import Loja
        try:
            loja = Loja.objects.select_related('owner').get(id=loja_id)
            if request.user == loja.owner:
                nome = request.user.get_full_name() or request.user.username or (request.user.email or '').split('@')[0]
                return Response({
                    'id': 'admin',
                    'nome': nome,
                    'email': request.user.email or '',
                    'is_admin': True,
                })
        except Loja.DoesNotExist:
            pass
        
        # Verificar se é vendedor
        try:
            vu = VendedorUsuario.objects.using('default').select_related('vendedor').get(
                user=request.user,
                loja_id=loja_id,
            )
            vendedor = vu.vendedor
            return Response({
                'id': vendedor.id,
                'nome': vendedor.nome,
                'email': vendedor.email or '',
                'is_admin': vendedor.is_admin,
            })
        except VendedorUsuario.DoesNotExist:
            return Response(
                {'detail': 'Vendedor não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha_administrador(self, request):
        """Reenvia senha provisória do administrador (Loja.owner)."""
        from django.utils.crypto import get_random_string
        from django.core.mail import send_mail
        from django.conf import settings
        from superadmin.models import Loja

        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            loja = Loja.objects.select_related('owner').get(id=loja_id)
        except Loja.DoesNotExist:
            return Response(
                {'detail': 'Loja não encontrada.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        owner = loja.owner
        if not owner.email:
            return Response(
                {'detail': 'Administrador não possui e-mail cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        senha_provisoria = get_random_string(8)
        owner.set_password(senha_provisoria)
        owner.save(update_fields=['password'])
        loja.senha_provisoria = senha_provisoria
        loja.senha_foi_alterada = False
        loja.save(update_fields=['senha_provisoria', 'senha_foi_alterada'])
        site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
        login_url = f"{site_url}/loja/{loja.slug}/login"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
        try:
            send_mail(
                subject='Nova senha provisória - CRM Vendas',
                message=(
                    f"Olá, {owner.get_full_name() or owner.username}!\n\n"
                    f"Sua senha foi redefinida.\n\n"
                    f"Login: {owner.username}\n"
                    f"Nova senha provisória: {senha_provisoria}\n\n"
                    f"Acesse: {login_url}\n\n"
                    f"Por segurança, altere sua senha no primeiro acesso."
                ),
                from_email=from_email,
                recipient_list=[owner.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return Response({
            'detail': f'Senha provisória enviada para {owner.email}',
            'email_enviado': owner.email,
        })

    @action(detail=True, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por e-mail. Funciona para vendedores e para o admin (owner)."""
        vendedor = self.get_object()
        if not vendedor.email:
            return Response(
                {'detail': 'Vendedor não possui e-mail cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        from django.contrib.auth import get_user_model
        from django.utils.crypto import get_random_string
        from django.core.mail import send_mail
        from django.conf import settings
        from superadmin.models import Loja, VendedorUsuario

        User = get_user_model()
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        loja = Loja.objects.using('default').select_related('owner').get(id=loja_id)
        senha_provisoria = get_random_string(8)
        site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
        login_url = f"{site_url}/loja/{loja.slug}/login"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'

        # Admin (owner): usa Loja.owner, não VendedorUsuario
        if vendedor.is_admin:
            if loja.owner.email.lower() != (vendedor.email or '').strip().lower():
                return Response(
                    {'detail': 'E-mail do administrador não corresponde ao proprietário da loja.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            loja.owner.set_password(senha_provisoria)
            loja.owner.save(update_fields=['password'])
            loja.senha_provisoria = senha_provisoria
            loja.senha_foi_alterada = False
            loja.save(update_fields=['senha_provisoria', 'senha_foi_alterada'])
        else:
            # Vendedor comum: usa VendedorUsuario
            try:
                vu = VendedorUsuario.objects.using('default').get(
                    loja_id=loja_id,
                    vendedor_id=vendedor.id,
                )
            except VendedorUsuario.DoesNotExist:
                return Response(
                    {'detail': 'Vendedor ainda não possui acesso ao sistema. Use "Criar acesso" ao editar.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            vu.user.set_password(senha_provisoria)
            vu.user.save(update_fields=['password'])
            vu.precisa_trocar_senha = True
            vu.save(update_fields=['precisa_trocar_senha'])

        try:
            send_mail(
                subject='Nova senha provisória - CRM Vendas',
                message=(
                    f"Olá, {vendedor.nome or 'Vendedor'}!\n\n"
                    f"Sua senha foi redefinida.\n\n"
                    f"Login: {vendedor.email}\n"
                    f"Nova senha provisória: {senha_provisoria}\n\n"
                    f"Acesse: {login_url}\n\n"
                    f"Por segurança, altere sua senha no primeiro acesso."
                ),
                from_email=from_email,
                recipient_list=[vendedor.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return Response({
            'detail': f'Senha provisória enviada para {vendedor.email}',
            'email_enviado': vendedor.email,
        })

    @action(detail=False, methods=['get'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def grupos_disponiveis(self, request):
        """Lista grupos disponíveis para atribuir a vendedores."""
        # Filtrar apenas grupos relacionados ao CRM
        grupos_crm = Group.objects.using('default').filter(
            name__in=['Gerente de Vendas', 'Vendedor']
        ).values('id', 'name').order_by('name')
        
        return Response(list(grupos_crm))


class ContaViewSet(CacheInvalidationMixin, BaseModelViewSet):
    queryset = Conta.objects.select_related('vendedor').prefetch_related('leads', 'contatos').all()
    serializer_class = ContaSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['contas']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('vendedor').prefetch_related('leads', 'contatos')
        # Filtro por tipo (cliente, prestadora, ambos)
        tipo = self.request.query_params.get('tipo')
        if tipo:
            if tipo == 'prestadora':
                qs = qs.filter(tipo__in=['prestadora', 'ambos'])
            elif tipo == 'cliente':
                qs = qs.filter(tipo__in=['cliente', 'ambos'])
            else:
                qs = qs.filter(tipo=tipo)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Adicionar headers para evitar cache do navegador
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_create(self, serializer):
        """
        Valida vendedor antes de salvar. Invalida cache de contas aqui porque este
        método substitui o do CacheInvalidationMixin (senão a lista serviria cache stale).
        """
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            # Validar se vendedor existe no schema isolado
            if Vendedor.objects.filter(id=vendedor_id).exists():
                serializer.save(vendedor_id=vendedor_id)
            else:
                # Vendedor não existe no schema, salvar sem vendedor
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"[ContaViewSet.perform_create] vendedor_id={vendedor_id} não existe no schema, "
                    f"salvando conta sem vendedor"
                )
                serializer.save()
        else:
            serializer.save()
        self._invalidate_caches()

    @action(detail=True, methods=['get'])
    def atividades(self, request, pk=None):
        """Lista atividades (histórico de interações) vinculadas a esta conta."""
        conta = self.get_object()
        atividades = Atividade.objects.filter(conta=conta).order_by('-data')[:50]
        from .serializers import AtividadeListSerializer
        serializer = AtividadeListSerializer(atividades, many=True)
        return Response(serializer.data)


class LeadViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = Lead.objects.select_related('conta', 'vendedor').prefetch_related('oportunidades').all()
    serializer_class = LeadSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = ['oportunidades__vendedor_id']
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['leads']

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        """
        Override para permitir que owner acesse qualquer lead no retrieve().
        IMPORTANTE: Owner sempre pode acessar qualquer lead, mesmo se tiver vendedor vinculado.
        Base: BaseModelViewSet (ensure_loja_context + isolamento por loja via LeadManager).
        """
        qs = super().get_queryset()
        # ✅ OTIMIZAÇÃO v1490: Adicionar prefetch para contato e oportunidades
        qs = qs.select_related('conta', 'vendedor', 'contato').prefetch_related(
            'oportunidades',
            'oportunidades__vendedor'  # Prefetch vendedor das oportunidades
        )

        # Para retrieve (GET /leads/{id}/), owner sempre tem acesso
        if self.action == 'retrieve':
            from superadmin.models import Loja
            loja_id = get_current_loja_id()
            if loja_id and self.request and self.request.user:
                try:
                    loja = Loja.objects.using('default').filter(id=loja_id).first()
                    if loja and loja.owner_id == self.request.user.id:
                        # Owner: retorna queryset sem filtro
                        status = self.request.query_params.get('status')
                        if status:
                            qs = qs.filter(status=status)
                        origem = self.request.query_params.get('origem')
                        if origem:
                            qs = qs.filter(origem=origem)
                        return qs
                except Exception:
                    pass
        
        # Para list e outras ações, aplicar filtro de vendedor
        qs = self.filter_by_vendedor(qs)
        
        # Filtros adicionais
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        origem = self.request.query_params.get('origem')
        if origem:
            qs = qs.filter(origem=origem)
        return qs

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Adicionar headers para evitar cache do navegador
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_create(self, serializer):
        """
        Cache invalidado automaticamente pelo CacheInvalidationMixin.
        Valida se vendedor existe antes de salvar.
        """
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            # Validar se vendedor existe no schema isolado
            if Vendedor.objects.filter(id=vendedor_id).exists():
                serializer.save(vendedor_id=vendedor_id)
            else:
                # Vendedor não existe no schema, salvar sem vendedor
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"[LeadViewSet.perform_create] vendedor_id={vendedor_id} não existe no schema, "
                    f"salvando lead sem vendedor"
                )
                serializer.save()
        else:
            serializer.save()
        self._invalidate_caches()


class ContatoViewSet(CacheInvalidationMixin, BaseModelViewSet):
    queryset = Contato.objects.select_related('conta').all()
    serializer_class = ContatoSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['contatos']

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Adicionar headers para evitar cache do navegador
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('conta')
        # Filtros adicionais (além do filtro de vendedor do mixin)
        conta_id = self.request.query_params.get('conta_id')
        if conta_id:
            qs = qs.filter(conta_id=conta_id)
        return qs

    def perform_update(self, serializer):
        """
        Ao editar um Contato, propaga nome/email/telefone para os Leads vinculados
        (Lead mantém cópia denormalizada desses campos).
        """
        instance_antes = self.get_object()
        nome_antes = instance_antes.nome
        email_antes = instance_antes.email
        telefone_antes = instance_antes.telefone

        instance = serializer.save()

        update_fields = {}
        if instance.nome != nome_antes:
            update_fields['nome'] = instance.nome
        if instance.email != email_antes:
            update_fields['email'] = instance.email or ''
        if instance.telefone != telefone_antes:
            update_fields['telefone'] = instance.telefone or ''

        if update_fields:
            updated = Lead.objects.filter(contato_id=instance.id).update(**update_fields)
            if updated:
                logger.info(
                    'Contato %s atualizado: propagados %s para %d Lead(s) vinculado(s).',
                    instance.id, list(update_fields.keys()), updated,
                )
                try:
                    CRMCacheManager.invalidate_dashboard(
                        getattr(instance, 'loja_id', None)
                    )
                except Exception:
                    pass

        self._invalidate_caches()


class OportunidadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = Oportunidade.objects.select_related('lead', 'vendedor', 'lead__conta', 'empresa_prestadora').prefetch_related('atividades').all()
    serializer_class = OportunidadeSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = []
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['oportunidades', 'dashboard']

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        # Auto-patch: garantir coluna conta_id na tabela atividade (migration 0056)
        db_name = get_current_tenant_db()
        if db_name and db_name != 'default':
            try:
                from django.db import connections
                conn = connections[db_name]
                with conn.cursor() as cur:
                    cur.execute(
                        "ALTER TABLE crm_vendas_atividade "
                        "ADD COLUMN IF NOT EXISTS conta_id BIGINT NULL;"
                    )
            except Exception:
                pass

    def _sanitize_vendedor_for_create(self, data):
        """
        Remove vendedor do payload se for inválido (não existe no tenant).
        Evita erro 400 quando frontend envia vendedor_id de outra loja ou inexistente.
        """
        vendedor_id = data.get('vendedor')
        if vendedor_id is None:
            return data
        try:
            vid = int(vendedor_id) if not isinstance(vendedor_id, int) else vendedor_id
        except (TypeError, ValueError):
            data = data.copy()
            data.pop('vendedor', None)
            return data
        if not Vendedor.objects.filter(id=vid).exists():
            logger.warning(
                'Oportunidade create: vendedor_id=%s não existe no tenant, removendo do payload',
                vid,
            )
            data = data.copy()
            data.pop('vendedor', None)
        return data

    def create(self, request, *args, **kwargs):
        """Override para sanitizar vendedor inválido antes da validação."""
        raw = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        data = self._sanitize_vendedor_for_create(raw)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Adicionar headers para evitar cache do navegador
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_create(self, serializer):
        """
        Cria oportunidade usando Service Layer.
        Delega lógica de negócio para OportunidadeService.
        Cache invalidado automaticamente pelo CacheInvalidationMixin.
        """
        service = OportunidadeService(self.request)
        oportunidade = service.criar_oportunidade(serializer.validated_data)
        # Atualizar serializer com a instância criada
        serializer.instance = oportunidade
        self._invalidate_caches()

    def perform_update(self, serializer):
        """
        Atualiza oportunidade usando Service Layer.
        Delega lógica de negócio para OportunidadeService.
        Cache invalidado automaticamente pelo CacheInvalidationMixin.
        """
        service = OportunidadeService(self.request)
        oportunidade = service.atualizar_oportunidade(serializer.instance, serializer.validated_data)
        # Atualizar serializer com a instância atualizada
        serializer.instance = oportunidade
        self._invalidate_caches()

    def get_queryset(self):
        qs = super().get_queryset()
        # ✅ OTIMIZAÇÃO v1490: Adicionar prefetch para itens e reduzir N+1 queries
        qs = qs.select_related('lead', 'vendedor', 'lead__conta', 'empresa_prestadora').prefetch_related(
            'atividades',
            'itens',  # Prefetch itens da oportunidade
            'itens__produto_servico'  # Prefetch produtos dos itens
        )
        # Filtros adicionais (além do filtro de vendedor do mixin)
        # Se não for vendedor, permitir filtrar por vendedor_id via query param
        if get_current_vendedor_id(self.request) is None:
            vendedor_id = self.request.query_params.get('vendedor_id')
            if vendedor_id:
                qs = qs.filter(vendedor_id=vendedor_id)
        etapa = self.request.query_params.get('etapa')
        if etapa:
            qs = qs.filter(etapa=etapa)
        return qs


class AtividadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    # ✅ OTIMIZAÇÃO v1490: Adicionar prefetch para vendedor e conta
    queryset = (
        Atividade.objects.select_related(
            'oportunidade',
            'lead',
            'oportunidade__vendedor',  # Prefetch vendedor da oportunidade
            'lead__conta'  # Prefetch conta do lead
        )
        .defer('google_event_id')  # Evita coluna que pode não existir em schemas antigos
        .all()
    )
    serializer_class = AtividadeListSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = ['lead__oportunidades__vendedor_id']
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['atividades', 'dashboard']
    
    def filter_by_vendedor(self, queryset):
        """
        Override para permitir atividades sem oportunidade/lead.
        Atividades órfãs: cada vendedor vê apenas as suas (criado_por_vendedor_id).
        Proprietário vê todas.
        """
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is None:
            # Proprietário: vê tudo
            return queryset
        
        # Vendedor vê:
        # 1. Atividades vinculadas às suas oportunidades
        # 2. Atividades vinculadas aos seus leads
        # 3. Atividades órfãs criadas/importadas por ele (criado_por_vendedor_id=vendedor_id)
        from django.db.models import Q
        filters = (
            Q(oportunidade__vendedor_id=vendedor_id) |
            Q(lead__oportunidades__vendedor_id=vendedor_id) |
            Q(oportunidade__isnull=True, lead__isnull=True, criado_por_vendedor_id=vendedor_id)
        )
        return queryset.filter(filters).distinct()

    def perform_create(self, serializer):
        """Cache invalidado automaticamente pelo CacheInvalidationMixin."""
        vendedor_id = get_current_vendedor_id(self.request)
        if vendedor_id is not None:
            serializer.save(criado_por_vendedor_id=vendedor_id)
        else:
            serializer.save()
        atividade = serializer.instance
        if atividade and getattr(atividade, 'loja_id', None):
            try:
                from superadmin.models import Loja
                from notificacoes.services import notify
                loja = Loja.objects.using('default').filter(id=atividade.loja_id).select_related('owner').first()
                if loja and loja.owner_id:
                    data_str = atividade.data.strftime('%d/%m/%Y %H:%M') if atividade.data else ''
                    tipo_label = atividade.get_tipo_display() if hasattr(atividade, 'get_tipo_display') else atividade.tipo
                    notify(
                        user=loja.owner,
                        titulo=f'Nova atividade: {atividade.titulo[:50]}{"..." if len(atividade.titulo) > 50 else ""}',
                        mensagem=f'{tipo_label}: {atividade.titulo} — {data_str}',
                        tipo='tarefa',
                        canal='in_app',
                        metadata={
                            'url': f'/loja/{loja.slug}/crm-vendas/calendario',
                            'atividade_id': atividade.id,
                            'loja_id': loja.id,
                        },
                    )
            except Exception:
                pass  # Notificação é best-effort; não falha a criação

            sync_atividade_create(self.request, atividade)
        self._invalidate_caches()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return AtividadeSerializer
        return AtividadeListSerializer

    @cache_list_response(CRMCacheManager.ATIVIDADES, ttl=30, extra_keys=['data_inicio', 'data_fim'])  # ✅ Cache reduzido para 30s
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        # Adicionar headers para evitar cache do navegador
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response

    def perform_update(self, serializer):
        """Cache invalidado automaticamente pelo CacheInvalidationMixin."""
        super().perform_update(serializer)
        atividade = serializer.instance

        if atividade and getattr(atividade, 'loja_id', None):
            sync_atividade_update(self.request, atividade)

    def perform_destroy(self, instance):
        """
        Deleta atividade e remove do Google Calendar se tiver google_event_id.
        Também remove a notificação associada.
        """
        # Remover notificação associada à atividade
        try:
            from notificacoes.models import Notification
            from superadmin.models import Loja
            
            loja_id = get_current_loja_id()
            loja = Loja.objects.using('default').filter(id=loja_id).select_related('owner').first()
            
            if loja and loja.owner_id:
                # Deletar notificações relacionadas a esta atividade
                Notification.objects.filter(
                    user=loja.owner,
                    metadata__atividade_id=instance.id
                ).delete()
                logger.info(f"✅ Notificações da atividade {instance.id} removidas")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao remover notificações da atividade: {e}")
        
        if instance.google_event_id:
            sync_atividade_delete(get_current_loja_id(), instance)

        super().perform_destroy(instance)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = (
            qs.select_related('oportunidade', 'lead')
            .defer('google_event_id')
        )
        # Filtros adicionais (além do filtro de vendedor do mixin)
        concluido = self.request.query_params.get('concluido')
        if concluido is not None:
            qs = qs.filter(concluido=concluido.lower() == 'true')
        oportunidade_id = self.request.query_params.get('oportunidade_id')
        if oportunidade_id:
            qs = qs.filter(oportunidade_id=oportunidade_id)
        lead_id = self.request.query_params.get('lead_id')
        if lead_id:
            qs = qs.filter(lead_id=lead_id)
        data_inicio = self.request.query_params.get('data_inicio')
        if data_inicio:
            dt = parse_datetime(data_inicio)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__gte=dt)
        data_fim = self.request.query_params.get('data_fim')
        if data_fim:
            dt = parse_datetime(data_fim)
            if dt and timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            if dt:
                qs = qs.filter(data__lte=dt)
        return qs


class CategoriaProdutoServicoViewSet(BaseModelViewSet):
    """CRUD de categorias para organizar produtos e serviços."""
    queryset = CategoriaProdutoServico.objects.select_related('loja').all()  # ✅ OTIMIZAÇÃO: select_related
    serializer_class = CategoriaProdutoServicoSerializer
    pagination_class = CRMPagination

    def perform_create(self, serializer):
        """Garante que loja_id seja definido ao criar categoria."""
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if loja_id:
            serializer.save(loja_id=loja_id)
        else:
            serializer.save()

    def get_queryset(self):
        """Filtra categorias por loja_id e aplica filtros adicionais."""
        from tenants.middleware import get_current_loja_id
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.warning(f"[CategoriaProdutoServicoViewSet] Acesso sem loja_id no contexto")
            return CategoriaProdutoServico.objects.none()
        
        # Filtrar por loja_id explicitamente
        qs = CategoriaProdutoServico.objects.filter(loja_id=loja_id)
        
        # Filtros adicionais
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')
        
        return qs


class ProdutoServicoViewSet(BaseModelViewSet):
    """CRUD de produtos e serviços para uso em oportunidades."""
    queryset = ProdutoServico.objects.select_related('loja', 'categoria').all()  # ✅ OTIMIZAÇÃO: select_related
    serializer_class = ProdutoServicoSerializer
    pagination_class = CRMPagination

    def perform_create(self, serializer):
        """Garante que loja_id seja definido ao criar produto/serviço."""
        from tenants.middleware import get_current_loja_id
        loja_id = get_current_loja_id()
        if loja_id:
            serializer.save(loja_id=loja_id)
        else:
            serializer.save()

    def get_queryset(self):
        """Filtra produtos/serviços por loja_id e aplica filtros adicionais."""
        from tenants.middleware import get_current_loja_id
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.warning(f"[ProdutoServicoViewSet] Acesso sem loja_id no contexto")
            return ProdutoServico.objects.none()
        
        # Filtrar por loja_id explicitamente
        qs = ProdutoServico.objects.filter(loja_id=loja_id)
        
        # Filtros adicionais
        ativo = self.request.query_params.get('ativo')
        if ativo is not None:
            qs = qs.filter(ativo=ativo.lower() == 'true')
        tipo = self.request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)
        sem_cat = self.request.query_params.get('sem_categoria')
        if sem_cat and str(sem_cat).lower() in ('1', 'true', 'yes'):
            qs = qs.filter(categoria__isnull=True)
        else:
            categoria = self.request.query_params.get('categoria')
            if categoria:
                qs = qs.filter(categoria_id=categoria)
        return qs


class OportunidadeItemViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    """Itens (produtos/serviços) de uma oportunidade."""
    queryset = OportunidadeItem.objects.select_related('oportunidade', 'produto_servico').all()
    serializer_class = OportunidadeItemSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = []
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['oportunidades', 'dashboard']

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('oportunidade', 'produto_servico')
        oportunidade_id = self.request.query_params.get('oportunidade_id')
        if oportunidade_id:
            qs = qs.filter(oportunidade_id=oportunidade_id)
        return qs

    def _recalcular_valor_oportunidade(self, oportunidade_id):
        """Recalcula valor da oportunidade e sincroniza propostas/contratos em rascunho."""
        from django.db.models import Sum, F
        itens = OportunidadeItem.objects.filter(oportunidade_id=oportunidade_id)
        total = itens.aggregate(
            total=Sum(F('quantidade') * F('preco_unitario'))
        )['total'] or 0
        Oportunidade.objects.filter(id=oportunidade_id).update(valor=total)
        # Sincronizar propostas e contratos (todas que não estão canceladas/rejeitadas)
        Proposta.objects.filter(oportunidade_id=oportunidade_id).exclude(status__in=['cancelada', 'rejeitada']).update(valor_total=total)
        Contrato.objects.filter(oportunidade_id=oportunidade_id).exclude(status='cancelado').update(valor_total=total)

    def perform_create(self, serializer):
        serializer.save()
        self._recalcular_valor_oportunidade(serializer.instance.oportunidade_id)
        self._invalidate_caches()

    def perform_update(self, serializer):
        serializer.save()
        self._recalcular_valor_oportunidade(serializer.instance.oportunidade_id)
        self._invalidate_caches()

    def perform_destroy(self, instance):
        oportunidade_id = instance.oportunidade_id
        instance.delete()
        self._recalcular_valor_oportunidade(oportunidade_id)
        self._invalidate_caches()


class PropostaViewSet(AssinaturaDigitalMixin, EnviarClienteMixin, DocumentoQuerysetMixin, VendedorFilterMixin, BaseModelViewSet):
    """Propostas comerciais vinculadas a oportunidades."""
    queryset = Proposta.objects.all()
    serializer_class = PropostaSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = []

    # Configuração dos mixins
    assinatura_doc_label = 'Proposta'
    assinatura_cache_key = 'propostas'
    enviar_cliente_label = 'Proposta'

    @action(detail=True, methods=['post'])
    def confirmar_pedido(self, request, pk=None):
        """Confirma a proposta como Pedido (após aceita)."""
        proposta = self.get_object()
        if proposta.status != 'aceita':
            return Response(
                {'detail': f'Apenas propostas Aceitas podem ser confirmadas como Pedido. Status atual: {proposta.get_status_display()}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposta.status = 'pedido'
        proposta.save(update_fields=['status', 'updated_at'])
        return Response({'detail': 'Proposta confirmada como Pedido.', 'status': 'pedido'})

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela a proposta com motivo obrigatório."""
        proposta = self.get_object()
        if proposta.status == 'cancelada':
            return Response({'detail': 'Proposta já está cancelada.'}, status=status.HTTP_400_BAD_REQUEST)
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Informe o motivo do cancelamento.'}, status=status.HTTP_400_BAD_REQUEST)
        proposta.status = 'cancelada'
        proposta.motivo_cancelamento = motivo
        proposta.save(update_fields=['status', 'motivo_cancelamento', 'updated_at'])
        return Response({'detail': 'Proposta cancelada com sucesso.', 'status': 'cancelada'})

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixa o PDF da proposta."""
        from .pdf_proposta_contrato import gerar_pdf_proposta
        from django.http import HttpResponse
        
        proposta = self.get_object()
        
        try:
            incluir_assinaturas = proposta.status_assinatura == 'concluido'
            pdf_buffer = gerar_pdf_proposta(proposta, incluir_assinaturas=incluir_assinaturas)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f'proposta_{proposta.numero or proposta.id}_{proposta.titulo.replace(" ", "_")}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download_docx(self, request, pk=None):
        """Baixa o Word (DOCX) da proposta."""
        from django.http import HttpResponse
        from .docx_proposta_contrato import gerar_docx_proposta

        proposta = self.get_object()
        try:
            docx_buffer = gerar_docx_proposta(proposta)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            safe_titulo = (proposta.titulo or "").replace(" ", "_")
            filename = f'proposta_{proposta.numero or proposta.id}_{safe_titulo}.docx'
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar DOCX: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PropostaTemplateViewSet(TemplateViewSetMixin, BaseModelViewSet):
    """Templates de propostas para reutilização."""
    queryset = PropostaTemplate.objects.all()
    serializer_class = PropostaTemplateSerializer
    pagination_class = CRMPagination
    template_model = PropostaTemplate


class ContratoTemplateViewSet(TemplateViewSetMixin, BaseModelViewSet):
    """Templates de contratos para reutilização."""
    queryset = ContratoTemplate.objects.all()
    serializer_class = ContratoTemplateSerializer
    pagination_class = CRMPagination
    template_model = ContratoTemplate


class ContratoViewSet(AssinaturaDigitalMixin, EnviarClienteMixin, DocumentoQuerysetMixin, BaseModelViewSet):
    """Contratos gerados a partir de oportunidades fechadas."""
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    pagination_class = CRMPagination

    # Configuração dos mixins
    assinatura_doc_label = 'Contrato'
    assinatura_cache_key = 'contratos'
    enviar_cliente_label = 'Contrato'

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        """Cancela o contrato com motivo obrigatório."""
        contrato = self.get_object()
        if contrato.status == 'cancelado':
            return Response({'detail': 'Contrato já está cancelado.'}, status=status.HTTP_400_BAD_REQUEST)
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Informe o motivo do cancelamento.'}, status=status.HTTP_400_BAD_REQUEST)
        contrato.status = 'cancelado'
        contrato.motivo_cancelamento = motivo
        contrato.save(update_fields=['status', 'motivo_cancelamento', 'updated_at'])
        return Response({'detail': 'Contrato cancelado com sucesso.', 'status': 'cancelado'})

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixa o PDF do contrato."""
        from .pdf_proposta_contrato import gerar_pdf_contrato
        from django.http import HttpResponse

        contrato = self.get_object()
        try:
            incluir_assinaturas = contrato.status_assinatura == 'concluido'
            pdf_buffer = gerar_pdf_contrato(contrato, incluir_assinaturas=incluir_assinaturas)

            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f'contrato_{contrato.numero or contrato.id}_{contrato.titulo.replace(" ", "_")}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def download_docx(self, request, pk=None):
        """Baixa o Word (DOCX) do contrato."""
        from django.http import HttpResponse
        from .docx_proposta_contrato import gerar_docx_contrato

        contrato = self.get_object()
        try:
            docx_buffer = gerar_docx_contrato(contrato)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            safe_titulo = (contrato.titulo or "").replace(" ", "_")
            filename = f'contrato_{contrato.numero or contrato.id}_{safe_titulo}.docx'
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": f"Erro ao gerar DOCX: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




# ===========================================================================
# Re-exports para compatibilidade com urls.py
# Funções movidas para arquivos separados (refatoração)
# ===========================================================================
from .views_config import (  # noqa: F401, E402
    _get_crm_config_for_loja,
    _empty_dashboard_response,
    crm_me,
    dashboard_data,
    WhatsAppConfigView,
    LoginConfigView,
    crm_busca,
    crm_config,
    crm_config_asaas_test,
    crm_config_issnet_test,
)
from .views_relatorios import gerar_relatorio  # noqa: F401, E402
from .views_assinatura_publica import AssinaturaPublicaView, AssinaturaPdfView  # noqa: F401, E402
