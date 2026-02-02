'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { clinicaApiClient } from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { ThemeToggle } from '@/components/ui/ThemeProvider';
import { DashboardSkeleton, AgendamentosListSkeleton } from '@/components/ui/Skeleton';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

interface EstatisticasCRM {
  leads_ativos: number;
  negociacoes: number;
  vendas_mes: number;
  receita: number;
}

interface Lead {
  id: number;
  nome: string;
  empresa: string;
  status: string;
  valor_estimado: number | string;
  created_at?: string;
}

// Valores do backend (Lead model) - usados no dashboard e modais
const ORIGENS_CRM = [
  { value: 'site', label: 'Site' },
  { value: 'indicacao', label: 'Indicação' },
  { value: 'redes_sociais', label: 'Redes Sociais' },
  { value: 'email_marketing', label: 'Email Marketing' },
  { value: 'evento', label: 'Evento' },
  { value: 'telefone', label: 'Telefone' },
  { value: 'outro', label: 'Outro' }
];
const STATUS_LEAD = [
  { value: 'novo', label: 'Novo Lead' },
  { value: 'contato_inicial', label: 'Contato Inicial' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'proposta_enviada', label: 'Proposta Enviada' },
  { value: 'negociacao', label: 'Negociação' },
  { value: 'fechado', label: 'Fechado' },
  { value: 'perdido', label: 'Perdido' }
];
const INTERESSES_CRM = ['Produto A', 'Produto B', 'Serviço Premium', 'Consultoria', 'Outro'];

export default function DashboardCRMVendas({ loja }: { loja: LojaInfo }) {
  const router = useRouter();
  const toast = useToast();
  const [showModalPipeline, setShowModalPipeline] = useState(false);
  const [showModalLead, setShowModalLead] = useState(false);
  const [showModalCliente, setShowModalCliente] = useState(false);
  const [showModalVendedor, setShowModalVendedor] = useState(false);
  const [showModalProduto, setShowModalProduto] = useState(false);
  const [showModalFuncionarios, setShowModalFuncionarios] = useState(false);

  const [estatisticas, setEstatisticas] = useState<EstatisticasCRM>({
    leads_ativos: 0,
    negociacoes: 0,
    vendas_mes: 0,
    receita: 0
  });
  const [leadsRecentes, setLeadsRecentes] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingLeads, setLoadingLeads] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setLoadingLeads(true);
      const [statsRes, leadsRes] = await Promise.all([
        clinicaApiClient.get<EstatisticasCRM>('/crm/vendas/estatisticas/'),
        clinicaApiClient.get<Lead[] | { results?: Lead[] }>('/crm/leads/recentes/')
      ]);
      // Estatísticas: aceitar objeto direto ou aninhado
      const stats = statsRes.data;
      setEstatisticas(
        stats && typeof stats === 'object' && 'leads_ativos' in stats
          ? stats as EstatisticasCRM
          : { leads_ativos: 0, negociacoes: 0, vendas_mes: 0, receita: 0 }
      );
      // Leads: aceitar array direto, formato paginado { results: [] } ou fallback []
      const leadsRaw = leadsRes.data;
      const leadsArray = Array.isArray(leadsRaw)
        ? leadsRaw
        : (leadsRaw && typeof leadsRaw === 'object' && Array.isArray((leadsRaw as { results?: Lead[] }).results))
          ? (leadsRaw as { results: Lead[] }).results
          : [];
      setLeadsRecentes(leadsArray);
    } catch (error) {
      console.error('Erro ao carregar dashboard CRM:', error);
      toast.error('Erro ao carregar dashboard');
      setLeadsRecentes([]);
    } finally {
      setLoading(false);
      setLoadingLeads(false);
    }
  }, [toast]);

  useEffect(() => {
    if (typeof window !== 'undefined' && loja?.id) {
      const current = sessionStorage.getItem('current_loja_id');
      if (current !== String(loja.id)) sessionStorage.setItem('current_loja_id', String(loja.id));
      if (loja.slug) sessionStorage.setItem('loja_slug', loja.slug);
    }
    loadDashboard();
  }, [loadDashboard, loja?.id, loja?.slug]);

  const handleNovoLead = () => setShowModalLead(true);
  const handleClientes = () => setShowModalCliente(true);
  const handleVendedores = () => setShowModalFuncionarios(true);
  const handleNovoProduto = () => setShowModalProduto(true);
  const handlePipeline = () => setShowModalPipeline(true);
  const handleRelatorios = () => router.push(`/loja/${loja.slug}/relatorios`);

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="space-y-6 sm:space-y-8 px-2 sm:px-4 lg:px-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard - {loja.nome}
        </h1>
        <ThemeToggle />
      </div>

      {/* Ações Rápidas */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg card-hover">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          🚀 Ações Rápidas
        </h3>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2 sm:gap-3 md:gap-4">
          <ActionButton onClick={handleNovoLead} color="#3B82F6" icon="🎯" label="Leads" />
          <ActionButton onClick={handleClientes} color="#F59E0B" icon="👤" label="Clientes" />
          <ActionButton onClick={handleVendedores} color="#EC4899" icon="👥" label="Funcionários" />
          <ActionButton onClick={handleNovoProduto} color="#06B6D4" icon="📦" label="Produto" />
          <ActionButton onClick={handlePipeline} color="#8B5CF6" icon="🔄" label="Pipeline" />
          <ActionButton onClick={handleRelatorios} color="#059669" icon="📊" label="Relatórios" />
        </div>
        <div className="mt-3 sm:mt-4 p-2 sm:p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
          <p className="text-[10px] sm:text-xs text-gray-600 dark:text-gray-400 text-center">
            💡 <strong>Dashboard CRM Vendas</strong> - Clique nas ações para gerenciar sua equipe e pipeline
          </p>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        <StatCard title="Leads Ativos" value={estatisticas.leads_ativos} icon="👥" cor={loja.cor_primaria} />
        <StatCard title="Negociações" value={estatisticas.negociacoes} icon="🤝" cor={loja.cor_primaria} />
        <StatCard title="Vendas Mês" value={estatisticas.vendas_mes} icon="📈" cor={loja.cor_primaria} />
        <StatCard title="Receita" value={`R$ ${Number(estatisticas.receita).toLocaleString('pt-BR')}`} icon="💰" cor={loja.cor_primaria} />
      </div>

      {/* Leads Recentes */}
      <div className="bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-xl shadow-lg">
        <div className="flex items-center justify-between mb-3 sm:mb-4">
          <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">Leads Recentes</h3>
          <button
            onClick={handleNovoLead}
            className="text-xs sm:text-sm px-3 sm:px-4 py-2 min-h-[40px] rounded-lg text-white hover:opacity-90 transition-all btn-press shadow-md"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo
          </button>
        </div>

        {loadingLeads ? (
          <AgendamentosListSkeleton count={3} />
        ) : !Array.isArray(leadsRecentes) || leadsRecentes.length === 0 ? (
          <EmptyState
            message="Nenhum lead cadastrado"
            subMessage="Comece adicionando seu primeiro lead"
            actionLabel="+ Adicionar Primeiro Lead"
            onAction={handleNovoLead}
            cor={loja.cor_primaria}
            icon="🎯"
          />
        ) : (
          <div className="space-y-4">
            {(Array.isArray(leadsRecentes) ? leadsRecentes : []).map((lead: Lead) => (
              <LeadCard key={lead.id} lead={lead} cor={loja.cor_primaria} />
            ))}
          </div>
        )}
      </div>

      {/* Modais */}
      {showModalLead && <ModalNovoLead loja={loja} onClose={() => setShowModalLead(false)} onSuccess={loadDashboard} />}
      {showModalCliente && <ModalNovoCliente loja={loja} onClose={() => setShowModalCliente(false)} />}
      {showModalVendedor && <ModalNovoVendedor loja={loja} onClose={() => setShowModalVendedor(false)} />}
      {showModalProduto && <ModalNovoProduto loja={loja} onClose={() => setShowModalProduto(false)} />}
      {showModalPipeline && <ModalPipeline loja={loja} onClose={() => setShowModalPipeline(false)} />}
      {showModalFuncionarios && <ModalFuncionarios loja={loja} onClose={() => setShowModalFuncionarios(false)} />}
    </div>
  );
}

