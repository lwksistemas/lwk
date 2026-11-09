"""Simulação ilustrativa dentro da consulta."""
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from superadmin.models import Loja

from .models import SimulacaoConsulta
from .permissions import CLINICA_CLINICAL
from .simulacao_consulta_service import acompanhar, iniciar, marcar_ciencia, serializar
from .simulacao_estetica_service import SimulacaoEsteticaError
from .views_base import GetObjectMixin
from .models import Consulta


class ConsultaSimulacaoListView(GetObjectMixin, APIView):
    permission_classes = CLINICA_CLINICAL
    model_class = Consulta
    not_found_message = "Consulta não encontrada"
    select_related_fields = ("patient",)

    def get(self, request, pk):
        consulta, erro = self.object_or_404(pk)
        if erro:
            return erro
        loja = Loja.objects.using("default").filter(pk=consulta.loja_id).first()
        itens = []
        for registro in SimulacaoConsulta.objects.filter(consulta_id=consulta.id).order_by("-created_at")[:30]:
            if loja and registro.status == SimulacaoConsulta.STATUS_PROCESSANDO:
                try:
                    itens.append(acompanhar(loja, registro))
                except Exception:
                    itens.append(serializar(registro))
            else:
                itens.append(serializar(registro))
        return Response({"resultados": itens})

    def post(self, request, pk):
        self.bloquear_andamento_alheio = True
        consulta, erro = self.object_or_404(pk)
        if erro:
            return erro
        loja = Loja.objects.using("default").filter(pk=consulta.loja_id).first()
        if loja is None:
            return Response({"error": "Clínica não encontrada"}, status=status.HTTP_404_NOT_FOUND)
        try:
            return Response(iniciar(loja, consulta, request.data or {}), status=status.HTTP_201_CREATED)
        except SimulacaoEsteticaError as exc:
            return Response({"error": exc.message}, status=exc.status)


class ConsultaSimulacaoCienciaView(GetObjectMixin, APIView):
    permission_classes = CLINICA_CLINICAL
    bloquear_andamento_alheio = True
    model_class = Consulta
    not_found_message = "Consulta não encontrada"

    def post(self, request, pk, simulacao_id):
        consulta, erro = self.object_or_404(pk)
        if erro:
            return erro
        registro = get_object_or_404(SimulacaoConsulta, pk=simulacao_id, consulta_id=consulta.id)
        try:
            return Response(marcar_ciencia(registro))
        except SimulacaoEsteticaError as exc:
            return Response({"error": exc.message}, status=exc.status)
