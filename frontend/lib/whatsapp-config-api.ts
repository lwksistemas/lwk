import axios from 'axios';
import apiClient from '@/lib/api-client';
import { getPrimaryApiBaseUrl } from '@/lib/api-base';
import {
  isTipoClinicaBeleza,
  isTipoClinicaEstetica,
  isTipoCRMVendas,
} from '@/lib/loja-tipo';

export interface WhatsAppConnectionState {
  provider?: string;
  connection_status: 'disconnected' | 'qr_pending' | 'connected' | 'error';
  connected_phone?: string;
  connected_at?: string | null;
  qr_base64?: string | null;
  pairing_code?: string | null;
  error?: string | null;
  evolution_available?: boolean;
}

export interface WhatsAppConfigData extends WhatsAppConnectionState {
  enviar_confirmacao: boolean;
  enviar_lembrete_24h: boolean;
  enviar_lembrete_2h: boolean;
  enviar_cobranca: boolean;
  enviar_lembrete_tarefas?: boolean;
  enviar_proposta_whatsapp?: boolean;
  enviar_contrato_whatsapp?: boolean;
  enviar_termo_consentimento_whatsapp?: boolean;
  mensagem_confirmacao_agenda?: string;
  whatsapp_numero: string;
  whatsapp_ativo: boolean;
  whatsapp_phone_id: string;
  whatsapp_token_set: boolean;
  whatsapp_provider?: 'meta' | 'evolution';
  evolution_available?: boolean;
}

const BASE = '/whatsapp/config';

/** Consulta health público — evolution_available não depende de login/tenant. */
export async function fetchEvolutionAvailableFromHealth(): Promise<boolean> {
  try {
    const healthUrl = `${getPrimaryApiBaseUrl()}/superadmin/health/`;
    const response = await axios.get<{ evolution_available?: boolean }>(healthUrl, { timeout: 8000 });
    return !!response.data?.evolution_available;
  } catch {
    return false;
  }
}

export const whatsappConfigApi = {
  get: () => apiClient.get<WhatsAppConfigData>(`${BASE}/`).then((r) => r.data),
  save: (body: Record<string, unknown>) =>
    apiClient.patch<WhatsAppConfigData>(`${BASE}/`, body).then((r) => r.data),
  connection: (withQr = false) =>
    apiClient
      .get<WhatsAppConnectionState>(`${BASE}/connection/`, { params: withQr ? { qr: '1' } : {} })
      .then((r) => r.data),
  connect: () => apiClient.post<WhatsAppConnectionState>(`${BASE}/connect/`).then((r) => r.data),
  disconnect: () => apiClient.post<WhatsAppConnectionState>(`${BASE}/disconnect/`).then((r) => r.data),
};

export type WhatsAppConfigVariant = 'clinica' | 'crm' | 'generic';

export interface WhatsAppFeatureFlags {
  showAgendaMessages: boolean;
  showCrmTasks: boolean;
  showCrmDocumentos: boolean;
  showTermoConsentimento: boolean;
  variant: WhatsAppConfigVariant;
}

export function whatsappFeaturesForTipoLoja(tipoLojaNome?: string | null): WhatsAppFeatureFlags {
  const tipo = tipoLojaNome || '';
  if (isTipoClinicaBeleza(tipo) || isTipoClinicaEstetica(tipo)) {
    return {
      showAgendaMessages: true,
      showCrmTasks: false,
      showCrmDocumentos: false,
      showTermoConsentimento: true,
      variant: 'clinica',
    };
  }
  if (isTipoCRMVendas(tipo)) {
    return {
      showAgendaMessages: false,
      showCrmTasks: true,
      showCrmDocumentos: true,
      showTermoConsentimento: false,
      variant: 'crm',
    };
  }
  return {
    showAgendaMessages: false,
    showCrmTasks: false,
    showCrmDocumentos: false,
    showTermoConsentimento: false,
    variant: 'generic',
  };
}
