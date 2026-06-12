"""
Views de Consultas — Clínica da Beleza
"""
from decimal import Decimal

from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from .permissions import CLINICA_MEMBER, CLINICA_CLINICAL
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
from .consulta_service import (
    consulta_esta_concluida,
    criar_consulta_avulsa,
    finalizar_consulta,
    iniciar_consulta,
    motivo_bloqueio_exclusao_consulta,
)
from .pagination import paginate_queryset
from .views_base import GetObjectMixin, resolve_loja_id_from_request


# ---------------------------------------------------------------------------
# Helpers de lookup — eliminam try/except repetido
# ---------------------------------------------------------------------------

def _get_consulta_or_404(pk, select_related=None):
    """Busca consulta com select_related padrão ou retorna (None, Response 404)."""
    if select_related is None:
        select_related = (
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
        )
    try:
        consulta = Consulta.objects.select_related(*select_related).get(pk=pk)
        return consulta, None
    except Consulta.DoesNotExist:
        return None, Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)


def _get_patient_or_404(patient_id):
    """Busca paciente ou retorna (None, Response 404)."""
    try:
        return Patient.objects.get(pk=patient_id), None
    except Patient.DoesNotExist:
        return None, Response({'error': 'Cliente não encontrado'}, status=status.HTTP_404_NOT_FOUND)


