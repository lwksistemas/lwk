import { imprimirConsultaPdfLazy, type ConsultaPrintMeta } from "@/lib/consulta-print-lazy";
import type { Anamnese } from "../consultas-types";
import { ANAMNESE_FIELDS } from "../consultas-types";
import { ConsultaPrintButton } from "../ConsultaPrintButton";

export function HistoricoAnamneseSection({
  anamnese,
  printMeta,
}: {
  anamnese: Anamnese;
  printMeta: ConsultaPrintMeta;
}) {
  const preenchidos = ANAMNESE_FIELDS.filter(([key]) => {
    const val = anamnese[key as keyof Anamnese];
    return val != null && String(val).trim() !== "";
  });

  if (preenchidos.length === 0) {
    return <p className="text-gray-500 text-sm">Nenhum dado de anamnese registrado para este paciente.</p>;
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <ConsultaPrintButton onPrint={() => imprimirConsultaPdfLazy(printMeta.consultaId, "anamnese")} />
      </div>
      {preenchidos.map(([key, label]) => (
        <div key={key}>
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap mt-0.5">
            {String(anamnese[key as keyof Anamnese])}
          </p>
        </div>
      ))}
      {(anamnese.peso || anamnese.altura) && (
        <div className="flex gap-6 text-sm text-gray-700 dark:text-gray-300">
          {anamnese.peso ? (
            <span>
              <strong>Peso:</strong> {anamnese.peso} kg
            </span>
          ) : null}
          {anamnese.altura ? (
            <span>
              <strong>Altura:</strong> {anamnese.altura} m
            </span>
          ) : null}
        </div>
      )}
    </div>
  );
}
