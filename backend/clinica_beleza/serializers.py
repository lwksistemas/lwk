"""
Serializers para Clínica da Beleza
"""
from rest_framework import serializers
from .models import Patient, Professional, Procedure, Appointment, Payment, BloqueioHorario


class ProfessionalCreateWithUserSerializer(serializers.Serializer):
    """
    Cria profissional e usuário de acesso (senha provisória enviada por e-mail).
    Campos: name, email (obrigatório para criar acesso), specialty, phone (opcional), criar_acesso (bool).
    """
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    specialty = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    criar_acesso = serializers.BooleanField(default=False, write_only=True)

    def create(self, validated_data):
        criar_acesso = validated_data.pop('criar_acesso', False)
        email = validated_data.get('email')
        name = validated_data.get('name')

        professional = Professional.objects.create(**validated_data)

        if criar_acesso:
            from django.contrib.auth import get_user_model
            from django.utils.crypto import get_random_string
            from django.core.mail import send_mail
            from django.conf import settings
            from superadmin.models import Loja, ProfissionalUsuario
            from tenants.middleware import get_current_loja_id

            User = get_user_model()
            # User/Loja/ProfissionalUsuario ficam no schema public (default)
            default_db = 'default'
            loja_id = get_current_loja_id()
            if not loja_id:
                raise serializers.ValidationError({'loja': 'Contexto de loja não encontrado.'})

            if User.objects.using(default_db).filter(username=email).exists():
                professional.delete()
                raise serializers.ValidationError({
                    'email': 'Já existe um usuário com este e-mail. Use outro ou não marque "Criar acesso".'
                })

            senha_provisoria = get_random_string(8)
            user = User.objects.using(default_db).create_user(
                username=email,
                email=email,
                password=senha_provisoria,
                first_name=name or '',
            )
            loja = Loja.objects.using(default_db).get(id=loja_id)
            ProfissionalUsuario.objects.using(default_db).create(
                user=user,
                loja=loja,
                professional_id=professional.id,
                precisa_trocar_senha=True,
            )

            site_url = getattr(settings, 'SITE_URL', 'https://lwksistemas.com.br').rstrip('/')
            login_url = f"{site_url}/loja/{loja.slug}/login"
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
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
            except Exception:
                pass  # não falha a criação se o e-mail falhar

        return professional


class PatientSerializer(serializers.ModelSerializer):
    """Serializer para Pacientes"""
    class Meta:
        model = Patient
        fields = '__all__'


class ProfessionalSerializer(serializers.ModelSerializer):
    """Serializer para Profissionais"""
    class Meta:
        model = Professional
        fields = '__all__'


class ProcedureSerializer(serializers.ModelSerializer):
    """Serializer para Procedimentos"""
    class Meta:
        model = Procedure
        fields = '__all__'


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
        fields = '__all__'


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
        fields = '__all__'


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
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'title', 'start', 'end',
            'backgroundColor', 'borderColor', 'textColor',
            'status', 'notes',
            'patient', 'patient_name', 'patient_phone',
            'professional', 'professional_name', 'professional_id',
            'procedure', 'procedure_name', 'procedure_duration', 'procedure_price'
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

