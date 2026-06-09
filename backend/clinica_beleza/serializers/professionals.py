"""Serializers de profissionais, horários e comissões."""
from rest_framework import serializers
from core.serializer_mixins import TextNormalizationMixin, UniqueDocumentoPerLojaMixin
from core.cpf_utils import documento_preenchido, existe_documento_duplicado, mensagem_documento_duplicado
from tenants.middleware import get_current_loja_id

from ..models import HorarioTrabalhoProfissional, Professional, ProfessionalCommission


class ProfessionalCreateWithUserSerializer(serializers.Serializer):
    """
    Cria profissional e usuário de acesso (senha provisória enviada por e-mail).
    """
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    specialty = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    registro_profissional = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    conselho = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    conselho_uf = serializers.CharField(max_length=2, required=False, allow_blank=True, allow_null=True)
    cpf = serializers.CharField(max_length=14, required=False, allow_blank=True, allow_null=True)
    data_nascimento = serializers.DateField(required=False, allow_null=True)
    sexo = serializers.ChoiceField(choices=['M', 'F'], required=False, allow_blank=True, allow_null=True)
    criar_acesso = serializers.BooleanField(default=False, write_only=True)
    perfil = serializers.ChoiceField(
        choices=[
            'administrador', 'profissional', 'recepcao', 'recepcionista',
            'caixa', 'limpeza', 'estoque',
        ],
        default='profissional',
        required=False,
        write_only=True,
    )

    def validate(self, attrs):
        cpf = attrs.get('cpf')
        if documento_preenchido(cpf):
            loja_id = get_current_loja_id()
            if loja_id and existe_documento_duplicado(
                model=Professional,
                field_name='cpf',
                value=cpf,
                loja_id=loja_id,
                apenas_ativos=True,
            ):
                raise serializers.ValidationError({
                    'cpf': mensagem_documento_duplicado('cpf', entidade='profissional'),
                })
        return attrs

    def create(self, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        perfil = validated_data.pop('perfil', 'profissional')
        email = validated_data.get('email')
        name = validated_data.pop('name', None)
        specialty = validated_data.pop('specialty', None)
        phone = validated_data.pop('phone', None) or ''
        registro = (validated_data.pop('registro_profissional', None) or '').strip() or None
        conselho = (validated_data.pop('conselho', None) or '').strip().upper() or None
        conselho_uf = (validated_data.pop('conselho_uf', None) or '').strip().upper() or None
        cpf = (validated_data.pop('cpf', None) or '').strip() or None
        data_nascimento = validated_data.pop('data_nascimento', None) or None
        sexo = (validated_data.pop('sexo', None) or '').strip().upper() or None

        professional = Professional.objects.create(
            nome=name,
            email=email,
            especialidade=specialty,
            telefone=phone,
            registro_profissional=registro,
            conselho=conselho,
            conselho_uf=conselho_uf,
            cpf=cpf,
            data_nascimento=data_nascimento,
            sexo=sexo,
        )

        if criar_acesso:
            from ..professional_service import criar_profissional_com_acesso, ProfessionalAccessError
            try:
                criar_profissional_com_acesso(
                    professional,
                    email=email,
                    name=name or '',
                    perfil=perfil,
                )
            except ProfessionalAccessError as e:
                professional.delete()
                raise serializers.ValidationError({e.field: e.message, 'detail': e.message})
            except Exception as e:
                professional.delete()
                import logging
                logging.getLogger(__name__).exception('Erro ao criar acesso do profissional: %s', e)
                msg = 'Erro ao criar acesso. Tente novamente ou cadastre sem "Criar acesso".'
                raise serializers.ValidationError({'detail': msg})

        return professional


class HorarioTrabalhoProfissionalSerializer(serializers.ModelSerializer):
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = HorarioTrabalhoProfissional
        fields = [
            'id', 'professional', 'dia_semana', 'dia_semana_display',
            'hora_entrada', 'hora_saida', 'intervalo_inicio', 'intervalo_fim', 'ativo',
        ]
        read_only_fields = ['professional']


class ProfessionalSerializer(UniqueDocumentoPerLojaMixin, TextNormalizationMixin, serializers.ModelSerializer):
    unique_documento_fields = ['cpf']
    unique_documento_entidade = 'profissional'
    unique_documento_apenas_ativos = True
    is_administrador_vinculado = serializers.SerializerMethodField(read_only=True)
    horarios_trabalho = HorarioTrabalhoProfissionalSerializer(many=True, read_only=True, required=False)
    uppercase_fields = ['nome', 'especialidade']
    phone_fields = ['telefone']

    class Meta:
        model = Professional
        exclude = ['loja_id']
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'telefone': {'required': False, 'allow_blank': True},
        }

    def get_is_administrador_vinculado(self, obj):
        owner_professional_id = self.context.get('owner_professional_id')
        if owner_professional_id is None:
            return False
        return obj.id == owner_professional_id


class ProfessionalCommissionSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True, default=None)
    local_atendimento_nome = serializers.CharField(
        source='local_atendimento.nome', read_only=True, default=None,
    )
    convenio_nome = serializers.CharField(source='convenio.nome', read_only=True, default=None)
    convenio_codigo = serializers.CharField(source='convenio.codigo', read_only=True, default=None)
    valor_display = serializers.CharField(read_only=True)

    class Meta:
        model = ProfessionalCommission
        fields = [
            'id', 'professional', 'tipo', 'modo', 'valor', 'procedure',
            'procedure_name', 'convenio', 'convenio_nome', 'convenio_codigo',
            'local_atendimento', 'local_atendimento_nome',
            'valor_display', 'is_active',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'professional': {'required': False},
            'procedure': {'required': False, 'allow_null': True},
            'convenio': {'required': False, 'allow_null': True},
            'local_atendimento': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        tipo = attrs.get('tipo')
        procedure = attrs.get('procedure')
        local = attrs.get('local_atendimento')
        convenio = attrs.get('convenio')
        if tipo == 'procedimento':
            if not procedure:
                raise serializers.ValidationError({'procedure': 'Procedimento obrigatório.'})
            if not convenio:
                raise serializers.ValidationError({'convenio': 'Convênio obrigatório.'})
            if local:
                raise serializers.ValidationError(
                    {'local_atendimento': 'Não use local em comissão de procedimento.'},
                )
        elif tipo == 'consulta':
            if procedure:
                raise serializers.ValidationError({'procedure': 'Consulta não vincula procedimento.'})
            if convenio:
                raise serializers.ValidationError({'convenio': 'Consulta não vincula convênio.'})
            if not local:
                raise serializers.ValidationError({
                    'local_atendimento': 'Informe o local de atendimento para a comissão da consulta.',
                })
        return attrs
