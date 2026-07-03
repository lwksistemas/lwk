import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";
import { ConsultaFotosTabLazy } from "./tab-panels-lazy";

export function FotosTabPanel({
  tab,
  selected,
  consultaAtiva,
  onToolbarChange,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaFotosTabLazy
      consultaId={selected.id}
      permiteEnviar={consultaAtiva}
      ativa={tab === "fotos" && consultaAtiva}
      onToolbarChange={onToolbarChange}
    />
  );
}
