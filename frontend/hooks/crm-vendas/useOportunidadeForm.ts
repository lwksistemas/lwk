'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { gerarTituloOportunidade, getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import {
  CRM_OPORTUNIDADE_FORM_INICIAL,
  type CrmOportunidadeContaOption,
  type CrmOportunidadeFormState,
  type CrmOportunidadeLeadOption,
  type CrmOportunidadeProdutoOption,
} from '@/lib/crm-oportunidade-form-types';

async function syncVendedorAposCriarOportunidade() {
  try {
    const meRes = await apiClient.get<{ vendedor_id: number | null; is_vendedor: boolean }>('/crm-vendas/me/');
    const { vendedor_id, is_vendedor } = meRes.data;
    if (vendedor_id && is_vendedor === true) {
      authService.setVendedorId(vendedor_id);
    } else if (vendedor_id && typeof window !== 'undefined') {
      sessionStorage.setItem('current_vendedor_id', String(vendedor_id));
    }
  } catch {
    /* ignore */
  }
}

function calcularTotalItens(itens: CrmOportunidadeFormState['itens']) {
  return itens.reduce(
    (s, i) => s + (parseFloat(i.quantidade) || 0) * (parseFloat(i.preco_unitario) || 0),
    0,
  );
}

export interface UseOportunidadeFormOptions {
  initialLeadId?: string;
  /** Quando false, não carrega dados (ex.: modal fechado). */
  enabled?: boolean;
}