function ActionButton({ onClick, color, icon, label }: { onClick: () => void; color: string; icon: string; label: string }) {
  return (
    <button
      onClick={onClick}
      className="group p-2 sm:p-3 md:p-4 rounded-lg sm:rounded-xl text-white font-semibold transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-md sm:shadow-lg hover:shadow-xl btn-press relative overflow-hidden min-h-[70px] sm:min-h-[80px] md:min-h-[100px]"
      style={{ backgroundColor: color }}
    >
      <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
      <div className="relative flex flex-col items-center justify-center h-full">
        <div className="text-xl sm:text-2xl md:text-3xl mb-1 sm:mb-2">{icon}</div>
        <div className="text-[10px] sm:text-xs md:text-sm leading-tight text-center">{label}</div>
      </div>
    </button>
  );
}

function StatCard({ title, value, icon, cor }: { title: string; value: string | number; icon: string; cor: string }) {
  return (
    <div className="bg-white dark:bg-gray-800 p-3 sm:p-4 md:p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 card-hover group">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="text-gray-500 dark:text-gray-400 text-xs sm:text-sm font-medium truncate">{title}</h3>
          <p className="text-xl sm:text-2xl md:text-3xl font-bold mt-1 sm:mt-2 text-gray-900 dark:text-white truncate" style={{ color: cor }}>
            {value}
          </p>
        </div>
        <div className="w-10 h-10 sm:w-12 sm:h-12 md:w-14 md:h-14 rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: `${cor}20` }}>
          <span className="text-xl sm:text-2xl md:text-3xl">{icon}</span>
        </div>
      </div>
    </div>
  );
}

function LeadCard({ lead, cor }: { lead: Lead; cor: string }) {
  const valor = typeof lead.valor_estimado === 'string' ? parseFloat(lead.valor_estimado) : Number(lead.valor_estimado);
  const statusLabel = STATUS_LEAD.find(s => s.value === lead.status)?.label ?? lead.status;
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between p-3 sm:p-4 bg-gray-50 dark:bg-gray-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 transition-all gap-3 sm:gap-4 card-hover">
      <div className="flex items-center space-x-3 sm:space-x-4">
        <div className="w-10 h-10 sm:w-12 sm:h-12 rounded-lg sm:rounded-xl flex items-center justify-center text-white font-bold flex-shrink-0 shadow-md" style={{ backgroundColor: cor }}>
          {lead.nome.charAt(0)}
        </div>
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-gray-900 dark:text-white text-sm sm:text-base truncate">{lead.nome}</p>
          <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 truncate">{lead.empresa}</p>
        </div>
      </div>
      <div className="flex sm:flex-col items-center sm:items-end gap-2">
        <p className="font-bold text-base sm:text-lg" style={{ color: cor }}>
          R$ {valor.toLocaleString('pt-BR')}
        </p>
        <span className="text-xs text-gray-600 dark:text-gray-400">{statusLabel}</span>
      </div>
    </div>
  );
}

