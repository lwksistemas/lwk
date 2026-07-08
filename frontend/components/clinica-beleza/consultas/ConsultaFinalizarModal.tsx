import { X } from "lucide-react";
import { CLINICA_BELEZA_PRIMARY } from "@/components/clinica-beleza/clinica-beleza-nav";
import { CLINICA_FORMA_PAGAMENTO_LABEL } from "@/lib/clinica-beleza-constants";

import { formatCurrency } from "@/lib/financeiro-helpers";
import type { LocalAtendimentoItem } from "@/lib/clinica-beleza-api";

interface FinalizarForm {
  payment_method: string;
  mark_as_paid: boolean;
  amount: string;
  local_atendimento: number | "";
}

export function ConsultaFinalizarModal({
  open,
  finalizando,
  form,
  valorConsulta,
  valorProcedimentos,
  locais,
  onClose,
  onChange,
  onConfirm,
}: {
  open: boolean;
  finalizando: boolean;
  form: FinalizarForm;
  valorConsulta?: string | number;
  valorProcedimentos?: string | number;
  locais: LocalAtendimentoItem[];
  onClose: () => void;
  onChange: (form: FinalizarForm) => void;
  onConfirm: () => void;
}) {
  const localSelecionado = locais.find((l) => l.id === form.local_atendimento);
  const taxaLocal = localSelecionado ? Number(localSelecionado.valor_consulta) : 0;
  const taxa = taxaLocal > 0 ? taxaLocal : Number(valorConsulta ?? 0);
  const procs = Number(valorProcedimentos ?? 0);
  const mostraDetalhe = taxa > 0 || procs > 0;
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-800 rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-4 border-b dark:border-neutral-700">
          <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">Finalizar consulta</h2>
          <button type="button" onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-neutral-700 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            A agenda será marcada como <strong>Concluída</strong>.
          </p>
          {locais.length > 0 && (
            <div>
              <label className="block text-sm font-medium mb-1">Local de atendimento</label>
              <select
                value={form.local_atendimento}
                onChange={(e) => {
                  const localId = e.target.value ? Number(e.target.value) : "";
                  const local = locais.find((l) => l.id === localId);
                  const novaTaxa = local ? Number(local.valor_consulta) : 0;
                  const totalSugerido = novaTaxa + procs;
                  onChange({
                    ...form,
                    local_atendimento: localId,
                    amount: totalSugerido > 0 ? String(totalSugerido) : form.amount,
                  });
                }}
                className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              >
                <option value="">Selecione o local</option>
                {locais.map((local) => (
                  <option key={local.id} value={local.id}>
                    {local.nome} — consulta {formatCurrency(local.valor_consulta)}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Necessário para calcular a comissão da consulta no relatório.
              </p>
            </div>
          )}
          <div>
            <label className="block text-sm font-medium mb-1">Valor (R$)</label>
            {mostraDetalhe && (
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1.5">
                {taxa > 0 && <>Consulta {formatCurrency(taxa)}</>}
                {taxa > 0 && procs > 0 && " + "}
                {procs > 0 && <>Procedimentos {formatCurrency(procs)}</>}
              </p>
            )}
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.amount}
              onChange={(e) => onChange({ ...form, amount: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
              placeholder="Calculado automaticamente"
            />
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Preenchido automaticamente. Ajuste somente se houver desconto ou acréscimo.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Forma de pagamento</label>
            <select
              value={form.payment_method}
              onChange={(e) => onChange({ ...form, payment_method: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-neutral-700 dark:border-neutral-600"
            >
              {Object.entries(CLINICA_FORMA_PAGAMENTO_LABEL).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={form.mark_as_paid}
              onChange={(e) => onChange({ ...form, mark_as_paid: e.target.checked })}
            />
            Registrar como pago agora
          </label>
          <div className="flex gap-2 pt-2">
            <button type="button" onClick={onClose} className="flex-1 py-2 rounded-lg border border-gray-300 dark:border-neutral-600">
              Cancelar
            </button>
            <button
              type="button"
              onClick={onConfirm}
              disabled={finalizando}
              className="flex-1 py-2 rounded-lg text-white disabled:opacity-50"
              style={{ backgroundColor: CLINICA_BELEZA_PRIMARY }}
            >
              {finalizando ? "Finalizando..." : "Confirmar"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
