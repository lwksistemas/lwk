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
