"""
URLs para Clínica da Beleza
"""
from django.urls import path, include
from .views import (
    DashboardView,
    LojaInfoView,
    PatientListView, PatientDetailView,
    ProfessionalListView, ProfessionalDetailView,
    ProfessionalMemedStatusView,
    HorarioTrabalhoProfissionalView,
    ProfessionalCommissionView,
    ProcedureListView, ProcedureDetailView,
    PaymentListView, PaymentDetailView,
    FinanceiroResumoView,
    AgendaView, AgendaHojeView, AgendaUpdateView, AgendaCreateView, AgendaDeleteView,
    AgendaReenviarMensagemView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
    WhatsAppConfigView,
    CampanhaPromocaoListView, CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView,
)
from .views_consultas import (
    ConsultaListView, ConsultaDetailView, ConsultaAplicarProtocoloView,
    ConsultaIniciarView, ConsultaFinalizarView,
    PatientAnamneseView, ConsultaEvolucaoListView, PatientHistoricoConsultasView,
    ConsultaPrescricaoView, PatientPrescricaoView,
    ConsultaProdutoListView, ConsultaProdutoDetailView,
)
from .views_estoque import (
    ProdutoEstoqueListView, ProdutoEstoqueDetailView,
    MovimentacaoEstoqueView, HistoricoEstoqueView, EstoqueResumoView,
)
from .views_protocolos import ProtocolListView, ProtocolDetailView
from .views_memed import MemedTokenView, MemedTimbradoView
from .views_documentos import (
    DocumentTemplateListView, DocumentTemplateDetailView,
    ConsultaDocumentoListView, ConsultaDocumentoDeleteView,
)
from .views_prontuario import (
    ProntuarioView, ProntuarioPDFView, DocumentoPDFView,
)
from .views_admin_professional import (
    AdminProfessionalStatusView, AdminProfessionalToggleView,
)
from .views_locais_atendimento import (
    LocalAtendimentoListView, LocalAtendimentoDetailView,
)
from .views_convenios import (
    ConvenioListView, ConvenioDetailView, ConvenioPrecosView,
)
from .views_relatorios import (
    RelatorioComissoesView,
    RelatorioComissoesPdfView,
    RelatorioRepasseConsultaView,
    RelatorioRepasseConsultaPdfView,
)

