"""Serializers de documentos clínicos, templates e prontuário."""
from rest_framework import serializers

from ..models import (
    ConsultaEvolucao, DocumentoClinico, DocumentTemplate,
    PatientAnamnese, PrescricaoMemed,
)


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer para CRUD de templates de documentos clínicos.
    - professional é associado automaticamente ao profissional do request na criação.
    - is_active é read_only (soft-delete controlado pela view).
    """
    TIPOS_PERMITIDOS = ['receituario', 'pedido_exame', 'atestado', 'documento_personalizado']

    professional = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DocumentTemplate
        fields = [
            'id', 'professional', 'nome', 'tipo', 'conteudo',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'professional', 'is_active', 'created_at', 'updated_at']

    def validate_nome(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError('O nome do template não pode ser vazio.')
        return value.strip()

    def validate_tipo(self, value):
        if value not in self.TIPOS_PERMITIDOS:
            raise serializers.ValidationError(
                f'Tipo inválido. Valores permitidos: {", ".join(self.TIPOS_PERMITIDOS)}',
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'professional'):
            validated_data['professional'] = request.professional
        return super().create(validated_data)


class DocumentoClinicoSerializer(serializers.ModelSerializer):
    """
    Serializer para documentos clínicos da consulta.
    Para criação (POST): aceita template_id (opcional), tipo e conteudo.
    """
    TIPOS_PERMITIDOS = ['receituario', 'pedido_exame', 'atestado', 'documento_personalizado']

    consulta = serializers.PrimaryKeyRelatedField(read_only=True)
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    professional = serializers.PrimaryKeyRelatedField(read_only=True)
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=DocumentTemplate.objects.all(),
        source='template',
        write_only=True,
        required=False,
        allow_null=True,
    )
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)
    template_name = serializers.CharField(source='template.nome', read_only=True, default=None)

    class Meta:
        model = DocumentoClinico
        fields = [
            'id', 'consulta', 'patient', 'professional', 'professional_name',
            'template', 'template_id', 'template_name',
            'tipo', 'titulo', 'conteudo', 'created_at',
        ]
        read_only_fields = ['id', 'consulta', 'patient', 'professional', 'created_at', 'template']

    def validate_tipo(self, value):
        if value not in self.TIPOS_PERMITIDOS:
            raise serializers.ValidationError(
                f'Tipo inválido. Valores permitidos: {", ".join(self.TIPOS_PERMITIDOS)}',
            )
        return value

    def validate_template_id(self, value):
        if value is None:
            return value
        if not value.is_active:
            raise serializers.ValidationError('O template selecionado está inativo.')
        request = self.context.get('request')
        if request and hasattr(request, 'professional'):
            if value.professional_id != request.professional.id:
                raise serializers.ValidationError(
                    'O template selecionado não pertence ao profissional atual.',
                )
        return value


class ProntuarioSectionSerializer(serializers.Serializer):
    """
    Serializer de resposta para prontuário agrupado por seção.
    Formata o dict retornado por listar_prontuario_paciente().
    """
    receituario = serializers.SerializerMethodField()
    pedido_exame = serializers.SerializerMethodField()
    atestado = serializers.SerializerMethodField()
    documento_personalizado = serializers.SerializerMethodField()
    evolucao = serializers.SerializerMethodField()
    anamnese = serializers.SerializerMethodField()

    def _serialize_documento(self, doc):
        return {
            'id': doc.id,
            'tipo': doc.tipo,
            'titulo': doc.titulo,
            'conteudo': doc.conteudo,
            'profissional_nome': doc.professional.nome if doc.professional else None,
            'consulta_id': doc.consulta_id,
            'data': doc.created_at.isoformat() if doc.created_at else None,
            'tipo_fonte': 'documento_clinico',
        }

    def _serialize_prescricao(self, presc):
        return {
            'id': presc.id,
            'tipo': 'receituario',
            'titulo': presc.resumo or 'Prescrição Memed',
            'conteudo': presc.resumo or '',
            'profissional_nome': presc.professional.nome if presc.professional else None,
            'consulta_id': presc.consulta_id,
            'data': presc.created_at.isoformat() if presc.created_at else None,
            'tipo_fonte': 'prescricao_memed',
            'pdf_url': presc.pdf_url,
        }

    def _serialize_evolucao(self, evo):
        return {
            'id': evo.id,
            'descricao': evo.descricao,
            'procedimento_realizado': evo.procedimento_realizado,
            'produtos_utilizados': evo.produtos_utilizados,
            'orientacoes': evo.orientacoes,
            'conteudo': evo.descricao or '',
            'profissional_nome': evo.professional.nome if evo.professional else None,
            'consulta_id': evo.consulta_id,
            'data': evo.created_at.isoformat() if evo.created_at else None,
            'tipo_fonte': 'evolucao',
        }

    def _serialize_anamnese(self, anamnese):
        if anamnese is None:
            return None
        return {
            'id': anamnese.id,
            'queixa_principal': anamnese.queixa_principal,
            'historico_medico': anamnese.historico_medico,
            'medicamentos_uso': anamnese.medicamentos_uso,
            'alergias': anamnese.alergias,
            'tipo_pele': anamnese.tipo_pele,
            'observacoes': anamnese.observacoes,
            'conteudo': anamnese.queixa_principal or '',
            'profissional_nome': None,
            'consulta_id': None,
            'data': anamnese.created_at.isoformat() if anamnese.created_at else None,
            'tipo_fonte': 'anamnese',
            'updated_at': anamnese.updated_at.isoformat() if anamnese.updated_at else None,
        }

    def get_receituario(self, obj):
        items = obj.get('receituario', [])
        result = []
        for item in items:
            if isinstance(item, DocumentoClinico):
                result.append(self._serialize_documento(item))
            elif isinstance(item, PrescricaoMemed):
                result.append(self._serialize_prescricao(item))
        return result

    def get_pedido_exame(self, obj):
        return [self._serialize_documento(doc) for doc in obj.get('pedido_exame', [])]

    def get_atestado(self, obj):
        return [self._serialize_documento(doc) for doc in obj.get('atestado', [])]

    def get_documento_personalizado(self, obj):
        return [self._serialize_documento(doc) for doc in obj.get('documento_personalizado', [])]

    def get_evolucao(self, obj):
        return [self._serialize_evolucao(evo) for evo in obj.get('evolucao', [])]

    def get_anamnese(self, obj):
        return self._serialize_anamnese(obj.get('anamnese'))
