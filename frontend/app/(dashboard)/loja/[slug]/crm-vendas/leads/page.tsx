'use client';

import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse } from '@/lib/crm-utils';
import { STATUS_LEAD_OPCOES } from '@/constants/crm';
import { Plus } from 'lucide-react';
import LeadsTable, { type Lead } from '@/components/crm-vendas/LeadsTable';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

const ModalLeadVer = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadVer'), { ssr: false });
const ModalLeadForm = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadForm'), { ssr: false });
const ModalLeadExcluir = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadExcluir'), { ssr: false });
const ModalLeadMudarStatus = dynamic(() => import('@/components/crm-vendas/modals/ModalLeadMudarStatus'), { ssr: false });
const ModalCriarOportunidade = dynamic(() => import('@/components/crm-vendas/modals/ModalCriarOportunidade'), { ssr: false });

function loadLeads(setLeads: (l: Lead[]) => void, setError: (e: string | null) => void) {
  const timestamp = new Date().getTime();
  apiClient
    .get<Lead[] | { results: Lead[] }>(`/crm-vendas/leads/?_t=${timestamp}`)
    .then((res) => {
      setLeads(normalizeListResponse(res.data));
      setError(null);
    })
    .catch((err) => {
      setError(err.response?.data?.detail || 'Erro ao carregar leads.');
    });
}

function formatarData(s: string) {
  if (!s) return '–';
  try {
    const d = new Date(s);
    return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return s;
  }
}

