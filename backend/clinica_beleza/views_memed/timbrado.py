"""Timbrado A4 (PDF) para receituário e exames na Memed — por loja."""
import re

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from clinica_beleza.permissions import CLINICA_CLINICAL


class MemedTimbradoView(APIView):
    """Timbrado A4 (PDF) para receituário e exames na Memed — por loja.

    GET  /clinica-beleza/memed/timbrado/  — status do timbrado salvo
    POST /clinica-beleza/memed/timbrado/  — upload PDF (multipart campo ``pdf``)
                                            ou JSON ``{"aplicar": true}`` para reaplicar
    """

    permission_classes = CLINICA_CLINICAL
    MAX_PDF_BYTES = 5 * 1024 * 1024

    def get(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.plano_features import loja_plano_permite_memed
        from clinica_beleza.models import MemedTimbrado

        ok, err = loja_plano_permite_memed(get_current_loja_id())
        if not ok:
            return Response({"error": err}, status=status.HTTP_403_FORBIDDEN)

        timbrado = MemedTimbrado.objects.first()
        if not timbrado or not timbrado.pdf:
            return Response({"tem_timbrado": False})
        pdf = bytes(timbrado.pdf)
        return Response({
            "tem_timbrado": True,
            "pdf_nome": timbrado.pdf_nome or "timbrado.pdf",
            "tamanho_bytes": len(pdf),
            "updated_at": timbrado.updated_at.isoformat() if timbrado.updated_at else None,
        })

    def post(self, request):
        from tenants.middleware import get_current_loja_id
        from superadmin.plano_features import loja_plano_permite_memed
        from clinica_beleza.memed_impressao import aplicar_timbrado_loja_a_profissionais, aviso_timbrado_nao_aplicado
        from clinica_beleza.models import MemedTimbrado, Professional

        ok, err = loja_plano_permite_memed(get_current_loja_id())
        if not ok:
            return Response({"error": err}, status=status.HTTP_403_FORBIDDEN)

        if request.data.get("aplicar") in (True, "true", "1", 1):
            timbrado = MemedTimbrado.objects.first()
            if not timbrado or not timbrado.pdf:
                return Response({"error": "Nenhum timbrado salvo. Envie o PDF primeiro."}, status=status.HTTP_400_BAD_REQUEST)
            pdf_bytes = bytes(timbrado.pdf)
            filename = timbrado.pdf_nome or "timbrado.pdf"
        else:
            upload = request.FILES.get("pdf")
            if not upload:
                return Response({"error": "Envie o arquivo PDF no campo pdf."}, status=status.HTTP_400_BAD_REQUEST)
            from core.upload_validation import validate_pdf_upload

            ok, err = validate_pdf_upload(upload)
            if not ok:
                return Response({"error": err}, status=status.HTTP_400_BAD_REQUEST)
            pdf_bytes = upload.read()
            if len(pdf_bytes) > self.MAX_PDF_BYTES:
                return Response({"error": "PDF muito grande (máx. 5 MB)."}, status=status.HTTP_400_BAD_REQUEST)
            filename = upload.name or "timbrado.pdf"
            loja_id = get_current_loja_id()
            MemedTimbrado.objects.update_or_create(
                loja_id=loja_id,
                defaults={"pdf": pdf_bytes, "pdf_nome": filename},
            )

        profs = [
            p for p in Professional.objects.filter(is_active=True)
            if len(re.sub(r"\D", "", p.cpf or "")) == 11
        ]
        if not profs:
            return Response({
                "error": "Timbrado salvo, mas nenhum profissional ativo com CPF para aplicar na Memed.",
            }, status=status.HTTP_400_BAD_REQUEST)

        resultado = aplicar_timbrado_loja_a_profissionais(pdf_bytes, filename, profs)
        payload = {
            "tem_timbrado": True,
            "pdf_nome": filename,
            "tamanho_bytes": len(pdf_bytes),
            "aplicados": resultado["aplicados"],
            "total": resultado["total"],
            "detalhes": resultado["detalhes"],
        }
        if resultado["aplicados"] == 0:
            payload["warning"] = aviso_timbrado_nao_aplicado(resultado)
        return Response(payload)
