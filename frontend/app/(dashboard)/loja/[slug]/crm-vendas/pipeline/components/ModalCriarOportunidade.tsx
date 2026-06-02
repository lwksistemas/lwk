'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { X } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import ProdutoSeletorCategoria from '@/components/crm-vendas/ProdutoSeletorCategoria';

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

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  slug: string;
  etapas: { key: string; label: string }[];
  initialLeadId?: string;
}

export default function ModalCriarOportunidade({ open, onClose, onSuccess, slug, etapas, initialLeadId }: Props) {
  const [leads, setLeads] = useState<LeadOption[]>([]);
  const [leadBusca, setLeadBusca] = useState('');
  const [contas, setContas] = useState<ContaOption[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [seletorCriarAberto, setSeletorCriarAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [formCriar, setFormCriar] = useState({
    lead_id: initialLeadId || '',
    titulo: '',
    empresa_prestadora_id: '',
    valor: '0',
    etapa: 'prospecting',
    valor_comissao: '',
    itens: [] as { produto_servico_id: number; quantidade: string; preco_unitario: string }[],
  });

  // Carregar dados ao abrir modal
  useEffect(() => {
    if (!open) return;
    setFormCriar({
      lead_id: initialLeadId || '',
      titulo: '',
      empresa_prestadora_id: '',
      valor: '0',
      etapa: 'prospecting',
      valor_comissao: '',
      itens: [],
    });
    setFormErro(null);
    setSeletorCriarAberto(false);

    apiClient
      .get<LeadOption[] | { results: LeadOption[] }>('/crm-vendas/leads/?page_size=500')
      .then((res) => {
        const list = normalizeListResponse(res.data);
        setLeads(list);
        if (list.length > 0 && !initialLeadId) {
          setFormCriar((f) => ({ ...f, lead_id: String(list[0].id) }));
        }
      })
      .catch(() => setLeads([]));
    apiClient
      .get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true')
      .then((res) => setProdutosServicos(normalizeListResponse(res.data)))
      .catch(() => setProdutosServicos([]));
    apiClient
      .get<ContaOption[] | { results: ContaOption[] }>('/crm-vendas/contas/?tipo=prestadora')
      .then((res) => setContas(normalizeListResponse(res.data)))
      .catch(() => setContas([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const leadsFiltrados = useMemo(() => {
    const q = leadBusca.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (!q) return leads;
    return leads.filter((l) => {
      const nome = (l.nome || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return nome.includes(q);
    });
  }, [leads, leadBusca]);

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
      // Título gerado automaticamente pelo nome da empresa prestadora
      const conta = contas.find((c) => String(c.id) === formCriar.empresa_prestadora_id);
      if (conta) {
        setFormCriar((f) => ({ ...f, titulo: conta.nome }));
      } else {
        setFormErro('Selecione a empresa prestadora.');
        return;
      }
    }
    // Empresa prestadora é obrigatória
    const empresaPrestadoraId = formCriar.empresa_prestadora_id
      ? parseInt(formCriar.empresa_prestadora_id, 10)
      : 0;
    if (!empresaPrestadoraId) {
      setFormErro('Selecione a empresa prestadora. Toda oportunidade precisa ter uma empresa prestadora vinculada.');
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
      titulo: formCriar.titulo.trim() || contas.find((c) => String(c.id) === formCriar.empresa_prestadora_id)?.nome || 'Oportunidade',
      valor,
      etapa: formCriar.etapa,
      valor_comissao,
      empresa_prestadora: empresaPrestadoraId,
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
          const meRes = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
          const { vendedor_id, is_vendedor } = meRes.data;
          // Só sincronizar se for vendedor explicitamente
          if (vendedor_id && is_vendedor === true) {
            authService.setVendedorId(vendedor_id);
          } else if (vendedor_id) {
            // Owner - só salva o ID
            if (typeof window !== 'undefined') {
              sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
            }
          }
        } catch {
          // Ignora erro de sincronização
        }
        
        onClose();
        onSuccess();
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

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 md:p-0 bg-black/50"
      onClick={() => !enviando && onClose()}
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
            onClick={() => !enviando && onClose()}
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
            <input
              type="text"
              placeholder="Buscar lead pelo nome..."
              value={leadBusca}
              onChange={(e) => setLeadBusca(e.target.value)}
              className="w-full px-3 py-2 mb-1 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-sm"
            />
            <select
              value={formCriar.lead_id}
              onChange={(e) => setFormCriar((f) => ({ ...f, lead_id: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
              size={leadBusca.trim() ? Math.min(leadsFiltrados.length + 1, 5) : 1}
            >
              <option value="">Selecione o lead</option>
              {leadsFiltrados.map((l) => (
                <option key={l.id} value={l.id}>{l.nome}</option>
              ))}
            </select>
            {leads.length === 0 && (
              <p className="text-xs text-amber-600 dark:text-amber-400 mt-1">
                Nenhum lead cadastrado. <Link href={`/loja/${slug}/crm-vendas/leads`} className="underline">Cadastre em Leads</Link>.
              </p>
            )}
          </div>
          {/* Empresa Prestadora — obrigatória, título gerado automaticamente */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Empresa Prestadora *
            </label>
            {contas.length > 0 ? (
              <select
                value={formCriar.empresa_prestadora_id}
                onChange={(e) => {
                  const id = e.target.value;
                  const conta = contas.find((c) => String(c.id) === id);
                  setFormCriar((f) => ({
                    ...f,
                    empresa_prestadora_id: id,
                    titulo: conta ? conta.nome : f.titulo,
                  }));
                }}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              >
                <option value="">Selecione a empresa prestadora</option>
                {contas.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}{c.cnpj ? ` — ${c.cnpj}` : ''}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-xs text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
                Nenhuma empresa prestadora cadastrada. Cadastre em{' '}
                <Link href={`/loja/${slug}/crm-vendas/contas`} className="underline font-medium">
                  Contas
                </Link>{' '}
                com tipo &quot;Prestadora&quot; antes de criar oportunidades.
              </p>
            )}
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
              <Link href={`/loja/${slug}/crm-vendas/produtos-servicos`} className="text-xs text-[#0176d3] hover:underline">
                Cadastrar
              </Link>
            </div>
            {/* Itens já adicionados */}
            {formCriar.itens.map((item, idx) => {
              const ps = produtosServicos.find(p => p.id === item.produto_servico_id);
              return (
                <div key={idx} className="flex gap-2 mb-2 items-center bg-gray-50 dark:bg-gray-700/50 rounded-lg px-2 py-1.5">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                      {ps?.codigo ? <span className="text-gray-400">[{ps.codigo}] </span> : null}
                      {ps?.nome || 'Produto'}
                    </p>
                    {ps?.categoria_nome && (
                      <p className="text-[10px] text-gray-500">{ps.categoria_nome}</p>
                    )}
                  </div>
                  <input
                    type="number" min="0.01" step="0.01"
                    value={item.preco_unitario}
                    onChange={(e) => updateItemCriar(idx, 'preco_unitario', e.target.value)}
                    className="w-20 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                    placeholder="Preço"
                  />
                  <input
                    type="number" min="0.01" step="0.01"
                    value={item.quantidade}
                    onChange={(e) => updateItemCriar(idx, 'quantidade', e.target.value)}
                    className="w-14 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700"
                    placeholder="Qtd"
                  />
                  <button type="button" onClick={() => removeItemCriar(idx)} className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/30 text-red-500">
                    <X size={13} />
                  </button>
                </div>
              );
            })}
            {/* Seletor por categoria */}
            {seletorCriarAberto && produtosServicos.length > 0 && (
              <div className="mb-2">
                <ProdutoSeletorCategoria
                  produtos={produtosServicos}
                  itensSelecionados={formCriar.itens.map(i => i.produto_servico_id)}
                  onSelecionar={(ps) => {
                    setFormCriar((f) => {
                      const newItens = [...f.itens, { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco }];
                      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
                      return { ...f, itens: newItens, valor: String(total.toFixed(2)) };
                    });
                    setSeletorCriarAberto(false);
                  }}
                  onFechar={() => setSeletorCriarAberto(false)}
                />
              </div>
            )}
            {produtosServicos.length > 0 && !seletorCriarAberto && (
              <button type="button" onClick={() => setSeletorCriarAberto(true)} className="text-sm text-[#0176d3] hover:underline">
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
              {etapas.map((o) => (
                <option key={o.key} value={o.key}>{o.label}</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => !enviando && onClose()}
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
  );
}
