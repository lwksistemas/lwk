"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { Loader2, Send, Users, X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { useToast } from "@/components/ui/Toast";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { entityName } from "@/lib/clinica-beleza-entities";

interface CampanhaResumo {
  id: number;
  titulo: string;
}

interface PacienteCampanha {
  id: number;
  name?: string;
  nome?: string;
  phone?: string;
  telefone?: string;
  allow_whatsapp?: boolean;
  is_active?: boolean;
}

type ModoEnvio = "todos" | "segmentacao";

interface CampanhaEnviarModalProps {
  open: boolean;
  campanha: CampanhaResumo | null;
  onClose: () => void;
  onSent: () => void;
}

function pacienteTelefone(p: PacienteCampanha): string {
  return (p.telefone || p.phone || "").trim();
}

function pacienteElegivel(p: PacienteCampanha): boolean {
  if (p.is_active === false) return false;
  if (p.allow_whatsapp === false) return false;
  return !!pacienteTelefone(p);
}

export function CampanhaEnviarModal({ open, campanha, onClose, onSent }: CampanhaEnviarModalProps) {
  const toast = useToast();
  const [mounted, setMounted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [modo, setModo] = useState<ModoEnvio>("todos");
  const [pacientes, setPacientes] = useState<PacienteCampanha[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [busca, setBusca] = useState("");

  useEffect(() => setMounted(true), []);

  const elegiveis = useMemo(() => pacientes.filter(pacienteElegivel), [pacientes]);

  const filtrados = useMemo(() => {
    const q = busca.trim().toLowerCase();
    if (!q) return elegiveis;
    return elegiveis.filter((p) => entityName(p).toLowerCase().includes(q));
  }, [busca, elegiveis]);

  const loadPacientes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.patients.list({ page_size: 500, is_active: true });
      const list = Array.isArray(data) ? data : (data as { results?: PacienteCampanha[] }).results ?? [];
      setPacientes(list);
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Não foi possível carregar pacientes para segmentação.");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    if (!open) {
      setModo("todos");
      setSelectedIds([]);
      setBusca("");
      return;
    }
    loadPacientes();
  }, [open, loadPacientes]);

  const toggleId = (id: number) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const handleEnviar = async () => {
    if (!campanha) return;
    if (modo === "segmentacao" && selectedIds.length === 0) {
      toast.warning("Selecione ao menos um paciente.");
      return;
    }

    setSending(true);
    try {
      const body = modo === "segmentacao" ? { patient_ids: selectedIds } : {};
      const data = (await ClinicaBelezaAPI.campanhas.enviar(campanha.id, body)) as {
        sent?: number;
        message?: string;
        error?: string;
      };
      if (data.sent !== undefined) {
        toast.success(data.message || `Enviado para ${data.sent} paciente(s).`);
        onSent();
        onClose();
      } else {
        toast.error(data.error || "Não foi possível enviar. Verifique o WhatsApp em Configurações.");
      }
    } catch (e: unknown) {
      if (e instanceof Error && e.message === "SESSION_ENDED") return;
      toast.error("Erro ao enviar campanha.");
    } finally {
      setSending(false);
    }
  };

  if (!open || !mounted || !campanha) return null;

  const destinoLabel =
    modo === "todos"
      ? `${elegiveis.length} paciente(s) com WhatsApp ativo`
      : `${selectedIds.length} selecionado(s)`;

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
                        <span className="text-sm text-gray-800 dark:text-gray-200 flex-1 truncate">
                          {entityName(p)}
                        </span>
                        <span className="text-xs text-gray-400">{pacienteTelefone(p)}</span>
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
            onClick={handleEnviar}
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
