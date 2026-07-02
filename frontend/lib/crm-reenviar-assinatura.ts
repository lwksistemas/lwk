import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';

export type CrmTipoDocumentoAssinatura = 'proposta' | 'contrato';

export function deveConfirmarReenvioAssinatura(statusAssinaturaAntes: string | undefined): boolean {
  return (
    statusAssinaturaAntes === 'aguardando_cliente' ||
    statusAssinaturaAntes === 'aguardando_vendedor'
  );
}

export function textoConfirmacaoReenvioAssinatura(
  tipo: CrmTipoDocumentoAssinatura,
  statusAssinaturaAntes: string | undefined,
): string {
  const docLabel = tipo === 'proposta' ? 'A proposta' : 'O contrato';
  const foiAlterado = tipo === 'proposta' ? 'foi alterada' : 'foi alterado';
  if (statusAssinaturaAntes === 'aguardando_cliente') {
    return `${docLabel} ${foiAlterado}. Deseja reenviar ao cliente o e-mail com o link de assinatura digital?`;
  }
  return `${docLabel} ${foiAlterado}. Deseja reenviar ao vendedor o e-mail com o link de assinatura digital?`;
}

export async function executarReenvioAssinatura(
  tipo: CrmTipoDocumentoAssinatura,
  documentoId: number,
): Promise<string> {
  const plural = tipo === 'proposta' ? 'propostas' : 'contratos';
  const res = await apiClient.post<{ message?: string }>(
    `/crm-vendas/${plural}/${documentoId}/reenviar_para_assinatura/`,
  );
  return res.data.message || 'Link reenviado.';
}

export function mensagemErroReenvioAssinatura(err: unknown): string {
  return getCrmApiErrorDetail(err, 'Erro ao reenviar assinatura.');
}

/** @deprecated Use deveConfirmarReenvioAssinatura + modal + executarReenvioAssinatura */
export async function reenviarAssinaturaAposEdicaoSeNecessario(
  tipo: CrmTipoDocumentoAssinatura,
  documentoId: number,
  statusAssinaturaAntes: string | undefined,
): Promise<void> {
  if (!deveConfirmarReenvioAssinatura(statusAssinaturaAntes)) return;
  const textoConfirm = textoConfirmacaoReenvioAssinatura(tipo, statusAssinaturaAntes);
  if (!window.confirm(textoConfirm)) return;
  await executarReenvioAssinatura(tipo, documentoId);
}
