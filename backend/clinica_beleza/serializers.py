"""
Serializers para Clínica da Beleza
"""
from rest_framework import serializers
from .models import Patient, Professional, Procedure, Appointment, Payment, BloqueioHorario, HorarioTrabalhoProfissional


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
        import logging
        logger = logging.getLogger(__name__)
        criar_acesso = validated_data.pop('criar_acesso', False)
        perfil = validated_data.pop('perfil', 'profissional')
        valid_perfis = ('administrador', 'profissional', 'recepcao', 'recepcionista', 'caixa', 'limpeza', 'estoque')
        if perfil not in valid_perfis:
            perfil = 'profissional'
        email = validated_data.get('email')
        name = validated_data.get('name')

        professional = Professional.objects.create(**validated_data)

        if criar_acesso:
            from django.contrib.auth import get_user_model
            from django.utils.crypto import get_random_string
            from django.core.mail import send_mail
            from django.conf import settings
            from django.db import IntegrityError
            from superadmin.models import Loja, ProfissionalUsuario
            from tenants.middleware import get_current_loja_id

            User = get_user_model()
            default_db = 'default'
            try:
                loja_id = get_current_loja_id()
                if not loja_id:
                    professional.delete()
                    msg = 'Contexto de loja não encontrado.'
                    raise serializers.ValidationError({'loja': msg, 'detail': msg})

                loja = Loja.objects.using(default_db).get(id=loja_id)
                senha_provisoria = get_random_string(8)
                user = None

                existing_user = User.objects.using(default_db).filter(username=email).first()
                if existing_user:
                    # Já é profissional DESTA loja -> não permitir duplicar
                    if ProfissionalUsuario.objects.using(default_db).filter(
                        user=existing_user,
                        loja_id=loja_id,
                    ).exists():
                        professional.delete()
                        msg = 'Este e-mail já possui acesso a esta loja. Use outro ou cadastre sem "Criar acesso".'
                        raise serializers.ValidationError({'email': msg, 'detail': msg})
                    # É proprietário de alguma loja -> não reutilizar
                    if existing_user.lojas_owned.exists():
                        professional.delete()
                        msg = 'Já existe um usuário (proprietário de loja) com este e-mail. Use outro ou não marque "Criar acesso".'
                        raise serializers.ValidationError({'email': msg, 'detail': msg})
                    # Usuário órfão ou só em outras lojas: reutilizar e vincular a esta loja
                    user = existing_user
                    user.set_password(senha_provisoria)
                    user.first_name = name or user.first_name or ''
                    user.save(update_fields=['password', 'first_name'])
                    ProfissionalUsuario.objects.using(default_db).create(
                        user=user,
                        loja=loja,
                        professional_id=professional.id,
                        perfil=perfil,
                        precisa_trocar_senha=True,
                    )
                    logger.info('Usuário órfão reutilizado para acesso à loja: %s (email=%s)', loja_id, email)
                else:
                    # Novo usuário
                    user = User.objects.db_manager(default_db).create_user(
                        username=email,
                        email=email,
                        password=senha_provisoria,
                        first_name=name or '',
                    )
                    ProfissionalUsuario.objects.using(default_db).create(
                        user=user,
                        loja=loja,
                        professional_id=professional.id,
                        perfil=perfil,
                        precisa_trocar_senha=True,
                    )

                site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
                login_url = f"{site_url}/loja/{loja.slug}/login"
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'noreply@lwksistemas.com.br'
                try:
                    send_mail(
                        subject='Acesso ao sistema - Clínica da Beleza',
                        message=(
                            f"Olá, {name or 'Profissional'}!\n\n"
                            f"Seu acesso ao sistema foi criado.\n\n"
                            f"Login: {email}\n"
                            f"Senha provisória: {senha_provisoria}\n\n"
                            f"Acesse: {login_url}\n\n"
                            f"Por segurança, altere sua senha no primeiro acesso."
                        ),
                        from_email=from_email,
                        recipient_list=[email],
                        fail_silently=True,
                    )
                except Exception as mail_err:
                    logger.warning('Envio de e-mail ao criar profissional falhou: %s', mail_err)
            except serializers.ValidationError:
                raise
            except Loja.DoesNotExist:
                professional.delete()
                logger.warning('Loja id=%s não encontrada ao criar acesso', loja_id)
                msg = 'Loja não encontrada. Tente novamente ou cadastre sem "Criar acesso".'
                raise serializers.ValidationError({'loja': msg, 'detail': msg})
            except IntegrityError as e:
                professional.delete()
                logger.warning('IntegrityError ao criar ProfissionalUsuario: %s', e)
                msg = 'Este e-mail já possui acesso a esta loja ou há conflito de dados. Cadastre sem "Criar acesso" ou use outro e-mail.'
                raise serializers.ValidationError({'email': msg, 'detail': msg})
            except Exception as e:
                professional.delete()
                logger.exception('Erro ao criar acesso do profissional: %s', e)
                msg = 'Erro ao criar acesso. Tente novamente ou cadastre sem "Criar acesso".'
                raise serializers.ValidationError({'detail': msg})

        return professional


