import { ConsultaEvolucaoTab } from "../ConsultaEvolucaoTab";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

const noop = () => {};

export function EvolucaoTabPanel({
  consultaFinalizada,
  evolucoes,
  editEvolucao,
  evolucaoForm,
  saving,
  formatData,
  printMeta,
  onStartEditEvolucao,
  onCancelEditEvolucao,
  onChangeEvolucaoForm,
  onSaveEvolucao,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaEvolucaoTab
      evolucoes={evolucoes}
      editEvolucao={consultaFinalizada ? false : editEvolucao}
      evolucaoForm={evolucaoForm}
      saving={saving}
      formatData={formatData}
      printMeta={printMeta}
      onStartEdit={consultaFinalizada ? noop : onStartEditEvolucao}
      onCancelEdit={onCancelEditEvolucao}
      onChangeForm={onChangeEvolucaoForm}
      onSave={onSaveEvolucao}
    />
  );
}
