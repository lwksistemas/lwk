"""
Views de Documentos Clínicos — Templates e Documentos da Consulta
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_CLINICAL
from rest_framework import status

from .models import Consulta, DocumentoClinico, DocumentTemplate, Professional
from .serializers import DocumentoClinicoSerializer, DocumentTemplateSerializer
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, resolve_loja_id_from_request
from .documento_service import criar_documento, render_template
from .utils import LojaContextHelper


def _documentos_da_consulta(consulta):
    """Lista documentos da consulta no schema correto (evita lista vazia após POST 201)."""
    from tenants.middleware import get_current_tenant_db

    tenant_db = get_current_tenant_db()
    qs = DocumentoClinico.objects.all_without_filter().filter(
        consulta_id=consulta.id,
    ).select_related('professional', 'template').order_by('-created_at')
    if tenant_db and tenant_db != 'default':
        qs = qs.using(tenant_db)
    return qs


def _get_professional_from_request(request):
    """
    Resolve o Professional do usuário logado na loja atual.
    Verifica:
    1. ProfissionalUsuario (acesso por vínculo)
    2. Owner da loja (admin habilitado como profissional)
    Retorna Professional ou None.
    """
    from superadmin.models import Loja, ProfissionalUsuario

    loja_id = resolve_loja_id_from_request(request)
    if not loja_id:
        return None

    # 1. Vínculo ProfissionalUsuario
    vinculo = ProfissionalUsuario.objects.using('default').filter(
        user=request.user,
        loja_id=loja_id,
    ).first()
    if vinculo:
        prof = Professional.objects.filter(pk=vinculo.professional_id).first()
        if prof:
            return prof

    # 2. Owner da loja — profissional vinculado (admin habilitado) ou email
    try:
        loja = Loja.objects.using('default').get(pk=loja_id)
        if loja.owner_id == request.user.id:
            owner_prof_id = LojaContextHelper.get_owner_professional_id()
            if owner_prof_id:
                prof = Professional.objects.filter(pk=owner_prof_id, is_active=True).first()
                if prof:
                    return prof
            if request.user.email:
                return Professional.objects.filter(
                    email=request.user.email, is_active=True,
                ).first()
    except Loja.DoesNotExist:
        pass

    return None


class DocumentTemplateListView(APIView):
    """
    GET  /clinica-beleza/templates/ — lista templates do profissional logado.
    POST /clinica-beleza/templates/ — cria novo template.

    Query params:
        ?tipo=receituario — filtra por tipo
        ?page=1&page_size=20 — paginação (opcional, retrocompatível)
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request):
        professional = _get_professional_from_request(request)
        if not professional:
            return Response(
                {'error': 'Profissional não encontrado para o usuário logado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        qs = DocumentTemplate.objects.filter(
            professional=professional,
            is_active=True,
        ).order_by('-updated_at')

        tipo = request.query_params.get('tipo')
        if tipo:
            qs = qs.filter(tipo=tipo)

        return paginate_queryset(qs, request, DocumentTemplateSerializer)

    def post(self, request):
        professional = _get_professional_from_request(request)
        if not professional:
            return Response(
                {'error': 'Profissional não encontrado para o usuário logado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DocumentTemplateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(professional=professional)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DocumentTemplateDetailView(GetObjectMixin, APIView):
    """
    GET    /clinica-beleza/templates/<id>/ — detalhe do template
    PUT    /clinica-beleza/templates/<id>/ — atualiza template
    DELETE /clinica-beleza/templates/<id>/ — soft-delete (is_active=False)
    """
    permission_classes = CLINICA_CLINICAL
    model_class = DocumentTemplate
    not_found_message = 'Template não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(DocumentTemplateSerializer(obj).data)

    def put(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = DocumentTemplateSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ═══════════════════════════════════════════════════════════════════════════════
# DOCUMENTOS DA CONSULTA
# ═══════════════════════════════════════════════════════════════════════════════


def _get_consulta_or_none(consulta_id):
    from .consulta_queries import get_consulta_for_tenant

    return get_consulta_for_tenant(
        consulta_id,
        select_related=('patient', 'professional', 'procedure'),
    )


class ConsultaDocumentoListView(APIView):
    """
    GET  /clinica-beleza/consultas/<consulta_id>/documentos/ — lista documentos da consulta.
    POST /clinica-beleza/consultas/<consulta_id>/documentos/ — cria documento na consulta.
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, consulta_id):
        consulta = _get_consulta_or_none(consulta_id)
        if not consulta:
            return Response({'error': 'Consulta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        documentos = _documentos_da_consulta(consulta)
        serializer = DocumentoClinicoSerializer(documentos, many=True)
        return Response(serializer.data)

    def post(self, request, consulta_id):
        consulta = _get_consulta_or_none(consulta_id)
        if not consulta:
            return Response({'error': 'Consulta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if consulta.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Documentos só podem ser criados em consultas em atendimento (IN_PROGRESS).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        professional = _get_professional_from_request(request)
        if not professional:
            return Response(
                {'error': 'Profissional não encontrado para o usuário logado.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = request.data
        tipo = data.get('tipo', '')
        titulo = data.get('titulo', '')
        template_id = data.get('template_id')
        conteudo = data.get('conteudo', '')

        template_obj = None
        if template_id:
            try:
                template_obj = DocumentTemplate.objects.get(pk=template_id, is_active=True)
            except DocumentTemplate.DoesNotExist:
                return Response({'error': 'Template não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

            context = {
                'patient': consulta.patient,
                'professional': professional,
                'consulta': consulta,
            }
            conteudo = render_template(template_obj.conteudo, context)

        documento = criar_documento(
            consulta=consulta,
            professional=professional,
            tipo=tipo,
            conteudo=conteudo,
            template=template_obj,
            titulo=titulo,
        )
        serializer = DocumentoClinicoSerializer(documento)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConsultaDocumentoDeleteView(GetObjectMixin, APIView):
    """
    DELETE /clinica-beleza/consultas/<consulta_id>/documentos/<doc_id>/ — exclui documento.
    Só permite exclusão se a consulta está IN_PROGRESS.
    """
    permission_classes = CLINICA_CLINICAL
    model_class = DocumentoClinico
    not_found_message = 'Documento não encontrado'
    select_related_fields = ['consulta']

    def delete(self, request, consulta_id, doc_id):
        consulta = _get_consulta_or_none(consulta_id)
        if not consulta:
            return Response({'error': 'Consulta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        obj = _documentos_da_consulta(consulta).filter(pk=doc_id).first()
        if not obj:
            return Response({'error': 'Documento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Valida que a consulta está IN_PROGRESS
        if obj.consulta.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Só é possível excluir documentos de consultas em atendimento (IN_PROGRESS).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