function EmptyState({ message, subMessage, actionLabel, onAction, cor, icon = '📋' }: {
  message: string;
  subMessage: string;
  actionLabel: string;
  onAction: () => void;
  cor: string;
  icon?: string;
}) {
  return (
    <div className="text-center py-8 sm:py-12 px-4">
      <div className="w-12 h-12 sm:w-16 sm:h-16 mx-auto mb-3 sm:mb-4 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        <span className="text-2xl sm:text-3xl">{icon}</span>
      </div>
      <p className="text-base sm:text-lg mb-1 sm:mb-2 text-gray-700 dark:text-gray-300">{message}</p>
      <p className="text-xs sm:text-sm mb-4 text-gray-500 dark:text-gray-500">{subMessage}</p>
      <button
        onClick={onAction}
        className="px-4 sm:px-6 py-2.5 sm:py-3 min-h-[44px] rounded-xl text-white hover:opacity-90 transition-all btn-press shadow-lg text-sm sm:text-base active:scale-95"
        style={{ backgroundColor: cor }}
      >
        {actionLabel}
      </button>
    </div>
  );
}

// Modal Gerenciar Leads (Listar, Criar, Editar, Excluir)
function ModalNovoLead({ loja, onClose, onSuccess }: { loja: LojaInfo; onClose: () => void; onSuccess?: () => void }) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [leadEditando, setLeadEditando] = useState<number | null>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    cargo: '',
    origem: 'site',
    interesse: 'Produto A',
    valor_estimado: '',
    status: 'novo',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const loadLeads = async () => {
    try {
      setLoadingLista(true);
      const res = await clinicaApiClient.get('/crm/leads/');
      setLeads(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      console.error('Erro ao carregar leads:', error);
      toast.error('Erro ao carregar leads');
      setLeads([]);
    } finally {
      setLoadingLista(false);
    }
  };

  useEffect(() => {
    loadLeads();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNovo = () => {
    setLeadEditando(null);
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cargo: '', origem: 'site', interesse: 'Produto A', valor_estimado: '', status: 'novo', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (lead: any) => {
    setLeadEditando(lead.id);
    setFormData({
      nome: lead.nome,
      email: lead.email,
      telefone: lead.telefone,
      empresa: lead.empresa,
      cargo: lead.cargo || '',
      origem: lead.origem || 'site',
      interesse: lead.interesse || 'Produto A',
      valor_estimado: String(lead.valor_estimado ?? ''),
      status: lead.status || 'novo',
      observacoes: lead.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (leadId: number, leadNome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o lead "${leadNome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/crm/leads/${leadId}/`);
      toast.success(`Lead "${leadNome}" excluído`);
      loadLeads();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir lead');
    }
  };

  const handleConverterCliente = async (lead: any) => {
    if (!confirm(`Converter o lead "${lead.nome}" em cliente?\n\nIsso significa que a venda foi fechada e o lead se tornou um cliente ativo.`)) return;
    try {
      await clinicaApiClient.post('/crm/clientes/', {
        nome: lead.nome,
        email: lead.email,
        telefone: lead.telefone,
        empresa: lead.empresa,
        cnpj: '',
        endereco: '',
        cidade: '',
        estado: '',
        observacoes: ''
      });
      await clinicaApiClient.delete(`/crm/leads/${lead.id}/`);
      toast.success(`Lead "${lead.nome}" convertido em cliente!`);
      loadLeads();
      onSuccess?.();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.response?.data?.nome?.[0] || 'Erro ao converter lead');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        nome: formData.nome,
        email: formData.email,
        telefone: formData.telefone,
        empresa: formData.empresa,
        cargo: formData.cargo || null,
        origem: formData.origem,
        interesse: formData.interesse,
        valor_estimado: formData.valor_estimado ? parseFloat(formData.valor_estimado) : 0,
        status: formData.status,
        observacoes: formData.observacoes || null
      };
      if (leadEditando) {
        await clinicaApiClient.put(`/crm/leads/${leadEditando}/`, payload);
        toast.success('Lead atualizado com sucesso');
      } else {
        await clinicaApiClient.post('/crm/leads/', payload);
        toast.success('Lead cadastrado com sucesso');
      }
      setMostrarFormulario(false);
      setLeadEditando(null);
      setFormData({ nome: '', email: '', telefone: '', empresa: '', cargo: '', origem: 'site', interesse: 'Produto A', valor_estimado: '', status: 'novo', observacoes: '' });
      loadLeads();
      onSuccess?.();
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.response?.data?.nome?.[0] || 'Erro ao salvar lead';
      toast.error(typeof msg === 'string' ? msg : 'Erro ao salvar lead');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
          <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>
            🎯 {leadEditando ? 'Editar' : 'Novo'} Lead
          </h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700">Informações do Lead</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo *</label>
                  <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: João Silva" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                  <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Empresa *</label>
                  <input type="text" name="empresa" value={formData.empresa} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Nome da empresa" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cargo</label>
                  <input type="text" name="cargo" value={formData.cargo} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: Gerente de Compras" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Origem *</label>
                  <select name="origem" value={formData.origem} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    {ORIGENS_CRM.map(o => (<option key={o.value} value={o.value}>{o.label}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Interesse *</label>
                  <select name="interesse" value={formData.interesse} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    {INTERESSES_CRM.map(int => (<option key={int} value={int}>{int}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Status *</label>
                  <select name="status" value={formData.status} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                    {STATUS_LEAD.map(st => (<option key={st.value} value={st.value}>{st.label}</option>))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Valor Estimado (R$)</label>
                  <input type="number" name="valor_estimado" value={formData.valor_estimado} onChange={handleChange} min="0" step="0.01" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="0.00" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                  <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o lead..." />
                </div>
              </div>
            </div>
            <div className="flex justify-end space-x-4 pt-4">
              <button type="button" onClick={() => { setMostrarFormulario(false); setLeadEditando(null); }} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (leadEditando ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  const getStatusLabel = (value: string) => STATUS_LEAD.find(s => s.value === value)?.label ?? value;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>🎯 Gerenciar Leads</h3>

        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando leads...</div>
        ) : !Array.isArray(leads) || leads.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="mb-4">Nenhum lead cadastrado.</p>
            <button onClick={handleNovo} className="px-6 py-2 rounded-lg text-white hover:opacity-90" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Lead</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {(Array.isArray(leads) ? leads : []).map((lead: any) => (
              <div key={lead.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-lg text-gray-900 dark:text-white">{lead.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 truncate">{lead.empresa} • {lead.email}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{lead.telefone} • {ORIGENS_CRM.find(o => o.value === lead.origem)?.label ?? lead.origem}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">{getStatusLabel(lead.status)}</span>
                    <span className="text-sm font-bold" style={{ color: loja.cor_primaria }}>R$ {Number(lead.valor_estimado).toLocaleString('pt-BR')}</span>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
                  <button onClick={() => handleEditar(lead)} className="px-3 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleConverterCliente(lead)} className="px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 min-h-[40px]">✅ Converter</button>
                  <button onClick={() => handleExcluir(lead.id, lead.nome)} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Lead</button>
        </div>
      </div>
    </div>
  );
}

// Modal Gerenciar Clientes (Listar, Criar, Editar, Excluir)
function ModalNovoCliente({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [clienteEditando, setClienteEditando] = useState<number | null>(null);
  const [clientes, setClientes] = useState<any[]>([]);
  const [loadingLista, setLoadingLista] = useState(true);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    empresa: '',
    cnpj: '',
    endereco: '',
    cidade: '',
    estado: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const estados = ['AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'];

  const loadClientes = async () => {
    try {
      setLoadingLista(true);
      const res = await clinicaApiClient.get('/crm/clientes/');
      setClientes(Array.isArray(res.data) ? res.data : res.data?.results ?? []);
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
      toast.error('Erro ao carregar clientes');
      setClientes([]);
    } finally {
      setLoadingLista(false);
    }
  };

  useEffect(() => {
    loadClientes();
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleNovo = () => {
    setClienteEditando(null);
    setFormData({ nome: '', email: '', telefone: '', empresa: '', cnpj: '', endereco: '', cidade: '', estado: '', observacoes: '' });
    setMostrarFormulario(true);
  };

  const handleEditar = (cliente: any) => {
    setClienteEditando(cliente.id);
    setFormData({
      nome: cliente.nome,
      email: cliente.email ?? '',
      telefone: cliente.telefone ?? '',
      empresa: cliente.empresa ?? '',
      cnpj: cliente.cnpj ?? cliente.cpf_cnpj ?? '',
      endereco: cliente.endereco || '',
      cidade: cliente.cidade || '',
      estado: cliente.estado || '',
      observacoes: cliente.observacoes || ''
    });
    setMostrarFormulario(true);
  };

  const handleExcluir = async (clienteId: number, clienteNome: string) => {
    if (!confirm(`Tem certeza que deseja excluir o cliente "${clienteNome}"?`)) return;
    try {
      await clinicaApiClient.delete(`/crm/clientes/${clienteId}/`);
      toast.success(`Cliente "${clienteNome}" excluído com sucesso`);
      loadClientes();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erro ao excluir cliente');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const payload = {
        nome: formData.nome,
        email: formData.email || null,
        telefone: formData.telefone,
        empresa: formData.empresa,
        cnpj: formData.cnpj || null,
        cpf_cnpj: formData.cnpj || null,
        endereco: formData.endereco || null,
        cidade: formData.cidade || null,
        estado: formData.estado || null
      };
      if (clienteEditando) {
        await clinicaApiClient.put(`/crm/clientes/${clienteEditando}/`, payload);
        toast.success('Cliente atualizado com sucesso');
      } else {
        await clinicaApiClient.post('/crm/clientes/', payload);
        toast.success('Cliente cadastrado com sucesso');
      }
      setMostrarFormulario(false);
      setClienteEditando(null);
      setFormData({ nome: '', email: '', telefone: '', empresa: '', cnpj: '', endereco: '', cidade: '', estado: '', observacoes: '' });
      loadClientes();
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.response?.data?.nome?.[0] || 'Erro ao salvar cliente';
      toast.error(typeof msg === 'string' ? msg : 'Erro ao salvar cliente');
    } finally {
      setLoading(false);
    }
  };

  if (mostrarFormulario) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👤 {clienteEditando ? 'Editar' : 'Novo'} Cliente</h3>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700 dark:text-gray-300">Dados do Cliente</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome/Razão Social *</label>
                  <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="Nome completo ou razão social" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email *</label>
                  <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="email@exemplo.com" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone *</label>
                  <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="(00) 00000-0000" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Empresa</label>
                  <input type="text" name="empresa" value={formData.empresa} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="Nome da empresa" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">CNPJ</label>
                  <input type="text" name="cnpj" value={formData.cnpj} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="00.000.000/0000-00" />
                </div>
              </div>
            </div>
            <div>
              <h4 className="text-lg font-semibold mb-3 text-gray-700 dark:text-gray-300">Endereço</h4>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Endereço Completo</label>
                  <input type="text" name="endereco" value={formData.endereco} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="Rua, número, bairro" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Estado</label>
                  <select name="estado" value={formData.estado} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white">
                    <option value="">Selecione...</option>
                    {estados.map(uf => (<option key={uf} value={uf}>{uf}</option>))}
                  </select>
                </div>
                <div className="md:col-span-3">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Cidade</label>
                  <input type="text" name="cidade" value={formData.cidade} onChange={handleChange} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="Ex: São Paulo" />
                </div>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
              <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white" placeholder="Informações adicionais sobre o cliente..." />
            </div>
            <div className="flex justify-end space-x-4 pt-4 border-t dark:border-gray-600">
              <button type="button" onClick={() => { setMostrarFormulario(false); setClienteEditando(null); }} disabled={loading} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white disabled:opacity-50">Cancelar</button>
              <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Salvando...' : (clienteEditando ? 'Atualizar' : 'Cadastrar')}</button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 sm:p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-xl sm:text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>👤 Gerenciar Clientes (Já compraram)</h3>

        {loadingLista ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando clientes...</div>
        ) : !Array.isArray(clientes) || clientes.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="mb-4">Nenhum cliente cadastrado.</p>
            <button onClick={handleNovo} className="px-6 py-2 rounded-lg text-white hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {(Array.isArray(clientes) ? clientes : []).map((cliente: any) => (
              <div key={cliente.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-lg text-gray-900 dark:text-white">{cliente.nome}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.empresa || ''} {cliente.cnpj || cliente.cpf_cnpj ? `• CNPJ: ${cliente.cnpj || cliente.cpf_cnpj}` : ''}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{cliente.email} • {cliente.telefone}</p>
                  {(cliente.cidade || cliente.estado) && <p className="text-sm text-gray-600 dark:text-gray-400">{[cliente.cidade, cliente.estado].filter(Boolean).join('/')}</p>}
                </div>
                <div className="flex flex-wrap items-center gap-2 flex-shrink-0">
                  <button onClick={() => handleEditar(cliente)} className="px-4 py-2 text-sm text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>✏️ Editar</button>
                  <button onClick={() => handleExcluir(cliente.id, cliente.nome)} className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 min-h-[40px]">🗑️ Excluir</button>
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button onClick={onClose} className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]">Fechar</button>
          <button onClick={handleNovo} className="px-6 py-2 text-white rounded-lg hover:opacity-90 min-h-[40px]" style={{ backgroundColor: loja.cor_primaria }}>+ Novo Cliente</button>
        </div>
      </div>
    </div>
  );
}

// Modal Novo Vendedor
function ModalNovoVendedor({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cpf: '',
    meta_mensal: '',
    comissao: '',
    data_admissao: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      alert(`✅ Vendedor cadastrado com sucesso!\n\nNome: ${formData.nome}\nMeta Mensal: R$ ${formData.meta_mensal}\nComissão: ${formData.comissao}%`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar vendedor');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>💼 Novo Vendedor</h3>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Pessoais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Completo *</label>
                <input type="text" name="nome" value={formData.nome} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Ex: Carlos Silva" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
                <input type="email" name="email" value={formData.email} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="email@exemplo.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                <input type="tel" name="telefone" value={formData.telefone} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="(00) 00000-0000" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">CPF *</label>
                <input type="text" name="cpf" value={formData.cpf} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="000.000.000-00" />
              </div>
            </div>
          </div>
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Dados Profissionais</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Meta Mensal (R$) *</label>
                <input type="number" name="meta_mensal" value={formData.meta_mensal} onChange={handleChange} required min="0" step="0.01" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="10000.00" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Comissão (%) *</label>
                <input type="number" name="comissao" value={formData.comissao} onChange={handleChange} required min="0" max="100" step="0.1" className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="5.0" />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Data de Admissão *</label>
                <input type="date" name="data_admissao" value={formData.data_admissao} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" />
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
            <textarea name="observacoes" value={formData.observacoes} onChange={handleChange} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" placeholder="Informações adicionais sobre o vendedor..." />
          </div>
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
            <button type="submit" disabled={loading} className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" style={{ backgroundColor: loja.cor_primaria }}>{loading ? 'Cadastrando...' : 'Cadastrar Vendedor'}</button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal Novo Produto/Serviço
function ModalNovoProduto({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const [formData, setFormData] = useState({
    tipo: '',
    nome: '',
    descricao: '',
    categoria: '',
    preco: '',
    custo: '',
    estoque: '',
    codigo: '',
    duracao: '',
    observacoes: ''
  });
  const [loading, setLoading] = useState(false);

  const categoriasProduto = ['Software', 'Hardware', 'Licença', 'Material', 'Equipamento', 'Outro'];
  const categoriasServico = ['Consultoria', 'Treinamento', 'Suporte', 'Implementação', 'Manutenção', 'Desenvolvimento', 'Outro'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: value,
      // Limpar categoria ao mudar tipo
      ...(name === 'tipo' ? { categoria: '' } : {})
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      const tipoTexto = formData.tipo === 'produto' ? 'Produto' : 'Serviço';
      alert(`✅ ${tipoTexto} cadastrado com sucesso!\n\nNome: ${formData.nome}\nPreço: R$ ${formData.preco}\nCategoria: ${formData.categoria}${formData.tipo === 'servico' && formData.duracao ? `\nDuração: ${formData.duracao}` : ''}`);
      onClose();
    } catch (error) {
      alert('❌ Erro ao cadastrar');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h3 className="text-2xl font-bold mb-6" style={{ color: loja.cor_primaria }}>📦 Novo Produto/Serviço</h3>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <h4 className="text-lg font-semibold mb-3 text-gray-700">Tipo</h4>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, tipo: 'produto', categoria: '' }))}
                className={`p-4 rounded-lg border-2 transition-all ${
                  formData.tipo === 'produto'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">📦</div>
                <div className="font-semibold">Produto</div>
                <div className="text-xs text-gray-600">Item físico ou digital</div>
              </button>
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, tipo: 'servico', categoria: '', estoque: '' }))}
                className={`p-4 rounded-lg border-2 transition-all ${
                  formData.tipo === 'servico'
                    ? 'border-green-500 bg-green-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <div className="text-3xl mb-2">🛠️</div>
                <div className="font-semibold">Serviço</div>
                <div className="text-xs text-gray-600">Consultoria, suporte, etc.</div>
              </button>
            </div>
          </div>

          {formData.tipo && (
            <>
              <div>
                <h4 className="text-lg font-semibold mb-3 text-gray-700">
                  Informações do {formData.tipo === 'produto' ? 'Produto' : 'Serviço'}
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nome do {formData.tipo === 'produto' ? 'Produto' : 'Serviço'} *
                    </label>
                    <input 
                      type="text" 
                      name="nome" 
                      value={formData.nome} 
                      onChange={handleChange} 
                      required 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder={formData.tipo === 'produto' ? 'Ex: Sistema CRM Premium' : 'Ex: Consultoria em Vendas'} 
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Descrição</label>
                    <textarea 
                      name="descricao" 
                      value={formData.descricao} 
                      onChange={handleChange} 
                      rows={3} 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder={formData.tipo === 'produto' ? 'Descreva o produto...' : 'Descreva o serviço...'} 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Categoria *</label>
                    <select name="categoria" value={formData.categoria} onChange={handleChange} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0">
                      <option value="">Selecione...</option>
                      {(formData.tipo === 'produto' ? categoriasProduto : categoriasServico).map(cat => (
                        <option key={cat} value={cat}>{cat}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Código/SKU</label>
                    <input 
                      type="text" 
                      name="codigo" 
                      value={formData.codigo} 
                      onChange={handleChange} 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="Ex: PROD-001" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Preço de Venda (R$) *</label>
                    <input 
                      type="number" 
                      name="preco" 
                      value={formData.preco} 
                      onChange={handleChange} 
                      required 
                      min="0" 
                      step="0.01" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="1000.00" 
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Custo (R$)</label>
                    <input 
                      type="number" 
                      name="custo" 
                      value={formData.custo} 
                      onChange={handleChange} 
                      min="0" 
                      step="0.01" 
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                      placeholder="500.00" 
                    />
                  </div>
                  
                  {formData.tipo === 'produto' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Estoque Inicial</label>
                      <input 
                        type="number" 
                        name="estoque" 
                        value={formData.estoque} 
                        onChange={handleChange} 
                        min="0" 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                        placeholder="0" 
                      />
                    </div>
                  )}
                  
                  {formData.tipo === 'servico' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Duração Estimada</label>
                      <input 
                        type="text" 
                        name="duracao" 
                        value={formData.duracao} 
                        onChange={handleChange} 
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                        placeholder="Ex: 2 horas, 1 dia, 1 semana" 
                      />
                    </div>
                  )}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Observações</label>
                <textarea 
                  name="observacoes" 
                  value={formData.observacoes} 
                  onChange={handleChange} 
                  rows={3} 
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-offset-0" 
                  placeholder="Informações adicionais..." 
                />
              </div>
            </>
          )}
          
          <div className="flex justify-end space-x-4 pt-4 border-t">
            <button type="button" onClick={onClose} disabled={loading} className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50">Cancelar</button>
            <button 
              type="submit" 
              disabled={loading || !formData.tipo} 
              className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50" 
              style={{ backgroundColor: loja.cor_primaria }}
            >
              {loading ? 'Cadastrando...' : `Cadastrar ${formData.tipo === 'produto' ? 'Produto' : formData.tipo === 'servico' ? 'Serviço' : ''}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// Modal Pipeline de Vendas (Modal Normal - Não Tela Cheia)
function ModalPipeline({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const etapas = [
    { nome: 'Novo Lead', quantidade: 0, valor: 0, cor: '#3B82F6' },
    { nome: 'Contato Inicial', quantidade: 0, valor: 0, cor: '#8B5CF6' },
    { nome: 'Qualificado', quantidade: 0, valor: 0, cor: '#EC4899' },
    { nome: 'Proposta Enviada', quantidade: 0, valor: 0, cor: '#F59E0B' },
    { nome: 'Negociação', quantidade: 0, valor: 0, cor: '#10B981' },
    { nome: 'Fechado', quantidade: 0, valor: 0, cor: '#059669' }
  ];

  const totalLeads = etapas.reduce((acc, e) => acc + e.quantidade, 0);
  const totalValor = etapas.reduce((acc, e) => acc + e.valor, 0);
  const taxaConversao = totalLeads > 0 ? ((etapas[etapas.length - 1].quantidade / etapas[0].quantidade) * 100).toFixed(1) : '0.0';

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 z-10 text-white p-4 rounded-t-lg flex items-center justify-between" style={{ backgroundColor: loja.cor_primaria }}>
          <h3 className="text-xl font-bold">🔄 Pipeline de Vendas</h3>
          <button onClick={onClose} className="p-1 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Conteúdo */}
        <div className="p-6">
          {/* Cards de Resumo */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Total de Leads</p>
              <p className="text-2xl font-bold mt-1">{totalLeads}</p>
              <p className="text-xs mt-1 opacity-75">no funil de vendas</p>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-green-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Valor Total</p>
              <p className="text-2xl font-bold mt-1">R$ {totalValor.toLocaleString('pt-BR')}</p>
              <p className="text-xs mt-1 opacity-75">em negociações</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 p-4 rounded-lg shadow text-white">
              <p className="text-xs font-medium opacity-90">Taxa de Conversão</p>
              <p className="text-2xl font-bold mt-1">{taxaConversao}%</p>
              <p className="text-xs mt-1 opacity-75">do início ao fim</p>
            </div>
          </div>

          {/* Funil Visual Compacto */}
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <h4 className="text-lg font-bold mb-4 text-gray-800">Funil de Vendas</h4>
            <div className="space-y-2">
              {etapas.map((etapa, index) => {
                const larguraBase = 100;
                const reducao = (index * 12);
                const largura = larguraBase - reducao;
                
                return (
                  <div key={etapa.nome} className="flex items-center space-x-3">
                    <div className="w-32 text-right flex-shrink-0">
                      <p className="text-sm font-semibold text-gray-700">{etapa.nome}</p>
                    </div>
                    <div className="flex-1">
                      <div 
                        className="relative rounded-lg p-3 transition-all hover:scale-105 cursor-pointer shadow"
                        style={{ 
                          backgroundColor: etapa.cor,
                          width: `${largura}%`,
                          marginLeft: `${reducao / 2}%`
                        }}
                      >
                        <div className="flex items-center justify-between text-white">
                          <div>
                            <p className="font-bold text-sm">{etapa.quantidade} leads</p>
                            <p className="text-xs opacity-90">R$ {etapa.valor.toLocaleString('pt-BR')}</p>
                          </div>
                          <div className="text-xl">
                            {index === 0 && '🎯'}
                            {index === 1 && '📞'}
                            {index === 2 && '✅'}
                            {index === 3 && '📄'}
                            {index === 4 && '🤝'}
                            {index === 5 && '🎉'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Tabela Compacta */}
          <div className="bg-white rounded-lg border">
            <h4 className="text-lg font-bold p-4 border-b text-gray-800">Detalhamento por Etapa</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Etapa</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Leads</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Valor Total</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Ticket Médio</th>
                    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-700 uppercase">Conversão</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {etapas.map((etapa, index) => {
                    const ticketMedio = etapa.quantidade > 0 ? etapa.valor / etapa.quantidade : 0;
                    const conversao = index > 0 && etapas[index - 1].quantidade > 0 
                      ? ((etapa.quantidade / etapas[index - 1].quantidade) * 100).toFixed(1) 
                      : '-';
                    
                    return (
                      <tr key={etapa.nome} className="hover:bg-gray-50">
                        <td className="px-4 py-2 whitespace-nowrap">
                          <div className="flex items-center">
                            <div className="w-3 h-3 rounded-full mr-2" style={{ backgroundColor: etapa.cor }}></div>
                            <span className="font-semibold text-gray-900 text-sm">{etapa.nome}</span>
                          </div>
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-gray-700 text-sm font-medium">{etapa.quantidade}</td>
                        <td className="px-4 py-2 whitespace-nowrap font-bold text-sm" style={{ color: etapa.cor }}>
                          R$ {etapa.valor.toLocaleString('pt-BR')}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap text-gray-700 text-sm">
                          R$ {ticketMedio.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap">
                          {conversao !== '-' ? (
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              parseFloat(conversao) >= 70 ? 'bg-green-100 text-green-800' :
                              parseFloat(conversao) >= 50 ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {conversao}%
                            </span>
                          ) : (
                            <span className="text-gray-400 text-sm">-</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Botão Fechar */}
          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Fechar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}


// Modal Gerenciar Funcionários (Vendedores)
function ModalFuncionarios({ loja, onClose }: { loja: LojaInfo; onClose: () => void }) {
  const toast = useToast();
  const [funcionarios, setFuncionarios] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingFuncionario, setEditingFuncionario] = useState<any>(null);
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cargo: '',
    meta_mensal: ''
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadFuncionarios();
  }, []);

  const loadFuncionarios = async () => {
    try {
      const lojaId = sessionStorage.getItem('current_loja_id') || String(loja.id);
      console.log('🔍 [loadFuncionarios] Loja ID:', lojaId);
      console.log('🔍 [loadFuncionarios] Loja object:', loja);
      
      if (!lojaId) {
        console.error('❌ [loadFuncionarios] Nenhuma loja_id disponível!');
        setFuncionarios([]);
        setLoading(false);
        return;
      }
      
      const response = await clinicaApiClient.get('/crm/vendedores/', {
        headers: {
          'X-Loja-ID': lojaId
        }
      });
      const data = response.data;
      const list = Array.isArray(data) ? data : (data?.results ?? []);
      console.log('✅ [loadFuncionarios] Funcionários carregados:', list.length);
      setFuncionarios(list);
    } catch (error) {
      console.error('❌ [loadFuncionarios] Erro ao carregar vendedores:', error);
      setFuncionarios([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (funcionario: any) => {
    setEditingFuncionario(funcionario);
    setFormData({
      nome: funcionario.nome || '',
      email: funcionario.email || '',
      telefone: funcionario.telefone || '',
      cargo: funcionario.cargo || '',
      meta_mensal: funcionario.meta_mensal?.toString() || '10000'
    });
    setShowForm(true);
  };

  const handleDelete = async (funcionario: any) => {
    if (!confirm(`Tem certeza que deseja excluir o funcionário ${funcionario.nome}?`)) return;
    
    try {
      await clinicaApiClient.delete(`/crm/vendedores/${funcionario.id}/`);
      toast.success('Funcionário excluído com sucesso!');
      loadFuncionarios();
    } catch (error: any) {
      console.error('Erro ao excluir funcionário:', error);
      toast.error(error.response?.data?.detail || 'Erro ao excluir funcionário');
    }
  };

  const resetForm = () => {
    setFormData({
      nome: '',
      email: '',
      telefone: '',
      cargo: '',
      meta_mensal: '10000'
    });
    setEditingFuncionario(null);
    setShowForm(false);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      if (editingFuncionario) {
        await clinicaApiClient.put(`/crm/vendedores/${editingFuncionario.id}/`, formData);
        toast.success('Funcionário atualizado com sucesso!');
      } else {
        await clinicaApiClient.post('/crm/vendedores/', formData);
        toast.success('Funcionário cadastrado com sucesso!');
      }
      loadFuncionarios();
      resetForm();
    } catch (error: any) {
      console.error('Erro ao salvar funcionário:', error);
      toast.error(error.response?.data?.detail || 'Erro ao salvar funcionário');
    } finally {
      setSubmitting(false);
    }
  };

  if (showForm) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
          <h3 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
            👥 {editingFuncionario ? 'Editar Funcionário' : 'Novo Funcionário'}
          </h3>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome Completo *
                </label>
                <input
                  type="text"
                  name="nome"
                  value={formData.nome}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white"
                  placeholder="Ex: João Silva"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email *
                </label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white"
                  placeholder="email@exemplo.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Telefone *
                </label>
                <input
                  type="tel"
                  name="telefone"
                  value={formData.telefone}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white"
                  placeholder="(00) 00000-0000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Função/Cargo *
                </label>
                <select
                  name="cargo"
                  value={formData.cargo}
                  onChange={handleChange}
                  required
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white"
                >
                  <option value="">Selecione a função...</option>
                  <option value="Vendedor">Vendedor</option>
                  <option value="Vendedor Sênior">Vendedor Sênior</option>
                  <option value="Gerente de Vendas">Gerente de Vendas</option>
                  <option value="Coordenador de Vendas">Coordenador de Vendas</option>
                  <option value="Supervisor de Vendas">Supervisor de Vendas</option>
                  <option value="Consultor de Vendas">Consultor de Vendas</option>
                  <option value="Representante Comercial">Representante Comercial</option>
                  <option value="Executivo de Contas">Executivo de Contas</option>
                  <option value="Assistente Comercial">Assistente Comercial</option>
                  <option value="Outro">Outro</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Meta Mensal (R$) *
                </label>
                <input
                  type="number"
                  name="meta_mensal"
                  value={formData.meta_mensal}
                  onChange={handleChange}
                  required
                  min="0"
                  step="0.01"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-offset-0 dark:bg-gray-700 dark:text-white"
                  placeholder="10000.00"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-4 pt-4 border-t dark:border-gray-600">
              <button
                type="button"
                onClick={resetForm}
                disabled={submitting}
                className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 dark:text-white disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
                style={{ backgroundColor: loja.cor_primaria }}
              >
                {submitting ? 'Salvando...' : (editingFuncionario ? 'Atualizar' : 'Cadastrar')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-4xl w-full max-h-[80vh] overflow-y-auto shadow-xl">
        <h3 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white" style={{ color: loja.cor_primaria }}>
          👥 Gerenciar Funcionários
        </h3>
        
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          💡 O administrador da loja aparece automaticamente na lista de funcionários
        </p>
        
        {loading ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">Carregando funcionários...</div>
        ) : !Array.isArray(funcionarios) || funcionarios.length === 0 ? (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            <p className="text-lg mb-2">Nenhum funcionário cadastrado</p>
            <p className="text-sm mb-4">Cadastre sua equipe de vendas</p>
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-3 rounded-md text-white hover:opacity-90 min-h-[44px]"
              style={{ backgroundColor: loja.cor_primaria }}
            >
              + Cadastrar Funcionário
            </button>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            {(Array.isArray(funcionarios) ? funcionarios : []).map((func: any) => (
              <div key={func.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 border dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 flex-wrap gap-2">
                    <p className="font-semibold text-lg text-gray-900 dark:text-white">{func.nome}</p>
                    {func.is_admin && (
                      <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-semibold rounded-full">
                        👤 Administrador
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{func.cargo}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{func.email} • {func.telefone}</p>
                  <p className="text-sm font-semibold mt-1" style={{ color: loja.cor_primaria }}>
                    Meta Mensal: R$ {parseFloat(func.meta_mensal || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2 flex-shrink-0">
                  <button
                    onClick={() => handleEdit(func)}
                    className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md hover:bg-blue-600 min-h-[40px]"
                  >
                    ✏️ Editar
                  </button>
                  {!func.is_admin && (
                    <button
                      onClick={() => handleDelete(func)}
                      className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 min-h-[40px]"
                    >
                      🗑️ Excluir
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end gap-3 pt-4 border-t dark:border-gray-600">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-900 dark:text-white min-h-[40px]"
          >
            Fechar
          </button>
          <button
            onClick={() => setShowForm(true)}
            className="px-6 py-2 text-white rounded-md hover:opacity-90 min-h-[40px]"
            style={{ backgroundColor: loja.cor_primaria }}
          >
            + Novo Funcionário
          </button>
        </div>
      </div>
    </div>
  );
}
