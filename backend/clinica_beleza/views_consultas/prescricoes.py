"""Prescrições Memed vinculadas à consulta."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Consulta, PrescricaoMemed, Professional
from ..permissions import CLINICA_CLINICAL
from ..serializers import PrescricaoMemedSerializer


def _preparar_dados_prescricao(request, consulta) -> tuple[dict, str, object, object]:
    """Retorna (data, pdf_url, loja, professional) a partir da request e consulta."""
    from superadmin.models import Loja

    from ..memed_prescricao_service import resolver_pdf_prescricao
    itens = request.data.get("itens") or []
    if not isinstance(itens, list):
        itens = []
    prescricao_id = str(request.data.get("prescricao_id") or "")[:64]
    prof_id = request.data.get("professional") or consulta.professional_id
    professional = consulta.professional
    if prof_id and (not professional or professional.id != prof_id):
        professional = Professional.objects.filter(pk=prof_id).first() or professional
    loja = Loja.objects.using("default").filter(id=consulta.loja_id).first()
    pdf_url = ""
    if loja and prescricao_id:
        pdf_url = resolver_pdf_prescricao(loja, professional, prescricao_id, str(request.data.get("pdf_url") or ""))
    data = {
        "consulta": consulta.id,
        "patient": consulta.patient_id,
        "professional": prof_id,
        "prescricao_id": prescricao_id,
        "resumo": request.data.get("resumo") or "",
        "itens": itens,
        "pdf_url": pdf_url,
    }
    return data, pdf_url, loja, professional


def _atualizar_prescricao_existente(existente, data: dict, pdf_url: str, loja, professional, prescricao_id: str, prof_id) -> None:
    """Atualiza campos de uma PrescricaoMemed existente e salva."""
    from ..memed_prescricao_service import resolver_pdf_prescricao
    existente.resumo = data["resumo"] or existente.resumo
    existente.itens = data["itens"] or existente.itens
    if pdf_url:
        existente.pdf_url = pdf_url
    elif not existente.pdf_url and loja and prescricao_id:
        novo_pdf = resolver_pdf_prescricao(loja, professional, prescricao_id, "")
        if novo_pdf:
            existente.pdf_url = novo_pdf
    if prof_id:
        existente.professional_id = prof_id
    existente.save()


class ConsultaPrescricaoView(APIView):
    """GET  /clinica-beleza/consultas/<consulta_id>/prescricoes/ — lista prescrições da consulta.
    POST /clinica-beleza/consultas/<consulta_id>/prescricoes/ — registra uma prescrição emitida
         na Memed (a partir do evento prescricaoImpressa).
    """

    permission_classes = CLINICA_CLINICAL

    def get(self, request, consulta_id):
        qs = PrescricaoMemed.objects.filter(consulta_id=consulta_id).select_related(
            "patient", "professional",
        ).order_by("-created_at")
        return Response(PrescricaoMemedSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        try:
            consulta = Consulta.objects.select_related("professional").get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({"error": "Consulta não encontrada"}, status=status.HTTP_404_NOT_FOUND)

        data, pdf_url, loja, professional = _preparar_dados_prescricao(request, consulta)
        prescricao_id = data["prescricao_id"]
        prof_id = data["professional"]

        if prescricao_id:
            existente = PrescricaoMemed.objects.filter(
                consulta_id=consulta.id, prescricao_id=prescricao_id,
            ).first()
            if existente:
                _atualizar_prescricao_existente(existente, data, pdf_url, loja, professional, prescricao_id, prof_id)
                return Response(PrescricaoMemedSerializer(existente).data, status=status.HTTP_200_OK)

        serializer = PrescricaoMemedSerializer(data=data)
        if serializer.is_valid():
            serializer.save(loja_id=consulta.loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientPrescricaoView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/prescricoes/ — prescrições do cliente (histórico)."""

    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        qs = PrescricaoMemed.objects.filter(patient_id=patient_id).select_related(
            "professional", "consulta",
        ).order_by("-created_at")
        return Response(PrescricaoMemedSerializer(qs, many=True).data)


class PrescricaoMemedPdfView(APIView):
    """POST /clinica-beleza/prescricoes-memed/<pk>/pdf/
    Busca o PDF na Memed (se ainda não salvo), arquiva no Cloudinary e retorna a URL.
    """

    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        from superadmin.models import Loja

        from ..memed_prescricao_service import resolver_pdf_prescricao

        try:
            presc = PrescricaoMemed.objects.select_related(
                "professional", "consulta", "consulta__professional",
            ).get(pk=pk)
        except PrescricaoMemed.DoesNotExist:
            return Response({"error": "Prescrição não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if presc.pdf_url:
            return Response({"pdf_url": presc.pdf_url})

        loja = Loja.objects.using("default").filter(id=presc.loja_id).first()
        if not loja:
            return Response({"error": "Loja não encontrada."}, status=status.HTTP_400_BAD_REQUEST)

        prescricao_id = (presc.prescricao_id or "").strip()
        professional = presc.professional or (
            presc.consulta.professional if presc.consulta_id else None
        )
        pdf_url = ""
        if prescricao_id:
            pdf_url = resolver_pdf_prescricao(loja, professional, prescricao_id, "")

        if not pdf_url:
            from ..memed_prescricao_service import arquivar_pdf_bytes_cloudinary
            from ..prontuario_pdf import gerar_pdf_prescricao_memed

            try:
                buffer = gerar_pdf_prescricao_memed(presc)
                pdf_url = arquivar_pdf_bytes_cloudinary(loja, buffer.getvalue())
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "Falha ao gerar PDF local da prescrição Memed %s", pk,
                )
                pdf_url = ""

        if not pdf_url:
            return Response(
                {
                    "error": (
                        "PDF não disponível na Memed. Verifique o certificado BirdID da profissional "
                        "ou reemita na aba Documentos."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        presc.pdf_url = pdf_url
        presc.save(update_fields=["pdf_url"])
        return Response({"pdf_url": pdf_url})
