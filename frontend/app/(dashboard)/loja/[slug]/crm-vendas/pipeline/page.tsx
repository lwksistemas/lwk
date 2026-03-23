'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse } from '@/lib/crm-utils';
import { DollarSign, LayoutDashboard, Plus, X, Mail, MessageCircle } from 'lucide-react';
import PipelineBoard, { type Oportunidade } from '@/components/crm-vendas/PipelineBoard';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

interface LeadOption {
  id: number;
  nome: string;
}

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
}

function loadOportunidades(setOportunidades: (o: Oportunidade[]) => void, setError: (e: string | null) => void) {
  // Adicionar timestamp para evitar cache
  const timestamp = new Date().getTime();
  apiClient
    .get<Oportunidade[] | { results: Oportunidade[] }>(`/crm-vendas/oportunidades/?_t=${timestamp}`)
    .then((res) => {
      setOportunidades(normalizeListResponse(res.data));
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
  const { etapasAtivas } = useCRMConfig();
  
  const [oportunidades, setOportunidades] = useState<Oportunidade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [vendedorIdSynced, setVendedorIdSynced] = useState(false);
  const [oportunidadeEditar, setOportunidadeEditar] = useState<Oportunidade | null>(null);
  const [etapaSelecionada, setEtapaSelecionada] = useState('');
  const [valorComissaoEdit, setValorComissaoEdit] = useState('');
  const [dataFechamentoGanho, setDataFechamentoGanho] = useState('');
  const [dataFechamentoPerdido, setDataFechamentoPerdido] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [modalCriar, setModalCriar] = useState(false);
  const [propostasOportunidade, setPropostasOportunidade] = useState<{ id: number; titulo: string }[]>([]);
  const [contratoOportunidade, setContratoOportunidade] = useState<{ id: number; titulo: string } | null>(null);
  const [enviandoEnvio, setEnviandoEnvio] = useState(false);
  const [modalExcluir, setModalExcluir] = useState(false);
  const [leads, setLeads] = useState<LeadOption[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [formCriar, setFormCriar] = useState({
    lead_id: '',
    titulo: '',
    valor: '0',
    etapa: 'prospecting',
    valor_comissao: '',
    itens: [] as { produto_servico_id: number; quantidade: string; preco_unitario: string }[],
  });
  const [itensEditar, setItensEditar] = useState<{ id?: number; produto_servico_id: number; quantidade: string; preco_unitario: string }[]>([]);

  // Sincronizar vendedor_id com backend ao montar componente
  useEffect(() => {
    apiClient
      .get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/')
      .then((res) => {
        const { vendedor_id } = res.data;
        if (vendedor_id) {
          authService.setVendedorId(vendedor_id);
        }
        setVendedorIdSynced(true);
      })
      .catch(() => {
        setVendedorIdSynced(true);
      });
  }, []);

  useEffect(() => {
    if (!vendedorIdSynced) return;
    
    apiClient
      .get<Oportunidade[] | { results: Oportunidade[] }>('/crm-vendas/oportunidades/')
      .then((res) => setOportunidades(normalizeListResponse(res.data)))
      .catch((err) => {
        setError(
          err.response?.data?.detail || 'Erro ao carregar oportunidades.'
        );
      })
      .finally(() => setLoading(false));
  }, [vendedorIdSynced]);

  useEffect(() => {
    const leadIdParam = searchParams.get('lead_id');
    if (searchParams.get('novo') === '1') {
      setModalCriar(true);
      // Se veio com lead_id, pré-selecionar
      if (leadIdParam) {
        setFormCriar((f) => ({ ...f, lead_id: leadIdParam }));
      }
      router.replace(`/loja/${slug}/crm-vendas/pipeline`, { scroll: false });
    }
  }, [searchParams, router, slug]);

  useEffect(() => {
    if (!modalCriar) return;
    apiClient
      .get<LeadOption[] | { results: LeadOption[] }>('/crm-vendas/leads/')
      .then((res) => {
        const list = normalizeListResponse(res.data);
        setLeads(list);
        if (list.length > 0 && !formCriar.lead_id) {
          setFormCriar((f) => ({ ...f, lead_id: String(list[0].id) }));
        }
      })
      .catch(() => setLeads([]));
    apiClient
      .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
      .then((res) => setProdutosServicos(normalizeListResponse(res.data)))
      .catch(() => setProdutosServicos([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Executar apenas ao abrir modal
  }, [modalCriar]);

  const handleAbrirCriar = () => {
    setModalCriar(true);
    setFormCriar({ lead_id: '', titulo: '', valor: '0', etapa: 'prospecting', valor_comissao: '', itens: [] });
    setFormErro(null);
  };

  const addItemCriar = () => {
    const first = produtosServicos[0];
    if (!first) return;
    setFormCriar((f) => {
      const newItens = [...f.itens, { produto_servico_id: first.id, quantidade: '1', preco_unitario: first.preco }];
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: String(total.toFixed(2)) };
    });
  };

  const updateItemCriar = (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
    setFormCriar((f) => {
      const newItens = f.itens.map((item, i) => {
        if (i !== idx) return item;
        const updated = { ...item, [field]: field === 'produto_servico_id' ? Number(value) : String(value) };
        if (field === 'produto_servico_id') {
          const ps = produtosServicos.find((p) => p.id === Number(value));
          if (ps) updated.preco_unitario = ps.preco;
        }
        return updated;
      });
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : f.valor };
    });
  };

  const removeItemCriar = (idx: number) => {
    setFormCriar((f) => {
      const newItens = f.itens.filter((_, i) => i !== idx);
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : '0' };
    });
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
    let valor = parseFloat(formCriar.valor) || 0;
    if (formCriar.itens.length > 0) {
      const totalItens = formCriar.itens.reduce(
        (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0),
        0
      );
      if (totalItens > 0) valor = totalItens;
    }
    const valor_comissao = formCriar.valor_comissao ? parseFloat(formCriar.valor_comissao) : null;
    setEnviando(true);
    const payload: Record<string, unknown> = {
      lead: leadId,
      titulo: formCriar.titulo.trim(),
      valor,
      etapa: formCriar.etapa,
      valor_comissao,
    };
    const vendedorId = authService.getVendedorId();
    if (vendedorId) payload.vendedor = vendedorId;
    apiClient
      .post<{ id: number }>('/crm-vendas/oportunidades/', payload)
      .then(async (res) => {
        const oportunidadeId = res.data?.id;
        if (oportunidadeId && formCriar.itens.length > 0) {
          // ✅ OTIMIZAÇÃO: Criar todos os itens em paralelo
          const promises = formCriar.itens.map((item) => {
            const qty = parseFloat(item.quantidade) || 1;
            const preco = parseFloat(item.preco_unitario) || 0;
            if (qty > 0 && preco >= 0) {
              return apiClient.post('/crm-vendas/oportunidade-itens/', {
                oportunidade: oportunidadeId,
                produto_servico: item.produto_servico_id,
                quantidade: qty,
                preco_unitario: preco,
              });
            }
            return Promise.resolve();
          });
          await Promise.all(promises);
        }
        
        // Sincronizar vendedor_id antes de recarregar lista
        try {
          const meRes = await apiClient.get<{ vendedor_id: number | null }>('/crm-vendas/me/');
          if (meRes.data.vendedor_id) {
            authService.setVendedorId(meRes.data.vendedor_id);
          }
        } catch {
          // Ignora erro de sincronização
        }
        
        setModalCriar(false);
        loadOportunidades(setOportunidades, setError);
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

  const handleCardClick = (op: Oportunidade) => {
    setOportunidadeEditar(op);
    setEtapaSelecionada(op.etapa);
    setValorComissaoEdit(op.valor_comissao || '');
    setDataFechamentoGanho(op.data_fechamento_ganho || '');
    setDataFechamentoPerdido(op.data_fechamento_perdido || '');
    setFormErro(null);
    setModalExcluir(false);
    setPropostasOportunidade([]);
    setContratoOportunidade(null);
    
    // Carregar itens da oportunidade
    apiClient
      .get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${op.id}`)
      .then((res) => {
        const itens = normalizeListResponse(res.data);
        setItensEditar(itens.map((item: any) => ({
          id: item.id,
          produto_servico_id: item.produto_servico,
          quantidade: String(item.quantidade),
          preco_unitario: String(item.preco_unitario),
        })));
      })
      .catch(() => setItensEditar([]));
    
    // Carregar produtos/serviços para o select
    apiClient
      .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
      .then((res) => setProdutosServicos(normalizeListResponse(res.data)))
      .catch(() => setProdutosServicos([]));
  };

  const addItemEditar = () => {
    const first = produtosServicos[0];
    if (!first) return;
    setItensEditar((itens) => [
      ...itens,
      { produto_servico_id: first.id, quantidade: '1', preco_unitario: first.preco },
    ]);
  };

  const updateItemEditar = (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
    setItensEditar((itens) =>
      itens.map((item, i) => {
        if (i !== idx) return item;
        const updated = { ...item, [field]: field === 'produto_servico_id' ? Number(value) : String(value) };
        if (field === 'produto_servico_id') {
          const ps = produtosServicos.find((p) => p.id === Number(value));
          if (ps) updated.preco_unitario = ps.preco;
        }
        return updated;
      })
    );
  };

  const removeItemEditar = (idx: number) => {
    setItensEditar((itens) => itens.filter((_, i) => i !== idx));
  };

  const handleExcluirOportunidade = async () => {
    if (!oportunidadeEditar) return;
    setEnviando(true);
    try {
      await apiClient.delete(`/crm-vendas/oportunidades/${oportunidadeEditar.id}/`);
      setOportunidadeEditar(null);
      setModalExcluir(false);
      loadOportunidades(setOportunidades, setError);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao excluir oportunidade.');
    } finally {
      setEnviando(false);
    }
  };

  useEffect(() => {
    if (!oportunidadeEditar) return;
    const isClosedWon = oportunidadeEditar.etapa === 'closed_won' || etapaSelecionada === 'closed_won';
    if (!isClosedWon) return;
    apiClient
      .get<{ results: { id: number; titulo: string }[] }>(`/crm-vendas/propostas/?oportunidade_id=${oportunidadeEditar.id}`)
      .then((r) => setPropostasOportunidade(normalizeListResponse(r.data)))
      .catch(() => setPropostasOportunidade([]));
    apiClient
      .get<{ results: { id: number; titulo: string }[] }>(`/crm-vendas/contratos/?oportunidade_id=${oportunidadeEditar.id}`)
      .then((r) => {
        const list = normalizeListResponse(r.data);
        setContratoOportunidade(list.length > 0 ? list[0] : null);
      })
      .catch(() => setContratoOportunidade(null));
  }, [oportunidadeEditar, etapaSelecionada]);

  const handleEnviarCliente = async (tipo: 'proposta' | 'contrato', id: number, canal: 'email' | 'whatsapp') => {
    setEnviandoEnvio(true);
    try {
      const url = tipo === 'proposta' ? `/crm-vendas/propostas/${id}/enviar_cliente/` : `/crm-vendas/contratos/${id}/enviar_cliente/`;
      await apiClient.post(url, { canal });
      alert(`Enviado por ${canal === 'email' ? 'e-mail' : 'WhatsApp'} com sucesso!`);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || 'Erro ao enviar.');
    } finally {
      setEnviandoEnvio(false);
    }
  };

  const handleSalvarEtapa = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oportunidadeEditar) return;
    setFormErro(null);
    setEnviando(true);
    
    try {
      const payload: Record<string, unknown> = { etapa: etapaSelecionada };
      
      // Adiciona valor_comissao se preenchido
      if (valorComissaoEdit) {
        payload.valor_comissao = parseFloat(valorComissaoEdit);
      }
      
      // Se mudou para closed_won, sugere data_fechamento_ganho
      if (etapaSelecionada === 'closed_won' && !dataFechamentoGanho) {
        payload.data_fechamento_ganho = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoGanho) {
        payload.data_fechamento_ganho = dataFechamentoGanho;
      }
      
      // Se mudou para closed_lost, sugere data_fechamento_perdido
      if (etapaSelecionada === 'closed_lost' && !dataFechamentoPerdido) {
        payload.data_fechamento_perdido = new Date().toISOString().split('T')[0];
      } else if (dataFechamentoPerdido) {
        payload.data_fechamento_perdido = dataFechamentoPerdido;
      }

      // Atualizar oportunidade
      await apiClient.patch(`/crm-vendas/oportunidades/${oportunidadeEditar.id}/`, payload);
      
      // Atualizar itens (produtos/serviços)
      // Buscar itens atuais do backend
      const resItens = await apiClient.get(`/crm-vendas/oportunidade-itens/?oportunidade_id=${oportunidadeEditar.id}`);
      const itensAtuais = normalizeListResponse(resItens.data);
      const idsAtuais = itensAtuais.map((item: any) => item.id);
      const idsEditados = itensEditar.filter(item => item.id).map(item => item.id);
      
      // Deletar itens removidos
      for (const id of idsAtuais) {
        if (!idsEditados.includes(id)) {
          await apiClient.delete(`/crm-vendas/oportunidade-itens/${id}/`);
        }
      }
      
      // Atualizar ou criar itens
      for (const item of itensEditar) {
        const itemData = {
          oportunidade: oportunidadeEditar.id,
          produto_servico: item.produto_servico_id,
          quantidade: parseFloat(item.quantidade),
          preco_unitario: parseFloat(item.preco_unitario),
        };
        
        if (item.id) {
          // Atualizar item existente
          await apiClient.patch(`/crm-vendas/oportunidade-itens/${item.id}/`, itemData);
        } else {
          // Criar novo item
          await apiClient.post('/crm-vendas/oportunidade-itens/', itemData);
        }
      }
      
      // Recalcular valor total da oportunidade
      if (itensEditar.length > 0) {
        const valorTotal = itensEditar.reduce(
          (sum, item) => sum + parseFloat(item.quantidade) * parseFloat(item.preco_unitario),
          0
        );
        await apiClient.patch(`/crm-vendas/oportunidades/${oportunidadeEditar.id}/`, {
          valor: valorTotal,
        });
      }
      
      setOportunidadeEditar(null);
      loadOportunidades(setOportunidades, setError);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setFormErro(e.response?.data?.detail || 'Erro ao atualizar.');
    } finally {
      setEnviando(false);
    }
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
          etapas={etapasAtivas()}
          onCardClick={handleCardClick}
        />
      </div>

      {modalCriar && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-0 bg-black/50"
          onClick={() => !enviando && setModalCriar(false)}
        >
          <div
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md max-h-[90vh] overflow-y-auto md:w-[calc(100vw-2rem)] md:max-w-4xl md:h-[calc(100vh-2rem)] md:max-h-none md:rounded-xl"
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
                  readOnly={formCriar.itens.length > 0}
                  className={`w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white ${formCriar.itens.length > 0 ? 'bg-gray-50 dark:bg-gray-600/50 cursor-not-allowed' : ''}`}
                  placeholder="0"
                />
                {formCriar.itens.length > 0 && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Valor calculado automaticamente pelos itens
                  </p>
                )}
              </div>
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Produtos e Serviços
                  </label>
                  <Link
                    href={`/loja/${slug}/crm-vendas/produtos-servicos`}
                    className="text-xs text-[#0176d3] hover:underline"
                  >
                    Cadastrar
                  </Link>
                </div>
                {formCriar.itens.map((item, idx) => (
                  <div key={idx} className="flex gap-2 mb-2 items-center">
                    <select
                      value={item.produto_servico_id}
                      onChange={(e) => updateItemCriar(idx, 'produto_servico_id', e.target.value)}
                      className="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                    >
                      {produtosServicos.length === 0 && (
                        <option value="">Nenhum produto cadastrado</option>
                      )}
                      {produtosServicos.map((ps) => (
                        <option key={ps.id} value={ps.id}>
                          {ps.tipo === 'produto' ? 'Produto' : 'Serviço'}: {ps.nome} - {parseFloat(ps.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.preco_unitario}
                      onChange={(e) => updateItemCriar(idx, 'preco_unitario', e.target.value)}
                      className="w-20 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      placeholder="Preço"
                    />
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.quantidade}
                      onChange={(e) => updateItemCriar(idx, 'quantidade', e.target.value)}
                      className="w-16 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      placeholder="Qtd"
                    />
                    <button
                      type="button"
                      onClick={() => removeItemCriar(idx)}
                      className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600"
                      aria-label="Remover"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
                {produtosServicos.length > 0 && (
                  <button
                    type="button"
                    onClick={addItemCriar}
                    className="text-sm text-[#0176d3] hover:underline"
                  >
                    + Adicionar item
                  </button>
                )}
                {produtosServicos.length === 0 && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    Cadastre produtos/serviços em <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline">Produtos e Serviços</Link>.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Valor da Comissão (R$)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={formCriar.valor_comissao}
                  onChange={(e) => setFormCriar((f) => ({ ...f, valor_comissao: e.target.value }))}
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
                  {etapasAtivas().map((o) => (
                    <option key={o.key} value={o.key}>{o.label}</option>
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
            className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-2xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
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
            <div className="p-4 flex-shrink-0">
              <p className="font-medium text-gray-900 dark:text-white">{oportunidadeEditar.titulo}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">{oportunidadeEditar.lead_nome}</p>
              <p className="text-sm font-semibold text-green-600 dark:text-green-400 mt-1">
                {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(String(oportunidadeEditar.valor)))}
              </p>
              {oportunidadeEditar.valor_comissao && (
                <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
                  Comissão: {new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(parseFloat(String(oportunidadeEditar.valor_comissao)))}
                </p>
              )}
            </div>
            <form id="form-editar-oportunidade" onSubmit={handleSalvarEtapa} className="overflow-y-auto flex-1">
              <div className="p-4 pt-0 space-y-4">
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
                  {etapasAtivas().map((o) => (
                    <option key={o.key} value={o.key}>{o.label}</option>
                  ))}
                </select>
              </div>
              
              {/* Produtos e Serviços */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Produtos e Serviços
                  </label>
                  <Link
                    href={`/loja/${slug}/crm-vendas/produtos-servicos`}
                    className="text-xs text-[#0176d3] hover:underline"
                  >
                    Cadastrar
                  </Link>
                </div>
                {itensEditar.map((item, idx) => (
                  <div key={idx} className="flex gap-2 mb-2 items-center">
                    <select
                      value={item.produto_servico_id}
                      onChange={(e) => updateItemEditar(idx, 'produto_servico_id', e.target.value)}
                      className="flex-1 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                    >
                      {produtosServicos.length === 0 && (
                        <option value="">Nenhum produto cadastrado</option>
                      )}
                      {produtosServicos.map((ps) => (
                        <option key={ps.id} value={ps.id}>
                          {ps.tipo === 'produto' ? 'Produto' : 'Serviço'}: {ps.nome} - {parseFloat(ps.preco).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </option>
                      ))}
                    </select>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.preco_unitario}
                      onChange={(e) => updateItemEditar(idx, 'preco_unitario', e.target.value)}
                      className="w-20 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      placeholder="Preço"
                    />
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.quantidade}
                      onChange={(e) => updateItemEditar(idx, 'quantidade', e.target.value)}
                      className="w-16 px-2 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700"
                      placeholder="Qtd"
                    />
                    <button
                      type="button"
                      onClick={() => removeItemEditar(idx)}
                      className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600"
                      aria-label="Remover"
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
                {produtosServicos.length > 0 && (
                  <button
                    type="button"
                    onClick={addItemEditar}
                    className="text-sm text-[#0176d3] hover:underline"
                  >
                    + Adicionar item
                  </button>
                )}
                {produtosServicos.length === 0 && (
                  <p className="text-xs text-amber-600 dark:text-amber-400">
                    Cadastre produtos/serviços em <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline">Produtos e Serviços</Link>.
                  </p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Valor da Comissão (R$)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  value={valorComissaoEdit}
                  onChange={(e) => setValorComissaoEdit(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="0"
                />
              </div>
              {(etapaSelecionada === 'closed_won' || oportunidadeEditar.data_fechamento_ganho) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data Fechamento Ganho
                  </label>
                  <input
                    type="date"
                    value={dataFechamentoGanho}
                    onChange={(e) => setDataFechamentoGanho(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              )}
              {(etapaSelecionada === 'closed_lost' || oportunidadeEditar.data_fechamento_perdido) && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Data Fechamento Perdido
                  </label>
                  <input
                    type="date"
                    value={dataFechamentoPerdido}
                    onChange={(e) => setDataFechamentoPerdido(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
              )}
              {(etapaSelecionada === 'closed_won' || oportunidadeEditar.etapa === 'closed_won') && (
                <div className="border-t border-gray-200 dark:border-gray-600 pt-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Enviar ao cliente
                  </label>
                  {(propostasOportunidade.length > 0 || contratoOportunidade) ? (
                    <div className="space-y-2">
                      {propostasOportunidade.map((p) => (
                        <div key={p.id} className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-sm truncate">Proposta: {p.titulo || `#${p.id}`}</span>
                          <div className="flex gap-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleEnviarCliente('proposta', p.id, 'email')}
                              disabled={enviandoEnvio}
                              className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50"
                              title="Enviar por e-mail"
                            >
                              <Mail size={16} />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleEnviarCliente('proposta', p.id, 'whatsapp')}
                              disabled={enviandoEnvio}
                              className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50"
                              title="Enviar por WhatsApp"
                            >
                              <MessageCircle size={16} />
                            </button>
                          </div>
                        </div>
                      ))}
                      {contratoOportunidade && (
                        <div className="flex items-center justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-sm truncate">Contrato: {contratoOportunidade.titulo || `#${contratoOportunidade.id}`}</span>
                          <div className="flex gap-1 shrink-0">
                            <button
                              type="button"
                              onClick={() => handleEnviarCliente('contrato', contratoOportunidade.id, 'email')}
                              disabled={enviandoEnvio}
                              className="p-1.5 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50 disabled:opacity-50"
                              title="Enviar por e-mail"
                            >
                              <Mail size={16} />
                            </button>
                            <button
                              type="button"
                              onClick={() => handleEnviarCliente('contrato', contratoOportunidade.id, 'whatsapp')}
                              disabled={enviandoEnvio}
                              className="p-1.5 rounded bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50"
                              title="Enviar por WhatsApp"
                            >
                              <MessageCircle size={16} />
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Crie uma proposta ou contrato em{' '}
                      <Link href={`/loja/${slug}/crm-vendas/propostas`} className="text-[#0176d3] hover:underline">Propostas</Link>
                      {' ou '}
                      <Link href={`/loja/${slug}/crm-vendas/contratos`} className="text-[#0176d3] hover:underline">Contratos</Link>
                      {' para enviar ao cliente.'}
                    </p>
                  )}
                </div>
              )}
              </div>
            </form>
            <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
              {!modalExcluir ? (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => !enviando && setOportunidadeEditar(null)}
                    className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={() => setModalExcluir(true)}
                    disabled={enviando}
                    className="px-4 py-2 rounded-lg border border-red-300 dark:border-red-600 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
                  >
                    Excluir
                  </button>
                  <button
                    type="submit"
                    form="form-editar-oportunidade"
                    disabled={enviando}
                    className="flex-1 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium"
                  >
                    {enviando ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Tem certeza que deseja excluir a oportunidade &quot;{oportunidadeEditar.titulo}&quot;? Esta ação não pode ser desfeita.
                  </p>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setModalExcluir(false)}
                      disabled={enviando}
                      className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50"
                    >
                      Cancelar
                    </button>
                    <button
                      type="button"
                      onClick={handleExcluirOportunidade}
                      disabled={enviando}
                      className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium"
                    >
                      {enviando ? 'Excluindo...' : 'Confirmar exclusão'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
