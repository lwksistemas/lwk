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

  // Callbacks estáveis: não depender de formData (evita recarregar proposta/contrato a cada tecla).
  const loadLeadInfo = useCallback(
    async (leadId: number) => {
      if (!leadId) {
        setLeadInfo(null);
        return;
      }
      try {
        const res = await apiClient.get<LeadInfo>(`/crm-vendas/leads/${leadId}/`);
        setLeadInfo(res.data);
        const nome = (res.data.nome || '').trim();
        if (nome) {
          setFormData((f) =>
            f.nome_cliente_assinatura ? f : { ...f, nome_cliente_assinatura: nome },
          );
        }
      } catch {
        setLeadInfo(null);
      }
    },
    [setFormData],
  );

  const loadVendedorInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<{ nome: string }>('/crm-vendas/vendedores/me/');
      const nome = (res.data.nome || '').trim();
      setVendedorNome(nome);
      if (nome) {
        setFormData((f) =>
          f.nome_vendedor_assinatura ? f : { ...f, nome_vendedor_assinatura: nome },
        );
      }
    } catch {
      setVendedorNome('');
    }
  }, [setFormData]);

  return { leadInfo, setLeadInfo, vendedorNome, loadLeadInfo, loadVendedorInfo };
}
