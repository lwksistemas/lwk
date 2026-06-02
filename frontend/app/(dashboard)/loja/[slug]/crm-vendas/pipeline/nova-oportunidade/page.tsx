'use client';

/**
 * Página dedicada para criação de oportunidade — CRM Vendas.
 * Substitui o modal ModalCriarOportunidade com layout full-page.
 * Seções: Lead, Empresa Prestadora, Produtos/Serviços, Valor, Comissão, Etapa.
 */

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { ArrowLeft, Save, X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse } from '@/lib/crm-utils';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

interface LeadOption {
  id: number;
  nome: string;
  conta?: number | null;
}

interface ContaOption {
  id: number;
  nome: string;
  cnpj?: string;
  tipo?: string;
}

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

const inputClass =
  'w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500';
const labelClass = 'block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1';

export default function NovaOportunidadePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const { etapasAtivas } = useCRMConfig();
  const etapas = etapasAtivas();

  const initialLeadId = searchParams.get('lead_id') || '';

  const [leads, setLeads] = useState<LeadOption[]>([]);
  const [leadBusca, setLeadBusca] = useState('');
  const [contas, setContas] = useState<ContaOption[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [seletorAberto, setSeletorAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [form, setForm] = useState({
    lead_id: initialLeadId,
    titulo: '',
    empresa_prestadora_id: '',
    valor: '0',
    etapa: 'prospecting',
    valor_comissao: '',
    itens: [] as { produto_servico_id: number; quantidade: string; preco_unitario: string }[],
  });

  // Carregar dados ao montar a página
  useEffect(() => {
    let cancelled = false;

    Promise.all([
      apiClient
        .get<LeadOption[] | { results: LeadOption[] }>('/crm-vendas/leads/?page_size=500')
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as LeadOption[]),
      apiClient
        .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as ProdutoServicoOption[]),
      apiClient
        .get<ContaOption[] | { results: ContaOption[] }>('/crm-vendas/contas/?tipo=prestadora')
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as ContaOption[]),
    ]).then(([leadsData, produtosData, contasData]) => {
      if (cancelled) return;
      setLeads(leadsData);
      setProdutosServicos(produtosData);
      setContas(contasData);

      // Pré-selecionar lead se veio pela URL
      if (initialLeadId) {
        const lead = leadsData.find((l) => String(l.id) === initialLeadId);
        if (lead) {
          setLeadBusca(lead.nome);
        }
      }
      setLoading(false);
    });

    return () => { cancelled = true; };
  }, [initialLeadId]);

  const leadsFiltrados = useMemo(() => {
    const q = leadBusca.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (!q) return leads;
    return leads.filter((l) => {
      const nome = (l.nome || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return nome.includes(q);
    });
  }, [leads, leadBusca]);

  const updateItem = (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
    setForm((f) => {
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

  const removeItem = (idx: number) => {
    setForm((f) => {
      const newItens = f.itens.filter((_, i) => i !== idx);
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : '0' };
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);

    const leadId = form.lead_id ? parseInt(form.lead_id, 10) : 0;
    if (!leadId) {
      setFormErro('Selecione um lead.');
      return;
    }

    const empresaPrestadoraId = form.empresa_prestadora_id ? parseInt(form.empresa_prestadora_id, 10) : 0;
    if (!empresaPrestadoraId) {
      setFormErro('Selecione a empresa prestadora. Toda oportunidade precisa ter uma empresa prestadora vinculada.');
      return;
    }

    // Título gerado automaticamente pelo nome da empresa prestadora
    let titulo = form.titulo.trim();
    if (!titulo) {
      const conta = contas.find((c) => String(c.id) === form.empresa_prestadora_id);
      if (conta) {
        titulo = conta.nome;
      } else {
        setFormErro('Selecione a empresa prestadora.');
        return;
      }
    }

    let valor = parseFloat(form.valor) || 0;
    if (form.itens.length > 0) {
      const totalItens = form.itens.reduce(
        (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0),
        0,
      );
      if (totalItens > 0) valor = totalItens;
    }

    const valor_comissao = form.valor_comissao ? parseFloat(form.valor_comissao) : null;

    setEnviando(true);

    const payload: Record<string, unknown> = {
      lead: leadId,
      titulo,
      valor,
      etapa: form.etapa,
      valor_comissao,
      empresa_prestadora: empresaPrestadoraId,
    };

    const vendedorId = authService.getVendedorId();
    if (vendedorId) payload.vendedor = vendedorId;

    try {
      const res = await apiClient.post<{ id: number }>('/crm-vendas/oportunidades/', payload);
      const oportunidadeId = res.data?.id;

      if (oportunidadeId && form.itens.length > 0) {
        const promises = form.itens.map((item) => {
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

      // Sincronizar vendedor_id
      try {
        const meRes = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
        const { vendedor_id, is_vendedor } = meRes.data;
        if (vendedor_id && is_vendedor === true) {
          authService.setVendedorId(vendedor_id);
        } else if (vendedor_id) {
          if (typeof window !== 'undefined') {
            sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
          }
        }
      } catch {
        // Ignora erro de sincronização
      }

      router.push(`/loja/${slug}/crm-vendas/pipeline`);
    } catch (err: any) {
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
    } finally {
      setEnviando(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center text-gray-500 dark:text-gray-400">Carregando...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-10">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={() => router.push(`/loja/${slug}/crm-vendas/pipeline`)}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#1e3a5f] transition"
        >
          <ArrowLeft size={18} />
          Voltar
        </button>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">
          Nova Oportunidade
        </h1>
      </div>

      {formErro && (
        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-sm text-red-800 dark:text-red-300">{formErro}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Seção: Lead */}
        <section className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Lead</h3>
          <div>
            <label className={labelClass}>Buscar lead *</label>
            <input
              type="text"
              placeholder="Digite o nome do lead..."
              value={leadBusca}
              onChange={(e) => {
                setLeadBusca(e.target.value);
                setForm((f) => ({ ...f, lead_id: '' }));
              }}
              className={inputClass}
            />
            {leadBusca.trim() && !form.lead_id && leadsFiltrados.length > 0 && (
              <div className="w-full mt-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#1e3a5f] max-h-48 overflow-y-auto shadow-lg">
                {leadsFiltrados.map((l) => (
                  <button
                    key={l.id}
                    type="button"
                    onClick={() => {
                      setForm((f) => ({ ...f, lead_id: String(l.id) }));
                      setLeadBusca(l.nome);
                    }}
                    className="w-full text-left px-3 py-2.5 text-sm text-gray-900 dark:text-white hover:bg-gray-100 dark:hover:bg-[#264a73] border-b border-gray-100 dark:border-gray-600 last:border-b-0 transition"
                  >
                    {l.nome}
                  </button>
                ))}
              </div>
            )}
            {leadBusca.trim() && !form.lead_id && leadsFiltrados.length === 0 && (
              <p className="text-xs text-gray-500 mt-1">Nenhum lead encontrado.</p>
            )}
            {form.lead_id && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                ✓ {leads.find((l) => String(l.id) === form.lead_id)?.nome}
              </p>
            )}
            {leads.length === 0 && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Nenhum lead cadastrado.{' '}
                <Link href={`/loja/${slug}/crm-vendas/leads`} className="underline font-medium">
                  Cadastre em Leads
                </Link>
                .
              </p>
            )}
          </div>
        </section>

        {/* Seção: Empresa Prestadora */}
        <section className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Empresa Prestadora</h3>
          <div>
            <label className={labelClass}>Empresa prestadora *</label>
            {contas.length > 0 ? (
              <select
                value={form.empresa_prestadora_id}
                onChange={(e) => {
                  const id = e.target.value;
                  const conta = contas.find((c) => String(c.id) === id);
                  setForm((f) => ({
                    ...f,
                    empresa_prestadora_id: id,
                    titulo: conta ? conta.nome : f.titulo,
                  }));
                }}
                className={inputClass}
                required
              >
                <option value="">Selecione a empresa prestadora</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                    {c.cnpj ? ` — ${c.cnpj}` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
                Nenhuma empresa prestadora cadastrada. Cadastre em{' '}
                <Link href={`/loja/${slug}/crm-vendas/contas`} className="underline font-medium">
                  Contas
                </Link>{' '}
                com tipo &quot;Prestadora&quot; antes de criar oportunidades.
              </p>
            )}
          </div>
        </section>

        {/* Seção: Produtos/Serviços */}
        <section className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Produtos e Serviços</h3>
            <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="text-xs text-blue-500 hover:underline">
              Cadastrar
            </Link>
          </div>

          {/* Itens já adicionados */}
          {form.itens.length > 0 && (
            <div className="space-y-2">
              {form.itens.map((item, idx) => {
                const ps = produtosServicos.find((p) => p.id === item.produto_servico_id);
                return (
                  <div
                    key={idx}
                    className="flex gap-2 items-center bg-gray-50 dark:bg-[#1e3a5f] rounded-lg px-3 py-2"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                        {ps?.codigo ? <span className="text-gray-400">[{ps.codigo}] </span> : null}
                        {ps?.nome || 'Produto'}
                      </p>
                      {ps?.categoria_nome && (
                        <p className="text-[10px] text-gray-500 dark:text-gray-400">{ps.categoria_nome}</p>
                      )}
                    </div>
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.preco_unitario}
                      onChange={(e) => updateItem(idx, 'preco_unitario', e.target.value)}
                      className="w-24 px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#264a73] text-gray-900 dark:text-white"
                      placeholder="Preço"
                    />
                    <input
                      type="number"
                      min="0.01"
                      step="0.01"
                      value={item.quantidade}
                      onChange={(e) => updateItem(idx, 'quantidade', e.target.value)}
                      className="w-16 px-2 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-[#264a73] text-gray-900 dark:text-white"
                      placeholder="Qtd"
                    />
                    <button
                      type="button"
                      onClick={() => removeItem(idx)}
                      className="p-1.5 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500 transition"
                    >
                      <X size={14} />
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Seletor por categoria */}
          {seletorAberto && produtosServicos.length > 0 && (
            <div>
              <ProdutoSeletorCategoria
                produtos={produtosServicos}
                itensSelecionados={form.itens.map((i) => i.produto_servico_id)}
                onSelecionar={(ps) => {
                  setForm((f) => {
                    const newItens = [
                      ...f.itens,
                      { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco },
                    ];
                    const total = newItens.reduce(
                      (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0),
                      0,
                    );
                    return { ...f, itens: newItens, valor: String(total.toFixed(2)) };
                  });
                  setSeletorAberto(false);
                }}
                onFechar={() => setSeletorAberto(false)}
              />
            </div>
          )}

          {produtosServicos.length > 0 && !seletorAberto && (
            <button
              type="button"
              onClick={() => setSeletorAberto(true)}
              className="text-sm text-blue-500 hover:underline font-medium"
            >
              + Adicionar item
            </button>
          )}

          {produtosServicos.length === 0 && (
            <p className="text-xs text-amber-600 dark:text-amber-400">
              Cadastre produtos/serviços em{' '}
              <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="underline font-medium">
                Produtos e Serviços
              </Link>
              .
            </p>
          )}
        </section>

        {/* Seção: Valor e Comissão */}
        <section className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Valor e Comissão</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Valor (R$)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.valor}
                onChange={(e) => setForm((f) => ({ ...f, valor: e.target.value }))}
                readOnly={form.itens.length > 0}
                className={`${inputClass} ${form.itens.length > 0 ? 'opacity-60 cursor-not-allowed' : ''}`}
                placeholder="0"
              />
              {form.itens.length > 0 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Valor calculado automaticamente pelos itens
                </p>
              )}
            </div>
            <div>
              <label className={labelClass}>Valor da Comissão (R$)</label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={form.valor_comissao}
                onChange={(e) => setForm((f) => ({ ...f, valor_comissao: e.target.value }))}
                className={inputClass}
                placeholder="0"
              />
            </div>
          </div>
        </section>

        {/* Seção: Etapa */}
        <section className="bg-white dark:bg-[#16325c] rounded-xl border border-gray-200 dark:border-gray-700 p-5 space-y-4 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Etapa</h3>
          <div>
            <label className={labelClass}>Etapa inicial</label>
            <select
              value={form.etapa}
              onChange={(e) => setForm((f) => ({ ...f, etapa: e.target.value }))}
              className={inputClass}
            >
              {etapas.map((o) => (
                <option key={o.key} value={o.key}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </section>

        {/* Botões de ação */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={() => router.push(`/loja/${slug}/crm-vendas/pipeline`)}
            className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#1e3a5f] transition"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={enviando || leads.length === 0}
            className="flex-1 py-2.5 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white text-sm font-medium inline-flex items-center justify-center gap-2 transition"
          >
            <Save size={16} />
            {enviando ? 'Criando...' : 'Criar Oportunidade'}
          </button>
        </div>
      </form>
    </div>
  );
}
