'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { DollarSign, LayoutDashboard, Plus, X } from 'lucide-react';
import PipelineBoard, { type Oportunidade } from '@/components/crm-vendas/PipelineBoard';

interface LeadOption {
  id: number;
  nome: string;
}

const ETAPAS_OPCOES = [
  { value: 'prospecting', label: 'Prospecção' },
  { value: 'qualification', label: 'Qualificação' },
  { value: 'proposal', label: 'Proposta' },
  { value: 'negotiation', label: 'Negociação' },
  { value: 'closed_won', label: 'Fechado ganho (venda fechada)' },
  { value: 'closed_lost', label: 'Fechado perdido' },
];

function loadOportunidades(setOportunidades: (o: Oportunidade[]) => void, setError: (e: string | null) => void) {
  apiClient
    .get<Oportunidade[] | { results: Oportunidade[] }>('/crm-vendas/oportunidades/')
    .then((res) => {
      const data = res.data;
      setOportunidades(
        Array.isArray(data)
          ? data
          : (data as { results: Oportunidade[] }).results ?? []
      );
      setError(null);
    })
    .catch((err) => {
      setError(err.response?.data?.detail || 'Erro ao carregar oportunidades.');
    });
}

export default function CrmVendasPipelinePage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [oportunidadeEditar, setOportunidadeEditar] = useState<Oportunidade | null>(null);
  const [etapaSelecionada, setEtapaSelecionada] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [modalCriar, setModalCriar] = useState(false);
  const [leads, setLeads] = useState<LeadOption[]>([]);
  const [formCriar, setFormCriar] = useState({
    lead_id: '',
    titulo: '',
    valor: '0',
    etapa: 'prospecting',
  });

  useEffect(() => {
    apiClient
      .get<Oportunidade[] | { results: Oportunidade[] }>('/crm-vendas/oportunidades/')
      .then((res) => {
        const data = res.data;
        setOportunidades(
          Array.isArray(data)
            ? data
            : (data as { results: Oportunidade[] }).results ?? []
        );
      })
      .catch((err) => {
        setError(
          err.response?.data?.detail || 'Erro ao carregar oportunidades.'
        );
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (searchParams.get('novo') === '1') {
      setModalCriar(true);
      router.replace(`/loja/${slug}/crm-vendas/pipeline`, { scroll: false });
    }
  }, [searchParams, router, slug]);

  useEffect(() => {
    if (!modalCriar) return;
    apiClient
      .get<LeadOption[] | { results: LeadOption[] }>('/crm-vendas/leads/')
      .then((res) => {
        const data = res.data;
        const list = Array.isArray(data) ? data : (data as { results: LeadOption[] }).results ?? [];
        setLeads(list);
        if (list.length > 0 && !formCriar.lead_id) {
          setFormCriar((f) => ({ ...f, lead_id: String(list[0].id) }));
        }
      })
      .catch(() => setLeads([]));
  }, [modalCriar]);

  const handleAbrirCriar = () => {
    setModalCriar(true);
    setFormCriar({ lead_id: '', titulo: '', valor: '0', etapa: 'prospecting' });
    setFormErro(null);
  };

  const handleCriarOportunidade = (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    const leadId = formCriar.lead_id ? parseInt(formCriar.lead_id, 10) : 0;
    if (!leadId) {
      setFormErro('Selecione um lead.');
      return;
    }
    if (!formCriar.titulo.trim()) {
      setFormErro('Informe o título da oportunidade.');
      return;
    }
    const valor = parseFloat(formCriar.valor) || 0;
    setEnviando(true);
    apiClient
      .post('/crm-vendas/oportunidades/', {
        lead: leadId,
        titulo: formCriar.titulo.trim(),
        valor,
        etapa: formCriar.etapa,
      })
      .then(() => {
        setModalCriar(false);
        loadOportunidades(setOportunidades, setError);
      })
      .catch((err) => {
        setFormErro(
          err.response?.data?.titulo?.[0] ||
            err.response?.data?.detail ||
            'Erro ao criar oportunidade.'
        );
      })
      .finally(() => setEnviando(false));
  };

  const handleCardClick = (op: Oportunidade) => {
    setOportunidadeEditar(op);
    setEtapaSelecionada(op.etapa);
    setFormErro(null);
  };

  const handleSalvarEtapa = (e: React.FormEvent) => {
    e.preventDefault();
    if (!oportunidadeEditar) return;
    setFormErro(null);
    setEnviando(true);
    apiClient
      .patch(`/crm-vendas/oportunidades/${oportunidadeEditar.id}/`, { etapa: etapaSelecionada })
      .then(() => {
        setOportunidadeEditar(null);
        loadOportunidades(setOportunidades, setError);
      })
      .catch((err) => {
        setFormErro(err.response?.data?.detail || 'Erro ao atualizar.');
      })
      .finally(() => setEnviando(false));
  };

  if (error) {
    return (
      <div className="rounded-xl bg-red-50 dark:bg-red-900/20 p-4 text-red-700 dark:text-red-300">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-3xl font-semibold text-gray-800 dark:text-white flex items-center gap-2">
          <DollarSign className="w-8 h-8" />
          Pipeline de vendas
        </h1>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={handleAbrirCriar}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 transition text-sm font-medium"
          >
            <Plus size={18} />
            Nova oportunidade
          </button>
          <Link
            href={`/loja/${slug}/crm-vendas/leads`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm font-medium"
          >
            Ver Leads
          </Link>
          <Link
            href={`/loja/${slug}/crm-vendas`}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600 transition text-sm font-medium"
          >
            <LayoutDashboard size={18} />
            Ver Dashboard
          </Link>
        </div>
      </div>
      <div className="bg-white dark:bg-slate-800 rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm p-6 hover:shadow-md hover:border-blue-100 dark:hover:border-slate-600 transition-all">
        <PipelineBoard
          oportunidades={oportunidades}
          loading={loading}
          onCardClick={handleCardClick}
        />
      </div>

      {modalCriar && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !enviando && setModalCriar(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Nova oportunidade
              </h2>
              <button
                type="button"
                onClick={() => !enviando && setModalCriar(false)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <form onSubmit={handleCriarOportunidade} className="p-4 space-y-4">
              {formErro && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  {formErro}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Lead *</label>
                <select
                  value={formCriar.lead_id}
                  onChange={(e) => setFormCriar((f) => ({ ...f, lead_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  required
                >
                  <option value="">Selecione o lead</option>
                  {leads.map((l) => (
                    <option key={l.id} value={l.id}>{l.nome}</option>
                  ))}
                </select>
                {leads.length === 0 && (
                  <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                    Nenhum lead cadastrado. <Link href={`/loja/${slug}/crm-vendas/leads`} className="underline">Cadastre em Leads</Link>.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Título *</label>
                <input
                  type="text"
                  value={formCriar.titulo}
                  onChange={(e) => setFormCriar((f) => ({ ...f, titulo: e.target.value }))}
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
                  value={formCriar.valor}
                  onChange={(e) => setFormCriar((f) => ({ ...f, valor: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="0"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Etapa inicial</label>
                <select
                  value={formCriar.etapa}
                  onChange={(e) => setFormCriar((f) => ({ ...f, etapa: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {ETAPAS_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => !enviando && setModalCriar(false)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviando || leads.length === 0}
                  className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium"
                >
                  {enviando ? 'Criando...' : 'Criar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {oportunidadeEditar && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
          onClick={() => !enviando && setOportunidadeEditar(null)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Editar oportunidade
              </h2>
              <button
                type="button"
                onClick={() => !enviando && setOportunidadeEditar(null)}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
                aria-label="Fechar"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-4">
              <p className="font-medium text-gray-900 dark:text-white">{oportunidadeEditar.titulo}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{oportunidadeEditar.lead_nome}</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-1">
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(String(oportunidadeEditar.valor)))}
              </p>
            </div>
            <form onSubmit={handleSalvarEtapa} className="p-4 pt-0 space-y-4">
              {formErro && (
                <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                  {formErro}
                </p>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Etapa (mudar para &quot;Fechado ganho&quot; = registrar venda)
                </label>
                <select
                  value={etapaSelecionada}
                  onChange={(e) => setEtapaSelecionada(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  {ETAPAS_OPCOES.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => !enviando && setOportunidadeEditar(null)}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={enviando || etapaSelecionada === oportunidadeEditar.etapa}
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