class ConsultaListView(APIView):
    """
    GET  /clinica-beleza/consultas/ — lista consultas.
    POST /clinica-beleza/consultas/ — abre uma consulta avulsa (sem agendamento na
         agenda) a partir do cadastro do cliente.
    """
    permission_classes = CLINICA_MEMBER

    def get(self, request):
        from django.db.models import Count

        from .serializers import ConsultaListSerializer

        qs = Consulta.objects.select_related(
            'patient', 'professional', 'procedure', 'protocol', 'appointment',
            'appointment__nome_agenda',
        ).prefetch_related(
            'appointment__appointment_procedures__procedure',
        ).annotate(
            total_evolucoes_count=Count('evolucoes'),
        ).exclude(
            status='CANCELLED',
        ).order_by('-data_inicio', '-created_at')
        if patient_id := request.query_params.get('patient'):
            qs = qs.filter(patient_id=patient_id)
        if professional_id := request.query_params.get('professional'):
            qs = qs.filter(professional_id=professional_id)
        if st := request.query_params.get('status'):
            qs = qs.filter(status=st)
        if appointment_id := request.query_params.get('appointment'):
            qs = qs.filter(appointment_id=appointment_id)
        return paginate_queryset(qs, request, ConsultaListSerializer)

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

        # Validação de pertencimento à loja
        loja_id = resolve_loja_id_from_request(request)
        if patient.loja_id != loja_id:
            return Response({'error': 'Paciente não pertence a esta loja.'}, status=status.HTTP_400_BAD_REQUEST)

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
        nome_agenda_id = request.data.get('nome_agenda')
        notes = request.data.get('notes')
        appointment_date = None
        if date_raw := request.data.get('date'):
            from django.utils.dateparse import parse_datetime
            appointment_date = parse_datetime(str(date_raw))
            if appointment_date is None:
                return Response({'error': 'Data/hora inválida.'}, status=status.HTTP_400_BAD_REQUEST)
        consulta = criar_consulta_avulsa(
            patient=patient,
            professional=professional,
            procedures=proc_list,
            loja_id=patient.loja_id,
            iniciar=bool(iniciar),
            local_atendimento_id=local_atendimento_id,
            valor_consulta=valor_consulta_override,
            convenio_id=convenio_id,
            nome_agenda_id=nome_agenda_id,
            appointment_date=appointment_date,
            notes=notes,
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
    prefetch_related_fields = ('appointment__appointment_procedures__procedure',)

    def get(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        return Response(ConsultaSerializer(obj).data)

    def put(self, request, pk):
        obj, err = self.object_or_404(pk)
        if err:
            return err
        if consulta_esta_concluida(obj):
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

        if motivo := motivo_bloqueio_exclusao_consulta(consulta):
            return Response({'error': motivo}, status=status.HTTP_403_FORBIDDEN)

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
        consulta, error = _get_consulta_or_404(pk, select_related=(
            'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
        ))
        if error:
            return error

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
        consulta, error = _get_consulta_or_404(pk, select_related=(
            'patient', 'professional', 'procedure', 'protocol', 'appointment', 'appointment__procedure',
        ))
        if error:
            return error

        mark_as_paid = bool(request.data.get('mark_as_paid'))
        payment_method = (request.data.get('payment_method') or request.data.get('forma_pagamento') or '').strip() or None
        amount = request.data.get('amount') or request.data.get('valor')
        local_atendimento_id = request.data.get('local_atendimento')

        try:
            finalizar_consulta(
                consulta,
                payment_method=payment_method,
                mark_as_paid=mark_as_paid,
                amount=amount,
                local_atendimento_id=local_atendimento_id,
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
        consulta, error = _get_consulta_or_404(pk, select_related=('procedure',))
        if error:
            return error

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
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        patient, error = _get_patient_or_404(patient_id)
        if error:
            return error
        obj, _ = PatientAnamnese.objects.get_or_create(
            patient_id=patient_id,
            defaults={'loja_id': patient.loja_id},
        )
        return Response(PatientAnamneseSerializer(obj).data)

    def put(self, request, patient_id):
        patient, error = _get_patient_or_404(patient_id)
        if error:
            return error
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
    permission_classes = CLINICA_CLINICAL

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


class ConsultaSecaoPDFView(APIView):
    """
    GET /clinica-beleza/consultas/<consulta_id>/pdf/?secao=atendimento|produtos|anamnese|evolucao
    Gera PDF da seção com logo ou papel timbrado da clínica.
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, consulta_id):
        from .consulta_queries import get_consulta_for_tenant

        consulta = get_consulta_for_tenant(
            consulta_id,
            select_related=('patient', 'professional', 'procedure', 'protocol'),
        )
        if not consulta:
            return Response({'error': 'Consulta não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        secao = request.query_params.get('secao', 'atendimento')
        try:
            from .prontuario_pdf import gerar_pdf_consulta_secao
            buffer = gerar_pdf_consulta_secao(consulta, secao)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception('Erro PDF consulta %s secao %s', consulta_id, secao)
            return Response(
                {'error': f'Erro ao gerar PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        filename = f'consulta_{consulta_id}_{secao}.pdf'
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response


class PatientHistoricoConsultasView(APIView):
    """GET /clinica-beleza/patients/<patient_id>/consultas/ — histórico do cliente."""
    permission_classes = CLINICA_CLINICAL

    def get(self, request, patient_id):
        from django.db.models import Count

        from .serializers import ConsultaListSerializer

        qs = Consulta.objects.filter(patient_id=patient_id).select_related(
            'professional', 'procedure', 'protocol', 'appointment', 'patient',
        ).prefetch_related(
            'appointment__appointment_procedures__procedure',
        ).annotate(
            total_evolucoes_count=Count('evolucoes'),
        ).order_by('-data_inicio', '-created_at')
        return paginate_queryset(qs, request, ConsultaListSerializer)


class ConsultaPrescricaoView(APIView):
    """
    GET  /clinica-beleza/consultas/<consulta_id>/prescricoes/ — lista prescrições da consulta.
    POST /clinica-beleza/consultas/<consulta_id>/prescricoes/ — registra uma prescrição emitida
         na Memed (a partir do evento prescricaoImpressa).
    """
    permission_classes = CLINICA_CLINICAL

    def get(self, request, consulta_id):
        qs = PrescricaoMemed.objects.filter(consulta_id=consulta_id).select_related(
            'patient', 'professional',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        from superadmin.models import Loja

        from .memed_prescricao_service import resolver_pdf_prescricao

        try:
            consulta = Consulta.objects.select_related('professional').get(pk=consulta_id)
        except Consulta.DoesNotExist:
            return Response({'error': 'Consulta não encontrada'}, status=status.HTTP_404_NOT_FOUND)

        itens = request.data.get('itens') or []
        if not isinstance(itens, list):
            itens = []
        prescricao_id = str(request.data.get('prescricao_id') or '')[:64]
        prof_id = request.data.get('professional') or consulta.professional_id
        professional = consulta.professional
        if prof_id and (not professional or professional.id != prof_id):
            professional = Professional.objects.filter(pk=prof_id).first() or professional

        loja = Loja.objects.using('default').filter(id=consulta.loja_id).first()
        pdf_url = ''
        if loja and prescricao_id:
            pdf_url = resolver_pdf_prescricao(
                loja,
                professional,
                prescricao_id,
                str(request.data.get('pdf_url') or ''),
            )

        data = {
            'consulta': consulta.id,
            'patient': consulta.patient_id,
            'professional': prof_id,
            'prescricao_id': prescricao_id,
            'resumo': request.data.get('resumo') or '',
            'itens': itens,
            'pdf_url': pdf_url,
        }

        if prescricao_id:
            existente = PrescricaoMemed.objects.filter(
                consulta_id=consulta.id,
                prescricao_id=prescricao_id,
            ).first()
            if existente:
                existente.resumo = data['resumo'] or existente.resumo
                existente.itens = itens or existente.itens
                if pdf_url:
                    existente.pdf_url = pdf_url
                elif not existente.pdf_url and loja and prescricao_id:
                    novo_pdf = resolver_pdf_prescricao(loja, professional, prescricao_id, '')
                    if novo_pdf:
                        existente.pdf_url = novo_pdf
                if prof_id:
                    existente.professional_id = prof_id
                existente.save()
                return Response(
                    PrescricaoMemedSerializer(existente).data,
                    status=status.HTTP_200_OK,
                )

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
            'professional', 'consulta',
        ).order_by('-created_at')
        return Response(PrescricaoMemedSerializer(qs, many=True).data)


class PrescricaoMemedPdfView(APIView):
    """
    POST /clinica-beleza/prescricoes-memed/<pk>/pdf/
    Busca o PDF na Memed (se ainda não salvo), arquiva no Cloudinary e retorna a URL.
    """
    permission_classes = CLINICA_CLINICAL

    def post(self, request, pk):
        from superadmin.models import Loja

        from .memed_prescricao_service import resolver_pdf_prescricao

        try:
            presc = PrescricaoMemed.objects.select_related(
                'professional', 'consulta', 'consulta__professional',
            ).get(pk=pk)
        except PrescricaoMemed.DoesNotExist:
            return Response({'error': 'Prescrição não encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        if presc.pdf_url:
            return Response({'pdf_url': presc.pdf_url})

        loja = Loja.objects.using('default').filter(id=presc.loja_id).first()
        if not loja:
            return Response({'error': 'Loja não encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

        prescricao_id = (presc.prescricao_id or '').strip()
        professional = presc.professional or (
            presc.consulta.professional if presc.consulta_id else None
        )
        pdf_url = ''
        if prescricao_id:
            pdf_url = resolver_pdf_prescricao(loja, professional, prescricao_id, '')

        if not pdf_url:
            from .memed_prescricao_service import arquivar_pdf_bytes_cloudinary
            from .prontuario_pdf import gerar_pdf_prescricao_memed

            try:
                buffer = gerar_pdf_prescricao_memed(presc)
                pdf_url = arquivar_pdf_bytes_cloudinary(loja, buffer.getvalue())
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    'Falha ao gerar PDF local da prescrição Memed %s', pk,
                )
                pdf_url = ''

        if not pdf_url:
            return Response(
                {
                    'error': (
                        'PDF não disponível na Memed. Verifique o certificado BirdID da profissional '
                        'ou reemita na aba Documentos.'
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        presc.pdf_url = pdf_url
        presc.save(update_fields=['pdf_url'])
        return Response({'pdf_url': pdf_url})


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

    def _ensure_consulta_produto_table(self):
        from .schema_ensure import ensure_consulta_produto_utilizado_for_tenant

        if not ensure_consulta_produto_utilizado_for_tenant():
            return Response(
                {'error': 'Estrutura de produtos da consulta indisponível. Contate o suporte.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return None

    def get(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error
        table_error = self._ensure_consulta_produto_table()
        if table_error:
            return Response([])
        qs = ConsultaProdutoUtilizado.objects.filter(
            consulta=consulta,
        ).select_related('produto').order_by('created_at')
        return Response(ConsultaProdutoUtilizadoSerializer(qs, many=True).data)

    def post(self, request, consulta_id):
        consulta, error = self._get_consulta(consulta_id)
        if error:
            return error
        table_error = self._ensure_consulta_produto_table()
        if table_error:
            return table_error
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
