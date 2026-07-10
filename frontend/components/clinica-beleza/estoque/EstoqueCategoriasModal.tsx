"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { ClinicaBelezaPortraitModal } from "@/components/clinica-beleza/ClinicaBelezaPortraitModal";
import {
  ESTOQUE_INPUT_CLASS,
  extractEstoqueApiError,
  type EstoqueCategoria,
} from "@/components/clinica-beleza/estoque/estoque-types";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";

interface Props {
  open: boolean;
  onClose: () => void;
  onChanged: () => void;
  lojaCtx?: { slug: string };
}

export function EstoqueCategoriasModal({ open, onClose, onChanged, lojaCtx }: Props) {
  const [categorias, setCategorias] = useState<EstoqueCategoria[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [formNome, setFormNome] = useState("");
  const [formCor, setFormCor] = useState("#8B3D52");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await ClinicaBelezaAPI.estoque.categorias.list(lojaCtx);
      setCategorias(Array.isArray(data) ? (data as EstoqueCategoria[]) : []);
    } catch (err) {
      setError(extractEstoqueApiError(err, "Não foi possível carregar categorias."));
      setCategorias([]);
    } finally {
      setLoading(false);
    }
  }, [lojaCtx]);

  useEffect(() => {
    if (open) void load();
  }, [open, load]);

  const resetForm = () => {
    setEditingId(null);
    setIsCreating(false);
    setFormNome("");
    setFormCor("#8B3D52");
    setError(null);
  };

  const startNew = () => {
    setEditingId(null);
    setIsCreating(true);
    setFormNome("");
    setFormCor("#8B3D52");
    setError(null);
  };

  const startEdit = (cat: EstoqueCategoria) => {
    setIsCreating(false);
    setEditingId(cat.id);
    setFormNome(cat.nome);
    setFormCor(cat.cor || "#8B3D52");
    setError(null);
  };

  const handleSave = async () => {
    const nome = formNome.trim();
    if (!nome) {
      setError("Informe o nome da categoria.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      if (editingId) {
        await ClinicaBelezaAPI.estoque.categorias.update(editingId, { nome, cor: formCor });
      } else {
        await ClinicaBelezaAPI.estoque.categorias.create({ nome, cor: formCor }, lojaCtx);
      }
      resetForm();
      await load();
      onChanged();
    } catch (err) {
      setError(extractEstoqueApiError(err, "Não foi possível salvar."));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (cat: EstoqueCategoria) => {
    if (!confirm(`Excluir a categoria "${cat.nome}"?`)) return;
    setSaving(true);
    setError(null);
    try {
      await ClinicaBelezaAPI.estoque.categorias.delete(cat.id);
      if (editingId === cat.id) resetForm();
      await load();
      onChanged();
    } catch (err) {
      setError(extractEstoqueApiError(err, "Não foi possível excluir."));
    } finally {
      setSaving(false);
    }
  };

  const formBusy = isCreating || editingId != null;

  return (
    <ClinicaBelezaPortraitModal
      open={open}
      onClose={() => {
        resetForm();
        onClose();
      }}
      title="Categorias do estoque"
      subtitle="Crie, edite ou remova categorias"
      footer={
        <div className="flex justify-between gap-2">
          {!formBusy && (
            <button
              type="button"
              onClick={startNew}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-white"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              <Plus size={14} />
              Nova categoria
            </button>
          )}
          <button
            type="button"
            onClick={() => {
              resetForm();
              onClose();
            }}
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

      {formBusy && (
        <div className="mb-4 p-3 rounded-lg border border-gray-200 dark:border-neutral-700 bg-gray-50/80 dark:bg-neutral-900/40 space-y-3">
          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
            {editingId ? "Editar categoria" : "Nova categoria"}
          </p>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Nome</label>
            <input
              type="text"
              value={formNome}
              onChange={(e) => setFormNome(e.target.value)}
              className={ESTOQUE_INPUT_CLASS}
              placeholder="Ex.: Injetáveis"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Cor</label>
            <input
              type="color"
              value={formCor}
              onChange={(e) => setFormCor(e.target.value)}
              className="h-9 w-16 rounded border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={saving}
              onClick={() => void handleSave()}
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-white disabled:opacity-60"
              style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
            >
              {saving ? "Salvando…" : "Salvar"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-400"
            >
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
      ) : categorias.length === 0 && !formBusy ? (
        <p className="text-center text-gray-500 dark:text-gray-400 text-sm py-8">
          Nenhuma categoria cadastrada.
        </p>
      ) : (
        <ul className="space-y-2">
          {categorias.map((cat) => (
            <li
              key={cat.id}
              className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 dark:border-neutral-700"
            >
              <span
                className="h-3 w-3 rounded-full shrink-0"
                style={{ backgroundColor: cat.cor || "#8B3D52" }}
              />
              <span className="flex-1 min-w-0">
                <span className="block text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {cat.nome}
                </span>
                <span className="block text-xs text-gray-500">
                  {cat.produtos_count ?? 0} produto{(cat.produtos_count ?? 0) !== 1 ? "s" : ""}
                </span>
              </span>
              <button
                type="button"
                onClick={() => startEdit(cat)}
                className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
                title="Editar"
              >
                <Pencil size={14} />
              </button>
              <button
                type="button"
                onClick={() => void handleDelete(cat)}
                className="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-900/20 text-red-500"
                title="Excluir"
                disabled={saving}
              >
                <Trash2 size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </ClinicaBelezaPortraitModal>
  );
}
