"use client";

import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL, CLINICA_PAGAMENTO_STATUS_LABEL } from "@/lib/clinica-beleza-constants";
import { ClinicaBelezaAPI } from "@/lib/clinica-beleza-api";
import { toUpperCase } from "@/lib/format-br";

export interface CategoriaDespesa {
  id: number;
  nome: string;
}

export interface DespesaItem {
  id: number;
  descricao: string;
  categoria: number | null;
  categoria_nome?: string;
  valor: string | number;
  status: string;
  data_vencimento: string;
  data_pagamento: string | null;
  forma_pagamento: string;
  observacoes?: string;
}

const inputClass =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";

const emptyForm = () => ({
  descricao: "",
  categoria: "" as number | "",
  valor: "",
  status: "PENDING",
  data_vencimento: new Date().toISOString().slice(0, 10),
  data_pagamento: "",
  forma_pagamento: "PIX",
  observacoes: "",
});

export function DespesaFormModal({
  open,
  editing,
  saving,
  onClose,
  onSaved,
}: {
  open: boolean;
  editing: DespesaItem | null;
  saving: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [form, setForm] = useState(emptyForm());
  const [categorias, setCategorias] = useState<CategoriaDespesa[]>([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (!open) return;
    ClinicaBelezaAPI.financeiro.despesas.categorias()
      .then((data) => setCategorias(Array.isArray(data) ? data : []))
      .catch(() => setCategorias([]));
  }, [open]);

  useEffect(() => {
    if (!open) return;
    if (editing) {
      setForm({
        descricao: editing.descricao,
        categoria: editing.categoria ?? "",
        valor: String(editing.valor),
        status: editing.status,
        data_vencimento: String(editing.data_vencimento).slice(0, 10),
        data_pagamento: editing.data_pagamento ? String(editing.data_pagamento).slice(0, 10) : "",
        forma_pagamento: editing.forma_pagamento || "PIX",
        observacoes: editing.observacoes || "",
      });
    } else {
      setForm(emptyForm());
    }
    setErro("");
  }, [open, editing]);

  const salvar = async () => {
    if (!form.descricao.trim()) {
      setErro("Informe a descrição.");
      return;
    }
    const valor = Number(form.valor);
    if (!valor || valor <= 0) {
      setErro("Informe um valor válido.");
      return;
    }
    if (!form.data_vencimento) {
      setErro("Informe o vencimento.");
      return;
    }
    setErro("");
    const payload: Record<string, unknown> = {
      descricao: form.descricao.trim(),
      valor,
      status: form.status,
      data_vencimento: form.data_vencimento,
      forma_pagamento: form.forma_pagamento,
      observacoes: form.observacoes.trim(),
    };
    if (form.categoria) payload.categoria = Number(form.categoria);
    if (form.status === "PAID") {
      payload.data_pagamento = form.data_pagamento || form.data_vencimento;
    } else {
      payload.data_pagamento = null;
    }
    try {
      if (editing) {
        await ClinicaBelezaAPI.financeiro.despesas.update(editing.id, payload);
      } else {
        await ClinicaBelezaAPI.financeiro.despesas.create(payload);
      }
      onSaved();
      onClose();
    } catch (e: unknown) {
      const msg =
        e && typeof e === "object" && "error" in e
          ? String((e as { error: string }).error)
          : "Não foi possível salvar a despesa.";
      setErro(msg);
    }
  };

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
              className={inputClass}
              placeholder="Ex: Aluguel, conta de luz..."
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Categoria</label>
              <select
                value={form.categoria}
                onChange={(e) => setForm({ ...form, categoria: e.target.value ? Number(e.target.value) : "" })}
                className={inputClass}
              >
                <option value="">Selecione...</option>
                {categorias.map((c) => (
                  <option key={c.id} value={c.id}>{c.nome}</option>
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
                className={inputClass}
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
                className={inputClass}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm({ ...form, status: e.target.value })}
                className={inputClass}
              >
                {Object.entries(CLINICA_PAGAMENTO_STATUS_LABEL).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
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
                  className={inputClass}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Forma de pagamento</label>
                <select
                  value={form.forma_pagamento}
                  onChange={(e) => setForm({ ...form, forma_pagamento: e.target.value })}
                  className={inputClass}
                >
                  {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
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
              className={inputClass}
            />
          </div>
          {erro && <p className="text-sm text-red-600 dark:text-red-400">{erro}</p>}
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button
              type="button"
              onClick={salvar}
              disabled={saving}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {saving ? "Salvando..." : "Salvar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
