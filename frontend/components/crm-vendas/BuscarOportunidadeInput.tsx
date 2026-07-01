'use client';

import { useCallback } from 'react';
import apiClient from '@/lib/api-client';
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
  const cliente = item.lead_empresa || item.lead_nome;
  const valor = item.valor
    ? ` — R$ ${parseFloat(item.valor).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
    : '';
  return cliente ? `${item.titulo} (${cliente})${valor}` : `${item.titulo}${valor}`;
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
    const res = await apiClient.get<{ titulo: string }>(`/crm-vendas/oportunidades/${id}/`);
    return { label: res.data.titulo };
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
