"""
URLs para Clínica da Beleza
"""
from django.urls import path
from .views import (
    DashboardView,
    AppointmentListView, AppointmentDetailView,
    PatientListView,
    ProfessionalListView,
    ProcedureListView,
    PaymentListView,
    AgendaView, AgendaUpdateView, AgendaCreateView, AgendaDeleteView
)

app_name = 'clinica_beleza'

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    
    # Agendamentos
    path('appointments/', AppointmentListView.as_view(), name='appointments-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointments-detail'),
    
    # Pacientes
    path('patients/', PatientListView.as_view(), name='patients-list'),
    
    # Profissionais
    path('professionals/', ProfessionalListView.as_view(), name='professionals-list'),
    
    # Procedimentos
    path('procedures/', ProcedureListView.as_view(), name='procedures-list'),
    
    # Pagamentos
    path('payments/', PaymentListView.as_view(), name='payments-list'),
    
    # Agenda/Calendário
    path('agenda/', AgendaView.as_view(), name='agenda'),
    path('agenda/create/', AgendaCreateView.as_view(), name='agenda-create'),
    path('agenda/<int:pk>/update/', AgendaUpdateView.as_view(), name='agenda-update'),
    path('agenda/<int:pk>/delete/', AgendaDeleteView.as_view(), name='agenda-delete'),
]
