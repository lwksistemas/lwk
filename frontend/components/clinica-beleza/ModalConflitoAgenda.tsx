"use client";

/**
 * Modal de conflito de sincronização (offline/online).
 * Exibe comparação local vs servidor e permite "Usar servidor" ou "Usar minha versão".
 */

import { X, Server, Smartphone, AlertTriangle } from "lucide-react";

const STATUS_LABEL: Record<string, string> = {
  SCHEDULED: "Agendado",
  CONFIRMED: "Confirmado",
  PENDING: "Pendente",
  IN_PROGRESS: "Em Atendimento",
  COMPLETED: "Concluído",
  CANCELLED: "Cancelado",
  NO_SHOW: "Faltou",
};

function formatDateTime(s: string | null | undefined): string {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleString("pt-BR", {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return String(s);
  }
}

export interface ConflitoAgendaData {
  server: {
    id: number;
    version?: number;
    status?: string;
    start?: string;
    end?: string;
    updated_at?: string;
    patient_name?: string;
    procedure_name?: string;
  };
  local: {
    id: number;
    version?: number;
    status?: string;
    date?: string;
    updated_at?: string;
  };
  resolution_hint?: string;
}

interface ModalConflitoAgendaProps {
  open: boolean;
  onClose: () => void;
  data: ConflitoAgendaData | null;
  onUseServer: () => void;
  onUseLocal: () => void;
  resolving?: boolean;
}

export function ModalConflitoAgenda({
  open,
  onClose,
  data,
  onUseServer,
  onUseLocal,
  resolving = false,
}: ModalConflitoAgendaProps) {
  if (!open) return null;

  const server = data?.server;
  const local = data?.local;
  const hint = data?.resolution_hint;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 dark:bg-black/70">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-hidden flex flex-col border border-gray-200 dark:border-neutral-700">
        <div className="p-4 border-b border-gray-200 dark:border-neutral-700 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
            <AlertTriangle className="w-6 h-6" />
            <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              Conflito de sincronização
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700 text-gray-600 dark:text-gray-400"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="px-4 pt-2 text-sm text-gray-600 dark:text-gray-400">
          Este agendamento foi alterado em outro dispositivo. Escolha qual versão manter.
        </p>

        {hint === "server_cancelled" && (
          <div className="mx-4 mt-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 text-sm">
            O servidor tem este agendamento como <strong>Cancelado</strong>. Recomendamos usar a versão do servidor.
          </div>
        )}
        {hint === "local_newer" && (
          <div className="mx-4 mt-2 p-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-800 dark:text-blue-200 text-sm">
            Sua alteração é mais recente. Pode usar sua versão com segurança.
          </div>
        )}

        <div className="p-4 overflow-y-auto flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="rounded-xl border-2 border-gray-200 dark:border-neutral-600 p-3 bg-gray-50 dark:bg-neutral-700/50">
            <div className="flex items-center gap-2 mb-2 text-gray-700 dark:text-gray-300 font-medium">
              <Server className="w-4 h-4" />
              Versão no servidor
            </div>
            {server && (
              <dl className="space-y-1 text-sm">
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Status</dt>
                  <dd className="font-medium text-gray-900 dark:text-gray-100">
                    {STATUS_LABEL[server.status ?? ""] ?? server.status ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Data/Hora</dt>
                  <dd className="font-medium text-gray-900 dark:text-gray-100">
                    {formatDateTime(server.start)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Atualizado em</dt>
                  <dd className="text-gray-600 dark:text-gray-300">
                    {formatDateTime(server.updated_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Versão</dt>
                  <dd className="text-gray-600 dark:text-gray-300">{server.version ?? "—"}</dd>
                </div>
              </dl>
            )}
          </div>

          <div className="rounded-xl border-2 border-purple-200 dark:border-purple-600 p-3 bg-purple-50/50 dark:bg-purple-900/20">
            <div className="flex items-center gap-2 mb-2 text-purple-700 dark:text-purple-300 font-medium">
              <Smartphone className="w-4 h-4" />
              Sua versão (dispositivo)
            </div>
            {local && (
              <dl className="space-y-1 text-sm">
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Status</dt>
                  <dd className="font-medium text-gray-900 dark:text-gray-100">
                    {STATUS_LABEL[local.status ?? ""] ?? local.status ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Data/Hora</dt>
                  <dd className="font-medium text-gray-900 dark:text-gray-100">
                    {formatDateTime(local.date ?? local.updated_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Atualizado em</dt>
                  <dd className="text-gray-600 dark:text-gray-300">
                    {formatDateTime(local.updated_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-gray-500 dark:text-gray-400">Versão</dt>
                  <dd className="text-gray-600 dark:text-gray-300">{local.version ?? "—"}</dd>
                </div>
              </dl>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-gray-200 dark:border-neutral-700 flex flex-col sm:flex-row gap-2 shrink-0">
          <button
            type="button"
            onClick={onUseServer}
            disabled={resolving}
            className="flex-1 px-4 py-3 rounded-xl bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 font-medium hover:bg-gray-300 dark:hover:bg-neutral-500 disabled:opacity-50"
          >
            Usar versão do servidor
          </button>
          <button
            type="button"
            onClick={onUseLocal}
            disabled={resolving}
            className="flex-1 px-4 py-3 rounded-xl bg-purple-600 text-white font-medium hover:bg-purple-700 disabled:opacity-50"
          >
            {resolving ? "Enviando..." : "Usar minha versão"}
          </button>
        </div>
      </div>
    </div>
  );
}
