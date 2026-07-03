import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import type { ProntuarioAnamneseItem } from "@/lib/clinica-beleza-api";
import { extractAnamneseDisplayFields, formatProntuarioDate } from "./prontuario-utils";

interface ProntuarioAnamneseSectionProps {
  anamnese: ProntuarioAnamneseItem | null | undefined;
}

export function ProntuarioAnamneseSection({ anamnese }: ProntuarioAnamneseSectionProps) {
  if (!anamnese) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhuma anamnese registrada para este paciente.
      </ClinicaBelezaPanel>
    );
  }

  const fields = extractAnamneseDisplayFields(anamnese);

  if (fields.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Anamnese sem dados preenchidos.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <ClinicaBelezaPanel className="p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Anamnese</h3>
        {anamnese.updated_at && (
          <span className="text-xs text-gray-500 dark:text-gray-400">
            Atualizado em {formatProntuarioDate(anamnese.updated_at)}
          </span>
        )}
      </div>
      <div className="space-y-4">
        {fields.map(({ label, value }) => (
          <div key={label}>
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-1">
              {label}
            </p>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{value}</p>
          </div>
        ))}
      </div>
    </ClinicaBelezaPanel>
  );
}
