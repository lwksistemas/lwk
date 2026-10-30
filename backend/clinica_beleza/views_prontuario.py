"""Views do Prontuário — Visualização e geração de PDF
"""
import logging
from uuid import uuid4

from django.core.cache import cache
from django.http import HttpResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .documento_service import listar_prontuario_paciente
from .models import DocumentoClinico, Patient
from .permissions import CLINICA_CLINICAL
from .prontuario_pdf import (
    gerar_pdf_documento,
    gerar_pdf_prontuario_completo,
    gerar_pdf_secao,
    nome_arquivo_pdf_prontuario,
)
from .serializers import ProntuarioSectionSerializer
from .views_base import MSG_ERRO_PDF, GetObjectMixin, resposta_erro_interno

logger = logging.getLogger(__name__)


_PDF_FILA_TTL = 1800


def _bytes_do_prontuario(pdf_ou_chave):
    """A fila recebe uma chave. A thread de reserva ainda recebe os bytes."""
    if isinstance(pdf_ou_chave, (bytes, bytearray)):
        return bytes(pdf_ou_chave), None
    chave = str(pdf_ou_chave or "")
    bruto = cache.get(chave) if chave else None
    if not isinstance(bruto, (bytes, bytearray)) or not bruto:
        return b"", chave
    return bytes(bruto), chave


def arquivar_prontuario_pdf(loja_id, patient_id, pdf_ou_chave, filename: str) -> None:
    """Arquiva o PDF do prontuário. O worker django-q chama esta função."""
    from django.db import connections

    chave = None
    try:
        pdf_bytes, chave = _bytes_do_prontuario(pdf_ou_chave)
        if not loja_id or not pdf_bytes:
            if chave:
                logger.warning("PDF do prontuário ausente na fila paciente=%s", patient_id)
            return
        from superadmin.models import Loja
        from tenants.middleware import _configure_tenant_db_for_loja, set_current_loja_id

        from .media_docs_service import arquivar_pdf_gerado
        from .models import Patient

        loja = Loja.objects.using("default").filter(pk=loja_id).first()
        if loja is None:
            return
        _configure_tenant_db_for_loja(loja)
        set_current_loja_id(loja.id)
        patient = Patient.objects.filter(pk=patient_id).first()
        arquivar_pdf_gerado(loja.id, patient, pdf_bytes, filename)
        if chave:
            cache.delete(chave)
    except Exception:
        logger.exception("Arquivo do prontuário em segundo plano falhou paciente=%s", patient_id)
    finally:
        connections.close_all()


def _arquivar_prontuario_em_segundo_plano(loja_id, patient_id, pdf_bytes: bytes, filename: str) -> None:
    """Enfileira a chave do PDF. O download da resposta continua síncrono."""
    if not loja_id or not pdf_bytes:
        return
    payload = bytes(pdf_bytes)
    task_name = f"pdf-prontuario-{patient_id}"
    func_path = "clinica_beleza.views_prontuario.arquivar_prontuario_pdf"
    from core.task_queue import task_queue_enabled

    if task_queue_enabled():
        chave = f"prontuario-pdf:{patient_id}:{uuid4().hex}"
        try:
            from django_q.tasks import async_task

            cache.set(chave, payload, timeout=_PDF_FILA_TTL)
            async_task(
                func_path,
                loja_id,
                patient_id,
                chave,
                filename,
                task_name=task_name,
                save=False,
            )
            return
        except Exception as exc:
            cache.delete(chave)
            logger.warning("Fila indisponível para arquivar prontuário: %s", exc)
    import threading

    threading.Thread(
        target=arquivar_prontuario_pdf,
        args=(loja_id, patient_id, payload, filename),
        daemon=True,
        name=task_name,
    ).start()


class ProntuarioView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/prontuario/
    Retorna prontuário do paciente agrupado por seção.

    Query params:
        ?secao=receituario — filtra por seção específica
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        if not Patient.objects.filter(pk=patient_id).exists():
            return Response(
                {"error": "Paciente não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        secao = request.query_params.get("secao")
        prontuario = listar_prontuario_paciente(patient_id, secao=secao)
        serializer = ProntuarioSectionSerializer(prontuario)
        return Response(serializer.data)


class ProntuarioPDFView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/prontuario/pdf/
    Gera PDF do prontuário (seção ou completo).

    Query params:
        ?secao=receituario — PDF de uma seção específica
        (sem parâmetro) — PDF completo
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        if not Patient.objects.filter(pk=patient_id).exists():
            return Response(
                {"error": "Paciente não encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        secao = request.query_params.get("secao")

        try:
            patient = Patient.objects.filter(pk=patient_id).first()
            if secao:
                buffer = gerar_pdf_secao(patient_id, secao)
            else:
                buffer = gerar_pdf_prontuario_completo(patient_id)
            filename = nome_arquivo_pdf_prontuario(getattr(patient, "nome", ""), secao)
            _arquivar_prontuario_em_segundo_plano(
                getattr(patient, "loja_id", None),
                patient_id,
                buffer.getvalue(),
                filename,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Erro ao gerar PDF do prontuário (paciente %s, seção %s)", patient_id, secao)
            return Response(
                {"error": "Não foi possível gerar o PDF. Tente novamente."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response


class DocumentoPDFView(GetObjectMixin, APIView):
    """GET /clinica-beleza/documentos/<doc_id>/pdf/
    Gera PDF de um documento individual.
    """

    permission_classes = CLINICA_CLINICAL
    model_class = DocumentoClinico
    not_found_message = "Documento não encontrado"

    def get(self, request, doc_id):
        obj, error = self.object_or_404(doc_id)
        if error:
            return error

        try:
            buffer = gerar_pdf_documento(obj)
        except Exception as e:
            return resposta_erro_interno(
                logger, f"Erro ao gerar PDF do documento {doc_id}", e, error=MSG_ERRO_PDF,
            )

        tipo = obj.tipo or "documento"
        filename = f"{tipo}_{obj.id}.pdf"
        from clinica_beleza.media_docs_service import arquivar_pdf_gerado
        arquivar_pdf_gerado(obj.loja_id, obj.patient, buffer.getvalue(), filename)
        response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{filename}"'
        return response
