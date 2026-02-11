"""
Admin para Clínica da Beleza
"""
from django.contrib import admin
from .models import Patient, Professional, Procedure, Appointment, Payment


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'phone', 'email', 'cpf']
    ordering = ['name']


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialty', 'phone', 'active', 'created_at']
    list_filter = ['active', 'specialty', 'created_at']
    search_fields = ['name', 'specialty', 'phone', 'email']
    ordering = ['name']


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration', 'active', 'created_at']
    list_filter = ['active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'patient', 'professional', 'procedure', 'status', 'created_at']
    list_filter = ['status', 'date', 'professional', 'created_at']
    search_fields = ['patient__name', 'professional__name', 'procedure__name']
    ordering = ['-date']
    date_hierarchy = 'date'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'appointment', 'amount', 'payment_method', 'status', 'payment_date', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_date', 'created_at']
    search_fields = ['appointment__patient__name']
    ordering = ['-created_at']
    date_hierarchy = 'payment_date'
