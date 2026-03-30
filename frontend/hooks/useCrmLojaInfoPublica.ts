import { useState, useCallback } from 'react';
import apiClient from '@/lib/api-client';
import type { LojaInfo } from '@/components/crm-vendas/modals/ModalPropostaForm';

/** Dados públicos da loja (slug) para modais de proposta/contrato CRM. */
export function useCrmLojaInfoPublica(slug: string) {
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);

  const loadLojaInfo = useCallback(async () => {
    try {
      const res = await apiClient.get<LojaInfo>(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(res.data);
    } catch {
      setLojaInfo(null);
    }
  }, [slug]);

  return { lojaInfo, loadLojaInfo };
}
