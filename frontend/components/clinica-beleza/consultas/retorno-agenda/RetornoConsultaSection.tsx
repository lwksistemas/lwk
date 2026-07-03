import type { AgendaRetornoConfigItem } from "@/lib/clinica-beleza-api";
import { RETORNO_INPUT_CLASS } from "./retorno-agenda-utils";

export function RetornoConsultaSection({
  config,
  salvando,
  onToggleAtivo,
  onChangeDias,
  onBlurDias,
}: {
  config: AgendaRetornoConfigItem;
  salvando: boolean;
  onToggleAtivo: (ativo: boolean) => void;
  onChangeDias: (dias: number) => void;
  onBlurDias: () => void;
}) {
  return (
    <section className="space-y-3">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Retorno por consulta</h3>
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Paciente com consulta concluída retorna dentro do prazo → não paga taxa de consulta.
      </p>
      <label className="flex items-center gap-2 text-sm text-gray-800 dark:text-gray-200">
        <input
          type="checkbox"
          checked={config.retorno_consulta_ativo}
          disabled={salvando}
          onChange={(e) => onToggleAtivo(e.target.checked)}
          className="rounded border-gray-300"
        />
        Ativar retorno por consulta
      </label>
      {config.retorno_consulta_ativo && (
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">
            Prazo (dias)
          </label>
          <input
            type="number"
            min={1}
            max={3650}
            value={config.dias_retorno_consulta}
            disabled={salvando}
            onChange={(e) => {
              const v = parseInt(e.target.value, 10);
              if (v > 0) onChangeDias(v);
            }}
            onBlur={onBlurDias}
            className={`${RETORNO_INPUT_CLASS} max-w-[120px]`}
          />
        </div>
      )}
    </section>
  );
}
