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
from .views_enviar_cliente import _enviar_proposta_contrato_cliente
from .services import (
    OportunidadeService,
    PropostaService,
    ContratoService,
    ProdutoServicoService,
)

logger = logging.getLogger(__name__)


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
        return qs.select_related('vendedor').prefetch_related('leads', 'contatos')

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


class OportunidadeViewSet(CacheInvalidationMixin, VendedorFilterMixin, BaseModelViewSet):
    queryset = Oportunidade.objects.select_related('lead', 'vendedor', 'lead__conta').prefetch_related('atividades').all()
    serializer_class = OportunidadeSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação
    
    # Configuração do VendedorFilterMixin
    vendedor_filter_field = 'vendedor_id'
    vendedor_filter_related = []
    
    # Configuração do CacheInvalidationMixin
    cache_keys = ['oportunidades', 'dashboard']

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
        qs = qs.select_related('lead', 'vendedor', 'lead__conta').prefetch_related(
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


class PropostaViewSet(VendedorFilterMixin, BaseModelViewSet):
    """Propostas comerciais vinculadas a oportunidades."""
    queryset = Proposta.objects.select_related('oportunidade', 'oportunidade__lead').prefetch_related(
        'oportunidade__itens__produto_servico'
    ).all()
    serializer_class = PropostaSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = 'oportunidade__vendedor_id'
    vendedor_filter_related = []

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('oportunidade', 'oportunidade__lead').prefetch_related(
            'oportunidade__itens__produto_servico'
        )
        oportunidade_id = self.request.query_params.get('oportunidade_id')
        if oportunidade_id:
            qs = qs.filter(oportunidade_id=oportunidade_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def enviar_cliente(self, request, pk=None):
        """Envia proposta ao cliente por email ou WhatsApp."""
        instance = self.get_object()
        canal = (request.data.get('canal') or '').strip().lower()
        if canal not in ('email', 'whatsapp'):
            return Response(
                {'detail': 'Informe o canal: email ou whatsapp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ok, err = _enviar_proposta_contrato_cliente(instance, canal, request)
        if ok:
            return Response({'message': f'Proposta enviada ao cliente por {canal} com sucesso.'})
        return Response({'detail': err or 'Erro ao enviar.'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        """Baixa o PDF da proposta."""
        from .pdf_proposta_contrato import gerar_pdf_proposta
        from django.http import HttpResponse
        
        proposta = self.get_object()
        
        try:
            # ✅ CORREÇÃO: Verificar status_assinatura (não status)
            # Incluir assinaturas se a proposta estiver concluída (ambas as partes assinaram)
            incluir_assinaturas = proposta.status_assinatura == 'concluido'
            
            # Gerar PDF
            pdf_buffer = gerar_pdf_proposta(proposta, incluir_assinaturas=incluir_assinaturas)
            
            # Preparar resposta
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f'proposta_{proposta.numero or proposta.id}_{proposta.titulo.replace(" ", "_")}.pdf'
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
        except Exception as e:
            return Response(
                {'detail': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    @invalidate_cache_on_change('propostas')
    def enviar_para_assinatura(self, request, pk=None):
        """
        Inicia workflow de assinatura digital.
        Envia email para cliente com link de assinatura.
        """
        from .assinatura_digital_service import criar_token_assinatura, enviar_email_assinatura_cliente
        
        proposta = self.get_object()
        loja_id = get_current_loja_id()
        
        # Validar que proposta tem oportunidade e lead
        if not proposta.oportunidade or not proposta.oportunidade.lead:
            return Response(
                {'detail': 'Proposta sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lead = proposta.oportunidade.lead
        if not lead.email:
            return Response(
                {'detail': 'Lead não possui email cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se já existe assinatura pendente
        if proposta.status_assinatura in ['aguardando_cliente', 'aguardando_vendedor']:
            return Response(
                {'detail': f'Proposta já está em processo de assinatura: {proposta.get_status_assinatura_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar token de assinatura para cliente
        assinatura = criar_token_assinatura(proposta, 'cliente', loja_id)
        
        # Atualizar status da proposta
        proposta.status_assinatura = 'aguardando_cliente'
        proposta.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Enviar email com link de assinatura
        ok, err = enviar_email_assinatura_cliente(proposta, assinatura, request)
        
        if ok:
            return Response({
                'message': f'Email de assinatura enviado para {lead.email}',
                'status_assinatura': 'aguardando_cliente'
            })
        else:
            # Reverter status se falhou
            proposta.status_assinatura = 'rascunho'
            proposta.save(update_fields=['status_assinatura', 'updated_at'])
            assinatura.delete()
            
            return Response(
                {'detail': err or 'Erro ao enviar email. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @invalidate_cache_on_change('propostas')
    def reenviar_para_assinatura(self, request, pk=None):
        """Reenvia e-mail com link de assinatura (novo token) em processo pendente."""
        from .assinatura_digital_service import reenviar_link_assinatura_pendente

        proposta = self.get_object()
        loja_id = get_current_loja_id()

        if not proposta.oportunidade or not proposta.oportunidade.lead:
            return Response(
                {'detail': 'Proposta sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, msg, err = reenviar_link_assinatura_pendente(proposta, loja_id, request)
        if ok:
            return Response({
                'message': msg,
                'status_assinatura': proposta.status_assinatura,
            })
        if err and err.startswith('Reenvio só é possível'):
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': err or 'Erro ao reenviar.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PropostaTemplateViewSet(BaseModelViewSet):
    """Templates de propostas para reutilização."""
    queryset = PropostaTemplate.objects.select_related('loja').all()  # ✅ OTIMIZAÇÃO: select_related
    serializer_class = PropostaTemplateSerializer
    pagination_class = CRMPagination

    def get_queryset(self):
        """Filtra templates por loja_id e aplica filtros adicionais."""
        from tenants.middleware import get_current_loja_id
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.warning(f"[PropostaTemplateViewSet] Acesso sem loja_id no contexto")
            return PropostaTemplate.objects.none()
        
        # Filtrar por loja_id explicitamente
        qs = PropostaTemplate.objects.filter(loja_id=loja_id)
        
        # Filtrar apenas ativos por padrão
        ativo = self.request.query_params.get('ativo')
        if ativo is None or ativo.lower() == 'true':
            qs = qs.filter(ativo=True)
        elif ativo.lower() == 'false':
            qs = qs.filter(ativo=False)
        
        return qs

    @action(detail=True, methods=['post'])
    def marcar_padrao(self, request, pk=None):
        """Marca este template como padrão (desmarca outros)."""
        template = self.get_object()
        template.is_padrao = True
        template.save()  # O método save() do modelo já desmarca outros
        return Response({'message': 'Template marcado como padrão.'})


class ContratoTemplateViewSet(BaseModelViewSet):
    """Templates de contratos para reutilização."""
    queryset = ContratoTemplate.objects.select_related('loja').all()  # ✅ OTIMIZAÇÃO: select_related
    serializer_class = ContratoTemplateSerializer
    pagination_class = CRMPagination

    def get_queryset(self):
        """Filtra templates por loja_id e aplica filtros adicionais."""
        from tenants.middleware import get_current_loja_id
        if hasattr(self, 'request') and self.request:
            ensure_loja_context(self.request)
        loja_id = get_current_loja_id()
        
        if not loja_id:
            logger.warning(f"[ContratoTemplateViewSet] Acesso sem loja_id no contexto")
            return ContratoTemplate.objects.none()
        
        # Filtrar por loja_id explicitamente
        qs = ContratoTemplate.objects.filter(loja_id=loja_id)
        
        # Filtrar apenas ativos por padrão
        ativo = self.request.query_params.get('ativo')
        if ativo is None or ativo.lower() == 'true':
            qs = qs.filter(ativo=True)
        elif ativo.lower() == 'false':
            qs = qs.filter(ativo=False)
        
        return qs

    @action(detail=True, methods=['post'])
    def marcar_padrao(self, request, pk=None):
        """Marca este template como padrão (desmarca outros)."""
        template = self.get_object()
        template.is_padrao = True
        template.save()  # O método save() do modelo já desmarca outros
        return Response({'message': 'Template marcado como padrão.'})


class ContratoViewSet(BaseModelViewSet):
    """Contratos gerados a partir de oportunidades fechadas."""
    queryset = Contrato.objects.select_related('oportunidade', 'oportunidade__lead').prefetch_related(
        'oportunidade__itens__produto_servico'
    ).all()
    serializer_class = ContratoSerializer
    pagination_class = CRMPagination

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.select_related('oportunidade', 'oportunidade__lead').prefetch_related(
            'oportunidade__itens__produto_servico'
        )
        oportunidade_id = self.request.query_params.get('oportunidade_id')
        if oportunidade_id:
            qs = qs.filter(oportunidade_id=oportunidade_id)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=True, methods=['post'])
    def enviar_cliente(self, request, pk=None):
        """Envia contrato ao cliente por email ou WhatsApp."""
        instance = self.get_object()
        canal = (request.data.get('canal') or '').strip().lower()
        if canal not in ('email', 'whatsapp'):
            return Response(
                {'detail': 'Informe o canal: email ou whatsapp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        ok, err = _enviar_proposta_contrato_cliente(instance, canal, request)
        if ok:
            return Response({'message': f'Contrato enviado ao cliente por {canal} com sucesso.'})
        return Response({'detail': err or 'Erro ao enviar.'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    @invalidate_cache_on_change('contratos')
    def enviar_para_assinatura(self, request, pk=None):
        """
        Inicia workflow de assinatura digital.
        Envia email para cliente com link de assinatura.
        """
        from .assinatura_digital_service import criar_token_assinatura, enviar_email_assinatura_cliente
        
        contrato = self.get_object()
        loja_id = get_current_loja_id()
        
        # Validar que contrato tem oportunidade e lead
        if not contrato.oportunidade or not contrato.oportunidade.lead:
            return Response(
                {'detail': 'Contrato sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        lead = contrato.oportunidade.lead
        if not lead.email:
            return Response(
                {'detail': 'Lead não possui email cadastrado.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar se já existe assinatura pendente
        if contrato.status_assinatura in ['aguardando_cliente', 'aguardando_vendedor']:
            return Response(
                {'detail': f'Contrato já está em processo de assinatura: {contrato.get_status_assinatura_display()}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Criar token de assinatura para cliente
        assinatura = criar_token_assinatura(contrato, 'cliente', loja_id)
        
        # Atualizar status do contrato
        contrato.status_assinatura = 'aguardando_cliente'
        contrato.save(update_fields=['status_assinatura', 'updated_at'])
        
        # Enviar email com link de assinatura
        ok, err = enviar_email_assinatura_cliente(contrato, assinatura, request)
        
        if ok:
            return Response({
                'message': f'Email de assinatura enviado para {lead.email}',
                'status_assinatura': 'aguardando_cliente'
            })
        else:
            # Reverter status se falhou
            contrato.status_assinatura = 'rascunho'
            contrato.save(update_fields=['status_assinatura', 'updated_at'])
            assinatura.delete()
            
            return Response(
                {'detail': err or 'Erro ao enviar email. Tente novamente.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    @invalidate_cache_on_change('contratos')
    def reenviar_para_assinatura(self, request, pk=None):
        """Reenvia e-mail com link de assinatura (novo token) em processo pendente."""
        from .assinatura_digital_service import reenviar_link_assinatura_pendente

        contrato = self.get_object()
        loja_id = get_current_loja_id()

        if not contrato.oportunidade or not contrato.oportunidade.lead:
            return Response(
                {'detail': 'Contrato sem oportunidade ou lead vinculado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ok, msg, err = reenviar_link_assinatura_pendente(contrato, loja_id, request)
        if ok:
            return Response({
                'message': msg,
                'status_assinatura': contrato.status_assinatura,
            })
        if err and err.startswith('Reenvio só é possível'):
            return Response({'detail': err}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': err or 'Erro ao reenviar.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _empty_dashboard_response():
    """Resposta vazia padrão quando não há contexto de loja."""
    return {
        'leads': 0,
        'oportunidades': 0,
        'receita': 0,
        'pipeline_aberto': 0,
        'valor_perdido': 0,
        'meta_vendas': 0,
        'taxa_conversao': 0,
        'pipeline_por_etapa': [],
        'atividades_hoje': [],
        'performance_vendedores': [],
    }


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
            vendedor = Vendedor.objects.filter(id=vendedor_id, loja_id=loja_id).first()
            user_display_name = vendedor.nome if vendedor else request.user.get_full_name() or request.user.username
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
    Dados do dashboard CRM (estilo Salesforce).
    Otimizado: cache 120s, queries consolidadas (pipeline em 1 query).
    
    IMPORTANTE: Owner SEMPRE vê todos os dados, mesmo se tiver vendedor vinculado.
    
    Parâmetros de filtro (query params):
    - periodo: mes_atual (padrão), ultimos_30_dias, ultimos_90_dias, este_ano
    - data_inicio: data inicial (formato YYYY-MM-DD) para período personalizado
    - data_fim: data final (formato YYYY-MM-DD) para período personalizado
    - vendedor_id: ID do vendedor (apenas para owner/admin)
    - status: todas (padrão), abertas, fechadas
    """
    import logging
    from datetime import timedelta

    logger = logging.getLogger(__name__)
    ensure_loja_context(request)
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response(_empty_dashboard_response(), status=200)

    # Verificar se é owner ANTES de aplicar filtro de vendedor
    from superadmin.models import Loja
    is_owner = False
    try:
        loja = Loja.objects.using('default').filter(id=loja_id).first()
        if loja and loja.owner_id == request.user.id:
            is_owner = True
    except Exception:
        pass

    # Parâmetros de filtro
    periodo = request.GET.get('periodo', 'mes_atual')
    data_inicio_param = request.GET.get('data_inicio')
    data_fim_param = request.GET.get('data_fim')
    vendedor_id_filtro = request.GET.get('vendedor_id')
    status_filtro = request.GET.get('status', 'todas')
    
    # Se há filtros ativos, não usar cache
    tem_filtros = (
        periodo != 'mes_atual' or 
        data_inicio_param or 
        data_fim_param or 
        vendedor_id_filtro or 
        status_filtro != 'todas'
    )

    vendedor_id = None if is_owner else get_current_vendedor_id(request)
    
    # Cache apenas se não houver filtros personalizados
    cache_key = None
    if not tem_filtros:
        cache_key = CRMCacheManager.get_cache_key(
            CRMCacheManager.DASHBOARD,
            loja_id,
            vendedor_id
        )
        
        if cache_key:
            from django.core.cache import cache
            cached = cache.get(cache_key)
            if cached:
                return Response(cached)

    last_error = None
    for attempt in range(2):
        try:
            from .models import Lead, Oportunidade, Atividade, Vendedor

            leads_qs = Lead.objects.all()
            opp_qs = Oportunidade.objects.all()
            atividades_qs = Atividade.objects.all()
            vendedores_qs = Vendedor.objects.filter(is_active=True)

            # Aplicar filtro de vendedor APENAS se não for owner
            if vendedor_id is not None:
                leads_qs = leads_qs.filter(
                    Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id)
                ).distinct()
                opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
                # Atividades: vendedor vê suas atividades + órfãs criadas por ele
                atividades_qs = atividades_qs.filter(
                    Q(oportunidade__vendedor_id=vendedor_id) |
                    Q(lead__oportunidades__vendedor_id=vendedor_id) |
                    Q(oportunidade__isnull=True, lead__isnull=True, criado_por_vendedor_id=vendedor_id)
                ).distinct()
                vendedores_qs = vendedores_qs.filter(id=vendedor_id)
            
            # Aplicar filtro de vendedor específico (apenas para owner/admin)
            if is_owner and vendedor_id_filtro and vendedor_id_filtro != 'todos':
                try:
                    vid = int(vendedor_id_filtro)
                    leads_qs = leads_qs.filter(
                        Q(oportunidades__vendedor_id=vid) | Q(vendedor_id=vid)
                    ).distinct()
                    opp_qs = opp_qs.filter(vendedor_id=vid)
                    atividades_qs = atividades_qs.filter(
                        Q(oportunidade__vendedor_id=vid) |
                        Q(lead__oportunidades__vendedor_id=vid) |
                        Q(oportunidade__isnull=True, lead__isnull=True, criado_por_vendedor_id=vid)
                    ).distinct()
                    vendedores_qs = vendedores_qs.filter(id=vid)
                except (ValueError, TypeError):
                    pass
            
            # Calcular intervalo de datas baseado no período
            _hoje = timezone.now().date()
            if periodo == 'personalizado' and data_inicio_param and data_fim_param:
                try:
                    from datetime import datetime
                    data_inicio_filtro = datetime.strptime(data_inicio_param, '%Y-%m-%d').date()
                    data_fim_filtro = datetime.strptime(data_fim_param, '%Y-%m-%d').date()
                except (ValueError, TypeError):
                    data_inicio_filtro = _hoje.replace(day=1)
                    data_fim_filtro = _hoje
            elif periodo == 'ultimos_30_dias':
                data_fim_filtro = _hoje
                data_inicio_filtro = _hoje - timedelta(days=30)
            elif periodo == 'ultimos_90_dias':
                data_fim_filtro = _hoje
                data_inicio_filtro = _hoje - timedelta(days=90)
            elif periodo == 'este_ano':
                data_inicio_filtro = _hoje.replace(month=1, day=1)
                data_fim_filtro = _hoje
            else:  # mes_atual (padrão)
                data_inicio_filtro = _hoje.replace(day=1)
                data_fim_filtro = _hoje
            
            # Aplicar filtro de status
            if status_filtro == 'abertas':
                opp_qs = opp_qs.filter(etapa__in=ETAPAS_EM_ANDAMENTO)
            elif status_filtro == 'fechadas':
                opp_qs = opp_qs.filter(etapa__in=['closed_won', 'closed_lost'])

            # Performance e comissão do mês: usar o intervalo calculado
            data_inicio_mes, data_fim_mes = data_inicio_filtro, data_fim_filtro
            filtro_opp_no_mes = (
                Q(data_fechamento_ganho__gte=data_inicio_mes, data_fechamento_ganho__lte=data_fim_mes)
                | (
                    Q(data_fechamento_ganho__isnull=True)
                    & Q(data_fechamento__gte=data_inicio_mes, data_fechamento__lte=data_fim_mes)
                )
            )

            # 1 query: totais agregados (receita DO MÊS, pipeline, fechados)
            agg = opp_qs.aggregate(
                total_oportunidades=Count('id'),
                receita=Sum('valor', filter=Q(etapa='closed_won') & filtro_opp_no_mes),
                pipeline_aberto=Sum('valor', filter=Q(etapa__in=ETAPAS_EM_ANDAMENTO)),
                oportunidades_em_andamento=Count('id', filter=Q(etapa__in=ETAPAS_EM_ANDAMENTO)),
                total_fechados=Count('id', filter=Q(etapa__in=['closed_won', 'closed_lost'])),
                total_ganhos=Count('id', filter=Q(etapa='closed_won')),
                valor_perdido=Sum('valor', filter=Q(etapa='closed_lost')),
            )
            total_oportunidades = agg['total_oportunidades'] or 0
            receita = float(agg['receita'] or 0)
            pipeline_aberto = float(agg['pipeline_aberto'] or 0)
            oportunidades_em_andamento = agg['oportunidades_em_andamento'] or 0
            total_fechados = agg['total_fechados'] or 0
            total_ganhos = agg['total_ganhos'] or 0
            taxa_conversao = round((total_ganhos / total_fechados * 100), 1) if total_fechados else 0

            # 1 query: pipeline por etapa (values + annotate)
            pipeline_map = {
                row['etapa']: {'valor': float(row['valor'] or 0), 'quantidade': row['qtd'] or 0}
                for row in opp_qs.filter(etapa__in=ETAPAS_PIPELINE)
                .values('etapa')
                .annotate(valor=Sum('valor'), qtd=Count('id'))
            }
            valor_perdido = float(agg.get('valor_perdido') or 0)
            pipeline_por_etapa = [
                {'etapa': e, **(pipeline_map.get(e, {'valor': 0, 'quantidade': 0}))}
                for e in ETAPAS_PIPELINE
            ]

            # 1 query: total leads
            total_leads = leads_qs.count()

            # 1 query: atividades próximas (pendentes + concluídas recentemente)
            hoje_inicio = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            proximos_7_dias = hoje_inicio + timedelta(days=7)

            atividades_pendentes = atividades_qs.filter(
                data__gte=hoje_inicio,
                data__lt=proximos_7_dias,
                concluido=False
            ).order_by('data').values('id', 'titulo', 'tipo', 'data', 'concluido', 'observacoes')[:10]

            if not atividades_pendentes:
                atividades_pendentes = atividades_qs.order_by('-data').values(
                    'id', 'titulo', 'tipo', 'data', 'concluido', 'observacoes'
                )[:5]

            atividades_hoje_data = list(atividades_pendentes)
            for a in atividades_hoje_data:
                if a.get('data'):
                    a['data'] = a['data'].isoformat() if hasattr(a['data'], 'isoformat') else str(a['data'])

            # Performance e comissão do mês: MESMO critério do PDF (relatorios.calcular_periodo('mes_atual')):
            # intervalo [primeiro dia do mês, hoje], inclusive. Antes o dashboard usava só ">= início do mês",
            # incluindo datas futuras ou data_fechamento sem teto, divergindo do relatório.
            _hoje = timezone.now().date()
            data_inicio_mes, data_fim_mes = _hoje.replace(day=1), _hoje
            filtro_oportunidades_no_mes = (
                Q(oportunidades__data_fechamento_ganho__gte=data_inicio_mes, oportunidades__data_fechamento_ganho__lte=data_fim_mes)
                | (
                    Q(oportunidades__data_fechamento_ganho__isnull=True)
                    & Q(
                        oportunidades__data_fechamento__gte=data_inicio_mes,
                        oportunidades__data_fechamento__lte=data_fim_mes,
                    )
                )
            )
            perf_qs = vendedores_qs.annotate(
                receita_mes=Sum(
                    'oportunidades__valor',
                    filter=Q(oportunidades__etapa='closed_won') & filtro_oportunidades_no_mes,
                ),
                comissao_mes=Sum(
                    'oportunidades__valor_comissao',
                    filter=Q(oportunidades__etapa='closed_won') & filtro_oportunidades_no_mes,
                ),
            )
            performance_vendedores = [
                {'id': v.id, 'nome': v.nome, 'receita_mes': float(v.receita_mes or 0), 'comissao_mes': float(v.comissao_mes or 0)}
                for v in perf_qs
            ]

            filtro_opp_no_mes = (
                Q(data_fechamento_ganho__gte=data_inicio_mes, data_fechamento_ganho__lte=data_fim_mes)
                | (
                    Q(data_fechamento_ganho__isnull=True)
                    & Q(data_fechamento__gte=data_inicio_mes, data_fechamento__lte=data_fim_mes)
                )
            )
            comissao_total_mes = opp_qs.filter(etapa='closed_won').filter(filtro_opp_no_mes).aggregate(
                total=Sum('valor_comissao')
            )['total'] or 0

            # Fechadas no mês sem vendedor OU com registro de vendedor inativo somam no administrador (is_admin).
            # Só "vendedor nulo" era mesclado antes — o restante (inativo) gerava linha extra / cache antigo.
            base_fechadas_mes = opp_qs.filter(etapa='closed_won').filter(filtro_opp_no_mes)
            extras_agg = base_fechadas_mes.filter(
                Q(vendedor_id__isnull=True) | Q(vendedor__is_active=False)
            ).aggregate(receita=Sum('valor'), comissao=Sum('valor_comissao'))
            rec_sem = float(extras_agg['receita'] or 0)
            com_sem = float(extras_agg['comissao'] or 0)
            if rec_sem > 0 or com_sem > 0:
                from .utils import get_vendedor_destino_merge_loja

                admin_v = get_vendedor_destino_merge_loja(loja_id)
                if admin_v:
                    merged = False
                    for row in performance_vendedores:
                        if row['id'] == admin_v.id:
                            row['receita_mes'] += rec_sem
                            row['comissao_mes'] += com_sem
                            merged = True
                            break
                    if not merged:
                        performance_vendedores.append(
                            {
                                'id': admin_v.id,
                                'nome': admin_v.nome,
                                'receita_mes': rec_sem,
                                'comissao_mes': com_sem,
                            }
                        )
                else:
                    performance_vendedores.append(
                        {
                            'id': None,
                            'nome': 'Sem vendedor',
                            'receita_mes': rec_sem,
                            'comissao_mes': com_sem,
                        }
                    )
            performance_vendedores.sort(key=lambda x: -x['receita_mes'])

            payload = {
                'leads': total_leads,
                'oportunidades': total_oportunidades,
                'receita': receita,
                'pipeline_aberto': pipeline_aberto,
                'oportunidades_em_andamento': oportunidades_em_andamento,
                'valor_perdido': valor_perdido,
                'meta_vendas': 0,
                'taxa_conversao': taxa_conversao,
                'pipeline_por_etapa': pipeline_por_etapa,
                'atividades_hoje': atividades_hoje_data,
                'performance_vendedores': performance_vendedores,
                'comissao_total_mes': float(comissao_total_mes),
            }
            if cache_key:
                from django.core.cache import cache
                cache.set(cache_key, payload, 120)
            return Response(payload)
        except Exception as e:
            last_error = e
            from django.db.utils import ProgrammingError, OperationalError
            if isinstance(e, (ProgrammingError, OperationalError)) and attempt == 0:
                from superadmin.models import Loja
                from .schema_service import configurar_schema_crm_loja
                loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
                if loja and configurar_schema_crm_loja(loja):
                    continue
            logger.exception('Erro no dashboard CRM: %s', e)
            if isinstance(last_error, (ProgrammingError, OperationalError)):
                return Response(
                    {
                        'detail': 'O banco de dados da loja precisa ser configurado. Entre em contato com o suporte.',
                        'code': 'SCHEMA_NOT_CONFIGURED',
                    },
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
        import logging
        logger = logging.getLogger(__name__)
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

    @require_admin_access()
    def get(self, request):
        config = self._get_config(request)
        if config is None:
            return Response(
                {'error': 'Contexto de loja não encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return Response({
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
        })

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
        loja = config.loja
        owner_telefone = (getattr(loja, 'owner_telefone', None) or '').strip()
        return Response({
            'enviar_confirmacao': config.enviar_confirmacao,
            'enviar_lembrete_24h': config.enviar_lembrete_24h,
            'enviar_lembrete_2h': config.enviar_lembrete_2h,
            'enviar_cobranca': config.enviar_cobranca,
            'enviar_lembrete_tarefas': getattr(config, 'enviar_lembrete_tarefas', True),
            'owner_telefone': owner_telefone,
            'whatsapp_numero': (config.whatsapp_numero or '').strip(),
            'whatsapp_ativo': getattr(config, 'whatsapp_ativo', False),
            'whatsapp_phone_id': (config.whatsapp_phone_id or '').strip(),
            'whatsapp_token_set': bool((config.whatsapp_token or '').strip()),
        })


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
    vendedor_id = get_current_vendedor_id(request)

    from .models import Lead, Oportunidade, Conta

    q_filter = Q(nome__icontains=term) | Q(empresa__icontains=term) | Q(email__icontains=term) | Q(telefone__icontains=term)
    leads_qs = Lead.objects.filter(q_filter)
    if vendedor_id is not None:
        leads_qs = leads_qs.filter(
            Q(oportunidades__vendedor_id=vendedor_id) | Q(vendedor_id=vendedor_id)
        ).distinct()
    leads_qs = list(leads_qs.values('id', 'nome', 'empresa', 'status')[:limit])

    opp_filter = (
        Q(titulo__icontains=term) |
        Q(lead__nome__icontains=term) |
        Q(lead__empresa__icontains=term) |
        Q(lead__conta__nome__icontains=term)
    )
    opp_qs = Oportunidade.objects.filter(opp_filter)
    if vendedor_id is not None:
        opp_qs = opp_qs.filter(vendedor_id=vendedor_id)
    opp_qs = list(opp_qs.values('id', 'titulo', 'valor', 'etapa', 'lead__nome', 'lead__empresa')[:limit])

    conta_filter = Q(nome__icontains=term) | Q(email__icontains=term) | Q(telefone__icontains=term)
    contas_qs = Conta.objects.filter(conta_filter)
    if vendedor_id is not None:
        contas_qs = contas_qs.filter(vendedor_id=vendedor_id)
    contas_qs = list(contas_qs.values('id', 'nome', 'segmento')[:limit])

    def lead_item(r):
        return {'id': r['id'], 'nome': r['nome'], 'empresa': r['empresa'] or '', 'status': r['status']}

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
        return {'id': r['id'], 'nome': r['nome'], 'segmento': r['segmento'] or ''}

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
        config = CRMConfig.get_or_create_for_loja(loja_id)
    except Exception as e:
        from django.db.utils import ProgrammingError, OperationalError
        if isinstance(e, (ProgrammingError, OperationalError)):
            # Auto-recovery: tentar configurar schema e retry
            from superadmin.models import Loja
            from .schema_service import configurar_schema_crm_loja
            loja = Loja.objects.filter(id=loja_id).select_related('tipo_loja').first()
            if loja and configurar_schema_crm_loja(loja):
                try:
                    config = CRMConfig.get_or_create_for_loja(loja_id)
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
        serializer = CRMConfigSerializer(config, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Invalidar cache do dashboard quando configurações mudarem
            CRMCacheManager.invalidate_dashboard(loja_id)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def gerar_relatorio(request):
    """
    Gera relatório de vendas em PDF.
    
    POST /crm-vendas/relatorios/gerar/
    Body: {
        "tipo": "vendas_total" | "vendas_vendedor" | "comissoes",
        "periodo": "mes_atual" | "mes_passado" | etc,
        "vendedor_id": 123 (opcional, apenas para vendas_vendedor),
        "acao": "pdf" | "email"
    }
    
    Vendedores só podem gerar relatórios das próprias vendas.
    Admin (proprietário) vê todos os relatórios.
    """
    try:
        from .relatorios import gerar_relatorio_vendas_total, gerar_relatorio_vendas_vendedor
    except ImportError as e:
        logger.error(f'Erro ao importar módulo de relatórios: {e}')
        return Response({
            'detail': 'Módulo de relatórios não disponível. Entre em contato com o suporte.'
        }, status=500)
    
    from superadmin.models import Loja
    
    loja_id = get_current_loja_id()
    if not loja_id:
        return Response({'detail': 'Loja não identificada.'}, status=400)
    
    current_vendedor_id = get_current_vendedor_id(request)
    tipo = request.data.get('tipo', 'vendas_total')
    periodo = request.data.get('periodo', 'mes_atual')
    vendedor_id = request.data.get('vendedor_id')
    acao = request.data.get('acao', 'pdf')
    
    # Verificar se é o proprietário da loja (admin tem acesso total)
    loja = Loja.objects.using('default').get(id=loja_id)
    is_owner = (request.user.id == loja.owner_id)
    
    # Vendedores (NÃO owners): restringir a apenas suas próprias vendas
    if current_vendedor_id is not None and not is_owner:
        if tipo == 'vendas_total':
            return Response(
                {'detail': 'Vendedores só podem gerar relatórios das próprias vendas. Use "Vendas por Vendedor" ou "Comissões".'},
                status=status.HTTP_403_FORBIDDEN
            )
        # Forçar vendedor_id = próprio (ignorar o que veio no request)
        vendedor_id = current_vendedor_id
    
    try:
        # Gerar PDF
        if tipo == 'vendas_total':
            pdf_buffer = gerar_relatorio_vendas_total(loja_id, periodo)
            filename = f'relatorio_vendas_total_{periodo}.pdf'
        elif tipo in ['vendas_vendedor', 'comissoes']:
            pdf_buffer = gerar_relatorio_vendas_vendedor(loja_id, periodo, vendedor_id)
            filename = f'relatorio_vendas_vendedor_{periodo}.pdf'
        else:
            return Response({'detail': 'Tipo de relatório inválido.'}, status=400)
        
        # Se ação for PDF, retornar arquivo
        if acao == 'pdf':
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        # Se ação for email, enviar por email
        elif acao == 'email':
            loja = Loja.objects.using('default').get(id=loja_id)
            user_email = request.user.email
            
            if not user_email:
                return Response({'detail': 'Usuário não possui email cadastrado.'}, status=400)
            
            email = EmailMessage(
                subject=f'Relatório de Vendas - {loja.nome}',
                body=f'Segue em anexo o relatório de vendas solicitado.\n\nPeríodo: {periodo}\nTipo: {tipo}',
                from_email='noreply@lwksistemas.com.br',
                to=[user_email],
            )
            
            email.attach(filename, pdf_buffer.read(), 'application/pdf')
            email.send(fail_silently=False)
            
            return Response({
                'success': True,
                'message': f'Relatório enviado para {user_email}'
            })
        
        else:
            return Response({'detail': 'Ação inválida.'}, status=400)
            
    except Exception as e:
        logger.exception(f'Erro ao gerar relatório: {e}')
        return Response({'detail': f'Erro ao gerar relatório: {str(e)}'}, status=500)



# ============================================================================
# VIEWS PÚBLICAS DE ASSINATURA DIGITAL (sem autenticação)
# ============================================================================

from django.views import View
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


def _configurar_tenant_para_assinatura_publica(loja_id):
    """
    Garante search_path / banco do tenant antes de consultar AssinaturaDigital.
    Sem isso, o manager usa apenas 'default' e o token não é encontrado no schema da loja.
    Retorna None se OK, ou string de erro para o cliente.
    """
    from tenants.middleware import set_current_loja_id, set_current_tenant_db
    from superadmin.models import Loja
    from core.db_config import ensure_loja_database_config

    set_current_loja_id(loja_id)
    loja = Loja.objects.using('default').filter(id=loja_id).first()
    if not loja:
        logger.error(f'[AssinaturaPublica] Loja id={loja_id} inexistente (token válido mas loja apagada?)')
        return 'Link de assinatura inválido.'

    db_name = getattr(loja, 'database_name', None) or f'loja_{getattr(loja, "slug", "")}'
    if not ensure_loja_database_config(db_name, conn_max_age=0) or db_name not in settings.DATABASES:
        logger.error(f'[AssinaturaPublica] Falha ensure_loja_database_config para db_name={db_name!r}')
        return 'Serviço temporariamente indisponível. Tente novamente ou solicite um novo link de assinatura.'

    set_current_tenant_db(db_name)
    logger.info(f'✅ [AssinaturaPublica] tenant db={db_name} loja_id={loja_id}')
    return None


@method_decorator(csrf_exempt, name='dispatch')
class AssinaturaPublicaView(View):
    """
    View pública para assinatura digital de propostas e contratos.
    GET /api/crm-vendas/assinar/{token}/ - Retorna dados do documento
    POST /api/crm-vendas/assinar/{token}/ - Registra assinatura
    """
    
    def get(self, request, token):
        """Retorna dados do documento para assinatura"""
        from .assinatura_digital_service import verificar_token_assinatura, normalizar_token_assinatura_url
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)
        preview = (token[:50] + '…') if len(token) > 50 else token
        logger.info(f'🔍 Recebendo requisição de assinatura - Token (preview): {preview}')

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
            logger.info(f'📦 Token decodificado - loja_id={loja_id}, doc_type={payload.get("doc_type")}, doc_id={payload.get("doc_id")}')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            logger.error('❌ Token não contém loja_id')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        # PASSO 2: Configurar tenant (obrigatório — antes caía em default sem schema)
        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            logger.warning(f'❌ Erro ao verificar token: {erro}')
            return JsonResponse({'error': erro}, status=400)
        
        logger.info(f'✅ Token válido - Assinatura ID: {assinatura.id}, Loja ID: {assinatura.loja_id}')
        
        documento = assinatura.documento
        
        # Determinar tipo de documento
        tipo_documento = 'proposta' if assinatura.proposta else 'contrato'
        
        # Retornar dados do documento
        return JsonResponse({
            'tipo_documento': tipo_documento,
            'titulo': documento.titulo,
            'valor_total': str(documento.valor_total or '0.00'),
            'nome_assinante': assinatura.nome_assinante,
            'tipo_assinante': assinatura.tipo,
            'tipo_assinante_display': assinatura.get_tipo_display(),
            'lead_nome': documento.oportunidade.lead.nome if documento.oportunidade else '',
            'lead_empresa': getattr(documento.oportunidade.lead, 'empresa', '') if documento.oportunidade else '',
        })
    
    def post(self, request, token):
        """Registra a assinatura"""
        from .assinatura_digital_service import (
            verificar_token_assinatura,
            registrar_assinatura,
            criar_token_assinatura,
            enviar_email_assinatura_vendedor,
            enviar_pdf_final,
            normalizar_token_assinatura_url,
        )
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            return JsonResponse({'error': erro}, status=400)
        
        # Obter IP do cliente
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')
        
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Registrar assinatura
        proximo_status = registrar_assinatura(assinatura, ip_address, user_agent)
        
        documento = assinatura.documento
        
        # Se cliente assinou, criar token e enviar para vendedor
        if proximo_status == 'aguardando_vendedor':
            try:
                assinatura_vendedor = criar_token_assinatura(documento, 'vendedor', loja_id)
                enviar_email_assinatura_vendedor(documento, assinatura_vendedor, request)
                
                logger.info(
                    f'Cliente assinou, email enviado para vendedor: '
                    f'documento={documento.__class__.__name__}#{documento.id}'
                )
            except Exception as e:
                logger.exception(f'Erro ao enviar email para vendedor: {e}')
                # Não falha a assinatura do cliente se email do vendedor falhar
        
        # Se vendedor assinou, enviar PDF final
        elif proximo_status == 'concluido':
            try:
                # Enviar PDF final de forma síncrona (rápido, não precisa de background)
                enviar_pdf_final(documento, loja_id)
                logger.info(
                    f'Vendedor assinou, PDF final enviado: '
                    f'documento={documento.__class__.__name__}#{documento.id}'
                )
            except Exception as e:
                logger.exception(f'Erro ao enviar PDF final: {e}')
                # Não falha a assinatura se envio do PDF falhar
        
        return JsonResponse({
            'success': True,
            'message': 'Documento assinado com sucesso!',
            'proximo_status': proximo_status,
            'proximo_status_display': documento.get_status_assinatura_display() if hasattr(documento, 'get_status_assinatura_display') else proximo_status
        })



@method_decorator(csrf_exempt, name='dispatch')
class AssinaturaPdfView(View):
    """
    View pública para visualizar/baixar PDF do documento antes de assinar.
    GET /api/crm-vendas/assinar/{token}/pdf/ - Retorna PDF do documento
    """
    
    def get(self, request, token):
        """Retorna PDF do documento para visualização"""
        from .assinatura_digital_service import verificar_token_assinatura, normalizar_token_assinatura_url
        from .pdf_proposta_contrato import gerar_pdf_proposta, gerar_pdf_contrato
        from django.http import HttpResponse
        from django.core.signing import loads, BadSignature

        token = normalizar_token_assinatura_url(token)
        logger.info(f'📄 Requisição de PDF - Token (preview): {(token[:50] + "…") if len(token) > 50 else token}')

        # PASSO 1: Decodificar token para extrair loja_id
        try:
            payload = loads(token)
            loja_id = payload.get('loja_id')
        except (BadSignature, Exception) as e:
            logger.error(f'❌ Erro ao decodificar token para PDF: {e}')
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        if not loja_id:
            return JsonResponse({'error': 'Link de assinatura inválido.'}, status=400)

        cfg_err = _configurar_tenant_para_assinatura_publica(loja_id)
        if cfg_err:
            status = 503 if 'indisponível' in cfg_err.lower() else 400
            return JsonResponse({'error': cfg_err}, status=status)

        # PASSO 3: Buscar token no banco (agora com contexto correto)
        assinatura, erro, _ = verificar_token_assinatura(token, loja_id=loja_id)
        
        if erro:
            logger.warning(f'❌ Erro ao verificar token para PDF: {erro}')
            return JsonResponse({'error': erro}, status=400)
        
        documento = assinatura.documento
        
        try:
            # Gerar PDF sem assinaturas (documento ainda não foi assinado)
            if assinatura.proposta:
                pdf_buffer = gerar_pdf_proposta(documento, incluir_assinaturas=False)
                filename = f'proposta_{documento.titulo or documento.id}.pdf'
            else:
                pdf_buffer = gerar_pdf_contrato(documento, incluir_assinaturas=False)
                filename = f'contrato_{documento.titulo or documento.id}.pdf'
            
            pdf_buffer.seek(0)
            
            logger.info(f'✅ PDF gerado com sucesso: {filename}')
            
            response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            return response
            
        except Exception as e:
            logger.exception(f'Erro ao gerar PDF: {e}')
            return JsonResponse({'error': 'Erro ao gerar PDF'}, status=500)
