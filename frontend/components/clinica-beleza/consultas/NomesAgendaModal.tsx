"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Loader2, CalendarDays } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";
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

  const formBusy = isCreating || editingId !== null;

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      onClose={onClose}
      title="Nomes de Agenda"
      subtitle="Cadastre os nomes usados ao agendar (ex: Estética, Dermatologia)"
      icon={<CalendarDays size={20} className="text-purple-600 shrink-0 mt-0.5" />}
      footer={
        <div className="flex justify-between gap-2">
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
      }
    >
      {error && (
        <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
          {error}
        </div>
      )}

      {(isCreating || editingId !== null) && (
        <div className="mb-4 p-3 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10 space-y-3">
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
          <div className="flex flex-wrap gap-2">
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
        <ul className="space-y-2">
          {nomes.map((item) => (
            <li
              key={item.id}
              className={`p-3 rounded-lg ${
                editingId === item.id
                  ? "border-2 border-purple-300 dark:border-purple-700 bg-purple-50/40"
                  : "bg-gray-50 dark:bg-neutral-800"
              }`}
            >
              {editingId === item.id ? (
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 break-words">{item.nome}</p>
              ) : (
                <div className="space-y-2">
                  <div className="min-w-0">
                    <span className="font-medium text-sm text-gray-900 dark:text-gray-100 break-words">{item.nome}</span>
                    {item.is_padrao && (
                      <span className="ml-1.5 text-xs font-normal px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 dark:bg-purple-900/40 dark:text-purple-200 whitespace-nowrap">
                        Padrão
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-1">
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
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </ClinicaBelezaPortraitModal>
  );
}
