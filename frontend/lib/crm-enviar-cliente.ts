import apiClient from '@/lib/api-client';

/** Segmento da API REST para listagens de documentos (propostas | contratos). */
export type CrmDocumentosApiSegment = 'propostas' | 'contratos';

export type CrmEnviarClienteContext = {
  statusAssinatura?: string;
  leadEmail?: string;
  leadTelefone?: string;
  vendedorEmail?: string;
  vendedorTelefone?: string;
};

type DocumentoApi = {
  status_assinatura?: string;
  lead_email?: string;
  lead_telefone?: string;
  vendedor_email?: string;
  vendedor_telefone?: string;
};

function erroApi(detail: string): Error {
  return Object.assign(new Error(detail), {
    response: { data: { detail } },
  });
}

async function carregarContextoDocumento(
  segment: CrmDocumentosApiSegment,
  documentoId: number,
  ctx?: CrmEnviarClienteContext,
): Promise<Required<Pick<CrmEnviarClienteContext, 'statusAssinatura' | 'leadEmail' | 'leadTelefone' | 'vendedorEmail' | 'vendedorTelefone'>>> {
  const res = await apiClient.get<DocumentoApi>(`/crm-vendas/${segment}/${documentoId}/`);
  const d = res.data;
  return {
    statusAssinatura: ctx?.statusAssinatura ?? d.status_assinatura ?? 'rascunho',
    leadEmail: ctx?.leadEmail ?? d.lead_email ?? '',
    leadTelefone: ctx?.leadTelefone ?? d.lead_telefone ?? '',
    vendedorEmail: ctx?.vendedorEmail ?? d.vendedor_email ?? '',
    vendedorTelefone: ctx?.vendedorTelefone ?? d.vendedor_telefone ?? '',
  };
}

function validarContato(
  canal: 'email' | 'whatsapp',
  ctx: CrmEnviarClienteContext,
  quem: 'cliente' | 'vendedor',
): void {
  if (quem === 'cliente') {
    if (canal === 'email' && !(ctx.leadEmail || '').trim()) {
      throw erroApi('Lead não possui e-mail cadastrado.');
    }
    if (canal === 'whatsapp' && !(ctx.leadTelefone || '').trim()) {
      throw erroApi('Lead não possui telefone cadastrado.');
    }
    return;
  }
  if (canal === 'email' && !(ctx.vendedorEmail || '').trim()) {
    throw erroApi('Vendedor não possui e-mail cadastrado.');
  }
  if (canal === 'whatsapp' && !(ctx.vendedorTelefone || '').trim()) {
    throw erroApi('Vendedor não possui telefone cadastrado.');
  }
}

/** Rótulos da coluna Enviar conforme etapa da assinatura. */
export function crmAssinaturaColunaLabels(statusAssinatura?: string): {
  titulo: string;
  subtitulo?: string;
} {
  if (statusAssinatura === 'aguardando_vendedor') {
    return { titulo: 'Vendedor assinar' };
  }
  if (statusAssinatura === 'aguardando_cliente') {
    return { titulo: 'Cliente assinar', subtitulo: 'Reenviar' };
  }
  if (statusAssinatura === 'concluido') {
    return { titulo: '' };
  }
  return { titulo: 'Cliente assinar', subtitulo: 'Vendedor: mesmo canal' };
}

export function crmAssinaturaBotaoTitle(
  canal: 'email' | 'whatsapp',
  statusAssinatura?: string,
): string {
  const meio = canal === 'whatsapp' ? 'WhatsApp' : 'e-mail';
  if (statusAssinatura === 'aguardando_vendedor') {
    return `Reenviar link de assinatura ao vendedor por ${meio}`;
  }
  if (statusAssinatura === 'aguardando_cliente') {
    return `Reenviar link de assinatura ao cliente por ${meio}`;
  }
  return `Enviar link ao cliente por ${meio} — vendedor receberá por ${meio} após o cliente assinar`;
}

/**
 * Envia ou reenvia link de assinatura digital.
 * Cliente e vendedor usam o mesmo canal (e-mail ou WhatsApp).
 */
async function crmEnviarAssinatura(
  segment: CrmDocumentosApiSegment,
  documentoId: number,
  canal: 'email' | 'whatsapp',
  ctx?: CrmEnviarClienteContext,
): Promise<string> {
  const fullCtx = await carregarContextoDocumento(segment, documentoId, ctx);
  const status = fullCtx.statusAssinatura || 'rascunho';
  const base = `/crm-vendas/${segment}/${documentoId}`;

  if (status === 'concluido') {
    throw erroApi('Assinatura já concluída.');
  }

  if (status === 'rascunho') {
    validarContato(canal, fullCtx, 'cliente');
    validarContato(canal, fullCtx, 'vendedor');
    const res = await apiClient.post<{ message?: string }>(`${base}/enviar_para_assinatura/`, {
      canal,
      canal_vendedor: canal,
    });
    const meio = canal === 'whatsapp' ? 'WhatsApp' : 'e-mail';
    return res.data.message || `Link enviado ao cliente por ${meio}. Vendedor assinará pelo mesmo canal.`;
  }

  if (status === 'aguardando_cliente') {
    validarContato(canal, fullCtx, 'cliente');
    const res = await apiClient.post<{ message?: string }>(`${base}/reenviar_para_assinatura/`, { canal });
    return res.data.message || 'Link reenviado ao cliente.';
  }

  if (status === 'aguardando_vendedor') {
    validarContato(canal, fullCtx, 'vendedor');
    const res = await apiClient.post<{ message?: string }>(`${base}/reenviar_para_assinatura/`, { canal });
    return res.data.message || 'Link reenviado ao vendedor.';
  }

  throw erroApi('Status de assinatura não permite envio.');
}

/**
 * Envia proposta/contrato para assinatura (e-mail ou WhatsApp).
 * O vendedor receberá o link pelo mesmo canal escolhido para o cliente.
 */
export async function crmEnviarCliente(
  segment: CrmDocumentosApiSegment,
  documentoId: number,
  canal: 'email' | 'whatsapp',
  ctx?: CrmEnviarClienteContext,
): Promise<string> {
  return crmEnviarAssinatura(segment, documentoId, canal, ctx);
}
