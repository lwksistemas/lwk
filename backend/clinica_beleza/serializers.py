"""
Serializers para Clínica da Beleza
"""
from rest_framework import serializers
from .models import Patient, Professional, Procedure, Appointment, Payment


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
    """Serializer para Pagamentos"""
    appointment_details = AppointmentListSerializer(source='appointment', read_only=True)
    
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