app_name = 'clinica_beleza'

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    # Dados do administrador da loja (nome, email, telefone)
    path('loja-info/', LojaInfoView.as_view(), name='loja-info'),
    
    # Pacientes
    path('patients/', PatientListView.as_view(), name='patients-list'),
    path('patients/<int:pk>/', PatientDetailView.as_view(), name='patients-detail'),
    path('patients/<int:patient_id>/anamnese/', PatientAnamneseView.as_view(), name='patient-anamnese'),
    path('patients/<int:patient_id>/consultas/', PatientHistoricoConsultasView.as_view(), name='patient-consultas-historico'),
    path('patients/<int:patient_id>/prescricoes/', PatientPrescricaoView.as_view(), name='patient-prescricoes'),

    # Consultas (criadas via agenda)
    path('consultas/', ConsultaListView.as_view(), name='consultas-list'),
    path('consultas/<int:pk>/', ConsultaDetailView.as_view(), name='consultas-detail'),
    path('consultas/<int:pk>/iniciar/', ConsultaIniciarView.as_view(), name='consultas-iniciar'),
    path('consultas/<int:pk>/finalizar/', ConsultaFinalizarView.as_view(), name='consultas-finalizar'),
    path('consultas/<int:pk>/aplicar-protocolo/', ConsultaAplicarProtocoloView.as_view(), name='consultas-aplicar-protocolo'),
    path('consultas/<int:consulta_id>/evolucoes/', ConsultaEvolucaoListView.as_view(), name='consultas-evolucoes'),
    path('consultas/<int:consulta_id>/prescricoes/', ConsultaPrescricaoView.as_view(), name='consultas-prescricoes'),
    path('consultas/<int:consulta_id>/produtos/', ConsultaProdutoListView.as_view(), name='consultas-produtos'),
    path('consultas/<int:consulta_id>/produtos/<int:pk>/', ConsultaProdutoDetailView.as_view(), name='consultas-produtos-detail'),

    # Locais de atendimento
    path('locais-atendimento/', LocalAtendimentoListView.as_view(), name='locais-atendimento-list'),
    path('locais-atendimento/<int:pk>/', LocalAtendimentoDetailView.as_view(), name='locais-atendimento-detail'),

    # Convênios
    path('convenios/', ConvenioListView.as_view(), name='convenios-list'),
    path('convenios/<int:pk>/', ConvenioDetailView.as_view(), name='convenios-detail'),
    path('convenios/<int:pk>/precos/', ConvenioPrecosView.as_view(), name='convenios-precos'),

    # Memed — prescrição digital (receituário e exames)
    path('memed/token/', MemedTokenView.as_view(), name='memed-token'),
    path('memed/timbrado/', MemedTimbradoView.as_view(), name='memed-timbrado'),
    
    # Profissionais
    path('professionals/admin-status/', AdminProfessionalStatusView.as_view(), name='admin-professional-status'),
    path('professionals/toggle-admin/', AdminProfessionalToggleView.as_view(), name='admin-professional-toggle'),
    path('professionals/memed-status/', ProfessionalMemedStatusView.as_view(), name='professionals-memed-status'),
    path('professionals/', ProfessionalListView.as_view(), name='professionals-list'),
    path('professionals/<int:pk>/', ProfessionalDetailView.as_view(), name='professionals-detail'),
    path('professionals/<int:pk>/horarios-trabalho/', HorarioTrabalhoProfissionalView.as_view(), name='horarios-trabalho'),
    path('professionals/<int:pk>/comissoes/', ProfessionalCommissionView.as_view(), name='professional-comissoes'),
    
    # Procedimentos
    path('procedures/', ProcedureListView.as_view(), name='procedures-list'),
    path('procedures/<int:pk>/', ProcedureDetailView.as_view(), name='procedures-detail'),
    # Protocolos de procedimentos
    path('protocolos/', ProtocolListView.as_view(), name='protocolos-list'),
    path('protocolos/<int:pk>/', ProtocolDetailView.as_view(), name='protocolos-detail'),
    
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
    # Estoque
    path('estoque/', ProdutoEstoqueListView.as_view(), name='estoque-list'),
    path('estoque/resumo/', EstoqueResumoView.as_view(), name='estoque-resumo'),
    path('estoque/<int:pk>/', ProdutoEstoqueDetailView.as_view(), name='estoque-detail'),
    path('estoque/<int:pk>/movimentar/', MovimentacaoEstoqueView.as_view(), name='estoque-movimentar'),
    path('estoque/<int:pk>/historico/', HistoricoEstoqueView.as_view(), name='estoque-historico'),
    # Templates de documentos clínicos
    path('templates/', DocumentTemplateListView.as_view(), name='templates-list'),
    path('templates/<int:pk>/', DocumentTemplateDetailView.as_view(), name='templates-detail'),
    # Documentos da consulta
    path('consultas/<int:consulta_id>/documentos/', ConsultaDocumentoListView.as_view(), name='consulta-documentos-list'),
    path('consultas/<int:consulta_id>/documentos/<int:doc_id>/', ConsultaDocumentoDeleteView.as_view(), name='consulta-documentos-delete'),
    # Prontuário do paciente
    path('patients/<int:patient_id>/prontuario/', ProntuarioView.as_view(), name='prontuario'),
    path('patients/<int:patient_id>/prontuario/pdf/', ProntuarioPDFView.as_view(), name='prontuario-pdf'),
    # PDF de documento individual
    path('documentos/<int:doc_id>/pdf/', DocumentoPDFView.as_view(), name='documento-pdf'),
    # Relatórios
    path('relatorios/comissoes/', RelatorioComissoesView.as_view(), name='relatorio-comissoes'),
    path('relatorios/comissoes/pdf/', RelatorioComissoesPdfView.as_view(), name='relatorio-comissoes-pdf'),
    path('relatorios/repasse-consultas/', RelatorioRepasseConsultaView.as_view(), name='relatorio-repasse-consultas'),
    path('relatorios/repasse-consultas/pdf/', RelatorioRepasseConsultaPdfView.as_view(), name='relatorio-repasse-consultas-pdf'),
]
