import type { ComponentType } from "react";
import type { TabId } from "../consultas-types";
import { AnamneseTabPanel } from "./AnamneseTabPanel";
import { AtendimentoTabPanel } from "./AtendimentoTabPanel";
import { DocumentosTabPanel } from "./DocumentosTabPanel";
import { EvolucaoTabPanel } from "./EvolucaoTabPanel";
import { FotosTabPanel } from "./FotosTabPanel";
import { HistoricoTabPanel } from "./HistoricoTabPanel";
import { ProdutosTabPanel } from "./ProdutosTabPanel";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

const TAB_PANELS: Record<TabId, ComponentType<ConsultaDetailTabPanelsProps>> = {
  produtos: ProdutosTabPanel,
  atendimento: AtendimentoTabPanel,
  anamnese: AnamneseTabPanel,
  evolucao: EvolucaoTabPanel,
  fotos: FotosTabPanel,
  historico: HistoricoTabPanel,
  documentos: DocumentosTabPanel,
};

export function ConsultaTabPanelRouter(props: ConsultaDetailTabPanelsProps) {
  const Panel = TAB_PANELS[props.tab];
  if (!Panel) return null;
  return <Panel {...props} />;
}
