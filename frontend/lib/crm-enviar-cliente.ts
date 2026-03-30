import apiClient from '@/lib/api-client';

/** Segmento da API REST para listagens de documentos (propostas | contratos). */
export type CrmDocumentosApiSegment = 'propostas' | 'contratos';

/**
 * Envia proposta/contrato ao cliente por e-mail ou WhatsApp.
 * POST /crm-vendas/{segment}/{id}/enviar_cliente/
 */
export async function crmEnviarCliente(
  segment: CrmDocumentosApiSegment,
  documentoId: number,
  canal: 'email' | 'whatsapp'
): Promise<void> {
  await apiClient.post(`/crm-vendas/${segment}/${documentoId}/enviar_cliente/`, { canal });
}
