import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import type { ProntuarioEvolucaoItem } from "@/lib/clinica-beleza-api";
import { extractEvolucaoDisplayFields, formatProntuarioDate } from "./prontuario-utils";

interface ProntuarioEvolucaoSectionProps {
  evolucoes: ProntuarioEvolucaoItem[] | null | undefined;
}

export function ProntuarioEvolucaoSection({ evolucoes }: ProntuarioEvolucaoSectionProps) {
  if (!evolucoes || evolucoes.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhuma evolução registrada para este paciente.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-4">
      {evolucoes.map((evo) => (
        <ClinicaBelezaPanel key={evo.id} className="p-5">
          <div className="flex items-start justify-between gap-4 mb-2">
            <div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Evolução</h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                {evo.professional_name && <span>{evo.professional_name} · </span>}
                {evo.created_at ? formatProntuarioDate(evo.created_at) : "—"}
                {evo.consulta_id && <span className="ml-2">Consulta #{evo.consulta_id}</span>}
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {extractEvolucaoDisplayFields(evo).map(({ label, value }) => (
              <div key={label}>
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-0.5">{label}</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{value}</p>
              </div>
            ))}
          </div>
        </ClinicaBelezaPanel>
      ))}
    </div>
  );
}
