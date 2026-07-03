import { ConsultaAnamneseTab } from "../ConsultaAnamneseTab";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

const noop = () => {};

export function AnamneseTabPanel({
  consultaFinalizada,
  anamnese,
  anamneseDraft,
  editAnamnese,
  saving,
  printMeta,
  onStartEditAnamnese,
  onCancelEditAnamnese,
  onChangeAnamneseDraft,
  onSaveAnamnese,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaAnamneseTab
      anamnese={anamnese}
      anamneseDraft={anamneseDraft}
      editAnamnese={consultaFinalizada ? false : editAnamnese}
      saving={saving}
      printMeta={printMeta}
      onStartEdit={consultaFinalizada ? noop : onStartEditAnamnese}
      onCancelEdit={onCancelEditAnamnese}
      onChangeDraft={onChangeAnamneseDraft}
      onSave={onSaveAnamnese}
    />
  );
}