export function useOportunidadeForm({ initialLeadId = '', enabled = true }: UseOportunidadeFormOptions = {}) {
  const [leads, setLeads] = useState<CrmOportunidadeLeadOption[]>([]);
  const [leadBusca, setLeadBusca] = useState('');
  const [contas, setContas] = useState<CrmOportunidadeContaOption[]>([]);
  const [produtosServicos, setProdutosServicos] = useState<CrmOportunidadeProdutoOption[]>([]);
  const [seletorAberto, setSeletorAberto] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [formErro, setFormErro] = useState<string | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [form, setForm] = useState<CrmOportunidadeFormState>({
    ...CRM_OPORTUNIDADE_FORM_INICIAL,
    lead_id: initialLeadId,
  });

  const resetForm = useCallback(() => {
    setForm({ ...CRM_OPORTUNIDADE_FORM_INICIAL, lead_id: initialLeadId || '' });
    setLeadBusca('');
    setFormErro(null);
    setSeletorAberto(false);
  }, [initialLeadId]);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    resetForm();

    Promise.all([
      apiClient
        .get<CrmOportunidadeLeadOption[] | { results: CrmOportunidadeLeadOption[] }>('/crm-vendas/leads/?page_size=500')
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as CrmOportunidadeLeadOption[]),
      apiClient
        .get<CrmOportunidadeProdutoOption[] | { results: CrmOportunidadeProdutoOption[] }>(
          '/crm-vendas/produtos-servicos/?ativo=true',
        )
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as CrmOportunidadeProdutoOption[]),
      apiClient
        .get<CrmOportunidadeContaOption[] | { results: CrmOportunidadeContaOption[] }>(
          '/crm-vendas/contas/?tipo=prestadora',
        )
        .then((res) => normalizeListResponse(res.data))
        .catch(() => [] as CrmOportunidadeContaOption[]),
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
      } else if (leadsData.length > 0) {
        setForm((f) => ({ ...f, lead_id: String(leadsData[0].id) }));
      }
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [enabled, initialLeadId, resetForm]);

  const leadsFiltrados = useMemo(() => {
    const q = leadBusca.trim().toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (!q) return leads;
    return leads.filter((l) => {
      const nome = (l.nome || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
      return nome.includes(q);
    });
  }, [leads, leadBusca]);

  const selecionarLead = useCallback((lead: CrmOportunidadeLeadOption) => {
    setForm((f) => ({
      ...f,
      lead_id: String(lead.id),
      titulo: gerarTituloOportunidade(lead),
    }));
    setLeadBusca(lead.nome);
  }, []);

  const updateItem = useCallback(
    (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
      setForm((f) => {
        const newItens = f.itens.map((item, i) => {
          if (i !== idx) return item;
          const updated = {
            ...item,
            [field]: field === 'produto_servico_id' ? Number(value) : String(value),
          };
          if (field === 'produto_servico_id') {
            const ps = produtosServicos.find((p) => p.id === Number(value));
            if (ps) updated.preco_unitario = ps.preco;
          }
          return updated;
        });
        const total = calcularTotalItens(newItens);
        return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : f.valor };
      });
    },
    [produtosServicos],
  );

  const removeItem = useCallback((idx: number) => {
    setForm((f) => {
      const newItens = f.itens.filter((_, i) => i !== idx);
      const total = calcularTotalItens(newItens);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : '0' };
    });
  }, []);

  const adicionarProduto = useCallback((ps: CrmOportunidadeProdutoOption) => {
    setForm((f) => {
      const newItens = [...f.itens, { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco }];
      const total = calcularTotalItens(newItens);
      return { ...f, itens: newItens, valor: String(total.toFixed(2)) };
    });
    setSeletorAberto(false);
  }, []);

  const validarForm = useCallback((): string | null => {
    const leadId = form.lead_id ? parseInt(form.lead_id, 10) : 0;
    if (!leadId) return 'Selecione um lead.';
    const empresaPrestadoraId = form.empresa_prestadora_id ? parseInt(form.empresa_prestadora_id, 10) : 0;
    if (!empresaPrestadoraId) {
      return 'Selecione a empresa prestadora. Toda oportunidade precisa ter uma empresa prestadora vinculada.';
    }
    const lead = leads.find((l) => String(l.id) === form.lead_id);
    if (!form.titulo.trim() && !lead) return 'Selecione um lead.';
    return null;
  }, [form, leads]);

  const montarPayload = useCallback(() => {
    const leadId = parseInt(form.lead_id, 10);
    const lead = leads.find((l) => l.id === leadId);
    let titulo = form.titulo.trim();
    if (!titulo && lead) titulo = gerarTituloOportunidade(lead);

    let valor = parseFloat(form.valor) || 0;
    if (form.itens.length > 0) {
      const totalItens = calcularTotalItens(form.itens);
      if (totalItens > 0) valor = totalItens;
    }

    const payload: Record<string, unknown> = {
      lead: leadId,
      titulo,
      valor,
      etapa: form.etapa,
      valor_comissao: form.valor_comissao ? parseFloat(form.valor_comissao) : null,
      empresa_prestadora: parseInt(form.empresa_prestadora_id, 10),
    };
    const vendedorId = authService.getVendedorId();
    if (vendedorId) payload.vendedor = vendedorId;
    return payload;
  }, [form, leads]);

  const criarOportunidade = useCallback(async (): Promise<number | null> => {
    setFormErro(null);
    const erro = validarForm();
    if (erro) {
      setFormErro(erro);
      return null;
    }

    setEnviando(true);
    try {
      const res = await apiClient.post<{ id: number }>('/crm-vendas/oportunidades/', montarPayload());
      const oportunidadeId = res.data?.id;

      if (oportunidadeId && form.itens.length > 0) {
        await Promise.all(
          form.itens.map((item) => {
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
          }),
        );
      }

      await syncVendedorAposCriarOportunidade();
      return oportunidadeId ?? null;
    } catch (err: unknown) {
      setFormErro(getCrmApiErrorDetail(err, 'Erro ao criar oportunidade.'));
      return null;
    } finally {
      setEnviando(false);
    }
  }, [form.itens, montarPayload, validarForm]);

  return {
    form,
    setForm,
    leads,
    leadBusca,
    setLeadBusca,
    leadsFiltrados,
    selecionarLead,
    contas,
    produtosServicos,
    seletorAberto,
    setSeletorAberto,
    enviando,
    formErro,
    loading,
    updateItem,
    removeItem,
    adicionarProduto,
    criarOportunidade,
    resetForm,
  };
}

export type UseOportunidadeFormReturn = ReturnType<typeof useOportunidadeForm>;
