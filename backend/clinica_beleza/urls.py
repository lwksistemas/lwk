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
    AgendaReenviarMensagemView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
    WhatsAppConfigView,
    CampanhaPromocaoListView, CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView,
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
    path('agenda/<int:pk>/reenviar-mensagem/', AgendaReenviarMensagemView.as_view(), name='agenda-reenviar-mensagem'),
    # Bloqueio de Horários
    path('bloqueios/', BloqueioHorarioListView.as_view(), name='bloqueios-list'),
    path('bloqueios/<int:pk>/', BloqueioHorarioDetailView.as_view(), name='bloqueios-detail'),
    # Configuração WhatsApp (ETAPA 4)
    path('whatsapp-config/', WhatsAppConfigView.as_view(), name='whatsapp-config'),
    # Campanhas de promoções
    path('campanhas/', CampanhaPromocaoListView.as_view(), name='campanhas-list'),
    path('campanhas/<int:pk>/', CampanhaPromocaoDetailView.as_view(), name='campanhas-detail'),
    path('campanhas/<int:pk>/enviar/', CampanhaPromocaoEnviarView.as_view(), name='campanhas-enviar'),
]
