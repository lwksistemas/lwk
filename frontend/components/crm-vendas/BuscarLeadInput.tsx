'use client';

import { useCallback } from 'react';
import apiClient from '@/lib/api-client';
import CrmSearchInput, { type CrmSearchInputProps } from '@/components/crm-vendas/CrmSearchInput';

export interface CrmLeadBuscaItem {
  id: number;
  nome: string;
  empresa: string;
  status?: string;
  cpf_cnpj?: string;
}

function rotuloLead(lead: CrmLeadBuscaItem): string {
  const empresa = (lead.empresa || '').trim();
  if (empresa && empresa.toLowerCase() !== (lead.nome || '').trim().toLowerCase()) {
    return `${lead.nome} — ${empresa}`;
  }
  if (lead.cpf_cnpj) {
    return `${lead.nome} — ${lead.cpf_cnpj}`;
  }
  return lead.nome;
}

interface BuscarLeadInputProps {
  leadId: string;
  onLeadChange: (id: string, lead?: CrmLeadBuscaItem) => void;
  initialNome?: string;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
  inputClassName?: string;
  limit?: number;
}

export default function BuscarLeadInput({
  leadId,
  onLeadChange,
  initialNome = '',
  placeholder = 'Buscar lead pelo nome, empresa ou CPF/CNPJ...',
  required = false,
  disabled = false,
  className = '',
  inputClassName = '',
  limit = 10,
}: BuscarLeadInputProps) {
  const fetchById = useCallback(async (id: string) => {
    const res = await apiClient.get<{ nome: string; empresa?: string }>(`/crm-vendas/leads/${id}/`);
    const label = res.data.empresa ? `${res.data.nome} — ${res.data.empresa}` : res.data.nome;
    return { label: res.data.nome, displayLabel: label };
  }, []);

  const fetchResults = useCallback(async (q: string, lim: number) => {
    const res = await apiClient.get<{ leads: CrmLeadBuscaItem[] }>('/crm-vendas/busca/', {
      params: { q, limit: lim },
    });
    return res.data.leads ?? [];
  }, []);

  const searchProps: CrmSearchInputProps<CrmLeadBuscaItem> = {
    selectedId: leadId,
    onSelectedIdChange: onLeadChange,
    initialLabel: initialNome,
    placeholder,
    required,
    disabled,
    className,
    inputClassName,
    hiddenInputName: 'lead_id',
    limit,
    fetchById,
    fetchResults,
    getItemId: (l) => String(l.id),
    formatLabel: rotuloLead,
    listClassName: 'rounded-lg',
  };

  return <CrmSearchInput {...searchProps} />;
}
