'use client';

import { useCallback, useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { gerarTituloOportunidade, getCrmApiErrorDetail, normalizeListResponse } from '@/lib/crm-utils';
import type { CrmLeadBuscaItem } from '@/components/crm-vendas/BuscarLeadInput';
import {
  CRM_OPORTUNIDADE_FORM_INICIAL,
  type CrmOportunidadeContaOption,
  type CrmOportunidadeFormState,
  type CrmOportunidadeLeadOption,
  type CrmOportunidadeProdutoOption,
} from '@/lib/crm-oportunidade-form-types';
import { atualizarOportunidadeItem, calcularTotalOportunidadeItens } from '@/lib/crm-oportunidade-itens-utils';

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

export interface UseOportunidadeFormOptions {
  initialLeadId?: string;
  /** Quando false, não carrega dados (ex.: modal fechado). */
  enabled?: boolean;
}

export function useOportunidadeForm({ initialLeadId = '', enabled = true }: UseOportunidadeFormOptions = {}) {
  const [leadResumo, setLeadResumo] = useState<CrmOportunidadeLeadOption | null>(null);
  const [leadLabel, setLeadLabel] = useState('');
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
    setLeadResumo(null);
    setLeadLabel('');
    setFormErro(null);
    setSeletorAberto(false);
  }, [initialLeadId]);

  const handleLeadChange = useCallback((id: string, lead?: CrmLeadBuscaItem) => {
    if (!id || !lead) {
      setLeadResumo(null);
      setLeadLabel('');
      setForm((f) => ({ ...f, lead_id: '', titulo: '' }));
      return;
    }
    const resumo: CrmOportunidadeLeadOption = {
      id: lead.id,
      nome: lead.nome,
      empresa: lead.empresa,
    };
    setLeadResumo(resumo);
    setLeadLabel(lead.nome);
    setForm((f) => ({
      ...f,
      lead_id: id,
      titulo: gerarTituloOportunidade(lead),
    }));
  }, []);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    resetForm();

    const loads: Promise<void>[] = [
      apiClient
        .get<CrmOportunidadeProdutoOption[] | { results: CrmOportunidadeProdutoOption[] }>(
          '/crm-vendas/produtos-servicos/?ativo=true',
        )
        .then((res) => {
          if (!cancelled) setProdutosServicos(normalizeListResponse(res.data));
        })
        .catch(() => {
          if (!cancelled) setProdutosServicos([]);
        }),
      apiClient
        .get<CrmOportunidadeContaOption[] | { results: CrmOportunidadeContaOption[] }>(
          '/crm-vendas/contas/?tipo=prestadora',
        )
        .then((res) => {
          if (!cancelled) setContas(normalizeListResponse(res.data));
        })
        .catch(() => {
          if (!cancelled) setContas([]);
        }),
    ];

    if (initialLeadId) {
      loads.push(
        apiClient
          .get<CrmOportunidadeLeadOption>(`/crm-vendas/leads/${initialLeadId}/`)
          .then((res) => {
            if (cancelled) return;
            const lead = res.data;
            setLeadResumo(lead);
            setLeadLabel(lead.nome);
            setForm((f) => ({
              ...f,
              lead_id: initialLeadId,
              titulo: gerarTituloOportunidade(lead),
            }));
          })
          .catch(() => {
            if (!cancelled) {
              setLeadResumo(null);
              setLeadLabel('');
            }
          }),
      );
    }

    Promise.all(loads).finally(() => {
      if (!cancelled) setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, [enabled, initialLeadId, resetForm]);

  const updateItem = useCallback(
    (idx: number, field: 'produto_servico_id' | 'quantidade' | 'preco_unitario', value: string | number) => {
      setForm((f) => {
        const newItens = atualizarOportunidadeItem(f.itens, idx, field, value, produtosServicos);
        const total = calcularTotalOportunidadeItens(newItens);
        return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : f.valor };
      });
    },
    [produtosServicos],
  );

  const removeItem = useCallback((idx: number) => {
    setForm((f) => {
      const newItens = f.itens.filter((_, i) => i !== idx);
      const total = calcularTotalOportunidadeItens(newItens);
      return { ...f, itens: newItens, valor: newItens.length > 0 ? String(total.toFixed(2)) : '0' };
    });
  }, []);

  const adicionarProduto = useCallback((ps: CrmOportunidadeProdutoOption) => {
    setForm((f) => {
      const newItens = [...f.itens, { produto_servico_id: ps.id, quantidade: '1', preco_unitario: ps.preco }];
      const total = calcularTotalOportunidadeItens(newItens);
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
    if (!form.titulo.trim() && !leadResumo) return 'Selecione um lead.';
    return null;
  }, [form, leadResumo]);

  const montarPayload = useCallback(() => {
    const leadId = parseInt(form.lead_id, 10);
    let titulo = form.titulo.trim();
    if (!titulo && leadResumo) titulo = gerarTituloOportunidade(leadResumo);

    let valor = parseFloat(form.valor) || 0;
    if (form.itens.length > 0) {
      const totalItens = calcularTotalOportunidadeItens(form.itens);
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
  }, [form, leadResumo]);

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
    leadLabel,
    handleLeadChange,
    leadResumo,
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
