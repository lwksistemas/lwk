/**
 * Hook reutilizável para salvar entidades com suporte offline.
 *
 * Encapsula:
 * 1. Detecção de estado offline
 * 2. Save direto offline se browser estiver offline
 * 3. Tentativa de save online → fallback offline se falhar por rede
 * 4. Gestão da fila de sincronização (IndexedDB)
 * 5. Atualização otimista da lista local (opcional)
 *
 * Consumidores: pacientes, procedimentos, profissionais
 */

import { useState } from 'react';
import {
  adicionarNaFilaSync,
  getLojaSlug,
  type FilaSyncItem,
} from '@/lib/offline-db';
import {
  bloquearCriacaoDuplicadaOffline,
  deveVerificarDuplicataOffline,
  gerarIdTemporarioOffline,
  isBrowserOffline,
  isFetchNetworkError,
  isRegistroPendenteSync,
  temDuplicataNaLista,
} from '@/lib/clinica-beleza-offline';
import { logger } from '@/lib/logger';

export type OfflineSaveResult =
  | { ok: true; offline: false }
  | { ok: true; offline: true; message: string }
  | { ok: false; offline: false; error: string }
  | { ok: false; offline: true; error: string };

export interface UseOfflineSaveOptions<T extends { id: number }> {
  entityType: FilaSyncItem['tipo'];
  saveOnline: (body: Record<string, unknown>, editing: T | null) => Promise<void>;
  /** Lista local — omitir em formulários sem lista (ex.: profissional) */
  list?: T[];
  setList?: (list: T[]) => void;
  saveOffline?: (list: T[]) => Promise<void>;
  buildNewEntity?: (body: Record<string, unknown>, tempId: number) => T;
  duplicatePredicate?: (item: T) => boolean;
  offlineMessage?: string;
}

export function useOfflineSave<T extends { id: number }>(
  options: UseOfflineSaveOptions<T>,
) {
  const {
    entityType,
    saveOnline,
    list = [],
    setList,
    saveOffline,
    buildNewEntity,
    duplicatePredicate,
    offlineMessage = 'Salvo offline. Será sincronizado quando você estiver online.',
  } = options;

  const [saving, setSaving] = useState(false);
  const hasOptimisticList = Boolean(setList && saveOffline && buildNewEntity);

  const _saveOfflineQueue = async (
    body: Record<string, unknown>,
    editing: T | null,
  ): Promise<OfflineSaveResult> => {
    const lojaSlug = getLojaSlug();

    if (editing && !isRegistroPendenteSync(editing.id)) {
      await adicionarNaFilaSync({
        tipo: entityType,
        payload: { action: 'update', id: editing.id, body },
        lojaSlug,
      });
      if (hasOptimisticList && setList && saveOffline) {
        const updated = list.map((item) =>
          item.id === editing.id ? { ...item, ...body } : item,
        ) as T[];
        setList(updated);
        await saveOffline(updated);
      }
    } else {
      await adicionarNaFilaSync({
        tipo: entityType,
        payload: { action: 'create', body },
        lojaSlug,
      });
      if (hasOptimisticList && setList && saveOffline && buildNewEntity) {
        const tempId = gerarIdTemporarioOffline();
        const newEntity = buildNewEntity(body, tempId);
        const updated = [newEntity, ...list];
        setList(updated);
        await saveOffline(updated);
      }
    }

    return { ok: true, offline: true, message: offlineMessage };
  };

  const save = async (
    body: Record<string, unknown>,
    editing: T | null,
  ): Promise<OfflineSaveResult> => {
    setSaving(true);

    try {
      if (isBrowserOffline()) {
        if (duplicatePredicate && deveVerificarDuplicataOffline(editing)) {
          if (temDuplicataNaLista(list, duplicatePredicate)) {
            return { ok: false, offline: true, error: 'Este registro já foi adicionado. Aguarde a sincronização.' };
          }
        }
        return await _saveOfflineQueue(body, editing);
      }

      await saveOnline(body, editing);
      return { ok: true, offline: false };
    } catch (e: unknown) {
      if (e instanceof Error && e.message === 'SESSION_ENDED') {
        return { ok: false, offline: false, error: '' };
      }

      const err = e && typeof e === 'object' ? (e as Record<string, unknown>) : {};
      const msg =
        (typeof err?.error === 'string' ? err.error : '') ||
        (typeof err?.detail === 'string' ? err.detail : '') ||
        (e instanceof Error ? e.message : 'Erro ao salvar');

      if (isFetchNetworkError(msg)) {
        if (duplicatePredicate && bloquearCriacaoDuplicadaOffline(editing, list, duplicatePredicate)) {
          return { ok: false, offline: true, error: 'Este registro já foi adicionado offline. Aguarde a sincronização.' };
        }
        try {
          return await _saveOfflineQueue(body, editing);
        } catch (offlineErr) {
          logger.warn('Erro ao salvar offline após falha de rede:', offlineErr);
          return { ok: false, offline: true, error: 'Sem conexão. Não foi possível salvar offline.' };
        }
      }

      return { ok: false, offline: false, error: msg };
    } finally {
      setSaving(false);
    }
  };

  return { save, saving };
}
