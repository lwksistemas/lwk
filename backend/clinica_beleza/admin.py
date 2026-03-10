"""
Admin para Clínica da Beleza
"""
from django.contrib import admin
from .models import Patient, Professional, Procedure, Appointment, Payment


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['nome', 'telefone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['nome', 'telefone', 'email', 'cpf']
    ordering = ['nome']


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'especialidade', 'telefone', 'is_active', 'created_at']
    list_filter = ['is_active', 'especialidade', 'created_at']
    search_fields = ['nome', 'especialidade', 'telefone', 'email']
    ordering = ['nome']


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao_minutos', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['nome', 'descricao']
    ordering = ['nome']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'patient', 'professional', 'procedure', 'status', 'created_at']
    list_filter = ['status', 'date', 'professional', 'created_at']
    search_fields = ['patient__nome', 'professional__nome', 'procedure__nome']
    ordering = ['-date']
    date_hierarchy = 'date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'payment_method', 'status', 'payment_date', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_date', 'created_at']
    search_fields = ['appointment__patient__nome']
    ordering = ['-created_at']
    date_hierarchy = 'payment_date'
