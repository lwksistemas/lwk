import { useState, useCallback, type Dispatch, type SetStateAction } from 'react';
import apiClient from '@/lib/api-client';
import type { LeadInfo } from '@/components/crm-vendas/modals/ModalPropostaForm';

/** Campos de nome para assinatura presentes em FormDataProposta / FormDataContrato. */
type FormComNomesAssinatura = {
  nome_cliente_assinatura?: string;
  nome_vendedor_assinatura?: string;
};

/**
 * Carrega lead e vendedor atual para modais CRM e pré-preenche nomes de assinatura quando vazios.
 */
export function useCrmLeadEVendedorForm<T extends FormComNomesAssinatura>(
  formData: T,
  setFormData: Dispatch<SetStateAction<T>>
) {
  const [leadInfo, setLeadInfo] = useState<LeadInfo | null>(null);
  const [vendedorNome, setVendedorNome] = useState<string>('');

  const loadLeadInfo = useCallback(
    async (leadId: number) => {
      if (!leadId) {
        setLeadInfo(null);
        return;
      }
      try {
        const res = await apiClient.get<LeadInfo>(`/crm-vendas/leads/${leadId}/`);
        setLeadInfo(res.data);
        if (res.data.nome && !formData.nome_cliente_assinatura) {
          setFormData((f) => ({ ...f, nome_cliente_assinatura: res.data.nome }));
        }
      } catch {
        setLeadInfo(null);
      }
    },
    [formData.nome_cliente_assinatura, setFormData]
  );

  const loadVendedorInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<{ nome: string }>('/crm-vendas/vendedores/me/');
      setVendedorNome(res.data.nome);
      if (res.data.nome && !formData.nome_vendedor_assinatura) {
        setFormData((f) => ({ ...f, nome_vendedor_assinatura: res.data.nome }));
      }
    } catch {
      setVendedorNome('');
    }
  }, [formData.nome_vendedor_assinatura, setFormData]);

  return { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo };
}
