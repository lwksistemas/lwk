"use client";

import { X } from "lucide-react";
import {
  TIPOS_BLOQUEIO,
  profissionalBloqueioLabel,
  type BloqueioProfessional,
} from "./modal-bloqueio-horario-utils";
import { useModalBloqueioHorario } from "./useModalBloqueioHorario";

export interface ModalBloqueioHorarioProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  professionals: BloqueioProfessional[];
  dataInicioSugerida?: Date | null;
  defaultProfessionalId?: string;
}

export function ModalBloqueioHorario({
  isOpen,
  onClose,
  onSuccess,
  professionals,
  dataInicioSugerida,
  defaultProfessionalId,
}: ModalBloqueioHorarioProps) {
  const state = useModalBloqueioHorario({
    isOpen,
    onClose,
    onSuccess,
    dataInicioSugerida,
    defaultProfessionalId,
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div
        className="bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white dark:bg-neutral-800 border-b border-gray-200 dark:border-neutral-700 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Bloquear Horário</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {state.erro && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 text-sm">
              {state.erro}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo de bloqueio
            </label>
            <select
              value={state.tipoSelecionado}
              onChange={(e) => state.setTipoSelecionado(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {TIPOS_BLOQUEIO.map((t) => (
                <option key={t.value || "outro"} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {state.tipoSelecionado === "" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Motivo (outro)
              </label>
              <input
                type="text"
                value={state.motivoOutro}
                onChange={(e) => state.setMotivoOutro(e.target.value)}
                placeholder="Ex.: Reunião, treinamento..."
                className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Profissional</label>
            <select
              value={state.professionalId}
              onChange={(e) => state.setProfessionalId(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Bloqueio geral (todos)</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>
                  {profissionalBloqueioLabel(p)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Início *</label>
            <input
              type="datetime-local"
              value={state.dataInicio}
              onChange={(e) => state.setDataInicio(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fim *</label>
            <input
              type="datetime-local"
              value={state.dataFim}
              onChange={(e) => state.setDataFim(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            Use início e fim para um único bloqueio (pode ser um horário no dia ou vários dias seguidos). O intervalo de
            almoço do profissional é configurado em Profissionais → Horários de trabalho.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Observações</label>
            <textarea
              value={state.observacoes}
              onChange={(e) => state.setObservacoes(e.target.value)}
              placeholder="Opcional"
              rows={2}
              className="w-full px-3 py-2.5 border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-50 dark:bg-neutral-700/50 px-6 py-4 flex gap-3 rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-3 min-h-[48px] bg-gray-200 dark:bg-neutral-600 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-neutral-500 transition-colors font-medium"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => void state.salvar()}
            disabled={state.loading}
            className="flex-1 px-4 py-3 min-h-[48px] bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {state.loading ? "Salvando..." : "🚫 Bloquear"}
          </button>
        </div>
      </div>
    </div>
  );
}