export default function CrmVendasLeadsPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const { colunasLeadsVisiveis, origensAtivas } = useCRMConfig();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
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
    cpf_cnpj: '',
    email: '',
    telefone: '',
    origem: 'site',
    status: 'novo',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
  });
  const [formOportunidade, setFormOportunidade] = useState({
    titulo: '',
    valor: '',
    etapa: 'prospecting',
  });

  useEffect(() => {
    const timestamp = new Date().getTime();
    apiClient
      .get<Lead[] | { results: Lead[] }>(`/crm-vendas/leads/?_t=${timestamp}`)
      .then((res) => setLeads(normalizeListResponse(res.data)))
      .catch((err) => setError(err.response?.data?.detail || 'Erro ao carregar leads.'))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (searchParams.get('novo') === '1') {
      router.replace(`/loja/${slug}/crm-vendas/leads/novo`, { scroll: false });
    }
  }, [searchParams, router, slug]);

  // Abrir modal de visualização quando ?ver=ID (ex.: vindo da busca global)
  useEffect(() => {
    const verId = searchParams.get('ver');
    if (!verId) return;
    const id = parseInt(verId, 10);
    if (isNaN(id)) return;
    const found = leads.find((l) => l.id === id);
    if (found) {
      setLeadVer(found);
      router.replace(`/loja/${slug}/crm-vendas/leads`, { scroll: false });
    } else if (!loading) {
      apiClient
        .get<Lead>(`/crm-vendas/leads/${id}/`)
        .then((res) => {
          setLeadVer(res.data);
          router.replace(`/loja/${slug}/crm-vendas/leads`, { scroll: false });
        })
        .catch(() => {});
    }
  }, [searchParams.get('ver'), leads, loading, router, slug]);

  const origemLabel = (value: string) => origensAtivas().find((o) => o.key === value)?.label ?? value;
  const statusLabel = (value: string) => STATUS_LEAD_OPCOES.find((o) => o.value === value)?.label ?? value;

  const handleEditarLead = (lead: Lead) => {
    setLeadEditar(lead);
    setForm({
      nome: lead.nome,
      empresa: lead.empresa || '',
      cpf_cnpj: lead.cpf_cnpj || '',
      email: lead.email || '',
      telefone: lead.telefone || '',
      origem: lead.origem,
      status: lead.status,
      cep: lead.cep || '',
      logradouro: lead.logradouro || '',
      numero: lead.numero || '',
      complemento: lead.complemento || '',
      bairro: lead.bairro || '',
      cidade: lead.cidade || '',
      uf: lead.uf || '',
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
        cpf_cnpj: form.cpf_cnpj.trim() || undefined,
        email: form.email.trim() || undefined,
        telefone: form.telefone.trim() || undefined,
        origem: form.origem,
        status: form.status,
        cep: form.cep.trim() || undefined,
        logradouro: form.logradouro.trim() || undefined,
        numero: form.numero.trim() || undefined,
        complemento: form.complemento.trim() || undefined,
        bairro: form.bairro.trim() || undefined,
        cidade: form.cidade.trim() || undefined,
        uf: form.uf.trim().toUpperCase() || undefined,
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
    const payload: Record<string, unknown> = {
      lead: leadCriarOportunidade.id,
      titulo: formOportunidade.titulo.trim(),
      valor,
      etapa: formOportunidade.etapa,
    };
    const vendedorId = authService.getVendedorId();
    if (vendedorId) payload.vendedor = vendedorId;
    apiClient
      .post('/crm-vendas/oportunidades/', payload)
      .then(() => {
        setLeadCriarOportunidade(null);
        loadLeads(setLeads, setError);
        router.push(`/loja/${slug}/crm-vendas/pipeline`);
      })
      .catch((err) => {
        const d = err.response?.data;
        const msg =
          d?.titulo?.[0] ||
          d?.valor?.[0] ||
          d?.lead?.[0] ||
          d?.vendedor?.[0] ||
          d?.etapa?.[0] ||
          (typeof d?.detail === 'string' ? d.detail : null) ||
          'Erro ao criar oportunidade.';
        setFormErro(msg);
      })
      .finally(() => setEnviando(false));
  };

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

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-gray-800 dark:text-white">Leads</h1>
        <a
          href={`/loja/${slug}/crm-vendas/leads/novo`}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium transition text-sm inline-flex items-center gap-2"
        >
          <Plus size={18} />
          Novo Lead
        </a>
      </div>

      <LeadsTable
        leads={leads}
        loading={loading}
        colunas={colunasLeadsVisiveis()}
        onVerLead={setLeadVer}
        onEditarLead={handleEditarLead}
        onExcluirLead={setLeadExcluir}
        onMudarStatus={handleMudarStatus}
      />

      {leadVer && (
        <ModalLeadVer
          lead={leadVer}
          slug={slug}
          origemLabel={origemLabel}
          statusLabel={statusLabel}
          formatarData={formatarData}
          onClose={() => setLeadVer(null)}
          onCriarOportunidade={handleCriarOportunidade}
        />
      )}

      {leadEditar && (
        <ModalLeadForm
          title="Editar lead"
          form={form}
          formErro={formErro}
          enviando={enviando}
          origensAtivas={origensAtivas}
          statusOpcoes={[...STATUS_LEAD_OPCOES]}
          onFormChange={setForm}
          onSubmit={handleSalvarEdicao}
          onClose={() => !enviando && setLeadEditar(null)}
        />
      )}

      {leadExcluir && (
        <ModalLeadExcluir
          lead={leadExcluir}
          excluindo={excluindo}
          onConfirm={confirmarExcluir}
          onClose={() => !excluindo && setLeadExcluir(null)}
        />
      )}

      {leadMudarStatus && (
        <ModalLeadMudarStatus
          lead={leadMudarStatus}
          novoStatus={novoStatus}
          formErro={formErro}
          enviando={enviando}
          statusOpcoes={[...STATUS_LEAD_OPCOES]}
          onNovoStatusChange={setNovoStatus}
          onSalvar={salvarNovoStatus}
          onClose={() => { if (!enviando) setLeadMudarStatus(null); setFormErro(null); }}
        />
      )}

      {leadCriarOportunidade && (
        <ModalCriarOportunidade
          lead={leadCriarOportunidade}
          form={formOportunidade}
          formErro={formErro}
          enviando={enviando}
          onFormChange={setFormOportunidade}
          onSubmit={submitCriarOportunidade}
          onClose={() => !enviando && setLeadCriarOportunidade(null)}
        />
      )}

    </div>
  );
}
