'use client';

import { useCallback } from 'react';
import apiClient from '@/lib/api-client';
import CrmSearchInput, { type CrmSearchInputProps } from '@/components/crm-vendas/CrmSearchInput';

export interface CrmContaBuscaItem {
  id: number;
  nome: string;
  segmento?: string;
  cnpj?: string;
}

function rotuloConta(conta: CrmContaBuscaItem): string {
  const extras: string[] = [];
  if (conta.cnpj) extras.push(conta.cnpj);
  if (conta.segmento) extras.push(conta.segmento);
  return extras.length ? `${conta.nome} — ${extras.join(' · ')}` : conta.nome;
}

interface BuscarContaInputProps {
  contaId: string;
  onContaChange: (id: string) => void;
  initialNome?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  limit?: number;
}

export default function BuscarContaInput({
  contaId,
  onContaChange,
  initialNome = '',
  placeholder = 'Buscar conta pelo nome, CNPJ ou e-mail...',
  required = false,
  disabled = false,
  className = '',
  inputClassName = '',
  limit = 10,
}: BuscarContaInputProps) {
  const fetchById = useCallback(async (id: string) => {
    const res = await apiClient.get<CrmContaBuscaItem>(`/crm-vendas/contas/${id}/`);
    return { label: res.data.nome };
  }, []);

  const fetchResults = useCallback(async (q: string, lim: number) => {
    const res = await apiClient.get<{ contas: CrmContaBuscaItem[] }>('/crm-vendas/busca/', {
      params: { q, limit: lim },
    });
    return res.data.contas ?? [];
  }, []);

  const searchProps: CrmSearchInputProps<CrmContaBuscaItem> = {
    selectedId: contaId,
    onSelectedIdChange: onContaChange,
    initialLabel: initialNome,
    placeholder,
    required,
    disabled,
    className,
    inputClassName,
    hiddenInputName: 'conta_id',
    limit,
    fetchById,
    fetchResults,
    getItemId: (c) => String(c.id),
    formatLabel: rotuloConta,
  };

  return <CrmSearchInput {...searchProps} />;
}
