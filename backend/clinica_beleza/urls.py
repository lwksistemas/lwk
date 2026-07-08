"""
URLs para Clínica da Beleza
"""
from django.urls import path, include
from .views import (
    DashboardView,
    LojaInfoView,
    PatientListView, PatientDetailView,
    ProfessionalListView, ProfessionalDetailView,
    HorarioTrabalhoProfissionalView,
    ProfessionalCommissionView,
    ProcedureListView, ProcedureDetailView,
    ProcedimentoConvenioPrecosMatrixView, ProcedurePrecosConvenioView,
    PaymentListView, PaymentDetailView, PaymentParcelaView,
    FinanceiroResumoView, CategoriaDespesaListView, DespesaListView, DespesaDetailView,
    AgendaView, AgendaUpdateView, AgendaCreateView, AgendaDeleteView,
    AgendaPagamentoView, AgendaReenviarMensagemView,
    BloqueioHorarioListView, BloqueioHorarioDetailView,
    CampanhaPromocaoListView, CampanhaPromocaoDetailView, CampanhaPromocaoEnviarView,
)
from .views_consultas import (
    ConsultaListView, ConsultaDetailView, ConsultaAplicarProtocoloView,
    ConsultaIniciarView, ConsultaFinalizarView,
    PatientAnamneseView, ConsultaEvolucaoListView, PatientHistoricoConsultasView,
    ConsultaPrescricaoView, PatientPrescricaoView, PrescricaoMemedPdfView,
    ConsultaProdutoListView, ConsultaProdutoDetailView,
    ConsultaProcedimentoListView, ConsultaProcedimentoDetailView,
    ConsultaSecaoPDFView,
)
from .views_estoque import (
    ProdutoEstoqueListView, ProdutoEstoqueDetailView,
    MovimentacaoEstoqueView, EstoqueResumoView, EstoqueImportarXmlView,
)
from .views_protocolos import ProtocolListView, ProtocolDetailView
from .views_memed import MemedTokenView, MemedTimbradoView, MemedStatusView
from .views_admin_professional import AdminProfessionalStatusView, AdminProfessionalToggleView
from .views_documentos import (
    DocumentTemplateListView, DocumentTemplateDetailView,
    ConsultaDocumentoListView, ConsultaDocumentoDeleteView,
)
from .views_prontuario import (
    ProntuarioView, ProntuarioPDFView, DocumentoPDFView,
)
from .views_locais_atendimento import (
    LocalAtendimentoListView, LocalAtendimentoDetailView,
)
from .views_nomes_agenda import (
    NomeAgendaListView, NomeAgendaDetailView,
)
from .views_retorno import (
    RetornoConfigView,
    RetornoProcedimentoRegraDetailView,
    RetornoProcedimentoRegraListView,
    RetornoVerificarView,
)
from .views_convenios import (
    ConvenioListView, ConvenioDetailView, ConvenioPrecosView,
)
from .views_relatorios import (
    RelatorioComissoesView,
    RelatorioComissoesPdfView,
    RelatorioFaturamentoView,
    RelatorioRepasseConsultaView,
    RelatorioRepasseConsultaPdfView,
)
from .views_assinatura_consentimento import (
    ConsultaAssinaturaPublicaView,
    ConsultaAssinaturaPdfPublicaView,
    ConsultaTermoConsentimentoStatusView,
    ConsultaEnviarTermoAssinaturaView,
    ConsultaReenviarTermoAssinaturaView,
    ConsultaDownloadTermoPdfView,
)
from .views_foto_paciente import (
    ConsultaFotosPacienteView,
    ConsultaFotoQrView,
    ConsultaFotoDeleteView,
    EnviarFotoPublicaView,
)
from .views_agenda_confirmacao import ConfirmarAgendamentoPublicaView
from .views_nfse_config import NFSeConfigView, NFSeConfigTestISSNetView
from .views_asaas_webhook import clinica_beleza_asaas_webhook

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
    path('prescricoes-memed/<int:pk>/pdf/', PrescricaoMemedPdfView.as_view(), name='prescricoes-memed-pdf'),
    path('consultas/<int:consulta_id>/produtos/', ConsultaProdutoListView.as_view(), name='consultas-produtos'),
    path('consultas/<int:consulta_id>/produtos/<int:pk>/', ConsultaProdutoDetailView.as_view(), name='consultas-produtos-detail'),
    path('consultas/<int:consulta_id>/procedimentos/', ConsultaProcedimentoListView.as_view(), name='consultas-procedimentos'),
    path('consultas/<int:consulta_id>/procedimentos/<int:pk>/', ConsultaProcedimentoDetailView.as_view(), name='consultas-procedimentos-detail'),
    path('consultas/<int:consulta_id>/pdf/', ConsultaSecaoPDFView.as_view(), name='consultas-secao-pdf'),
    path('consultas/<int:pk>/termo-consentimento/', ConsultaTermoConsentimentoStatusView.as_view(), name='consultas-termo-status'),
    path('consultas/<int:pk>/termo-consentimento/enviar/', ConsultaEnviarTermoAssinaturaView.as_view(), name='consultas-termo-enviar'),
    path('consultas/<int:pk>/termo-consentimento/reenviar/', ConsultaReenviarTermoAssinaturaView.as_view(), name='consultas-termo-reenviar'),
    path('consultas/<int:pk>/termo-consentimento/pdf/', ConsultaDownloadTermoPdfView.as_view(), name='consultas-termo-pdf'),
    path('assinar-consentimento/<path:token>/pdf/', ConsultaAssinaturaPdfPublicaView.as_view(), name='assinar-consentimento-pdf'),
    path('assinar-consentimento/<path:token>/', ConsultaAssinaturaPublicaView.as_view(), name='assinar-consentimento'),
    path('consultas/<int:pk>/fotos/', ConsultaFotosPacienteView.as_view(), name='consultas-fotos'),
    path('consultas/<int:pk>/fotos/qr/', ConsultaFotoQrView.as_view(), name='consultas-fotos-qr'),
    path('consultas/<int:pk>/fotos/<int:foto_id>/', ConsultaFotoDeleteView.as_view(), name='consultas-fotos-delete'),
    path('enviar-foto/', EnviarFotoPublicaView.as_view(), name='enviar-foto-query'),
    path('enviar-foto/<path:token>/', EnviarFotoPublicaView.as_view(), name='enviar-foto'),

    # Locais de atendimento
    path('locais-atendimento/', LocalAtendimentoListView.as_view(), name='locais-atendimento-list'),
    path('locais-atendimento/<int:pk>/', LocalAtendimentoDetailView.as_view(), name='locais-atendimento-detail'),

    # Nomes de agenda
    path('nomes-agenda/', NomeAgendaListView.as_view(), name='nomes-agenda-list'),
    path('nomes-agenda/<int:pk>/', NomeAgendaDetailView.as_view(), name='nomes-agenda-detail'),

    # Retorno gratuito (taxa de consulta)
    path('retorno/config/', RetornoConfigView.as_view(), name='retorno-config'),
    path('retorno/procedimentos/', RetornoProcedimentoRegraListView.as_view(), name='retorno-procedimentos-list'),
    path('retorno/procedimentos/<int:pk>/', RetornoProcedimentoRegraDetailView.as_view(), name='retorno-procedimentos-detail'),
    path('retorno/verificar/', RetornoVerificarView.as_view(), name='retorno-verificar'),

    # Convênios
    path('convenios/', ConvenioListView.as_view(), name='convenios-list'),
    path('convenios/<int:pk>/', ConvenioDetailView.as_view(), name='convenios-detail'),
    path('convenios/<int:pk>/precos/', ConvenioPrecosView.as_view(), name='convenios-precos'),

    # Memed — prescrição digital (receituário e exames)
    path('memed/token/', MemedTokenView.as_view(), name='memed-token'),
    path('memed/status/', MemedStatusView.as_view(), name='memed-status'),
    path('memed/timbrado/', MemedTimbradoView.as_view(), name='memed-timbrado'),
    
    # Profissionais
    path('professionals/', ProfessionalListView.as_view(), name='professionals-list'),
    path('professionals/admin-status/', AdminProfessionalStatusView.as_view(), name='professionals-admin-status'),
    path('professionals/toggle-admin/', AdminProfessionalToggleView.as_view(), name='professionals-toggle-admin'),
    path('professionals/<int:pk>/', ProfessionalDetailView.as_view(), name='professionals-detail'),
    path('professionals/<int:pk>/horarios-trabalho/', HorarioTrabalhoProfissionalView.as_view(), name='horarios-trabalho'),
    path('professionals/<int:pk>/comissoes/', ProfessionalCommissionView.as_view(), name='professional-comissoes'),
    
    # Procedimentos
    path(
        'procedures/convenio-precos-matrix/',
        ProcedimentoConvenioPrecosMatrixView.as_view(),
        name='procedures-convenio-precos-matrix',
    ),
    path('procedures/', ProcedureListView.as_view(), name='procedures-list'),
    path(
        'procedures/<int:pk>/precos-convenio/',
        ProcedurePrecosConvenioView.as_view(),
        name='procedures-precos-convenio',
    ),
    path('procedures/<int:pk>/', ProcedureDetailView.as_view(), name='procedures-detail'),
    # Protocolos de procedimentos
    path('protocolos/', ProtocolListView.as_view(), name='protocolos-list'),
    path('protocolos/<int:pk>/', ProtocolDetailView.as_view(), name='protocolos-detail'),
    
    # Pagamentos / Financeiro
    path('payments/', PaymentListView.as_view(), name='payments-list'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payments-detail'),
    path('payments/<int:pk>/parcelas/', PaymentParcelaView.as_view(), name='payments-parcelas'),
    path('financeiro/resumo/', FinanceiroResumoView.as_view(), name='financeiro-resumo'),
    path('despesas/categorias/', CategoriaDespesaListView.as_view(), name='despesas-categorias'),
    path('despesas/', DespesaListView.as_view(), name='despesas-list'),
    path('despesas/<int:pk>/', DespesaDetailView.as_view(), name='despesas-detail'),
    
    # Agenda/Calendário
    path('agenda/', AgendaView.as_view(), name='agenda'),
    path('agenda/create/', AgendaCreateView.as_view(), name='agenda-create'),
    path('agenda/<int:pk>/update/', AgendaUpdateView.as_view(), name='agenda-update'),
    path('agenda/<int:pk>/delete/', AgendaDeleteView.as_view(), name='agenda-delete'),
    path('agenda/<int:pk>/pagamento/', AgendaPagamentoView.as_view(), name='agenda-pagamento'),
    path('agenda/<int:pk>/reenviar-mensagem/', AgendaReenviarMensagemView.as_view(), name='agenda-reenviar-mensagem'),
    path('confirmar-agendamento/<path:token>/', ConfirmarAgendamentoPublicaView.as_view(), name='confirmar-agendamento'),
    # Bloqueio de Horários
    path('bloqueios/', BloqueioHorarioListView.as_view(), name='bloqueios-list'),
    path('bloqueios/<int:pk>/', BloqueioHorarioDetailView.as_view(), name='bloqueios-detail'),
    # Campanhas de promoções
    path('campanhas/', CampanhaPromocaoListView.as_view(), name='campanhas-list'),
    path('campanhas/<int:pk>/', CampanhaPromocaoDetailView.as_view(), name='campanhas-detail'),
    path('campanhas/<int:pk>/enviar/', CampanhaPromocaoEnviarView.as_view(), name='campanhas-enviar'),
    # Estoque
    path('estoque/', ProdutoEstoqueListView.as_view(), name='estoque-list'),
    path('estoque/resumo/', EstoqueResumoView.as_view(), name='estoque-resumo'),
    path('estoque/importar-xml/', EstoqueImportarXmlView.as_view(), name='estoque-importar-xml'),
    path('estoque/<int:pk>/', ProdutoEstoqueDetailView.as_view(), name='estoque-detail'),
    path('estoque/<int:pk>/movimentar/', MovimentacaoEstoqueView.as_view(), name='estoque-movimentar'),
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
    path('relatorios/faturamento/', RelatorioFaturamentoView.as_view(), name='relatorio-faturamento'),
    path('relatorios/repasse-consultas/', RelatorioRepasseConsultaView.as_view(), name='relatorio-repasse-consultas'),
    path('relatorios/repasse-consultas/pdf/', RelatorioRepasseConsultaPdfView.as_view(), name='relatorio-repasse-consultas-pdf'),

    # Configuração NFS-e (individual por loja)
    path('nfse-config/', NFSeConfigView.as_view(), name='nfse-config'),
    path('nfse-config/test-issnet/', NFSeConfigTestISSNetView.as_view(), name='nfse-config-test-issnet'),

    # Webhook Asaas da loja (conta própria — configurar URL no painel Asaas)
    path('webhooks/asaas/<str:loja_slug>/', clinica_beleza_asaas_webhook, name='asaas-webhook'),
]
