/**
 * Sincronização automática da fila offline quando voltar online.
 * Processa agendamentos (e outros itens) enfileirados e limpa a fila.
 */

import { obterFilaSync, removerItemFilaSync } from "./offline-db";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } from "./clinica-beleza-api";

let syncInProgress = false;

export async function sincronizarFila(): Promise<{ enviados: number; erros: number }> {
  if (syncInProgress) return { enviados: 0, erros: 0 };
  if (typeof window === "undefined" || !navigator.onLine) return { enviados: 0, erros: 0 };

  syncInProgress = true;
  let enviados = 0;
  let erros = 0;

  try {
    const pendentes = await obterFilaSync();

    for (const item of pendentes) {
      const key = item.id;
      if (key == null) continue;

      try {
        if (item.tipo === "agendamento") {
          const baseURL = getClinicaBelezaBaseUrl();
          const headers = getClinicaBelezaHeaders();
          const res = await fetch(`${baseURL}/agenda/create/`, {
            method: "POST",
            headers,
            body: JSON.stringify(item.payload),
          });
          if (!res.ok) {
            const data = await res.json().catch(() => ({}));
            throw new Error(data.error || `Erro ${res.status}`);
          }
          await removerItemFilaSync(key);
          enviados++;
        }

        if (item.tipo === "paciente") {
          const baseURL = getClinicaBelezaBaseUrl();
          const headers = getClinicaBelezaHeaders();
          const payload = item.payload as { action: "create" | "update"; id?: number; body: Record<string, unknown> };
          if (payload.action === "create") {
            const res = await fetch(`${baseURL}/patients/`, {
              method: "POST",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              throw new Error(typeof data.detail === "string" ? data.detail : data.error || `Erro ${res.status}`);
            }
          } else if (payload.action === "update" && payload.id != null) {
            const res = await fetch(`${baseURL}/patients/${payload.id}/`, {
              method: "PUT",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              throw new Error(typeof data.detail === "string" ? data.detail : data.error || `Erro ${res.status}`);
            }
          }
          await removerItemFilaSync(key);
          enviados++;
        }
      } catch (e) {
        console.warn("[offline-sync] Erro ao enviar item da fila:", e);
        erros++;
      }
    }
  } finally {
    syncInProgress = false;
  }

  return { enviados, erros };
}

let registered = false;

export function registrarSincronizacaoAoVoltarOnline(): void {
  if (typeof window === "undefined" || registered) return;
  registered = true;

  window.addEventListener("online", () => {
    sincronizarFila().then(({ enviados }) => {
      if (enviados > 0) {
        window.dispatchEvent(new CustomEvent("offline-sync-done", { detail: { enviados } }));
      }
    });
  });
}
