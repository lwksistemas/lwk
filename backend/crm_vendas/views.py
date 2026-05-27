from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count, Q, Exists, OuterRef
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.conf import settings
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
    AtividadeListSerializer,
    ProdutoServicoSerializer,
    CategoriaProdutoServicoSerializer,
    OportunidadeItemSerializer,
    PropostaSerializer,
    PropostaTemplateSerializer,
    ContratoTemplateSerializer,
    ContratoSerializer,
)
from tenants.middleware import get_current_loja_id, ensure_loja_context
from .utils import get_current_vendedor_id, get_loja_from_context
from .mixins import CRMPermissionMixin, VendedorFilterMixin, CacheInvalidationMixin
from .cache import CRMCacheManager
from .decorators import cache_list_response, require_admin_access, invalidate_cache_on_change
from .mixins_assinatura import AssinaturaDigitalMixin
from .mixins_documento import DocumentoQuerysetMixin, EnviarClienteMixin, TemplateViewSetMixin
from .services import (
    PropostaService,
    ContratoService,
    ProdutoServicoService,
)
from .vendedor_admin_service import (
    aplicar_cache_control_sem_store,
    ajustar_lista_vendedores_com_admin,
    listar_grupos_crm_disponiveis,
    reenviar_senha_administrador_loja,
    reenviar_senha_vendedor,
    resposta_vendedor_me,
)

from .views_common import CRMPagination

logger = logging.getLogger(__name__)


class VendedorViewSet(CRMPermissionMixin, BaseModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer
    pagination_class = CRMPagination  # ✅ OTIMIZAÇÃO: Paginação

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
        loja_id = get_current_loja_id()
        for attempt in range(2):
            try:
                response = super().list(request, *args, **kwargs)
                loja_id = get_current_loja_id()
                if loja_id:
                    from superadmin.models import Loja

                    try:
                        loja = Loja.objects.select_related('owner').get(id=loja_id)
                        data = response.data
                        results = list(
                            data.get('results', []) if isinstance(data, dict) else (data or [])
                        )
                        results = ajustar_lista_vendedores_com_admin(
                            loja,
                            loja_id,
                            results,
                            serialize_vendedor=lambda v: self.get_serializer(v).data,
                        )
                        if isinstance(data, dict):
                            response.data['results'] = results
                            response.data['count'] = len(results)
                        else:
                            response.data = results
                    except Loja.DoesNotExist:
                        pass
                aplicar_cache_control_sem_store(response)
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
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return resposta_vendedor_me(request, loja_id)

    @action(detail=False, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha_administrador(self, request):
        """Reenvia senha provisória do administrador (Loja.owner)."""
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload, erro, http_status = reenviar_senha_administrador_loja(loja_id)
        if erro:
            return Response({'detail': erro}, status=http_status)
        return Response(payload, status=http_status)

    @action(detail=True, methods=['post'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def reenviar_senha(self, request, pk=None):
        """Gera nova senha provisória e envia por e-mail. Funciona para vendedores e para o admin (owner)."""
        loja_id = get_current_loja_id()
        if not loja_id:
            return Response(
                {'detail': 'Contexto de loja não encontrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        payload, erro, http_status = reenviar_senha_vendedor(loja_id, self.get_object())
        if erro:
            return Response({'detail': erro}, status=http_status)
        return Response(payload, status=http_status)

    @action(detail=False, methods=['get'])
    @require_admin_access('Vendedores não têm permissão para acessar configurações de funcionários.')
    def grupos_disponiveis(self, request):
        """Lista grupos disponíveis para atribuir a vendedores."""
        return Response(listar_grupos_crm_disponiveis())


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
        """Cancela a proposta com motivo obrigatório. Move a oportunidade para 'Fechado perdido'."""
        proposta = self.get_object()
        if proposta.status == 'cancelada':
            return Response({'detail': 'Proposta já está cancelada.'}, status=status.HTTP_400_BAD_REQUEST)
        motivo = (request.data.get('motivo') or '').strip()
        if not motivo:
            return Response({'detail': 'Informe o motivo do cancelamento.'}, status=status.HTTP_400_BAD_REQUEST)
        proposta.status = 'cancelada'
        proposta.motivo_cancelamento = motivo
        # Cancelar assinatura digital se estiver em andamento
        if proposta.status_assinatura not in ('rascunho', 'concluido', 'cancelado'):
            proposta.status_assinatura = 'cancelado'
            proposta.save(update_fields=['status', 'motivo_cancelamento', 'status_assinatura', 'updated_at'])
        else:
            proposta.save(update_fields=['status', 'motivo_cancelamento', 'updated_at'])

        # Mover oportunidade para "Fechado perdido" automaticamente
        oportunidade = proposta.oportunidade
        if oportunidade and oportunidade.etapa not in ('closed_won', 'closed_lost'):
            from django.utils import timezone
            oportunidade.etapa = 'closed_lost'
            oportunidade.data_fechamento_perdido = timezone.now().date()
            oportunidade.save(update_fields=['etapa', 'data_fechamento_perdido', 'updated_at'])

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
from .crm_config_helpers import get_crm_config_for_loja as _get_crm_config_for_loja  # noqa: F401, E402
from .views_config import (  # noqa: F401, E402
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
from .views_pipelines import AtividadeViewSet, OportunidadeViewSet  # noqa: F401, E402
