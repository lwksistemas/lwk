"use client";

import { createPortal } from "react-dom";
import { Loader2, Send, Users, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useToast } from "@/components/ui/Toast";
import { entityName } from "@/lib/clinica-beleza-entities";
import {
  buildCampanhaDestinoLabel,
  pacienteCampanhaTelefone,
  type CampanhaResumo,
} from "./campanha-enviar-modal-types";
import { useCampanhaEnviarModal } from "./useCampanhaEnviarModal";

export interface CampanhaEnviarModalProps {
  open: boolean;
  campanha: CampanhaResumo | null;
  onClose: () => void;
  onSent: () => void;
}

export function CampanhaEnviarModal({ open, campanha, onClose, onSent }: CampanhaEnviarModalProps) {
  const toast = useToast();
  const {
    mounted,
    loading,
    sending,
    modo,
    setModo,
    selectedIds,
    busca,
    setBusca,
    filtrados,
    elegiveis,
    toggleId,
    handleEnviar,
  } = useCampanhaEnviarModal({ open, campanha, onClose, onSent, toast });

  if (!open || !mounted || !campanha) return null;

  const destinoLabel = buildCampanhaDestinoLabel(modo, elegiveis.length, selectedIds.length);

  return createPortal(
    <div className="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50" onClick={onClose}>
      <div
        className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3 p-5 border-b border-gray-200 dark:border-neutral-700">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Send size={18} style={{ color: CLINICA_BELEZA_PRIMARY }} />
              Enviar campanha
            </h2>
            <p className="text-sm text-gray-500 mt-1 line-clamp-2">{campanha.titulo}</p>
          </div>
          <button type="button" onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800">
            <X size={18} />
          </button>
        </div>

        <div className="p-5 space-y-4 overflow-y-auto flex-1">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setModo("todos")}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border ${
                modo === "todos"
                  ? "border-transparent text-white"
                  : "border-gray-200 dark:border-neutral-700 text-gray-700 dark:text-gray-300"
              }`}
              style={modo === "todos" ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
            >
              Todos elegíveis
            </button>
            <button
              type="button"
              onClick={() => setModo("segmentacao")}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium border ${
                modo === "segmentacao"
                  ? "border-transparent text-white"
                  : "border-gray-200 dark:border-neutral-700 text-gray-700 dark:text-gray-300"
              }`}
              style={modo === "segmentacao" ? { backgroundColor: CLINICA_BELEZA_PRIMARY } : undefined}
            >
              Segmentar
            </button>
          </div>

          {modo === "segmentacao" && (
            <div className="space-y-2">
              <input
                type="search"
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar paciente..."
                className="w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-800"
              />
              {loading ? (
                <div className="flex items-center justify-center py-8 text-gray-500 text-sm gap-2">
                  <Loader2 size={16} className="animate-spin" />
                  Carregando pacientes...
                </div>
              ) : filtrados.length === 0 ? (
                <p className="text-sm text-gray-500 py-4 text-center">Nenhum paciente elegível encontrado.</p>
              ) : (
                <ul className="max-h-52 overflow-y-auto border dark:border-neutral-700 rounded-lg divide-y dark:divide-neutral-700">
                  {filtrados.map((p) => (
                    <li key={p.id}>
                      <label className="flex items-center gap-3 px-3 py-2 cursor-pointer hover:bg-gray-50 dark:hover:bg-neutral-800">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(p.id)}
                          onChange={() => toggleId(p.id)}
                          className="rounded"
                          style={{ accentColor: CLINICA_BELEZA_PRIMARY }}
                        />
                        <span className="text-sm text-gray-800 dark:text-gray-200 flex-1 truncate">{entityName(p)}</span>
                        <span className="text-xs text-gray-400">{pacienteCampanhaTelefone(p)}</span>
                      </label>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <p className="text-xs text-gray-500 flex items-center gap-1.5">
            <Users size={14} />
            Destino: {destinoLabel}
          </p>
        </div>

        <div className="flex gap-3 p-5 border-t border-gray-200 dark:border-neutral-700">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 py-2.5 rounded-lg border border-gray-300 dark:border-neutral-600 text-sm font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => void handleEnviar()}
            disabled={sending || (modo === "segmentacao" && selectedIds.length === 0)}
            className="flex-1 py-2.5 rounded-lg text-white text-sm font-medium disabled:opacity-50 flex items-center justify-center gap-2"
            style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
          >
            {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            {sending ? "Enviando..." : "Enviar WhatsApp"}
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
