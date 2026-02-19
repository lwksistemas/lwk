"use client";

/**
 * Modal de Bloqueio de Horários - Clínica da Beleza
 * Tipos: 🚫 Almoço | 🏖 Férias | 🛠 Manutenção | 📅 Evento interno | Outro
 * Responsivo (mobile/tablet/desktop), integrado com a API.
 */

import { useState, useEffect } from "react";
import { X } from "lucide-react";

const TIPOS_BLOQUEIO = [
  { value: "Horário de almoço", label: "🚫 Horário de almoço" },
  { value: "Férias do profissional", label: "🏖 Férias do profissional" },
  { value: "Manutenção", label: "🛠 Manutenção" },
  { value: "Evento interno", label: "📅 Evento interno" },
  { value: "", label: "✏️ Outro (digite abaixo)" },
] as const;


function formatDateTimeLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const h = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day}T${h}:${min}`;
}

interface Professional {
  id: number;
  name: string;
  specialty?: string;
}

interface ModalBloqueioHorarioProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  professionals: Professional[];
  /** Data/hora inicial sugerida (ex.: clique no calendário) */
  dataInicioSugerida?: Date | null;
}

export function ModalBloqueioHorario({
  isOpen,
  onClose,
  onSuccess,
  professionals,
  dataInicioSugerida,
}: ModalBloqueioHorarioProps) {
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [tipoSelecionado, setTipoSelecionado] = useState<string>(TIPOS_BLOQUEIO[0].value);
  const [motivoOutro, setMotivoOutro] = useState("");
  const [professionalId, setProfessionalId] = useState<string>("");
  const [observacoes, setObservacoes] = useState("");
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState("");

  const motivoFinal = tipoSelecionado || motivoOutro.trim() || "Bloqueio";

  useEffect(() => {
    if (!isOpen) return;
    setErro("");
    const now = new Date();
    const base = dataInicioSugerida || now;
    setTipoSelecionado(TIPOS_BLOQUEIO[0].value);
    setMotivoOutro("");
    setProfessionalId("");
    setObservacoes("");
    // Padrão "Horário de almoço": 12:00 às 14:00 no dia selecionado
    const inicio = new Date(base.getFullYear(), base.getMonth(), base.getDate(), 12, 0, 0);
    const fim = new Date(base.getFullYear(), base.getMonth(), base.getDate(), 14, 0, 0);
    setDataInicio(formatDateTimeLocal(inicio));
    setDataFim(formatDateTimeLocal(fim));
  }, [isOpen, dataInicioSugerida]);

  const salvar = async () => {
    if (!dataInicio || !dataFim) {
      setErro("Preencha data/hora de início e fim.");
      return;
    }
    if (new Date(dataFim) <= new Date(dataInicio)) {
      setErro("O fim deve ser depois do início.");
      return;
    }
    if (!motivoFinal.trim()) {
      setErro("Informe o motivo (tipo ou outro).");
      return;
    }
    setLoading(true);
    setErro("");

    try {
      const { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } = await import("@/lib/clinica-beleza-api");
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const inicioDate = dataInicio.includes("T") ? new Date(dataInicio) : new Date(`${dataInicio}T12:00:00`);
      const fimDate = dataFim.includes("T") ? new Date(dataFim) : new Date(`${dataFim}T14:00:00`);

      const body: Record<string, unknown> = {
        data_inicio: inicioDate.toISOString(),
        data_fim: fimDate.toISOString(),
        motivo: motivoFinal.trim(),
      };
      if (observacoes.trim()) body.observacoes = observacoes.trim();
      if (professionalId) body.professional = parseInt(professionalId, 10);

      const res = await fetch(`${baseURL}/bloqueios/`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        const msg = data.error || data.detail || data.motivo || (Array.isArray(data.data_inicio) ? data.data_inicio[0] : null) || (Array.isArray(data.data_fim) ? data.data_fim[0] : null) || `Erro ${res.status}`;
        throw new Error(typeof msg === "string" ? msg : "Erro ao criar bloqueio.");
      }
      onSuccess();
      onClose();
    } catch (e: unknown) {
      setErro(e instanceof Error ? e.message : "Erro ao criar bloqueio.");
    } finally {
      setLoading(false);
    }
  };

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
          {erro && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-400 text-sm">
              {erro}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Tipo de bloqueio
            </label>
            <select
              value={tipoSelecionado}
              onChange={(e) => setTipoSelecionado(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {TIPOS_BLOQUEIO.map((t) => (
                <option key={t.value || "outro"} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          {tipoSelecionado === "" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Motivo (outro)
              </label>
              <input
                type="text"
                value={motivoOutro}
                onChange={(e) => setMotivoOutro(e.target.value)}
                placeholder="Ex.: Reunião, treinamento..."
                className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Profissional
            </label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              <option value="">Bloqueio geral (todos)</option>
              {professionals.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Início *
            </label>
            <input
              type="datetime-local"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Fim *
            </label>
            <input
              type="datetime-local"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400">
            Use início e fim para um único bloqueio (pode ser um horário no dia ou vários dias seguidos).
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Observações
            </label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
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
            onClick={salvar}
            disabled={loading}
            className="flex-1 px-4 py-3 min-h-[48px] bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? "Salvando..." : "🚫 Bloquear"}
          </button>
        </div>
      </div>
    </div>
  );
}
