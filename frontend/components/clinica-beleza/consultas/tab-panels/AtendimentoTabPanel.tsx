import { ConsultaAtendimentoTab } from "../ConsultaAtendimentoTab";
import type { ConsultaDetailTabPanelsProps } from "./tab-panels-types";

const noop = () => {};

export function AtendimentoTabPanel({
  selected,
  consultaFinalizada,
  protocolos,
  protocoloPreview,
  editAtendimento,
  observacoes,
  observacoesDraft,
  saving,
  printMeta,
  procedimentosRealizados,
  onSelectProtocolo,
  onConfirmProtocolo,
  onCancelProtocolo,
  onStartEditAtendimento,
  onCancelEditAtendimento,
  onChangeObservacoesDraft,
  onSaveAtendimento,
  onRefreshConsulta,
}: ConsultaDetailTabPanelsProps) {
  return (
    <ConsultaAtendimentoTab
      consultaId={selected.id}
      protocolos={consultaFinalizada ? [] : protocolos}
      protocoloPreview={protocoloPreview}
      editAtendimento={consultaFinalizada ? false : editAtendimento}
      observacoes={observacoes}
      observacoesDraft={observacoesDraft}
      saving={saving}
      printMeta={printMeta}
      protocolName={selected.protocol_name}
      procedimentosRealizados={procedimentosRealizados}
      consultaFinalizada={consultaFinalizada}
      onSelectProtocolo={consultaFinalizada ? noop : onSelectProtocolo}
      onConfirmProtocolo={onConfirmProtocolo}
      onCancelProtocolo={onCancelProtocolo}
      onStartEdit={consultaFinalizada ? noop : onStartEditAtendimento}
      onCancelEdit={onCancelEditAtendimento}
      onChangeDraft={onChangeObservacoesDraft}
      onSave={onSaveAtendimento}
      onProcedimentosChanged={onRefreshConsulta}
    />
  );
}
