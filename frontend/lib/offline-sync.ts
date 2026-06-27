/**
 * Sincronização automática da fila offline quando voltar online.
 */

import { obterFilaSync, removerItemFilaSync } from './offline-db';
import { clinicaBelezaFetch } from './clinica-beleza-api';
import { isBrowserOffline } from './clinica-beleza-offline';
import { logger } from './logger';

let syncInProgress = false;

type OfflinePayload = { action: 'create' | 'update'; id?: number; body: Record<string, unknown> };

async function syncEntityItem(
  tipo: 'paciente' | 'profissional' | 'procedimento',
  pathBase: string,
  payload: OfflinePayload,
): Promise<void> {
  if (payload.action === 'create') {
    const res = await clinicaBelezaFetch(pathBase, {
      method: 'POST',
      body: JSON.stringify(payload.body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400) {
        logger.warn(`⚠️ [offline-sync] Erro de validação ${tipo} (400), removendo da fila`);
        return;
      }
      throw new Error(extractApiError(data, res.status));
    }
    return;
  }
  if (payload.action === 'update' && payload.id != null && payload.id > 0) {
    const res = await clinicaBelezaFetch(`${pathBase}${payload.id}/`, {
      method: 'PUT',
      body: JSON.stringify(payload.body),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      if (res.status === 400 || res.status === 404) {
        logger.warn(`⚠️ [offline-sync] Erro ${tipo} (${res.status}), removendo da fila`);
        return;
      }
      throw new Error(extractApiError(data, res.status));
    }
  }
}

function extractApiError(data: Record<string, unknown>, status: number): string {
  const fieldMsg = ['phone', 'email', 'name'].map((k) => {
    const v = data[k];
    return Array.isArray(v) ? v[0] : undefined;
  }).find(Boolean);
  if (fieldMsg) return String(fieldMsg);
  if (typeof data.detail === 'string') return data.detail;
  if (typeof data.error === 'string') return data.error;
  return `Erro ${status}`;
}

export async function sincronizarFila(): Promise<{ enviados: number; erros: number }> {
  if (syncInProgress) {
    logger.log('⏳ [offline-sync] Sincronização já em andamento, aguardando...');
    return { enviados: 0, erros: 0 };
  }
  if (typeof window === 'undefined' || isBrowserOffline()) {
    logger.log('📵 [offline-sync] Offline ou não é navegador, pulando sincronização');
    return { enviados: 0, erros: 0 };
  }

  syncInProgress = true;
  let enviados = 0;
  let erros = 0;

  try {
    const pendentes = await obterFilaSync();
    logger.log(`📋 [offline-sync] ${pendentes.length} ${pendentes.length === 1 ? 'item pendente' : 'itens pendentes'} na fila`);

    for (const item of pendentes) {
      const key = item.id;
      if (key == null) continue;

      logger.log(`🔄 [offline-sync] Processando ${item.tipo} (key: ${key})...`);

      try {
        if (item.tipo === 'agendamento') {
          logger.log('📤 [offline-sync] Enviando agendamento para /agenda/create/');
          const res = await clinicaBelezaFetch('/agenda/create/', {
            method: 'POST',
            body: JSON.stringify(item.payload),
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            logger.warn(`❌ [offline-sync] Resposta de erro (${res.status}):`, data);
            if (res.status === 400) {
              const errorMsg = (data as { error?: string }).error || JSON.stringify(data);
              logger.warn(`⚠️ [offline-sync] Erro de validação (400), mantendo na fila: ${errorMsg}`);
              erros++;
              if (typeof window !== 'undefined') {
                alert(`❌ Agendamento não pôde ser sincronizado:\n\n${errorMsg}\n\nO item permanece na fila. Corrija (ex.: outro horário) e clique em 🔄 Sincronizar agora.`);
              }
              continue;
            }
            throw new Error((data as { error?: string }).error || `Erro ${res.status}`);
          }
          await removerItemFilaSync(key);
          logger.log('✅ [offline-sync] Agendamento sincronizado com sucesso');
          enviados++;
          continue;
        }

        if (item.tipo === 'paciente') {
          await syncEntityItem('paciente', '/patients/', item.payload as OfflinePayload);
          await removerItemFilaSync(key);
          logger.log('✅ [offline-sync] Paciente sincronizado com sucesso');
          enviados++;
          continue;
        }

        if (item.tipo === 'profissional') {
          await syncEntityItem('profissional', '/professionals/', item.payload as OfflinePayload);
          await removerItemFilaSync(key);
          logger.log('✅ [offline-sync] Profissional sincronizado com sucesso');
          enviados++;
          continue;
        }

        if (item.tipo === 'procedimento') {
          await syncEntityItem('procedimento', '/procedures/', item.payload as OfflinePayload);
          await removerItemFilaSync(key);
          logger.log('✅ [offline-sync] Procedimento sincronizado com sucesso');
          enviados++;
          continue;
        }

        if (item.tipo === 'consulta') {
          logger.log('📤 [offline-sync] Enviando consulta para /consultas/');
          const res = await clinicaBelezaFetch('/consultas/', {
            method: 'POST',
            body: JSON.stringify(item.payload),
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            if (res.status === 400) {
              logger.warn(`⚠️ [offline-sync] Erro de validação consulta (400), removendo da fila`);
              continue;
            }
            throw new Error((data as { error?: string }).error || `Erro ${res.status}`);
          }
          await removerItemFilaSync(key);
          logger.log('✅ [offline-sync] Consulta sincronizada com sucesso');
          enviados++;
        }
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        if (msg === 'SESSION_ENDED' || msg.includes('401') || msg.includes('sessão')) {
          logger.warn('⚠️ [offline-sync] Sessão expirada. Faça login novamente.');
          if (typeof window !== 'undefined') {
            alert('Sessão expirada. Faça login novamente para sincronizar itens pendentes.');
          }
        }
        logger.warn(`❌ [offline-sync] Erro ao enviar ${item.tipo}:`, e);
        erros++;
      }
    }
  } finally {
    syncInProgress = false;
  }

  return { enviados, erros };
}

let registered = false;
let wasOffline = false;

async function executarSincronizacaoAutomatica(): Promise<void> {
  const pendentes = await obterFilaSync();
  if (pendentes.length === 0) return;

  logger.log('🌐 [offline-sync] Conexão detectada. Sincronização automática...');
  await new Promise((r) => setTimeout(r, 800));

  const { enviados, erros } = await sincronizarFila();
  logger.log(`✅ [offline-sync] Sincronização automática: ${enviados} enviados, ${erros} erros`);

  if (enviados > 0 || erros > 0) {
    window.dispatchEvent(new CustomEvent('offline-sync-done', { detail: { enviados, erros } }));
  }
  if (enviados > 0 && typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    new Notification('Sincronização concluída', {
      body: `${enviados} ${enviados === 1 ? 'item foi sincronizado' : 'itens foram sincronizados'} com sucesso!`,
      icon: '/icon-192x192.png',
    });
  }
  if (erros > 0 && typeof window !== 'undefined') {
    alert(
      `⚠️ Atenção: ${erros} ${erros === 1 ? 'item falhou' : 'itens falharam'} ao sincronizar.\n\nVerifique o console (F12) ou use o botão 🗑️ para limpar a fila.`,
    );
  }
}

export function registrarSincronizacaoAoVoltarOnline(): void {
  if (typeof window === 'undefined' || registered) return;
  registered = true;
  wasOffline = isBrowserOffline();

  window.addEventListener('online', () => {
    logger.log('🌐 [offline-sync] Evento online disparado. Iniciando sincronização automática...');
    executarSincronizacaoAutomatica();
    wasOffline = false;
  });

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'visible' || isBrowserOffline()) return;
    obterFilaSync().then((pendentes) => {
      if (pendentes.length > 0) {
        logger.log('🌐 [offline-sync] Aba ativa e online com itens na fila. Sincronizando...');
        executarSincronizacaoAutomatica();
      }
    });
  });

  const INTERVALO_MS = 15000;
  setInterval(async () => {
    if (isBrowserOffline()) {
      wasOffline = true;
      return;
    }
    const pendentes = await obterFilaSync();
    if (pendentes.length === 0) return;
    if (wasOffline) {
      wasOffline = false;
      logger.log('🌐 [offline-sync] Conexão detectada (verificação periódica). Sincronizando...');
      executarSincronizacaoAutomatica();
    }
  }, INTERVALO_MS);

  if (!isBrowserOffline()) {
    obterFilaSync().then((pendentes) => {
      if (pendentes.length > 0) {
        logger.log('🌐 [offline-sync] Página carregada online com itens na fila. Sincronizando...');
        executarSincronizacaoAutomatica();
      }
    });
  }
}
