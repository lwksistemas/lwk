import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import type { ProntuarioData } from "@/lib/clinica-beleza-api";
import { ProntuarioAnamneseSection } from "./ProntuarioAnamneseSection";
import { ProntuarioDocumentoCard } from "./ProntuarioDocumentoCard";
import { ProntuarioEvolucaoSection } from "./ProntuarioEvolucaoSection";
import { documentoCardKey, getProntuarioDocsForTab, isProntuarioDocTab } from "./prontuario-utils";
import type { ProntuarioTabId } from "./prontuario-types";

interface ProntuarioTabContentProps {
  data: ProntuarioData;
  activeTab: ProntuarioTabId;
}

export function ProntuarioTabContent({ data, activeTab }: ProntuarioTabContentProps) {
  if (activeTab === "anamnese") {
    return <ProntuarioAnamneseSection anamnese={data.anamnese} />;
  }

  if (activeTab === "evolucao") {
    return <ProntuarioEvolucaoSection evolucoes={data.evolucao} />;
  }

  if (!isProntuarioDocTab(activeTab)) {
    return null;
  }

  const docs = getProntuarioDocsForTab(data, activeTab);
  if (docs.length === 0) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Nenhum registro encontrado nesta seção.
      </ClinicaBelezaPanel>
    );
  }

  return (
    <div className="space-y-4">
      {docs.map((doc) => (
        <ProntuarioDocumentoCard key={documentoCardKey(doc)} doc={doc} />
      ))}
    </div>
  );
}
