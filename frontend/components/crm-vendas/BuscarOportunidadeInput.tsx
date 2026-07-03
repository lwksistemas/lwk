'use client';

import { useCallback } from 'react';
import apiClient from '@/lib/api-client';
import { formatOportunidadeVinculoLabel } from '@/lib/crm-utils';
import type { CrmPropostaOportunidadeOption } from '@/lib/crm-proposta-form-types';
import CrmSearchInput, { type CrmSearchInputProps } from '@/components/crm-vendas/CrmSearchInput';

export interface CrmOportunidadeBuscaItem {
  id: number;
  titulo: string;
  lead_nome: string;
  lead_empresa: string;
  valor: string;
  etapa: string;
}

function rotuloOportunidade(item: CrmOportunidadeBuscaItem): string {
  return formatOportunidadeVinculoLabel({
    titulo: item.titulo,
    lead_nome: item.lead_nome,
    valor: item.valor,
    conta_nome: item.lead_empresa,
  });
}

interface BuscarOportunidadeInputProps {
  oportunidadeId: string;
  onOportunidadeChange: (id: string) => void;
  initialTitulo?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  limit?: number;
}

export default function BuscarOportunidadeInput({
  oportunidadeId,
  onOportunidadeChange,
  initialTitulo = '',
  placeholder = 'Buscar oportunidade pelo título ou cliente...',
  required = false,
  disabled = false,
  className = '',
  limit = 10,
}: BuscarOportunidadeInputProps) {
  const fetchById = useCallback(async (id: string) => {
    const res = await apiClient.get<CrmPropostaOportunidadeOption>(`/crm-vendas/oportunidades/${id}/`);
    const label = formatOportunidadeVinculoLabel({
      titulo: res.data.titulo,
      lead_nome: res.data.lead_nome,
      valor: res.data.valor,
      conta_nome: res.data.conta_nome,
      empresa_prestadora_nome: res.data.empresa_prestadora_nome,
    });
    return { label };
  }, []);

  const fetchResults = useCallback(async (q: string, lim: number) => {
    const res = await apiClient.get<{ oportunidades: CrmOportunidadeBuscaItem[] }>('/crm-vendas/busca/', {
      params: { q, limit: lim },
    });
    return res.data.oportunidades ?? [];
  }, []);

  const searchProps: CrmSearchInputProps<CrmOportunidadeBuscaItem> = {
    selectedId: oportunidadeId,
    onSelectedIdChange: onOportunidadeChange,
    initialLabel: initialTitulo,
    placeholder,
    required,
    disabled,
    className,
    hiddenInputName: 'oportunidade_id',
    limit,
    fetchById,
    fetchResults,
    getItemId: (o) => String(o.id),
    formatLabel: rotuloOportunidade,
    listClassName: 'rounded-lg',
  };

  return <CrmSearchInput {...searchProps} />;
}
