/**
 * Sincronização automática da fila offline quando voltar online.
 * Processa agendamentos (e outros itens) enfileirados e limpa a fila.
 */

import { obterFilaSync, removerItemFilaSync } from "./offline-db";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders, clinicaBelezaFetch } from "./clinica-beleza-api";

let syncInProgress = false;

export async function sincronizarFila(): Promise<{ enviados: number; erros: number }> {
  if (syncInProgress) {
    console.log("⏳ [offline-sync] Sincronização já em andamento, aguardando...");
    return { enviados: 0, erros: 0 };
  }
  if (typeof window === "undefined" || !navigator.onLine) {
    console.log("📵 [offline-sync] Offline ou não é navegador, pulando sincronização");
    return { enviados: 0, erros: 0 };
  }

  syncInProgress = true;
  let enviados = 0;
  let erros = 0;

  try {
    const pendentes = await obterFilaSync();
    console.log(`📋 [offline-sync] ${pendentes.length} ${pendentes.length === 1 ? 'item pendente' : 'itens pendentes'} na fila`);

    for (const item of pendentes) {
      const key = item.id;
      if (key == null) continue;

      console.log(`🔄 [offline-sync] Processando ${item.tipo} (key: ${key})...`);

      try {
        if (item.tipo === "agendamento") {
          const baseURL = getClinicaBelezaBaseUrl();
          console.log(`📤 [offline-sync] Enviando agendamento para ${baseURL}/agenda/create/`);
          console.log(`📦 [offline-sync] Payload:`, item.payload);
          try {
            const res = await clinicaBelezaFetch("/agenda/create/", {
              method: "POST",
              body: JSON.stringify(item.payload),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              console.error(`❌ [offline-sync] Resposta de erro (${res.status}):`, data);
              if (res.status === 400) {
                const errorMsg = data.error || JSON.stringify(data);
                console.warn(`⚠️ [offline-sync] Erro de validação (400), mantendo na fila para retry: ${errorMsg}`);
                erros++;
                if (typeof window !== "undefined") {
                  alert(`❌ Agendamento não pôde ser sincronizado:\n\n${errorMsg}\n\nO item permanece na fila. Corrija (ex.: outro horário) e clique em 🔄 Sincronizar agora.`);
                }
                continue;
              }
              throw new Error(data.error || `Erro ${res.status}`);
            }
            await removerItemFilaSync(key);
            console.log(`✅ [offline-sync] Agendamento sincronizado com sucesso`);
            enviados++;
          } catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            if (msg === "SESSION_ENDED" || msg.includes("401") || msg.includes("sessão")) {
              console.warn(`⚠️ [offline-sync] Sessão expirada ao sincronizar agendamento. Faça login novamente.`);
              if (typeof window !== "undefined") {
                alert("Sessão expirada. Faça login novamente para sincronizar o agendamento pendente.");
              }
            }
            throw e;
          }
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
              if (res.status === 400) {
                console.warn(`⚠️ [offline-sync] Erro de validação paciente (400), removendo da fila`);
                await removerItemFilaSync(key);
                erros++;
                continue;
              }
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
              if (res.status === 400 || res.status === 404) {
                console.warn(`⚠️ [offline-sync] Erro paciente (${res.status}), removendo da fila`);
                await removerItemFilaSync(key);
                erros++;
                continue;
              }
              throw new Error(typeof data.detail === "string" ? data.detail : data.error || `Erro ${res.status}`);
            }
          }
          await removerItemFilaSync(key);
          console.log(`✅ [offline-sync] Paciente sincronizado com sucesso`);
          enviados++;
        }

        if (item.tipo === "profissional") {
          const baseURL = getClinicaBelezaBaseUrl();
          const headers = getClinicaBelezaHeaders();
          const payload = item.payload as { action: "create" | "update"; id?: number; body: Record<string, unknown> };
          if (payload.action === "create") {
            const res = await fetch(`${baseURL}/professionals/`, {
              method: "POST",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              const msg = data.phone?.[0] ?? data.email?.[0] ?? data.name?.[0] ?? (typeof data.detail === "string" ? data.detail : data.error) ?? `Erro ${res.status}`;
              throw new Error(String(msg));
            }
          } else if (payload.action === "update" && payload.id != null && payload.id > 0) {
            const res = await fetch(`${baseURL}/professionals/${payload.id}/`, {
              method: "PUT",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              const msg = data.phone?.[0] ?? data.email?.[0] ?? data.name?.[0] ?? (typeof data.detail === "string" ? data.detail : data.error) ?? `Erro ${res.status}`;
              throw new Error(String(msg));
            }
          }
          await removerItemFilaSync(key);
          console.log(`✅ [offline-sync] Profissional sincronizado com sucesso`);
          enviados++;
        }

        if (item.tipo === "procedimento") {
          const baseURL = getClinicaBelezaBaseUrl();
          const headers = getClinicaBelezaHeaders();
          const payload = item.payload as { action: "create" | "update"; id?: number; body: Record<string, unknown> };
          if (payload.action === "create") {
            const res = await fetch(`${baseURL}/procedures/`, {
              method: "POST",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              const msg = data.name?.[0] ?? (typeof data.detail === "string" ? data.detail : data.error) ?? `Erro ${res.status}`;
              throw new Error(String(msg));
            }
          } else if (payload.action === "update" && payload.id != null && payload.id > 0) {
            const res = await fetch(`${baseURL}/procedures/${payload.id}/`, {
              method: "PUT",
              headers,
              body: JSON.stringify(payload.body),
            });
            if (!res.ok) {
              const data = await res.json().catch(() => ({}));
              const msg = data.name?.[0] ?? (typeof data.detail === "string" ? data.detail : data.error) ?? `Erro ${res.status}`;
              throw new Error(String(msg));
            }
          }
          await removerItemFilaSync(key);
          console.log(`✅ [offline-sync] Procedimento sincronizado com sucesso`);
          enviados++;
        }
      } catch (e) {
        console.error(`❌ [offline-sync] Erro ao enviar ${item.tipo}:`, e);
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

  window.addEventListener("online", async () => {
    console.log("🌐 [offline-sync] Internet voltou! Iniciando sincronização...");
    
    // Aguardar um pouco para garantir que a conexão está estável
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const { enviados, erros } = await sincronizarFila();
    
    console.log(`✅ [offline-sync] Sincronização concluída: ${enviados} enviados, ${erros} erros`);
    
    if (enviados > 0) {
      // Notificar que a sincronização foi concluída
      window.dispatchEvent(new CustomEvent("offline-sync-done", { detail: { enviados, erros } }));
      
      // Mostrar notificação ao usuário
      if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
        new Notification("Sincronização concluída", {
          body: `${enviados} ${enviados === 1 ? 'item foi sincronizado' : 'itens foram sincronizados'} com sucesso!`,
          icon: "/icon-192x192.png",
        });
      }
    }
    
    if (erros > 0) {
      console.warn(`⚠️ [offline-sync] ${erros} ${erros === 1 ? 'erro ocorreu' : 'erros ocorreram'} durante a sincronização`);
      
      // Mostrar alerta ao usuário sobre erros
      if (typeof window !== "undefined") {
        alert(`⚠️ Atenção: ${erros} ${erros === 1 ? 'item falhou' : 'itens falharam'} ao sincronizar.\n\nVerifique o console (F12) para mais detalhes ou use o botão 🗑️ para limpar a fila.`);
      }
      
      // Disparar evento mesmo com erros para atualizar a interface
      window.dispatchEvent(new CustomEvent("offline-sync-done", { detail: { enviados, erros } }));
    }
  });
}
