"""Views de Nomes de Agenda — Clínica da Beleza"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import NomeAgenda
from .permissions import CLINICA_RECEPCAO
from .serializers import NomeAgendaSerializer
from .views_base import GetObjectMixin


class NomeAgendaListView(APIView):
    """
    GET /clinica-beleza/nomes-agenda/ — lista nomes ativos da loja
    POST /clinica-beleza/nomes-agenda/ — cria novo nome
    """
    permission_classes = CLINICA_RECEPCAO

    def get(self, request):
        queryset = NomeAgenda.objects.filter(is_active=True).order_by('nome')
        return Response(NomeAgendaSerializer(queryset, many=True).data)

    def post(self, request):
        serializer = NomeAgendaSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            # Se não existe nenhum padrão, marcar este como padrão
            tem_padrao = NomeAgenda.objects.using(instance._state.db).filter(
                loja_id=instance.loja_id, is_padrao=True, is_active=True,
            ).exists()
            if not tem_padrao:
                instance.is_padrao = True
                instance.save(update_fields=['is_padrao'])
            return Response(NomeAgendaSerializer(instance).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NomeAgendaDetailView(GetObjectMixin, APIView):
    """GET / PUT / PATCH / DELETE /clinica-beleza/nomes-agenda/<pk>/"""
    permission_classes = CLINICA_RECEPCAO
    model_class = NomeAgenda
    not_found_message = 'Nome de agenda não encontrado'

    def get(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        return Response(NomeAgendaSerializer(obj).data)

    def _update(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        serializer = NomeAgendaSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            # Se marcou como padrão, desmarcar os outros da mesma loja
            if instance.is_padrao:
                NomeAgenda.objects.using(instance._state.db).filter(
                    loja_id=instance.loja_id, is_padrao=True,
                ).exclude(pk=instance.pk).update(is_padrao=False)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        return self._update(request, pk)

    def patch(self, request, pk):
        return self._update(request, pk)

    def delete(self, request, pk):
        obj, error = self.object_or_404(pk)
        if error:
            return error
        obj.is_active = False
        obj.save(update_fields=['is_active', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
