"""
Serializers para Clínica da Beleza
"""
from rest_framework import serializers

from .bloqueio_utils import bloqueio_datetime_range, split_datetime_range
from .models import (
    Patient, Professional, Procedure, ProcedureProtocol,
    Appointment, AppointmentProcedure, Payment, BloqueioHorario,
    HorarioTrabalhoProfissional,
    Consulta, PatientAnamnese, ConsultaEvolucao, PrescricaoMemed,
    ProdutoEstoque, MovimentacaoEstoque,
)
from core.serializer_mixins import TextNormalizationMixin, CpfNormalizationMixin
from core.logging_utils import mask_email


class ProfessionalCreateWithUserSerializer(serializers.Serializer):
    """
    Cria profissional e usuário de acesso (senha provisória enviada por e-mail).
    Campos: name, email (obrigatório para criar acesso), specialty, phone (opcional),
    criar_acesso (bool), perfil (profissional | recepcao) quando criar_acesso=True.
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
        help_text='Perfil de acesso: administrador, profissional, recepcionista, caixa, limpeza, estoque',
    )

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
            from .professional_service import criar_profissional_com_acesso, ProfessionalAccessError
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



class PatientSerializer(CpfNormalizationMixin, TextNormalizationMixin, serializers.ModelSerializer):
    """Serializer para Pacientes. Aceita phone opcional e birth_date em YYYY-MM-DD ou DD/MM/YYYY."""
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'])
    
    # Campos de telefone a normalizar
    phone_fields = ['phone', 'telefone']
    # Campos de texto para maiúsculas
    uppercase_fields = ['name', 'nome', 'cidade', 'estado', 'address', 'endereco']

    class Meta:
        model = Patient
        exclude = ['loja_id']  # loja_id é preenchido automaticamente
        extra_kwargs = {
            'nome': {'required': True},
            'telefone': {'required': False, 'allow_blank': True, 'default': ''},
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'cpf': {'required': False, 'allow_blank': True, 'allow_null': True},
            'data_nascimento': {'required': False, 'allow_null': True},
            'endereco': {'required': False, 'allow_blank': True, 'default': ''},
            'cidade': {'required': False, 'allow_blank': True, 'default': ''},
            'estado': {'required': False, 'allow_blank': True, 'default': ''},
            'observacoes': {'required': False, 'allow_blank': True, 'default': ''},
            'allow_whatsapp': {'required': False, 'default': True},
            'address': {'required': False, 'allow_blank': True, 'allow_null': True},
            'notes': {'required': False, 'allow_blank': True, 'allow_null': True},
        }


class HorarioTrabalhoProfissionalSerializer(serializers.ModelSerializer):
    """Dias e horários de trabalho por profissional."""
    dia_semana_display = serializers.CharField(source='get_dia_semana_display', read_only=True)

    class Meta:
        model = HorarioTrabalhoProfissional
        fields = [
            'id', 'professional', 'dia_semana', 'dia_semana_display',
            'hora_entrada', 'hora_saida', 'intervalo_inicio', 'intervalo_fim', 'ativo',
        ]
        read_only_fields = ['professional']


class ProfessionalSerializer(serializers.ModelSerializer):
    """Serializer para Profissionais. Inclui is_administrador_vinculado quando context['owner_professional_id'] é passado."""
    is_administrador_vinculado = serializers.SerializerMethodField(read_only=True)
    horarios_trabalho = HorarioTrabalhoProfissionalSerializer(many=True, read_only=True, required=False)

    class Meta:
        model = Professional
        exclude = ['loja_id']  # loja_id é preenchido automaticamente
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'telefone': {'required': False, 'allow_blank': True},
        }

    def get_is_administrador_vinculado(self, obj):
        owner_professional_id = self.context.get('owner_professional_id')
        if owner_professional_id is None:
            return False
        return obj.id == owner_professional_id


class ProcedureSerializer(serializers.ModelSerializer):
    """Serializer para Procedimentos"""
    class Meta:
        model = Procedure
        exclude = ['loja_id']
        extra_kwargs = {
            'categoria': {'required': False, 'allow_blank': True, 'default': ''},
        }


class ProcedureProtocolSerializer(serializers.ModelSerializer):
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    procedure_categoria = serializers.CharField(source='procedure.categoria', read_only=True)

    class Meta:
        model = ProcedureProtocol
        exclude = ['loja_id']
        extra_kwargs = {
            'descricao': {'required': False, 'allow_blank': True},
            'preparacao': {'required': False, 'allow_blank': True},
            'execucao': {'required': False, 'allow_blank': True},
            'pos_procedimento': {'required': False, 'allow_blank': True},
            'materiais_necessarios': {'required': False, 'allow_blank': True},
            'contraindicacoes': {'required': False, 'allow_blank': True},
            'cuidados_especiais': {'required': False, 'allow_blank': True},
        }


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos"""
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True)
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    procedure_price = serializers.DecimalField(source='procedure.preco', max_digits=10, decimal_places=2, read_only=True)
    time = serializers.SerializerMethodField()

    def get_time(self, obj):
        from django.utils import timezone
        local_dt = timezone.localtime(obj.date)
        return local_dt.strftime('%H:%M')
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'time', 'status', 
            'patient', 'patient_name',
            'professional', 'professional_name',
            'procedure', 'procedure_name', 'procedure_price',
            'notes', 'created_at', 'updated_at'
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Serializer detalhado para agendamentos"""
    patient = PatientSerializer(read_only=True)
    professional = ProfessionalSerializer(read_only=True)
    procedure = ProcedureSerializer(read_only=True)
    
    class Meta:
        model = Appointment
        exclude = ['loja_id']  # loja_id é preenchido automaticamente


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer para criação de agendamentos (suporta múltiplos procedimentos)."""
    procedures_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
        help_text="Lista de IDs de procedimentos. Se enviado, substitui o campo 'procedure'.",
    )

    class Meta:
        model = Appointment
        fields = ['date', 'status', 'patient', 'professional', 'procedure', 'procedures_ids', 'notes']
        extra_kwargs = {
            'procedure': {'required': False, 'allow_null': True},
        }

    def validate(self, attrs):
        procedures_ids = attrs.pop('procedures_ids', None)
        procedure = attrs.get('procedure')
        if not procedures_ids and not procedure:
            raise serializers.ValidationError({'procedure': 'Informe pelo menos um procedimento.'})
        if procedures_ids:
            procedures = list(Procedure.objects.filter(id__in=procedures_ids, is_active=True))
            if len(procedures) != len(procedures_ids):
                raise serializers.ValidationError({'procedures_ids': 'Um ou mais procedimentos não encontrados.'})
            attrs['_procedures_list'] = procedures
            # Usa o primeiro como procedure principal (retrocompatibilidade)
            if not procedure:
                attrs['procedure'] = procedures[0]
        return attrs

    def create(self, validated_data):
        procedures_list = validated_data.pop('_procedures_list', None)
        appointment = super().create(validated_data)
        if procedures_list:
            for ordem, proc in enumerate(procedures_list):
                AppointmentProcedure.objects.create(
                    appointment=appointment,
                    procedure=proc,
                    ordem=ordem,
                    loja_id=appointment.loja_id,
                )
        elif appointment.procedure_id:
            # Cria o item na tabela intermediária para consistência
            AppointmentProcedure.objects.create(
                appointment=appointment,
                procedure=appointment.procedure,
                ordem=0,
                loja_id=appointment.loja_id,
            )
        return appointment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para Pagamentos (financeiro da clínica)"""
    appointment_details = AppointmentListSerializer(source='appointment', read_only=True)
    paciente_nome = serializers.CharField(source='appointment.patient.nome', read_only=True)
    profissional_nome = serializers.CharField(source='appointment.professional.nome', read_only=True)
    procedimento_nome = serializers.CharField(source='appointment.procedure.nome', read_only=True)
    data_atendimento = serializers.DateTimeField(source='appointment.date', read_only=True)

    class Meta:
        model = Payment
        exclude = ['loja_id']  # loja_id é preenchido automaticamente


class AppointmentProcedureSerializer(serializers.ModelSerializer):
    """Serializer para procedimentos de um agendamento."""
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    duracao = serializers.SerializerMethodField()
    valor_efetivo = serializers.SerializerMethodField()

    class Meta:
        model = AppointmentProcedure
        fields = ['id', 'procedure', 'procedure_name', 'duracao_minutos', 'duracao', 'valor', 'valor_efetivo', 'ordem']

    def get_duracao(self, obj):
        return obj.get_duracao()

    def get_valor_efetivo(self, obj):
        return float(obj.get_valor())


class AgendaEventSerializer(serializers.ModelSerializer):
    """
    Serializer para eventos da agenda (formato FullCalendar)
    Compatível com drag & drop
    """
    title = serializers.SerializerMethodField()
    start = serializers.DateTimeField(source='date')
    end = serializers.SerializerMethodField()
    backgroundColor = serializers.SerializerMethodField()
    borderColor = serializers.SerializerMethodField()
    textColor = serializers.SerializerMethodField()

    # Dados extras
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    patient_phone = serializers.CharField(source='patient.telefone', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True)
    professional_id = serializers.IntegerField(source='professional.id', read_only=True)
    procedure_name = serializers.SerializerMethodField()
    procedure_duration = serializers.SerializerMethodField()
    duracao_minutos = serializers.SerializerMethodField()
    procedure_price = serializers.SerializerMethodField()
    procedures_list = serializers.SerializerMethodField()

    # Sincronização offline: version e updated_at para detecção de conflito
    version = serializers.IntegerField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    updated_by_id = serializers.IntegerField(read_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'title', 'start', 'end',
            'backgroundColor', 'borderColor', 'textColor',
            'status', 'notes',
            'patient', 'patient_name', 'patient_phone',
            'professional', 'professional_name', 'professional_id',
            'procedure', 'procedure_name', 'procedure_duration', 'duracao_minutos',
            'procedure_price', 'procedures_list',
            'version', 'updated_at', 'updated_by_id',
        ]

    def get_title(self, obj):
        """Título do evento no calendário"""
        procs = obj.appointment_procedures.select_related('procedure').all()
        if procs:
            nomes = ', '.join(ap.procedure.nome for ap in procs)
            return f"{obj.patient.nome} - {nomes}"
        if obj.procedure_id:
            return f"{obj.patient.nome} - {obj.procedure.nome}"
        return obj.patient.nome

    def get_procedure_name(self, obj):
        procs = obj.appointment_procedures.select_related('procedure').all()
        if procs:
            return ', '.join(ap.procedure.nome for ap in procs)
        return obj.procedure.nome if obj.procedure_id else None

    def get_procedure_duration(self, obj):
        return obj.get_duracao_efetiva()

    def get_duracao_minutos(self, obj):
        return obj.get_duracao_efetiva()

    def get_procedure_price(self, obj):
        return float(obj.valor_total)

    def get_procedures_list(self, obj):
        """Lista detalhada dos procedimentos para o frontend."""
        procs = obj.appointment_procedures.select_related('procedure').all()
        if not procs:
            if obj.procedure_id:
                return [{'id': obj.procedure_id, 'nome': obj.procedure.nome,
                         'duracao': obj.procedure.duracao_minutos,
                         'valor': float(obj.procedure.preco or 0)}]
            return []
        return [
            {'id': ap.procedure_id, 'nome': ap.procedure.nome,
             'duracao': ap.get_duracao(), 'valor': float(ap.get_valor())}
            for ap in procs
        ]

    def get_end(self, obj):
        from datetime import timedelta
        return obj.date + timedelta(minutes=obj.get_duracao_efetiva())

    def get_backgroundColor(self, obj):
        colors = {
            'CONFIRMED': '#10b981',
            'PENDING': '#f59e0b',
            'SCHEDULED': '#3b82f6',
            'IN_PROGRESS': '#8b5cf6',
            'COMPLETED': '#6b7280',
            'CANCELLED': '#ef4444',
            'NO_SHOW': '#dc2626',
        }
        return colors.get(obj.status, '#3b82f6')

    def get_borderColor(self, obj):
        return self.get_backgroundColor(obj)

    def get_textColor(self, obj):
        return '#ffffff'


class BloqueioHorarioSerializer(serializers.ModelSerializer):
    """Serializer para Bloqueio de Horário (API usa datetime ISO; model usa date + time)."""
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)
    data_inicio = serializers.DateTimeField()
    data_fim = serializers.DateTimeField()

    class Meta:
        model = BloqueioHorario
        fields = [
            'id', 'professional', 'professional_name',
            'data_inicio', 'data_fim', 'motivo', 'observacoes', 'criado_em',
        ]
        read_only_fields = ['criado_em']

    def to_representation(self, instance):
        inicio, fim = bloqueio_datetime_range(instance)
        prof = instance.professional
        return {
            'id': instance.id,
            'professional': instance.professional_id,
            'professional_name': prof.nome if prof else None,
            'data_inicio': inicio.isoformat(),
            'data_fim': fim.isoformat(),
            'motivo': instance.motivo,
            'observacoes': instance.observacoes,
            'criado_em': instance.criado_em,
        }

    def validate(self, attrs):
        inicio = attrs.get('data_inicio')
        fim = attrs.get('data_fim')
        if inicio and fim and fim <= inicio:
            raise serializers.ValidationError({'data_fim': 'O fim deve ser depois do início.'})
        return attrs

    def create(self, validated_data):
        start = validated_data.pop('data_inicio')
        end = validated_data.pop('data_fim')
        parts = split_datetime_range(start, end)
        motivo = (validated_data.get('motivo') or '').strip() or 'Bloqueio'
        return BloqueioHorario.objects.create(
            **validated_data,
            **parts,
            titulo=motivo,
            tipo='outros',
        )

    def update(self, instance, validated_data):
        start = validated_data.pop('data_inicio', None)
        end = validated_data.pop('data_fim', None)
        if start is not None and end is not None:
            for k, v in split_datetime_range(start, end).items():
                setattr(instance, k, v)
        motivo = validated_data.get('motivo')
        if motivo is not None:
            instance.titulo = motivo
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class PatientAnamneseSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)

    class Meta:
        model = PatientAnamnese
        fields = [
            'id', 'patient', 'patient_name',
            'queixa_principal', 'historico_medico', 'medicamentos_uso', 'alergias',
            'condicoes_clinicas', 'tipo_pele', 'pressao_arterial', 'peso', 'altura',
            'observacoes', 'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class ConsultaEvolucaoSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)

    class Meta:
        model = ConsultaEvolucao
        fields = [
            'id', 'consulta', 'patient', 'patient_name', 'professional', 'professional_name',
            'descricao', 'procedimento_realizado', 'produtos_utilizados', 'orientacoes',
            'protocolo_snapshot', 'satisfacao', 'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id']


class PrescricaoMemedSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)

    class Meta:
        model = PrescricaoMemed
        fields = [
            'id', 'consulta', 'patient', 'patient_name', 'professional', 'professional_name',
            'prescricao_id', 'resumo', 'itens', 'created_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'loja_id']


class ProdutoEstoqueSerializer(serializers.ModelSerializer):
    """Serializer para produtos do estoque — substitui serialização manual."""
    categoria_display = serializers.CharField(source='get_categoria_display', read_only=True)
    estoque_baixo = serializers.BooleanField(read_only=True)

    class Meta:
        model = ProdutoEstoque
        exclude = ['loja_id']


class MovimentacaoEstoqueSerializer(serializers.ModelSerializer):
    """Serializer para movimentações de estoque."""
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    profissional_nome = serializers.CharField(
        source='profissional.nome', read_only=True, default=None,
    )

    class Meta:
        model = MovimentacaoEstoque
        exclude = ['loja_id']


class ConsultaSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.nome', read_only=True)
    professional_name = serializers.CharField(source='professional.nome', read_only=True, default=None)
    procedure_name = serializers.CharField(source='procedure.nome', read_only=True)
    protocol_name = serializers.CharField(source='protocol.nome', read_only=True, default=None)
    appointment_date = serializers.DateTimeField(source='appointment.date', read_only=True)
    appointment_status = serializers.CharField(source='appointment.status', read_only=True)
    duracao_minutos = serializers.ReadOnlyField()
    total_evolucoes = serializers.SerializerMethodField()

    class Meta:
        model = Consulta
        fields = [
            'id', 'appointment', 'patient', 'patient_name', 'professional', 'professional_name',
            'procedure', 'procedure_name', 'protocol', 'protocol_name', 'status',
            'data_inicio', 'data_fim', 'duracao_minutos', 'observacoes_gerais', 'protocolo_notas',
            'valor_consulta', 'appointment_date', 'appointment_status', 'total_evolucoes',
            'created_at', 'updated_at', 'loja_id',
        ]
        read_only_fields = ['created_at', 'updated_at', 'loja_id', 'appointment']

    def get_total_evolucoes(self, obj):
        return obj.evolucoes.count()

