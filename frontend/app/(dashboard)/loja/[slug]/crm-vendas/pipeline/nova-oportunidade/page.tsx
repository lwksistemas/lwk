'use client';

/**
 * Página dedicada para criação de oportunidade — CRM Vendas.
 * Layout full-page (mesmo padrão cadastro de lead), sem cabeçalho extra.
 */

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse, gerarTituloOportunidade } from '@/lib/crm-utils';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';
import { CrmFormPageShell } from '@/components/crm-vendas/CrmFormPageShell';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

interface LeadOption {
  id: number;
  nome: string;
  empresa?: string;
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
  'w-full px-3 py-2 text-sm border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#0176d3] focus:ring-offset-0';
const labelClass = 'block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1';
const sectionTitleClass =
  'text-sm font-semibold text-gray-800 dark:text-gray-200 border-b border-gray-100 dark:border-[#0d1f3c] pb-2';

export default function NovaOportunidadePage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const slug = (params?.slug as string) ?? '';
  const pipelinePath = `/loja/${slug}/crm-vendas/pipeline`;
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

      if (initialLeadId) {
        const lead = leadsData.find((l) => String(l.id) === initialLeadId);
        if (lead) {
          setLeadBusca(lead.nome);
          setForm((f) => ({
            ...f,
            lead_id: initialLeadId,
            titulo: gerarTituloOportunidade(lead),
          }));
        }
      }
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
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

  const handleSave = async () => {
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

    const lead = leads.find((l) => String(l.id) === form.lead_id);
    let titulo = form.titulo.trim();
    if (!titulo) {
      if (lead) {
        titulo = gerarTituloOportunidade(lead);
      } else {
        setFormErro('Selecione um lead.');
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
        /* ignore */
      }

      router.push(pipelinePath);
    } catch (err: unknown) {
      const d = (err as { response?: { data?: Record<string, unknown> } })?.response?.data;
      const msg =
        (Array.isArray(d?.titulo) ? d?.titulo[0] : null) ||
        (Array.isArray(d?.valor) ? d?.valor[0] : null) ||
        (Array.isArray(d?.lead) ? d?.lead[0] : null) ||
        (Array.isArray(d?.vendedor) ? d?.vendedor[0] : null) ||
        (Array.isArray(d?.etapa) ? d?.etapa[0] : null) ||
        (typeof d?.detail === 'string' ? d.detail : null) ||
        'Erro ao criar oportunidade.';
      setFormErro(String(msg));
    } finally {
      setEnviando(false);
    }
  };

  if (loading) {
    return (
      <div className="-m-4 sm:-m-6 lg:-m-8 flex flex-1 items-center justify-center min-h-[calc(100dvh-3.5rem)] bg-[#f3f2f2] dark:bg-[#0d1f3c]">
        <p className="text-gray-500 dark:text-gray-400">Carregando...</p>
      </div>
    );
  }

  return (
    <CrmFormPageShell
      error={formErro}
      saving={enviando}
      saveLabel="Criar oportunidade"
      savingLabel="Criando..."
      onSave={handleSave}
      onCancel={() => router.push(pipelinePath)}
      saveDisabled={leads.length === 0}
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-10 xl:gap-14 w-full">
        <div className="space-y-6">
          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Lead</h3>
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
                <div className="w-full mt-1 border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#1e3a5f] max-h-48 overflow-y-auto shadow-sm">
                  {leadsFiltrados.map((l) => (
                    <button
                      key={l.id}
                      type="button"
                      onClick={() => {
                        setForm((f) => ({
                          ...f,
                          lead_id: String(l.id),
                          titulo: gerarTituloOportunidade(l),
                        }));
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

          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Empresa prestadora</h3>
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
                  com tipo &quot;Prestadora&quot;.
                </p>
              )}
            </div>
          </section>

          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Etapa</h3>
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
        </div>

        <div className="space-y-6">
          <section className="space-y-4">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-[#0d1f3c] pb-2">
              <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Produtos e serviços</h3>
              <Link
                href={`/loja/${slug}/crm-vendas/produtos-servicos`}
                className="text-xs text-[#0176d3] hover:underline"
              >
                Cadastrar
              </Link>
            </div>

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
                        className="w-24 px-2 py-1.5 text-xs border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#264a73] text-gray-900 dark:text-white"
                        placeholder="Preço"
                      />
                      <input
                        type="number"
                        min="0.01"
                        step="0.01"
                        value={item.quantidade}
                        onChange={(e) => updateItem(idx, 'quantidade', e.target.value)}
                        className="w-16 px-2 py-1.5 text-xs border border-gray-200 dark:border-neutral-600 rounded-lg bg-white dark:bg-[#264a73] text-gray-900 dark:text-white"
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

            {seletorAberto && produtosServicos.length > 0 && (
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
            )}

            {produtosServicos.length > 0 && !seletorAberto && (
              <button
                type="button"
                onClick={() => setSeletorAberto(true)}
                className="text-sm text-[#0176d3] hover:underline font-medium"
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

          <section className="space-y-4">
            <h3 className={sectionTitleClass}>Valor e comissão</h3>
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
                <label className={labelClass}>Valor da comissão (R$)</label>
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
        </div>
      </div>
    </CrmFormPageShell>
  );
}
