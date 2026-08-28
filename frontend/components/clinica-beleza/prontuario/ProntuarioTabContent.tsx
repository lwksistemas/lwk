import { ClinicaBelezaPanel } from "@/components/clinica-beleza/ClinicaBelezaPageContent";
import type { ProntuarioData } from "@/lib/clinica-beleza-api";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import { ProntuarioAnamneseSection } from "./ProntuarioAnamneseSection";
import { ProntuarioDocumentoCard } from "./ProntuarioDocumentoCard";
import { ProntuarioEvolucaoSection } from "./ProntuarioEvolucaoSection";
import { ProntuarioFotosSection } from "./ProntuarioFotosSection";
import { ProntuarioResumoSection } from "./ProntuarioResumoSection";
import { documentoCardKey, getProntuarioDocsForTab, isProntuarioDocTab } from "./prontuario-utils";
import type { ProntuarioTabId } from "./prontuario-types";

interface ProntuarioTabContentProps {
  data: ProntuarioData | null;
  activeTab: ProntuarioTabId;
  consultas: Consulta[];
  consultasLoading: boolean;
  consultaParaFotosId: number | null;
  iniciandoId: number | null;
  excluindoId: number | null;
  recebendoId: number | null;
  onAbrirConsulta: (consultaId: number) => void;
  onIniciarConsulta: (consulta: Consulta) => void;
  onReceberConsulta: (consulta: Consulta) => void;
  onExcluirConsulta: (consulta: Consulta) => void;
}

export function ProntuarioTabContent({
  data,
  activeTab,
  consultas,
  consultasLoading,
  consultaParaFotosId,
  iniciandoId,
  excluindoId,
  recebendoId,
  onAbrirConsulta,
  onIniciarConsulta,
  onReceberConsulta,
  onExcluirConsulta,
}: ProntuarioTabContentProps) {
  if (activeTab === "resumo") {
    return (
      <ProntuarioResumoSection
        consultas={consultas}
        loading={consultasLoading}
        iniciandoId={iniciandoId}
        excluindoId={excluindoId}
        recebendoId={recebendoId}
        onAbrirConsulta={onAbrirConsulta}
        onIniciarConsulta={onIniciarConsulta}
        onReceberConsulta={onReceberConsulta}
        onExcluirConsulta={onExcluirConsulta}
      />
    );
  }

  if (activeTab === "fotos") {
    return <ProntuarioFotosSection consultaId={consultaParaFotosId} />;
  }

  if (!data) {
    return (
      <ClinicaBelezaPanel className="p-12 text-center text-gray-500 dark:text-gray-400 text-sm">
        Não foi possível carregar esta seção. Tente novamente.
      </ClinicaBelezaPanel>
    );
  }

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
