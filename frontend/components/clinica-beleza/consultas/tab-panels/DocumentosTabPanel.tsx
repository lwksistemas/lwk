import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";
import { ConsultaDocumentosTabLazy } from "./tab-panels-lazy";

export function DocumentosTabPanel({
  selected,
  consultaAtiva,
  prescricoesRefresh,
  onUsarMemed,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaDocumentosTabLazy
      consultaId={selected.id}
      consultaAtiva={consultaAtiva}
      professionalId={selected.professional}
      onUsarMemed={onUsarMemed}
      refreshPrescricoes={prescricoesRefresh}
    />
  );
}
