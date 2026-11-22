"""Views de resultado de exame (PDF do laboratório na consulta de retorno)."""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Consulta, ResultadoExamePaciente
from .permissions import CLINICA_CLINICAL
from .views_base import GetObjectMixin
from .resultado_exame_service import (
    ResultadoExameErro,
    atualizar_marcadores,
    importar_pdf_resultado,
    listar_resultados_consulta,
    serializar_resultado,
)
from .acesso_leitura import registrar_leitura_clinica

logger = logging.getLogger(__name__)


class ConsultaResultadoExameView(GetObjectMixin, APIView):
    """GET lista pedidos pendentes e resultados. POST importa PDF."""

    permission_classes = CLINICA_CLINICAL
    bloquear_andamento_alheio = True
    model_class = Consulta
    not_found_message = "Consulta não encontrada"
    select_related_fields = ("patient",)

    def get(self, request, pk):
        consulta = self.get_object(pk)
        if consulta is None:
            return Response({"error": self.not_found_message}, status=status.HTTP_404_NOT_FOUND)
        registrar_leitura_clinica(request, consulta.patient_id, "Resultados de exame")
        return Response(listar_resultados_consulta(consulta))

    def post(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        arquivo = request.FILES.get("arquivo") or request.FILES.get("file")
        if not arquivo:
            return Response({"error": "Envie o PDF em 'arquivo'."}, status=status.HTTP_400_BAD_REQUEST)
        conteudo = arquivo.read()
        nome = getattr(arquivo, "name", "") or "resultado_exame.pdf"
        try:
            documento_id = request.data.get("documento_origem_id") or request.POST.get("documento_origem_id")
            memed_id = request.data.get("prescricao_origem_id") or request.POST.get("prescricao_origem_id")
            consulta_origem_id = request.data.get("consulta_origem_id") or request.POST.get("consulta_origem_id")
            resultado = importar_pdf_resultado(
                consulta,
                arquivo_bytes=conteudo,
                nome_arquivo=nome,
                documento_origem_id=int(documento_id) if documento_id else None,
                prescricao_origem_id=int(memed_id) if memed_id else None,
                consulta_origem_id=int(consulta_origem_id) if consulta_origem_id else None,
            )
        except ResultadoExameErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({"error": "Identificador do pedido inválido."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Erro ao importar resultado de exame")
            return Response({"error": "Não foi possível importar o PDF."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {"message": "Resultado importado.", "resultado": serializar_resultado(resultado)},
            status=status.HTTP_201_CREATED,
        )


class ConsultaResultadoExameDetailView(GetObjectMixin, APIView):
    """PATCH atualiza marcadores e recalcula sugestão. DELETE remove o registro."""

    permission_classes = CLINICA_CLINICAL
    bloquear_andamento_alheio = True
    model_class = Consulta
    not_found_message = "Consulta não encontrada"

    def _resultado(self, consulta: Consulta, resultado_id: int):
        return ResultadoExamePaciente.objects.filter(
            id=resultado_id, patient_id=consulta.patient_id,
        ).first()

    def patch(self, request, pk, resultado_id):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        resultado = self._resultado(consulta, resultado_id)
        if not resultado:
            return Response({"error": "Resultado não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        try:
            atualizado = atualizar_marcadores(resultado, request.data.get("marcadores") or [])
        except ResultadoExameErro as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"resultado": serializar_resultado(atualizado)})

    def delete(self, request, pk, resultado_id):
        consulta, err = self.object_or_404(pk)
        if err:
            return err
        resultado = self._resultado(consulta, resultado_id)
        if not resultado:
            return Response({"error": "Resultado não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        resultado.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
