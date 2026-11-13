"""ViewSets de propostas, contratos e templates."""
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import BaseModelViewSet

from .mixins import CrmGranularPermissionMixin, CRMSchemaRecoveryMixin, VendedorFilterMixin
from .mixins_assinatura import AssinaturaDigitalMixin
from .mixins_documento import DocumentoQuerysetMixin, TemplateViewSetMixin
from .models import Contrato, ContratoTemplate, NfseDescricaoTemplate, Proposta, PropostaTemplate
from .serializers import (
    ContratoSerializer,
    ContratoTemplateSerializer,
    NfseDescricaoTemplateSerializer,
    PropostaSerializer,
    PropostaTemplateSerializer,
)
from .serializers.documentos import MENSAGEM_DOCUMENTO_ASSINADO, documento_assinado_pelas_duas_partes
from .views_common import CRMPagination


def _resposta_documento_assinado(documento):
    if documento_assinado_pelas_duas_partes(documento):
        return Response({"detail": MENSAGEM_DOCUMENTO_ASSINADO}, status=status.HTTP_400_BAD_REQUEST)
    return None


class PropostaViewSet(
    CRMSchemaRecoveryMixin,
    CrmGranularPermissionMixin,
    AssinaturaDigitalMixin,
    DocumentoQuerysetMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Proposta.objects.all()
    serializer_class = PropostaSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = "oportunidade__vendedor_id"
    vendedor_filter_related = []
    vendedor_escopo_qualidade = True

    assinatura_doc_label = "Proposta"
    assinatura_cache_key = "propostas"
    crm_permission_model = "proposta"

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied

        from .acesso_oportunidade import oportunidade_do_usuario

        oportunidade = serializer.validated_data.get("oportunidade")
        if not oportunidade_do_usuario(self.request, getattr(oportunidade, "id", oportunidade)):
            raise PermissionDenied("Esta oportunidade é de outro vendedor.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        bloqueio = _resposta_documento_assinado(self.get_object())
        if bloqueio:
            return bloqueio
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def confirmar_pedido(self, request, pk=None):
        proposta = self.get_object()
        bloqueio = _resposta_documento_assinado(proposta)
        if bloqueio:
            return bloqueio
        if proposta.status != "aceita":
            return Response(
                {
                    "detail": (
                        f"Apenas propostas Aceitas podem ser confirmadas como Pedido. "
                        f"Status atual: {proposta.get_status_display()}."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposta.status = "pedido"
        proposta.save(update_fields=["status", "updated_at"])
        return Response({"detail": "Proposta confirmada como Pedido.", "status": "pedido"})

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        proposta = self.get_object()
        bloqueio = _resposta_documento_assinado(proposta)
        if bloqueio:
            return bloqueio
        if proposta.status == "cancelada":
            return Response(
                {"detail": "Proposta já está cancelada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get("motivo") or "").strip()
        if not motivo:
            return Response(
                {"detail": "Informe o motivo do cancelamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        proposta.status = "cancelada"
        proposta.motivo_cancelamento = motivo
        if proposta.status_assinatura not in ("rascunho", "concluido", "cancelado"):
            proposta.status_assinatura = "cancelado"
            proposta.save(
                update_fields=["status", "motivo_cancelamento", "status_assinatura", "updated_at"],
            )
        else:
            proposta.save(update_fields=["status", "motivo_cancelamento", "updated_at"])

        oportunidade = proposta.oportunidade
        if oportunidade and oportunidade.etapa not in ("closed_won", "closed_lost"):
            oportunidade.etapa = "closed_lost"
            oportunidade.data_fechamento_perdido = timezone.now().date()
            oportunidade.save(update_fields=["etapa", "data_fechamento_perdido", "updated_at"])

        return Response({"detail": "Proposta cancelada com sucesso.", "status": "cancelada"})

    @action(detail=True, methods=["post"])
    def renovar_validade(self, request, pk=None):
        """Reinicia o prazo comercial. Não mexe em número, valores nem em proposta assinada."""
        from .proposta_identificacao import validar_dias_comerciais

        proposta = self.get_object()
        bloqueio = _resposta_documento_assinado(proposta)
        if bloqueio:
            return bloqueio
        informado = request.data.get("validade_dias", proposta.validade_dias)
        try:
            dias = validar_dias_comerciais(informado)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        proposta.validade_dias = dias
        proposta.validade_inicio = timezone.localdate()
        proposta.save(update_fields=["validade_dias", "validade_inicio", "updated_at"])
        return Response(self.get_serializer(proposta).data)

    @action(detail=True, methods=["post"])
    def reemitir(self, request, pk=None):
        """Cria outra proposta com o próximo número. A original, assinada ou não, permanece."""
        origem = self.get_object()
        nova = Proposta(
            loja_id=origem.loja_id,
            oportunidade_id=origem.oportunidade_id,
            titulo=origem.titulo,
            conteudo=origem.conteudo,
            valor_total=origem.valor_total,
            desconto_tipo=origem.desconto_tipo,
            desconto_valor=origem.desconto_valor,
            validade_dias=origem.validade_dias or 15,
            observacoes=origem.observacoes,
            nome_vendedor_assinatura=origem.nome_vendedor_assinatura,
            nome_cliente_assinatura=origem.nome_cliente_assinatura,
            emitente_nome=origem.emitente_nome,
            emitente_endereco=origem.emitente_endereco,
            emitente_cpf_cnpj=origem.emitente_cpf_cnpj,
            emitente_responsavel=origem.emitente_responsavel,
            emitente_email=origem.emitente_email,
            canal_assinatura_vendedor=origem.canal_assinatura_vendedor,
            status="rascunho",
            status_assinatura="rascunho",
        )
        nova.save()
        return Response(self.get_serializer(nova).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        from .pdf_proposta_contrato import gerar_pdf_proposta

        proposta = self.get_object()
        try:
            incluir_assinaturas = proposta.status_assinatura == "concluido"
            pdf_buffer = gerar_pdf_proposta(proposta, incluir_assinaturas=incluir_assinaturas)
            pdf_bytes = pdf_buffer.getvalue()
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            from .nome_arquivo import nome_arquivo_download

            filename = nome_arquivo_download(
                "proposta", proposta.numero or proposta.id, proposta.titulo, extensao="pdf",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": "Erro ao gerar PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def download_docx(self, request, pk=None):
        from .docx_proposta_contrato import gerar_docx_proposta

        proposta = self.get_object()
        try:
            docx_buffer = gerar_docx_proposta(proposta)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            from .nome_arquivo import nome_arquivo_download

            filename = nome_arquivo_download(
                "proposta", proposta.numero or proposta.id, proposta.titulo, extensao="docx",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": "Erro ao gerar DOCX."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PropostaTemplateViewSet(CRMSchemaRecoveryMixin, TemplateViewSetMixin, BaseModelViewSet):
    queryset = PropostaTemplate.objects.all()
    serializer_class = PropostaTemplateSerializer
    pagination_class = CRMPagination
    template_model = PropostaTemplate

    def get_queryset(self):
        qs = super().get_queryset().select_related("prestadora")
        prestadora = (self.request.query_params.get("prestadora") or "").strip()
        if not prestadora:
            return qs
        if not prestadora.isdigit():
            return qs.none()
        return qs.filter(prestadora_id=int(prestadora))


class ContratoTemplateViewSet(CRMSchemaRecoveryMixin, TemplateViewSetMixin, BaseModelViewSet):
    queryset = ContratoTemplate.objects.all()
    serializer_class = ContratoTemplateSerializer
    pagination_class = CRMPagination
    template_model = ContratoTemplate


class NfseDescricaoTemplateViewSet(CRMSchemaRecoveryMixin, TemplateViewSetMixin, BaseModelViewSet):
    queryset = NfseDescricaoTemplate.objects.all()
    serializer_class = NfseDescricaoTemplateSerializer
    pagination_class = CRMPagination
    template_model = NfseDescricaoTemplate

    def get_queryset(self):
        qs = super().get_queryset().select_related("prestadora")
        prestadora = (self.request.query_params.get("prestadora") or "").strip()
        if not prestadora:
            return qs
        if not prestadora.isdigit():
            return qs.none()
        return qs.filter(prestadora_id=int(prestadora))


class ContratoViewSet(
    CRMSchemaRecoveryMixin,
    CrmGranularPermissionMixin,
    AssinaturaDigitalMixin,
    DocumentoQuerysetMixin,
    VendedorFilterMixin,
    BaseModelViewSet,
):
    queryset = Contrato.objects.all()
    serializer_class = ContratoSerializer
    pagination_class = CRMPagination

    vendedor_filter_field = "oportunidade__vendedor_id"
    vendedor_filter_related = []
    vendedor_escopo_qualidade = True
    assinatura_doc_label = "Contrato"
    assinatura_cache_key = "contratos"
    crm_permission_model = "contrato"

    def perform_create(self, serializer):
        from rest_framework.exceptions import PermissionDenied

        from .acesso_oportunidade import oportunidade_do_usuario

        oportunidade = serializer.validated_data.get("oportunidade")
        if not oportunidade_do_usuario(self.request, getattr(oportunidade, "id", oportunidade)):
            raise PermissionDenied("Esta oportunidade é de outro vendedor.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        bloqueio = _resposta_documento_assinado(self.get_object())
        if bloqueio:
            return bloqueio
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        contrato = self.get_object()
        bloqueio = _resposta_documento_assinado(contrato)
        if bloqueio:
            return bloqueio
        if contrato.status == "cancelado":
            return Response(
                {"detail": "Contrato já está cancelado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        motivo = (request.data.get("motivo") or "").strip()
        if not motivo:
            return Response(
                {"detail": "Informe o motivo do cancelamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        contrato.status = "cancelado"
        contrato.motivo_cancelamento = motivo
        contrato.save(update_fields=["status", "motivo_cancelamento", "updated_at"])
        return Response({"detail": "Contrato cancelado com sucesso.", "status": "cancelado"})

    @action(detail=True, methods=["get"])
    def download_pdf(self, request, pk=None):
        from .pdf_proposta_contrato import gerar_pdf_contrato

        contrato = self.get_object()
        try:
            incluir_assinaturas = contrato.status_assinatura == "concluido"
            pdf_buffer = gerar_pdf_contrato(contrato, incluir_assinaturas=incluir_assinaturas)
            pdf_bytes = pdf_buffer.getvalue()
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            from .nome_arquivo import nome_arquivo_download

            filename = nome_arquivo_download(
                "contrato", contrato.numero or contrato.id, contrato.titulo, extensao="pdf",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": "Erro ao gerar PDF."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"])
    def download_docx(self, request, pk=None):
        from .docx_proposta_contrato import gerar_docx_contrato

        contrato = self.get_object()
        try:
            docx_buffer = gerar_docx_contrato(contrato)
            response = HttpResponse(
                docx_buffer.getvalue(),
                content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
            from .nome_arquivo import nome_arquivo_download

            filename = nome_arquivo_download(
                "contrato", contrato.numero or contrato.id, contrato.titulo, extensao="docx",
            )
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"detail": "Erro ao gerar DOCX."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
