import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";
import { ConsultaHistoricoTabLazy } from "./tab-panels-lazy";

export function HistoricoTabPanel({
  selected,
  historico,
  anamnese,
  prescricoes,
  observacoes,
  formatData,
  printMeta,
  onLoadDetalhes,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaHistoricoTabLazy
      historico={historico}
      selectedId={selected.id}
      consultaId={selected.id}
      anamnese={anamnese}
      prescricoes={prescricoes}
      observacoesAtual={observacoes}
      protocoloNotasAtual={selected.protocolo_notas}
      formatData={formatData}
      printMeta={printMeta}
      onSelect={onLoadDetalhes}
    />
  );
}
