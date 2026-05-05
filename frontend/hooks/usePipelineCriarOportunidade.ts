/**
 * Hook que encapsula a lógica de criação de oportunidade no Pipeline.
 * Extraído de pipeline/page.tsx para melhor organização.
 */
import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import { normalizeListResponse, getCrmApiErrorDetail } from '@/lib/crm-utils';
import { authService } from '@/lib/auth';

interface ProdutoServicoOption {
  id: number;
  nome: string;
  tipo: string;
  preco: string;
  codigo?: string;
  categoria_nome?: string;
}

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

export interface FormCriar {
  lead_id: string;
  titulo: string;
  valor: string;
  etapa: string;
  valor_comissao: string;
  itens: { produto_servico_id: number; quantidade: string; preco_unitario: string }[];
}

const FORM_INICIAL: FormCriar = {
  lead_id: '',
  titulo: '',
  valor: '0',
  etapa: 'prospecting',
  valor_comissao: '',
  itens: [],
};

export function usePipelineCriarOportunidade(slug: string, onSucesso: () => void) {
  const [modalCriar, setModalCriar] = useState(false);
  const [formCriar, setFormCriar] = useState<FormCriar>(FORM_INICIAL);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [leads, setLeads] = useState<LeadOption[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<ProdutoServicoOption[]>([]);
  const [contas, setContas] = useState<ContaOption[]>([]);
  const [contaSelecionada, setContaSelecionada] = useState<ContaOption | null>(null);
  const [tituloSugestoes, setTituloSugestoes] = useState<ContaOption[]>([]);
  const [showTituloSugestoes, setShowTituloSugestoes] = useState(false);
  const [seletorCriarAberto, setSeletorCriarAberto] = useState(false);

  const abrirModal = useCallback(() => {
    setModalCriar(true);
    setFormCriar(FORM_INICIAL);
    setFormErro(null);
    setContaSelecionada(null);
    setTituloSugestoes([]);
    setShowTituloSugestoes(false);
  }, []);

  const fecharModal = useCallback(() => {
    setModalCriar(false);
  }, []);

  const carregarDados = useCallback(async () => {
    try {
      const [h, p, c] = await Promise.all([
        apiClient.get<LeadOption[] | { results: LeadOption[] }>('/crm-vendas/leads/'),
        apiClient.get<ProdutoServicoOption[] | { results: ProdutoServicoOption[] }>('/crm-vendas/produtos-servicos/?ativo=true'),
        apiClient.get<ContaOption[] | { results: ContaOption[] }>('/crm-vendas/contas/?tipo=prestadora'),
      ]);
      const leadsList = normalizeListResponse(h.data);
      setLeads(leadsList);
      setProdutosServicos(normalizeListResponse(p.data));
      setContas(normalizeListResponse(c.data));
      if (leadsList.length > 0 && !formCriar.lead_id) {
        setFormCriar((f) => ({ ...f, lead_id: String(leadsList[0].id) }));
      }
    } catch { /* best-effort */ }
  }, [formCriar.lead_id]);

  const handleTituloChange = useCallback((valor: string) => {
    setFormCriar((f) => ({ ...f, titulo: valor }));
    if (valor.trim().length >= 1 && contas.length > 0) {
      const termo = valor.toLowerCase();
      const filtradas = contas.filter(
        (c) => c.nome.toLowerCase().includes(termo) || (c.cnpj && c.cnpj.includes(termo))
      );
      setTituloSugestoes(filtradas.slice(0, 8));
      setShowTituloSugestoes(filtradas.length > 0);
    } else {
      setTituloSugestoes([]);
      setShowTituloSugestoes(false);
    }
    if (!valor.trim()) setContaSelecionada(null);
  }, [contas]);

  const handleSelecionarConta = useCallback((conta: ContaOption) => {
    setFormCriar((f) => ({ ...f, titulo: conta.nome }));
    setContaSelecionada(conta);
    setShowTituloSugestoes(false);
    setTituloSugestoes([]);
  }, []);

  const calcNoites = (checkin: string, checkout: string): number => {
    if (!checkin || !checkout) return 0;
    const d1 = new Date(checkin + 'T00:00:00');
    const d2 = new Date(checkout + 'T00:00:00');
    const diff = Math.round((d2.getTime() - d1.getTime()) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : 0;
  };

  const adicionarItem = useCallback((produto: ProdutoServicoOption) => {
    setFormCriar((f) => {
      const newItens = [...f.itens, { produto_servico_id: produto.id, quantidade: '1', preco_unitario: produto.preco }];
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: String(total.toFixed(2)) };
    });
  }, []);

  const atualizarItem = useCallback((idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
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
  }, [produtosServicos]);

  const removerItem = useCallback((idx: number) => {
    setFormCriar((f) => {
      const newItens = f.itens.filter((_, i) => i !== idx);
      const total = newItens.reduce((s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : '0' };
    });
  }, []);

  const submeter = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setFormErro(null);
    const leadId = formCriar.lead_id ? parseInt(formCriar.lead_id, 10) : 0;
    if (!leadId) { setFormErro('Selecione um lead.'); return; }
    if (!formCriar.titulo.trim()) { setFormErro('Informe o título da oportunidade.'); return; }

    let valor = parseFloat(formCriar.valor) || 0;
    if (formCriar.itens.length > 0) {
      const totalItens = formCriar.itens.reduce(
        (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0), 0
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
    if (contaSelecionada) payload.empresa_prestadora = contaSelecionada.id;
    const vendedorId = authService.getVendedorId();
    if (vendedorId) payload.vendedor = vendedorId;

    try {
      const res = await apiClient.post<{ id: number }>('/crm-vendas/oportunidades/', payload);
      const oportunidadeId = res.data?.id;

      if (oportunidadeId && formCriar.itens.length > 0) {
        await Promise.all(formCriar.itens.map((item) => {
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
        }));
      }

      // Sincronizar vendedor_id
      try {
        const meRes = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
        if (meRes.data?.vendedor_id && meRes.data?.is_vendedor === true) {
          authService.setVendedorId(meRes.data.vendedor_id);
        }
      } catch { /* ignora */ }

      setModalCriar(false);
      onSucesso();
    } catch (err: any) {
      const d = err.response?.data;
      const msg = d?.titulo?.[0] || d?.valor?.[0] || d?.lead?.[0] || d?.vendedor?.[0] || d?.etapa?.[0]
        || (typeof d?.detail === 'string' ? d.detail : null) || 'Erro ao criar oportunidade.';
      setFormErro(msg);
    } finally {
      setEnviando(false);
    }
  }, [formCriar, contaSelecionada, onSucesso]);

  return {
    modalCriar, setModalCriar, abrirModal, fecharModal,
    formCriar, setFormCriar, formErro, enviando,
    leads, produtosServicos, contas,
    contaSelecionada, tituloSugestoes, showTituloSugestoes,
    seletorCriarAberto, setSeletorCriarAberto,
    carregarDados, handleTituloChange, handleSelecionarConta,
    adicionarItem, atualizarItem, removerItem, submeter,
  };
}
