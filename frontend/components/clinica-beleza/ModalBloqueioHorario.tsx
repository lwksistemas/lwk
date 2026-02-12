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
    const inicio = dataInicioSugerida || now;
    const fim = new Date(inicio.getTime() + 60 * 60 * 1000); // +1h
    setDataInicio(formatDateTimeLocal(inicio));
    setDataFim(formatDateTimeLocal(fim));
    setTipoSelecionado(TIPOS_BLOQUEIO[0].value);
    setMotivoOutro("");
    setProfessionalId("");
    setObservacoes("");
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
      const body: Record<string, unknown> = {
        data_inicio: new Date(dataInicio).toISOString(),
        data_fim: new Date(dataFim).toISOString(),
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
        throw new Error(data.detail || data.motivo || data.error || `Erro ${res.status}`);
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
        className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between rounded-t-2xl">
          <h2 className="text-lg font-bold text-gray-900">Bloquear Horário</h2>
          <button
            type="button"
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {erro && (
            <div className="p-3 rounded-lg bg-red-50 text-red-800 text-sm">
              {erro}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tipo de bloqueio
            </label>
            <select
              value={tipoSelecionado}
              onChange={(e) => setTipoSelecionado(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Motivo (outro)
              </label>
              <input
                type="text"
                value={motivoOutro}
                onChange={(e) => setMotivoOutro(e.target.value)}
                placeholder="Ex.: Reunião, treinamento..."
                className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Profissional
            </label>
            <select
              value={professionalId}
              onChange={(e) => setProfessionalId(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 rounded-lg bg-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Início *
            </label>
            <input
              type="datetime-local"
              value={dataInicio}
              onChange={(e) => setDataInicio(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Fim *
            </label>
            <input
              type="datetime-local"
              value={dataFim}
              onChange={(e) => setDataFim(e.target.value)}
              className="w-full px-3 py-2.5 min-h-[44px] border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Observações
            </label>
            <textarea
              value={observacoes}
              onChange={(e) => setObservacoes(e.target.value)}
              placeholder="Opcional"
              rows={2}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent resize-none"
            />
          </div>
        </div>

        <div className="sticky bottom-0 bg-gray-50 px-6 py-4 flex gap-3 rounded-b-2xl">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-3 min-h-[48px] bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors font-medium"
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
