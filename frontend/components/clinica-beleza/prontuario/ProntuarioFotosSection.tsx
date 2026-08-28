"use client";

import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import { ConsultaFotosTab } from "@/components/clinica-beleza/consultas/ConsultaFotosTab";

interface ProntuarioFotosSectionProps {
  consultaId: number | null;
}

export function ProntuarioFotosSection({ consultaId }: ProntuarioFotosSectionProps) {
  if (!consultaId) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-sm text-gray-500 dark:text-gray-400">
        Nenhuma foto ainda. As fotos são enviadas somente dentro de uma consulta.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-gray-500 dark:text-gray-400">
        Visualização do acompanhamento. Para incluir ou remover fotos, abra a consulta atual.
      </p>
      <ConsultaFotosTab consultaId={consultaId} permiteEnviar={false} ativa ocultarAvisoFinalizada />
    </div>
  );
}
