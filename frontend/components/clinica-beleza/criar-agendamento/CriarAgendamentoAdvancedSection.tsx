import { ChevronDown, ChevronUp } from "lucide-react";
import { CRIAR_AGENDAMENTO_INPUT_CLASS } from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { FieldLabel } from "./CriarAgendamentoFormFields";

type Props = Pick<
  UseCriarAgendamentoReturn,
  | "showAdvanced"
  | "setShowAdvanced"
  | "retornoProcAtivo"
  | "regrasRetornoProc"
  | "patientId"
  | "retornoProcedureId"
  | "setRetornoProcedureId"
  | "verificandoRetorno"
  | "retornoInfo"
  | "notes"
  | "setNotes"
>;

export function CriarAgendamentoAdvancedSection({
  showAdvanced,
  setShowAdvanced,
  retornoProcAtivo,
  regrasRetornoProc,
  patientId,
  retornoProcedureId,
  setRetornoProcedureId,
  verificandoRetorno,
  retornoInfo,
  notes,
  setNotes,
}: Props) {
  const inputClass = CRIAR_AGENDAMENTO_INPUT_CLASS;

  return (
    <div className="mt-6 pt-6 border-t border-gray-100 dark:border-neutral-800 space-y-3">
      <button
        type="button"
        onClick={() => setShowAdvanced((v) => !v)}
        className="w-full flex items-center justify-between gap-2 text-sm font-medium text-gray-700 dark:text-gray-300"
      >
        <span>Mais opções (retorno, observações…)</span>
        {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {showAdvanced && (
        <div className="space-y-4 pt-2">
          {retornoProcAtivo && regrasRetornoProc.length > 0 && patientId && (
            <div>
              <FieldLabel>Retorno do procedimento</FieldLabel>
              <select
                value={retornoProcedureId}
                onChange={(e) => setRetornoProcedureId(e.target.value ? Number(e.target.value) : "")}
                className={inputClass}
              >
                <option value="">Não é retorno de procedimento</option>
                {regrasRetornoProc.map((r) => (
                  <option key={r.id} value={r.procedure}>
                    {r.procedure_name} — prazo {r.dias_retorno} dias
                  </option>
                ))}
              </select>
            </div>
          )}

          {verificandoRetorno && patientId && !retornoInfo?.elegivel && (
            <p className="text-xs text-gray-500 dark:text-gray-400">Verificando retorno...</p>
          )}

          <div>
            <FieldLabel>Observações</FieldLabel>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              className={`${inputClass} resize-y min-h-[72px]`}
              placeholder="Opcional"
            />
          </div>
        </div>
      )}
    </div>
  );
}
