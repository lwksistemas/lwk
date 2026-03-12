'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { DollarSign, Plus, X } from 'lucide-react';
import LeadsTable, { type Lead } from '@/components/crm-vendas/LeadsTable';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

const ETAPAS_OPORTUNIDADE = [
  { value: 'prospecting', label: 'Prospecção' },
  { value: 'qualification', label: 'Qualificação' },
  { value: 'proposal', label: 'Proposta' },
  { value: 'negotiation', label: 'Negociação' },
  { value: 'closed_won', label: 'Fechado ganho (venda)' },
  { value: 'closed_lost', label: 'Fechado perdido' },
];

const ORIGEM_OPCOES = [
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'facebook', label: 'Facebook' },
  { value: 'instagram', label: 'Instagram' },
  { value: 'site', label: 'Site' },
  { value: 'indicacao', label: 'Indicação' },
  { value: 'outro', label: 'Outro' },
];

const STATUS_OPCOES = [
  { value: 'novo', label: 'Novo' },
  { value: 'contato', label: 'Contato feito' },
  { value: 'qualificado', label: 'Qualificado' },
  { value: 'perdido', label: 'Perdido' },
];

function loadLeads(setLeads: (l: Lead[]) => void, setError: (e: string | null) => void) {
  apiClient
    .get<Lead[] | { results: Lead[] }>('/crm-vendas/leads/')
    .then((res) => {
      const data = res.data;
      setLeads(Array.isArray(data) ? data : (data as { results: Lead[] }).results || []);
      setError(null);
    })
    .catch((err) => {
      setError(err.response?.data?.detail || 'Erro ao carregar leads.');
    });
}

