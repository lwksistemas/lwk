"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Loader2, CalendarDays } from "lucide-react";
import { ClinicaBelezaAPI, type NomeAgendaItem } from "@/lib/clinica-beleza-api";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface NomesAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const val of Object.values(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return val[0];
    if (typeof val === "string") return val;
  }
  return fallback;
}

export function NomesAgendaModal({ open, onClose }: NomesAgendaModalProps) {
  const [nomes, setNomes] = useState<NomeAgendaItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formNome, setFormNome] = useState("");
  const [error, setError] = useState("");

  const loadNomes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.nomesAgenda.list();
      setNomes(Array.isArray(data) ? data : []);
    } catch {
      setError("Erro ao carregar nomes de agenda.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadNomes();
      setIsCreating(false);
      setEditingId(null);
      setFormNome("");
      setError("");
    }
  }, [open, loadNomes]);

  const resetForm = () => {
    setFormNome("");
    setEditingId(null);
    setIsCreating(false);
    setError("");
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    if (!nome) {
      setError("O nome da agenda é obrigatório.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await ClinicaBelezaAPI.nomesAgenda.update(editingId, { nome });
      } else {
        await ClinicaBelezaAPI.nomesAgenda.create({ nome });
      }
      resetForm();
      await loadNomes();
    } catch (err) {
      setError(extractApiError(err, "Erro ao salvar nome de agenda."));
    } finally {
      setSaving(false);
    }
  };

  const handleSetPadrao = async (id: number) => {
    try {
      await ClinicaBelezaAPI.nomesAgenda.update(id, { is_padrao: true });
      await loadNomes();
    } catch (err) {
      setError(extractApiError(err, "Erro ao definir padrão."));
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deseja excluir este nome de agenda?")) return;
    try {
      await ClinicaBelezaAPI.nomesAgenda.delete(id);
      if (editingId === id) resetForm();
      await loadNomes();
    } catch (err) {
      setError(extractApiError(err, "Erro ao excluir."));
    }
  };

  if (!open) return null;

  const formBusy = isCreating || editingId !== null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-0 sm:p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-t-xl sm:rounded-xl shadow-xl w-full max-w-md sm:max-w-4xl sm:w-[calc(100vw-2rem)] max-h-[95vh] sm:max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div className="flex items-center gap-2">
            <CalendarDays size={20} className="text-purple-600" />
            <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100">
              Nomes de Agenda
            </h2>
          </div>
          <button type="button" onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800" aria-label="Fechar">
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4">
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
            Cadastre os nomes usados ao agendar (ex: Estética, Dermatologia, Consultório 1).
          </p>

          {error && (
            <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {(isCreating || editingId !== null) && (
            <div className="mb-4 p-4 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10 space-y-3">
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400">
                Nome da agenda *
              </label>
              <input
                type="text"
                value={formNome}
                onChange={(e) => setFormNome(e.target.value)}
                placeholder="Ex: Estética, Dermatologia..."
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm"
                autoFocus
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm font-medium disabled:opacity-50"
                  style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
                >
                  {saving ? <Loader2 size={14} className="animate-spin" /> : null}
                  {editingId ? "Salvar" : "Adicionar"}
                </button>
                <button type="button" onClick={resetForm} className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400">
                  Cancelar
                </button>
              </div>
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              <Loader2 size={24} className="animate-spin mx-auto mb-2" />
              Carregando...
            </div>
          ) : nomes.length === 0 && !isCreating ? (
            <p className="text-center text-gray-500 text-sm py-8">Nenhum nome cadastrado.</p>
          ) : (
            <ul className="space-y-2 sm:grid sm:grid-cols-2 lg:grid-cols-3 sm:gap-3 sm:space-y-0">
              {nomes.map((item) => (
                <li
                  key={item.id}
                  className={`flex items-center justify-between gap-3 p-3 rounded-lg ${
                    editingId === item.id
                      ? "border-2 border-purple-300 dark:border-purple-700 bg-purple-50/40"
                      : "bg-gray-50 dark:bg-neutral-800"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="font-medium text-sm text-gray-900 dark:text-gray-100">{item.nome}</span>
                    {item.is_padrao && (
                      <span className="text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200">
                        Padrão
                      </span>
                    )}
                  </div>
                  {editingId !== item.id && (
                    <div className="flex gap-1 shrink-0">
                      {!item.is_padrao && (
                        <button
                          type="button"
                          onClick={() => handleSetPadrao(item.id)}
                          disabled={formBusy}
                          className="px-2 py-1 text-xs rounded border border-gray-300 dark:border-neutral-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-700 disabled:opacity-40"
                          title="Definir como padrão"
                        >
                          Definir padrão
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          setIsCreating(false);
                          setEditingId(item.id);
                          setFormNome(item.nome);
                          setError("");
                        }}
                        disabled={formBusy}
                        className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-neutral-700 disabled:opacity-40"
                        title="Editar"
                      >
                        <Pencil size={14} className="text-gray-500" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDelete(item.id)}
                        disabled={formBusy}
                        className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
                        title="Excluir"
                      >
                        <Trash2 size={14} className="text-red-500" />
                      </button>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between shrink-0">
          {!formBusy && (
            <button
              type="button"
              onClick={() => {
                setEditingId(null);
                setFormNome("");
                setIsCreating(true);
                setError("");
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Plus size={14} />
              Novo nome
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800 ml-auto"
          >
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
