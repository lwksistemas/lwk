"""
Views de Consultas — Clínica da Beleza
"""
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_MEMBER
from rest_framework import status

from .models import (
    Consulta, ConsultaProdutoUtilizado, PatientAnamnese, ConsultaEvolucao,
    ProcedureProtocol, Patient, Professional, Procedure, PrescricaoMemed, ProdutoEstoque,
)
from .serializers import (
    ConsultaSerializer, ConsultaProdutoUtilizadoSerializer,
    PatientAnamneseSerializer, ConsultaEvolucaoSerializer,
    PrescricaoMemedSerializer,
)
from .consulta_service import finalizar_consulta, iniciar_consulta, criar_consulta_avulsa
from .pagination import paginate_queryset
from .views_base import GetObjectMixin


class ConsultaListView(APIView):
    """
    GET  /clinica-beleza/consultas/ — lista consultas.
    POST /clinica-beleza/consultas/ — abre uma consulta avulsa (sem agendamento na
         agenda) a partir do cadastro do cliente.
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        qs = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).order_by('-data_inicio', '-created_at')
        if patient_id := request.query_params.get('patient'):
            qs = qs.filter(patient_id=patient_id)
        if professional_id := request.query_params.get('professional'):
            qs = qs.filter(professional_id=professional_id)
        if st := request.query_params.get('status'):
            qs = qs.filter(status=st)
        if appointment_id := request.query_params.get('appointment'):
            qs = qs.filter(appointment_id=appointment_id)
        return paginate_queryset(qs, request, ConsultaSerializer)

    def post(self, request):
        patient_id = request.data.get('patient')
        professional_id = request.data.get('professional')
        procedure_id = request.data.get('procedure')
        procedures_ids = request.data.get('procedures_ids') or []
        if not patient_id or not professional_id:
            return Response(
                {'error': 'Informe cliente e profissional.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not procedures_ids and not procedure_id:
            return Response(
                {'error': 'Informe pelo menos um procedimento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            professional = Professional.objects.get(pk=professional_id)
        except Professional.DoesNotExist:
            return Response({'error': 'Profissional não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Resolver procedimentos
        if procedures_ids:
            proc_list = list(Procedure.objects.filter(id__in=procedures_ids, is_active=True))
            if not proc_list:
                return Response({'error': 'Nenhum procedimento válido encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                proc_list = [Procedure.objects.get(pk=procedure_id)]
            except Procedure.DoesNotExist:
                return Response({'error': 'Procedimento não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        iniciar = request.data.get('iniciar', False)
        local_atendimento_id = request.data.get('local_atendimento')
        valor_consulta_override = request.data.get('valor_consulta')
        convenio_id = request.data.get('convenio')
        consulta = criar_consulta_avulsa(
            patient=patient,
            professional=professional,
            procedures=proc_list,
            loja_id=patient.loja_id,
            iniciar=bool(iniciar),
            local_atendimento_id=local_atendimento_id,
            valor_consulta=valor_consulta_override,
            convenio_id=convenio_id,
        )
        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=consulta.id)
        return Response(ConsultaSerializer(consulta).data, status=status.HTTP_201_CREATED)


class ConsultaDetailView(GetObjectMixin, APIView):
    """GET / PUT / PATCH /clinica-beleza/consultas/<id>/"""
    permission_classes = CLINICA_MEMBER
    model_class = Consulta
    not_found_message = 'Consulta não encontrada'
    select_related_fields = (
        'patient', 'professional', 'procedure', 'protocol', 'appointment',
        'local_atendimento', 'convenio',
    )

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(ConsultaSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        if obj.status == 'COMPLETED':
            return Response(
                {'error': 'Consulta finalizada não pode ser editada.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = ConsultaSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        return self.put(request, pk)

    def delete(self, request, pk):
        consulta, err = self.object_or_404(pk)
        if err:
            return err

        # Só permite excluir consultas que ainda não foram concluídas
        if consulta.status == 'COMPLETED':
            return Response(
                {'error': 'Consultas concluídas não podem ser excluídas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cancela o agendamento vinculado (se existir e estiver aberto)
        appointment = consulta.appointment
        if appointment and appointment.status not in ('COMPLETED', 'CANCELLED'):
            appointment.status = 'CANCELLED'
            appointment.version = (appointment.version or 1) + 1
            appointment.save(update_fields=['status', 'version', 'updated_at'])

        consulta.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ConsultaIniciarView(APIView):
    """POST /clinica-beleza/consultas/<id>/iniciar/ — inicia atendimento (consulta + agenda)."""
    permission_classes = CLINICA_MEMBER

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related(
                'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
            ).get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        try:
            iniciar_consulta(consulta)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaFinalizarView(APIView):
    """POST /clinica-beleza/consultas/<id>/finalizar/ — conclui consulta, agenda e financeiro."""
    permission_classes = CLINICA_MEMBER

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related(
                'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
            ).get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        mark_as_paid = bool(request.data.get('mark_as_paid'))
        payment_method = (request.data.get('payment_method') or request.data.get('forma_pagamento') or '').strip() or None
        amount = request.data.get('amount') or request.data.get('valor')

        try:
            finalizar_consulta(
                consulta,
                payment_method=payment_method,
                mark_as_paid=mark_as_paid,
                amount=amount,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        consulta = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        ).get(pk=pk)
        return Response(ConsultaSerializer(consulta).data)


class ConsultaAplicarProtocoloView(APIView):
    """POST /clinica-beleza/consultas/<id>/aplicar-protocolo/ — vincula protocolo e preenche notas."""
    permission_classes = CLINICA_MEMBER

    def post(self, request, pk):
        try:
            consulta = Consulta.objects.select_related('procedure').get(pk=pk)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        protocol_id = request.data.get('protocol_id')
        if not protocol_id:
            return Response({'error': 'Informe protocol_id'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            protocol = ProcedureProtocol.objects.get(pk=protocol_id, is_active=True)
        except ProcedureProtocol.DoesNotExist:
            return Response({'error': 'Protocolo não encontrado'}, status=status.HTTP_404_NOT_FOUND)

        if protocol.procedure_id != consulta.procedure_id:
            return Response({'error': 'Protocolo não pertence ao procedimento da consulta'}, status=status.HTTP_400_BAD_REQUEST)

        notas = (
            f"=== {protocol.nome} ===\n\n"
            f"Preparação:\n{protocol.preparacao}\n\n"
            f"Execução:\n{protocol.execucao}\n\n"
            f"Pós-procedimento:\n{protocol.pos_procedimento}\n\n"
            f"Materiais:\n{protocol.materiais_necessarios}"
        )
        consulta.protocol = protocol
        consulta.protocolo_notas = notas
        consulta.save(update_fields=['protocol', 'protocolo_notas', 'updated_at'])
        return Response(ConsultaSerializer(consulta).data)


class PatientAnamneseView(APIView):
    """GET / PUT /clinica-beleza/patients/<patient_id>/anamnese/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request, patient_id):
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        return Response(PatientAnamneseSerializer(obj).data)

    def put(self, request, patient_id):
        try:
            patient = Patient.objects.get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        serializer = PatientAnamneseSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultaEvolucaoListView(APIView):
    """GET / POST /clinica-beleza/consultas/<consulta_id>/evolucoes/"""
    permission_classes = CLINICA_MEMBER

    def get(self, request, consulta_id):
        qs = ConsultaEvolucao.objects.filter(consulta_id=consulta_id).select_related(
            'patient', 'professional',
        ).order_by('-created_at')
        return Response(ConsultaEvolucaoSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        try:
            consulta = Consulta.objects.get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if consulta.status == 'COMPLETED':
            return Response(
                {'error': 'Consulta finalizada não permite novas evoluções.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        data = {
            **request.data,
            'consulta': consulta.id,
            'patient': consulta.patient_id,
            'professional': request.data.get('professional') or consulta.professional_id,
        }
        serializer = ConsultaEvolucaoSerializer(data=data)
        if serializer.is_valid():
            serializer.save(loja_id=consulta.loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientHistoricoConsultasView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/consultas/ — histórico do cliente."""
    permission_classes = CLINICA_MEMBER

    def get(self, request, patient_id):
        qs = Consulta.objects.filter(patient_id=patient_id).select_related(
            'professional', 'procedure', 'protocol', 'appointment',
        ).order_by('-data_inicio', '-created_at')
        return Response(ConsultaSerializer(qs, many=True).data)


class ConsultaPrescricaoView(APIView):
    """
    GET  /clinica-beleza/consultas/<consulta_id>/prescricoes/ — lista prescrições da consulta.
    POST /clinica-beleza/consultas/<consulta_id>/prescricoes/ — registra uma prescrição emitida
         na Memed (a partir do evento prescricaoImpressa).
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request, consulta_id):
        qs = PrescricaoMemed.objects.filter(consulta_id=consulta_id).select_related(
            'patient', 'professional',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        try:
            consulta = Consulta.objects.get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        itens = request.data.get('itens') or []
        if not isinstance(itens, list):
            itens = []
        data = {
            'consulta': consulta.id,
            'patient': consulta.patient_id,
            'professional': request.data.get('professional') or consulta.professional_id,
            'prescricao_id': str(request.data.get('prescricao_id') or '')[:64],
            'resumo': request.data.get('resumo') or '',
            'itens': itens,
        }
        serializer = PrescricaoMemedSerializer(data=data)
        if serializer.is_valid():
            serializer.save(loja_id=consulta.loja_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PatientPrescricaoView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/prescricoes/ — prescrições do cliente (histórico)."""
    permission_classes = CLINICA_MEMBER

    def get(self, request, patient_id):
        qs = PrescricaoMemed.objects.filter(patient_id=patient_id).select_related(
            'professional', 'consulta',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)


class ConsultaProdutoListView(APIView):
    """
    GET  /clinica-beleza/consultas/<consulta_id>/produtos/
    POST /clinica-beleza/consultas/<consulta_id>/produtos/
    """
    permission_classes = CLINICA_MEMBER

    def _get_consulta(self, consulta_id):
        try:
            return Consulta.objects.get(pk=consulta_id), None
        except Consulta.DoesNotExist:
            return None, Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

    def get(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error
        qs = ConsultaProdutoUtilizado.objects.filter(
            consulta=consulta,
        ).select_related('produto').order_by('created_at')
        return Response(ConsultaProdutoUtilizadoSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error
        if consulta.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Só é possível registrar produtos com a consulta em atendimento.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        produto_id = request.data.get('produto')
        if not produto_id:
            return Response({'error': 'Informe o produto.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            produto = ProdutoEstoque.objects.get(pk=produto_id, is_active=True)
        except ProdutoEstoque.DoesNotExist:
            return Response({'error': 'Produto não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            quantidade = Decimal(str(request.data.get('quantidade', 0)))
            if quantidade <= 0:
                raise ValueError
        except Exception:
            return Response({'error': 'Quantidade inválida.'}, status=status.HTTP_400_BAD_REQUEST)

        lote = (request.data.get('lote') or produto.lote or '').strip()
        validade = request.data.get('validade') or produto.validade

        data = {
            'consulta': consulta.id,
            'produto': produto.id,
            'quantidade': quantidade,
            'lote': lote,
            'validade': validade or None,
        }
        serializer = ConsultaProdutoUtilizadoSerializer(data=data)
        if serializer.is_valid():
            obj = serializer.save(loja_id=consulta.loja_id)
            obj = ConsultaProdutoUtilizado.objects.select_related('produto').get(pk=obj.pk)
            return Response(
                ConsultaProdutoUtilizadoSerializer(obj).data,
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConsultaProdutoDetailView(APIView):
    """DELETE /clinica-beleza/consultas/<consulta_id>/produtos/<pk>/"""
    permission_classes = CLINICA_MEMBER

    def delete(self, request, consulta_id, pk):
        try:
            consulta = Consulta.objects.get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        if consulta.status != 'IN_PROGRESS':
            return Response(
                {'error': 'Não é possível remover produtos após finalizar a consulta.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = ConsultaProdutoUtilizado.objects.get(pk=pk, consulta=consulta)
        except ConsultaProdutoUtilizado.DoesNotExist:
            return Response({'error': 'Registro não encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        if item.estoque_baixado:
            return Response(
                {'error': 'Produto já baixado do estoque.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