export default function CrmVendasLeadsPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const { colunasLeadsVisiveis } = useCRMConfig();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalAberto, setModalAberto] = useState(false);
  const [leadVer, setLeadVer] = useState<Lead | null>(null);
  const [leadEditar, setLeadEditar] = useState<Lead | null>(null);
  const [leadExcluir, setLeadExcluir] = useState<Lead | null>(null);
  const [leadMudarStatus, setLeadMudarStatus] = useState<Lead | null>(null);
  const [leadCriarOportunidade, setLeadCriarOportunidade] = useState<Lead | null>(null);
  const [novoStatus, setNovoStatus] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [excluindo, setExcluindo] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [form, setForm] = useState({
    nome: '',
    empresa: '',
    email: '',
    telefone: '',
    origem: 'site',
    status: 'novo',
  });
  const [formOportunidade, setFormOportunidade] = useState({
    titulo: '',
    valor: '',
    etapa: 'prospecting',
  });

  useEffect(() => {
    apiClient
      .get<Lead[] | { results: Lead[] }>('/crm-vendas/leads/')
      .then((res) => {
        const data = res.data;
        setLeads(Array.isArray(data) ? data : (data as { results: Lead[] }).results || []);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Erro ao carregar leads.');
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (searchParams.get('novo') === '1') {
      setModalAberto(true);
      router.replace(`/loja/${slug}/crm-vendas/leads`, { scroll: false });
    }
  }, [searchParams, router, slug]);

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Leads</h1>
        <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
          {error}
        </div>
      </div>
    );
  }

  const handleCriarLead = (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setEnviando(true);
    apiClient
      .post('/crm-vendas/leads/', {
        nome: form.nome.trim(),
        empresa: form.empresa.trim() || undefined,
        email: form.email.trim() || undefined,
        telefone: form.telefone.trim() || undefined,
        origem: form.origem,
        status: form.status,
      })
      .then(() => {
        setModalAberto(false);
        setForm({ nome: '', empresa: '', email: '', telefone: '', origem: 'site', status: 'novo' });
        loadLeads(setLeads, setError);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.nome?.[0] || err.response?.data?.detail || 'Erro ao salvar lead.'
        );
      })
      .finally(() => setEnviando(false));
  };

  const handleVerLead = (lead: Lead) => setLeadVer(lead);

  const handleEditarLead = (lead: Lead) => {
    setLeadEditar(lead);
    setForm({
      nome: lead.nome,
      empresa: lead.empresa || '',
      email: lead.email || '',
      telefone: lead.telefone || '',
      origem: lead.origem,
      status: lead.status,
    });
    setFormErro(null);
  };

  const handleSalvarEdicao = (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadEditar) return;
    setFormErro(null);
    if (!form.nome.trim()) {
      setFormErro('Informe o nome.');
      return;
    }
    setEnviando(true);
    apiClient
      .patch(`/crm-vendas/leads/${leadEditar.id}/`, {
        nome: form.nome.trim(),
        empresa: form.empresa.trim() || undefined,
        email: form.email.trim() || undefined,
        telefone: form.telefone.trim() || undefined,
        origem: form.origem,
        status: form.status,
      })
      .then(() => {
        setLeadEditar(null);
        loadLeads(setLeads, setError);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.nome?.[0] || err.response?.data?.detail || 'Erro ao salvar.'
        );
      })
      .finally(() => setEnviando(false));
  };

  const handleExcluirLead = (lead: Lead) => setLeadExcluir(lead);

  const confirmarExcluir = () => {
    if (!leadExcluir) return;
    setExcluindo(true);
    apiClient
      .delete(`/crm-vendas/leads/${leadExcluir.id}/`)
      .then(() => {
        setLeadExcluir(null);
        loadLeads(setLeads, setError);
      })
      .catch((err) => {
        setError(err.response?.data?.detail || 'Erro ao excluir lead.');
      })
      .finally(() => setExcluindo(false));
  };

  const handleMudarStatus = (lead: Lead) => {
    setLeadMudarStatus(lead);
    setNovoStatus(lead.status);
  };

  const salvarNovoStatus = () => {
    if (!leadMudarStatus || novoStatus === leadMudarStatus.status) {
      setLeadMudarStatus(null);
      return;
    }
    setFormErro(null);
    setEnviando(true);
    apiClient
      .patch(`/crm-vendas/leads/${leadMudarStatus.id}/`, { status: novoStatus })
      .then(() => {
        setLeadMudarStatus(null);
        loadLeads(setLeads, setError);
      })
      .catch((err) => {
        setFormErro(err.response?.data?.detail || 'Erro ao atualizar status.');
      })
      .finally(() => setEnviando(false));
  };

  const handleCriarOportunidade = (lead: Lead) => {
    setLeadCriarOportunidade(lead);
    setFormOportunidade({
      titulo: `Negócio - ${lead.nome}`,
      valor: lead.valor_estimado ? String(lead.valor_estimado) : '0',
      etapa: 'prospecting',
    });
    setFormErro(null);
  };

  const submitCriarOportunidade = (e: React.FormEvent) => {
    e.preventDefault();
    if (!leadCriarOportunidade) return;
    setFormErro(null);
    const valor = parseFloat(formOportunidade.valor) || 0;
    if (!formOportunidade.titulo.trim()) {
      setFormErro('Informe o título da oportunidade.');
      return;
    }
    setEnviando(true);
    apiClient
      .post('/crm-vendas/oportunidades/', {
        lead: leadCriarOportunidade.id,
        titulo: formOportunidade.titulo.trim(),
        valor,
        etapa: formOportunidade.etapa,
      })
      .then(() => {
        setLeadCriarOportunidade(null);
        loadLeads(setLeads, setError);
        router.push(`/loja/${slug}/crm-vendas/pipeline`);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.titulo?.[0] ||
            err.response?.data?.valor?.[0] ||
            err.response?.data?.detail ||
            'Erro ao criar oportunidade.'
        );
      })
      .finally(() => setEnviando(false));
  };

  const origemLabel = (value: string) => ORIGEM_OPCOES.find((o) => o.value === value)?.label ?? value;
  const statusLabel = (value: string) => STATUS_OPCOES.find((o) => o.value === value)?.label ?? value;
  const formatarData = (s: string) => {
    if (!s) return '–';
    try {
      const d = new Date(s);
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return s;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Leads</h1>
        <button
          type="button"
          onClick={() => setModalAberto(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition text-sm inline-flex items-center gap-2"
        >
          <Plus size={18} />
          Novo Lead
        </button>
      </div>

      <LeadsTable
        leads={leads}
        loading={loading}
        colunas={colunasLeadsVisiveis()}
        onVerLead={handleVerLead}
        onEditarLead={handleEditarLead}
        onExcluirLead={handleExcluirLead}
        onMudarStatus={handleMudarStatus}
      />

      {leadVer && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => setLeadVer(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Detalhes do lead</h2>
              <button
                type="button"
                onClick={() => setLeadVer(null)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center gap-3 pb-3 border-b border-gray-100 dark:border-gray-700">
                <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center text-blue-600 dark:text-blue-300 font-semibold text-lg">
                  {leadVer.nome.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">{leadVer.nome}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{leadVer.empresa || 'Sem empresa'}</p>
                </div>
              </div>
              <div className="flex gap-2 pb-3 border-b border-gray-100 dark:border-gray-700">
                <button
                  type="button"
                  onClick={() => handleCriarOportunidade(leadVer)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700"
                >
                  <DollarSign size={16} />
                  Criar oportunidade (venda)
                </button>
                <Link
                  href={`/loja/${slug}/crm-vendas/pipeline`}
                  className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Ver pipeline
                </Link>
              </div>
              <dl className="space-y-3 text-sm">
                <div>
                  <dt className="text-gray-500 dark:text-gray-400 font-medium">Email</dt>
                  <dd className="text-gray-900 dark:text-white mt-0.5">{leadVer.email || '–'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400 font-medium">Telefone</dt>
                  <dd className="text-gray-900 dark:text-white mt-0.5">{leadVer.telefone || '–'}</dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400 font-medium">Origem</dt>
                  <dd className="mt-0.5">
                    <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-700 dark:bg-purple-500/20 dark:text-purple-300">
                      {origemLabel(leadVer.origem)}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400 font-medium">Status</dt>
                  <dd className="mt-0.5">
                    <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-300">
                      {statusLabel(leadVer.status)}
                    </span>
                  </dd>
                </div>
                {leadVer.valor_estimado != null && leadVer.valor_estimado !== '' && (
                  <div>
                    <dt className="text-gray-500 dark:text-gray-400 font-medium">Valor estimado</dt>
                    <dd className="text-gray-900 dark:text-white mt-0.5">
                      {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(leadVer.valor_estimado))}
                    </dd>
                  </div>
                )}
                <div>
                  <dt className="text-gray-500 dark:text-gray-400 font-medium">Cadastrado em</dt>
                  <dd className="text-gray-900 dark:text-white mt-0.5">{formatarData(leadVer.created_at)}</dd>
                </div>
              </dl>
              <div className="pt-2">
                <button
                  type="button"
                  onClick={() => setLeadVer(null)}
                  className="w-full px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 font-medium"
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {leadEditar && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !enviando && setLeadEditar(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Editar lead</h2>
              <button
                type="button"
                onClick={() => !enviando && setLeadEditar(null)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleSalvarEdicao} className="p-4 space-y-4">
              {formErro && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  {formErro}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Nome *</label>
                <input
                  type="text"
                  value={form.nome}
                  onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Nome do lead"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Empresa</label>
                <input
                  type="text"
                  value={form.empresa}
                  onChange={(e) => setForm((f) => ({ ...f, empresa: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Empresa"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="email@exemplo.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Telefone</label>
                <input
                  type="text"
                  value={form.telefone}
                  onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Origem</label>
                <select
                  value={form.origem}
                  onChange={(e) => setForm((f) => ({ ...f, origem: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {ORIGEM_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Status</label>
                <select
                  value={form.status}
                  onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {STATUS_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => !enviando && setLeadEditar(null)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {leadExcluir && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !excluindo && setLeadExcluir(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Excluir lead?</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Tem certeza que deseja excluir <strong>{leadExcluir.nome}</strong>? Esta ação não pode ser desfeita.
            </p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => !excluindo && setLeadExcluir(null)}
                className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmarExcluir}
                disabled={excluindo}
                className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium"
              >
                {excluindo ? 'Excluindo...' : 'Excluir'}
              </button>
            </div>
          </div>
        </div>
      )}

      {leadMudarStatus && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => { if (!enviando) { setLeadMudarStatus(null); setFormErro(null); } }}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-sm p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Mudar status</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{leadMudarStatus.nome}</p>
            {formErro && (
              <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg mb-3">
                {formErro}
              </p>
            )}
            <select
              value={novoStatus}
              onChange={(e) => setNovoStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white mb-4"
            >
              {STATUS_OPCOES.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => !enviando && setLeadMudarStatus(null)}
                className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={salvarNovoStatus}
                disabled={enviando || novoStatus === leadMudarStatus.status}
                className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
              >
                {enviando ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        </div>
      )}

      {leadCriarOportunidade && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !enviando && setLeadCriarOportunidade(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Criar oportunidade (venda)
              </h2>
              <button
                type="button"
                onClick={() => !enviando && setLeadCriarOportunidade(null)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <p className="px-4 pt-2 text-sm text-gray-500 dark:text-gray-400">
              Lead: <strong className="text-gray-800 dark:text-white">{leadCriarOportunidade.nome}</strong>
            </p>
            <form onSubmit={submitCriarOportunidade} className="p-4 space-y-4">
              {formErro && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  {formErro}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título *</label>
                <input
                  type="text"
                  value={formOportunidade.titulo}
                  onChange={(e) => setFormOportunidade((f) => ({ ...f, titulo: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Ex: Venda produto X"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor (R$)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formOportunidade.valor}
                  onChange={(e) => setFormOportunidade((f) => ({ ...f, valor: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Etapa inicial</label>
                <select
                  value={formOportunidade.etapa}
                  onChange={(e) => setFormOportunidade((f) => ({ ...f, etapa: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {ETAPAS_OPORTUNIDADE.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => !enviando && setLeadCriarOportunidade(null)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Criando...' : 'Criar e ir ao pipeline'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {modalAberto && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !enviando && setModalAberto(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Novo Lead</h2>
              <button
                type="button"
                onClick={() => !enviando && setModalAberto(false)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCriarLead} className="p-4 space-y-4">
              {formErro && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  {formErro}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome *
                </label>
                <input
                  type="text"
                  value={form.nome}
                  onChange={(e) => setForm((f) => ({ ...f, nome: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Nome do lead"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Empresa
                </label>
                <input
                  type="text"
                  value={form.empresa}
                  onChange={(e) => setForm((f) => ({ ...f, empresa: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Empresa"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="email@exemplo.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Telefone
                </label>
                <input
                  type="text"
                  value={form.telefone}
                  onChange={(e) => setForm((f) => ({ ...f, telefone: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="(00) 00000-0000"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Origem
                </label>
                <select
                  value={form.origem}
                  onChange={(e) => setForm((f) => ({ ...f, origem: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {ORIGEM_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Status
                </label>
                <select
                  value={form.status}
                  onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {STATUS_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => !enviando && setModalAberto(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviando}
                  className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Salvando...' : 'Salvar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
