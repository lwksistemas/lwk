import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';

export type CrmTipoDocumentoAssinatura = 'proposta' | 'contrato';

/**
 * Após PUT de proposta/contrato em fluxo de assinatura, pergunta se reenvia o e-mail com novo link.
 */
export async function reenviarAssinaturaAposEdicaoSeNecessario(
  tipo: CrmTipoDocumentoAssinatura,
  documentoId: number,
  statusAssinaturaAntes: string | undefined
): Promise<void> {
  if (statusAssinaturaAntes !== 'aguardando_cliente' && statusAssinaturaAntes !== 'aguardando_vendedor') {
    return;
  }
  const docLabel = tipo === 'proposta' ? 'A proposta' : 'O contrato';
  const foiAlterado = tipo === 'proposta' ? 'foi alterada' : 'foi alterado';
  const textoConfirm =
    statusAssinaturaAntes === 'aguardando_cliente'
      ? `${docLabel} ${foiAlterado}. Deseja reenviar ao cliente o e-mail com o link de assinatura digital?`
      : `${docLabel} ${foiAlterado}. Deseja reenviar ao vendedor o e-mail com o link de assinatura digital?`;
  if (!window.confirm(textoConfirm)) return;

  const plural = tipo === 'proposta' ? 'propostas' : 'contratos';
  try {
    const res = await apiClient.post<{ message?: string }>(
      `/crm-vendas/${plural}/${documentoId}/reenviar_para_assinatura/`
    );
    alert(res.data.message || 'Link reenviado.');
  } catch (err: unknown) {
    alert(getCrmApiErrorDetail(err, 'Erro ao reenviar assinatura.'));
  }
}
