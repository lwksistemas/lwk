"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Loader2 } from "lucide-react";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface LocaisAtendimentoModalProps {
  open: boolean;
  onClose: () => void;
}

function parseValorInput(value: string): number {
  const trimmed = value.trim();
  if (!trimmed) return NaN;
  if (trimmed.includes(",")) {
    return parseFloat(trimmed.replace(/\./g, "").replace(",", "."));
  }
  return parseFloat(trimmed);
}

function valorToInput(value: string | number | null | undefined): string {
  if (value == null || value === "") return "";
  const num = typeof value === "string" ? parseFloat(value.replace(",", ".")) : Number(value);
  return Number.isFinite(num) ? String(num) : "";
}

function extractApiError(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const body = err as Record<string, unknown>;
  if (typeof body.error === "string") return body.error;
  if (typeof body.detail === "string") return body.detail;
  for (const [key, val] of Object.entries(body)) {
    if (Array.isArray(val) && typeof val[0] === "string") return `${key}: ${val[0]}`;
    if (typeof val === "string") return val;
  }
  return fallback;
}

function LocalFormFields({
  formNome,
  formValor,
  onNomeChange,
  onValorChange,
  onSave,
  onCancel,
  saving,
  saveLabel,
}: {
  formNome: string;
  formValor: string;
  onNomeChange: (v: string) => void;
  onValorChange: (v: string) => void;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
  saveLabel: string;
}) {
  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Nome do local
        </label>
        <input
          type="text"
          value={formNome}
          onChange={(e) => onNomeChange(e.target.value)}
          placeholder="Ex: Consultório, Home Care..."
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
          autoFocus
        />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
          Valor da consulta (R$)
        </label>
        <input
          type="number"
          step="0.01"
          min="0"
          value={formValor}
          onChange={(e) => onValorChange(e.target.value)}
          placeholder="0,00"
          className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500/40"
        />
      </div>
      <div className="flex gap-2">
        <button
          type="button"
          onClick={onSave}
          disabled={saving}
          className="flex items-center gap-1.5 px-3 py-1.5 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
        >
          {saving ? <Loader2 size={14} className="animate-spin" /> : null}
          {saveLabel}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}

export function LocaisAtendimentoModal({ open, onClose }: LocaisAtendimentoModalProps) {
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formNome, setFormNome] = useState("");
  const [formValor, setFormValor] = useState("");
  const [error, setError] = useState("");

  const loadLocais = useCallback(async () => {
    setLoading(true);
    try {
      const data = await ClinicaBelezaAPI.locaisAtendimento.list();
      setLocais(Array.isArray(data) ? data : []);
    } catch {
      setError("Erro ao carregar locais de atendimento.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      loadLocais();
      setIsCreating(false);
      setEditingId(null);
      setFormNome("");
      setFormValor("");
      setError("");
    }
  }, [open, loadLocais]);

  const resetForm = () => {
    setFormNome("");
    setFormValor("");
    setEditingId(null);
    setIsCreating(false);
    setError("");
  };

  const startEdit = (local: LocalAtendimentoItem) => {
    setIsCreating(false);
    setEditingId(local.id);
    setFormNome(local.nome);
    setFormValor(valorToInput(local.valor_consulta));
    setError("");
  };

  const startNew = () => {
    setEditingId(null);
    setFormNome("");
    setFormValor("");
    setIsCreating(true);
    setError("");
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    const valor = parseValorInput(formValor);

    if (!nome) {
      setError("O nome do local é obrigatório.");
      return;
    }
    if (!Number.isFinite(valor) || valor < 0) {
      setError("O valor deve ser um número maior ou igual a zero.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      const payload = { nome, valor_consulta: valor };
      if (editingId) {
        await ClinicaBelezaAPI.locaisAtendimento.update(editingId, payload);
      } else {
        await ClinicaBelezaAPI.locaisAtendimento.create(payload);
      }
      resetForm();
      await loadLocais();
    } catch (err) {
      setError(extractApiError(err, "Erro ao salvar local de atendimento."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deseja realmente excluir este local de atendimento?")) return;
    try {
      await ClinicaBelezaAPI.locaisAtendimento.delete(id);
      if (editingId === id) resetForm();
      await loadLocais();
    } catch (err) {
      setError(extractApiError(err, "Erro ao excluir local de atendimento."));
    }
  };

  const formatCurrencyBR = (value: string | number) => {
    const num = typeof value === "string" ? parseFloat(value.replace(",", ".")) : value;
    if (!Number.isFinite(num)) return "—";
    return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  };

  if (!open) return null;

  const formBusy = isCreating || editingId !== null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Locais de Atendimento
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800"
            aria-label="Fechar"
          >
            <X size={20} className="text-gray-500" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {isCreating && (
            <div className="mb-4 p-4 rounded-lg border-2 border-purple-200 dark:border-purple-800 bg-purple-50/50 dark:bg-purple-900/10">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">Novo local</p>
              <LocalFormFields
                formNome={formNome}
                formValor={formValor}
                onNomeChange={setFormNome}
                onValorChange={setFormValor}
                onSave={handleSave}
                onCancel={resetForm}
                saving={saving}
                saveLabel="Adicionar"
              />
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              <Loader2 size={24} className="animate-spin mx-auto mb-2" />
              Carregando...
            </div>
          ) : locais.length === 0 && !isCreating ? (
            <p className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
              Nenhum local cadastrado.
            </p>
          ) : (
            <ul className="space-y-2">
              {locais.map((local) => (
                <li
                  key={local.id}
                  className={`p-3 rounded-lg ${
                    editingId === local.id
                      ? "border-2 border-purple-300 dark:border-purple-700 bg-purple-50/40 dark:bg-purple-900/10"
                      : "bg-gray-50 dark:bg-neutral-800"
                  }`}
                >
                  {editingId === local.id ? (
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                        Editando: {local.nome}
                      </p>
                      <LocalFormFields
                        formNome={formNome}
                        formValor={formValor}
                        onNomeChange={setFormNome}
                        onValorChange={setFormValor}
                        onSave={handleSave}
                        onCancel={resetForm}
                        saving={saving}
                        saveLabel="Salvar"
                      />
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                          {local.nome}
                        </span>
                        <span className="ml-2 text-gray-500 dark:text-gray-400 text-sm">
                          {formatCurrencyBR(local.valor_consulta)}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          type="button"
                          onClick={() => startEdit(local)}
                          disabled={formBusy}
                          className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-neutral-700 disabled:opacity-40"
                          aria-label={`Editar ${local.nome}`}
                          title="Editar"
                        >
                          <Pencil size={14} className="text-gray-500" />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(local.id)}
                          disabled={formBusy}
                          className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40"
                          aria-label={`Excluir ${local.nome}`}
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
        </div>

        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between shrink-0">
          {!formBusy && (
            <button
              type="button"
              onClick={startNew}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              <Plus size={14} />
              Novo local
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