class PatientSerializer(serializers.ModelSerializer):
    """Serializer para Pacientes. Aceita phone opcional e birth_date em YYYY-MM-DD ou DD/MM/YYYY."""
    phone = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=20)
    birth_date = serializers.DateField(required=False, allow_null=True, input_formats=['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'])

    class Meta:
        model = Patient
        exclude = ['loja_id']  # loja_id é preenchido automaticamente
        extra_kwargs = {
            'email': {'required': False, 'allow_blank': True, 'allow_null': True},
            'cpf': {'required': False, 'allow_blank': True, 'allow_null': True},
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
            'phone': {'required': False, 'allow_blank': True, 'allow_null': True},
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
        exclude = ['loja_id']  # loja_id é preenchido automaticamente


class AppointmentListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de agendamentos"""
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    professional_name = serializers.CharField(source='professional.name', read_only=True)
    procedure_name = serializers.CharField(source='procedure.name', read_only=True)
    procedure_price = serializers.DecimalField(source='procedure.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'date', 'status', 
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
    """Serializer para criação de agendamentos"""
    class Meta:
        model = Appointment
        fields = ['date', 'status', 'patient', 'professional', 'procedure', 'notes']


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer para Pagamentos (financeiro da clínica)"""
    appointment_details = AppointmentListSerializer(source='appointment', read_only=True)
    paciente_nome = serializers.CharField(source='appointment.patient.name', read_only=True)
    profissional_nome = serializers.CharField(source='appointment.professional.name', read_only=True)
    procedimento_nome = serializers.CharField(source='appointment.procedure.name', read_only=True)
    data_atendimento = serializers.DateTimeField(source='appointment.date', read_only=True)

    class Meta:
        model = Payment
        exclude = ['loja_id']  # loja_id é preenchido automaticamente


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
    patient_name = serializers.CharField(source='patient.name', read_only=True)
    patient_phone = serializers.CharField(source='patient.phone', read_only=True)
    professional_name = serializers.CharField(source='professional.name', read_only=True)
    professional_id = serializers.IntegerField(source='professional.id', read_only=True)
    procedure_name = serializers.CharField(source='procedure.name', read_only=True)
    procedure_duration = serializers.IntegerField(source='procedure.duration', read_only=True)
    procedure_price = serializers.DecimalField(source='procedure.price', max_digits=10, decimal_places=2, read_only=True)
    
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
            'procedure', 'procedure_name', 'procedure_duration', 'procedure_price',
            'version', 'updated_at', 'updated_by_id',
        ]
    
    def get_title(self, obj):
        """Título do evento no calendário"""
        return f"{obj.patient.name} - {obj.procedure.name}"
    
    def get_end(self, obj):
        """Calcula o fim do evento baseado na duração do procedimento"""
        from datetime import timedelta
        return obj.date + timedelta(minutes=obj.procedure.duration)
    
    def get_backgroundColor(self, obj):
        """Cor de fundo baseada no status"""
        colors = {
            'CONFIRMED': '#10b981',  # Verde
            'PENDING': '#f59e0b',    # Amarelo
            'SCHEDULED': '#3b82f6',  # Azul
            'IN_PROGRESS': '#8b5cf6', # Roxo
            'COMPLETED': '#6b7280',  # Cinza
            'CANCELLED': '#ef4444',  # Vermelho
            'NO_SHOW': '#dc2626',    # Vermelho escuro
        }
        return colors.get(obj.status, '#3b82f6')
    
    def get_borderColor(self, obj):
        """Cor da borda (mesma do fundo, mais escura)"""
        return self.get_backgroundColor(obj)
    
    def get_textColor(self, obj):
        """Cor do texto (sempre branco)"""
        return '#ffffff'


class BloqueioHorarioSerializer(serializers.ModelSerializer):
    """Serializer para Bloqueio de Horário"""
    professional_name = serializers.CharField(source='professional.name', read_only=True, default=None)

    class Meta:
        model = BloqueioHorario
        fields = [
            'id', 'professional', 'professional_name',
            'data_inicio', 'data_fim', 'motivo', 'observacoes', 'criado_em',
        ]
        read_only_fields = ['criado_em']

