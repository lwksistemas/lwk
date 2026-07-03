import { ConsultaProdutosTab } from "../ConsultaProdutosTab";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

export function ProdutosTabPanel({
  selected,
  consultaFinalizada,
  printMeta,
  onRefreshConsulta,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaProdutosTab
      consultaId={selected.id}
      somenteLeitura={consultaFinalizada}
      printMeta={printMeta}
      onItensChanged={onRefreshConsulta}
    />
  );
}
