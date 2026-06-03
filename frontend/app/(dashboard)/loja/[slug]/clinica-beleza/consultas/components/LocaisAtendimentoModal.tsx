"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Loader2 } from "lucide-react";
import { ClinicaBelezaAPI, type LocalAtendimentoItem } from "@/lib/clinica-beleza-api";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";

interface LocaisAtendimentoModalProps {
  open: boolean;
  onClose: () => void;
}

export function LocaisAtendimentoModal({ open, onClose }: LocaisAtendimentoModalProps) {
  const [locais, setLocais] = useState<LocalAtendimentoItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
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
      setShowForm(false);
      setEditingId(null);
      setError("");
    }
  }, [open, loadLocais]);

  const resetForm = () => {
    setFormNome("");
    setFormValor("");
    setEditingId(null);
    setShowForm(false);
    setError("");
  };

  const startEdit = (local: LocalAtendimentoItem) => {
    setEditingId(local.id);
    setFormNome(local.nome);
    setFormValor(String(local.valor_consulta));
    setShowForm(true);
    setError("");
  };

  const startNew = () => {
    setEditingId(null);
    setFormNome("");
    setFormValor("");
    setShowForm(true);
    setError("");
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    const valor = parseFloat(formValor);

    if (!nome) {
      setError("O nome do local é obrigatório.");
      return;
    }
    if (isNaN(valor) || valor < 0) {
      setError("O valor deve ser um número maior ou igual a zero.");
      return;
    }

    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await ClinicaBelezaAPI.locaisAtendimento.update(editingId, { nome, valor_consulta: valor });
      } else {
        await ClinicaBelezaAPI.locaisAtendimento.create({ nome, valor_consulta: valor });
      }
      resetForm();
      await loadLocais();
    } catch {
      setError("Erro ao salvar local de atendimento.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Deseja realmente excluir este local de atendimento?")) return;
    try {
      await ClinicaBelezaAPI.locaisAtendimento.delete(id);
      await loadLocais();
    } catch {
      setError("Erro ao excluir local de atendimento.");
    }
  };

  const formatCurrencyBR = (value: string | number) => {
    const num = typeof value === "string" ? parseFloat(value) : value;
    return num.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-neutral-700">
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {error && (
            <div className="mb-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-8 text-gray-500">
              <Loader2 size={24} className="animate-spin mx-auto mb-2" />
              Carregando...
            </div>
          ) : locais.length === 0 && !showForm ? (
            <p className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
              Nenhum local cadastrado.
            </p>
          ) : (
            <ul className="space-y-2">
              {locais.map((local) => (
                <li
                  key={local.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-neutral-800"
                >
                  <div>
                    <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
                      {local.nome}
                    </span>
                    <span className="ml-2 text-gray-500 dark:text-gray-400 text-sm">
                      {formatCurrencyBR(local.valor_consulta)}
                    </span>
                  </div>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => startEdit(local)}
                      className="p-1.5 rounded hover:bg-gray-200 dark:hover:bg-neutral-700"
                      aria-label="Editar"
                    >
                      <Pencil size={14} className="text-gray-500" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(local.id)}
                      className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
                      aria-label="Excluir"
                    >
                      <Trash2 size={14} className="text-red-500" />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}

          {/* Inline form */}
          {showForm && (
            <div className="mt-4 p-4 rounded-lg border border-gray-200 dark:border-neutral-700 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
                  Nome do local
                </label>
                <input
                  type="text"
                  value={formNome}
                  onChange={(e) => setFormNome(e.target.value)}
                  placeholder="Ex: Consultório, Home Care..."
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-opacity-50"
                  style={{ focusRingColor: CLINICA_BELEZA_PRIMARY } as never}
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
                  onChange={(e) => setFormValor(e.target.value)}
                  placeholder="0,00"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-opacity-50"
                />
              </div>
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
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-3 py-1.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-neutral-800"
                >
                  Cancelar
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-200 dark:border-neutral-700 flex justify-between">
          {!showForm && (
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
