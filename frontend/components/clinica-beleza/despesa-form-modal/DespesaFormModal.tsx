"use client";

import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL, CLINICA_PAGAMENTO_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { toUpperCase } from "@/lib/format-br";
import type { DespesaItem } from "./despesa-form-modal-types";
import { DESPESA_FORM_INPUT_CLASS } from "./despesa-form-modal-types";
import { useDespesaFormModal } from "./useDespesaFormModal";

export interface DespesaFormModalProps {
  open: boolean;
  editing: DespesaItem | null;
  saving: boolean;
  onClose: () => void;
  onSaved: () => void;
}

export function DespesaFormModal({ open, editing, saving: savingProp, onClose, onSaved }: DespesaFormModalProps) {
  const { form, setForm, categorias, erro, saving, salvar } = useDespesaFormModal({
    open,
    editing,
    onClose,
    onSaved,
  });
  const isSaving = savingProp || saving;

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700 sticky top-0 bg-white dark:bg-neutral-800">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
            {editing ? "Editar despesa" : "Nova despesa"}
          </h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Descrição *</label>
            <input
              type="text"
              value={form.descricao}
              onChange={(e) => setForm({ ...form, descricao: toUpperCase(e.target.value) })}
              className={DESPESA_FORM_INPUT_CLASS}
              placeholder="Ex: Aluguel, conta de luz..."
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Categoria</label>
              <select
                value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value ? Number(e.target.value) : "" })}
                className={DESPESA_FORM_INPUT_CLASS}
              >
                <option value="">Selecione...</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.nome}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Valor (R$) *</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={form.valor}
                onChange={(e) => setForm({ ...form, valor: e.target.value })}
                className={DESPESA_FORM_INPUT_CLASS}
              />
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Vencimento *</label>
              <input
                type="date"
                value={form.data_vencimento}
                onChange={(e) => setForm({ ...form, data_vencimento: e.target.value })}
                className={DESPESA_FORM_INPUT_CLASS}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className={DESPESA_FORM_INPUT_CLASS}
              >
                {Object.entries(CLINICA_PAGAMENTO_STATUS_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
          </div>
          {form.status === "PAID" && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Data pagamento</label>
                <input
                  type="date"
                  value={form.data_pagamento}
                  onChange={(e) => setForm({ ...form, data_pagamento: e.target.value })}
                  className={DESPESA_FORM_INPUT_CLASS}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Forma de pagamento</label>
                <select
                  value={form.forma_pagamento}
                  onChange={(e) => setForm({ ...form, forma_pagamento: e.target.value })}
                  className={DESPESA_FORM_INPUT_CLASS}
                >
                  {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Observações</label>
            <textarea
              rows={2}
              value={form.observacoes}
              onChange={(e) => setForm({ ...form, observacoes: e.target.value })}
              className={DESPESA_FORM_INPUT_CLASS}
            />
          </div>
          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => void salvar()}
              disabled={isSaving}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {isSaving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
