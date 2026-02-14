"""
URLs para Clínica da Beleza
"""
from django.urls import path, include
from .views import (
    DashboardView,
    LojaInfoView,
    AppointmentListView, AppointmentDetailView,
    PatientListView, PatientDetailView,
    ProfessionalListView, ProfessionalDetailView,
    ProcedureListView, ProcedureDetailView,
    PaymentListView, PaymentDetailView,
    FinanceiroResumoView,
    AgendaView, AgendaHojeView, AgendaUpdateView, AgendaCreateView, AgendaDeleteView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
)

app_name = 'clinica_beleza'

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # Dados do administrador da loja (nome, email, telefone)
    path('loja-info/', LojaInfoView.as_view(), name='loja-info'),
    
    # Agendamentos
    path('appointments/', AppointmentListView.as_view(), name='appointments-list'),
    path('appointments/<int:pk>/', AppointmentDetailView.as_view(), name='appointments-detail'),
    
    # Pacientes
    path('patients/', PatientListView.as_view(), name='patients-list'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patients-detail'),
    
    # Profissionais
    path('professionals/', ProfessionalListView.as_view(), name='professionals-list'),
    path('professionals/<int:pk>/', ProfessionalDetailView.as_view(), name='professionals-detail'),
    
    # Procedimentos
    path('procedures/', ProcedureListView.as_view(), name='procedures-list'),
    path('procedures/<int:pk>/', ProcedureDetailView.as_view(), name='procedures-detail'),
    
    # Pagamentos / Financeiro
    path('payments/', PaymentListView.as_view(), name='payments-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payments-detail'),
    path('financeiro/resumo/', FinanceiroResumoView.as_view(), name='financeiro-resumo'),
    
    # Agenda/Calendário
    path('agenda/', AgendaView.as_view(), name='agenda'),
    path('agenda/hoje/', AgendaHojeView.as_view(), name='agenda-hoje'),
    path('agenda/create/', AgendaCreateView.as_view(), name='agenda-create'),
    path('agenda/<int:pk>/update/', AgendaUpdateView.as_view(), name='agenda-update'),
    path('agenda/<int:pk>/delete/', AgendaDeleteView.as_view(), name='agenda-delete'),
    # Bloqueio de Horários
    path('bloqueios/', BloqueioHorarioListView.as_view(), name='bloqueios-list'),
    path('bloqueios/<int:pk>/', BloqueioHorarioDetailView.as_view(), name='bloqueios-detail'),
]
