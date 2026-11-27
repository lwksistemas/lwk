import { ClipboardList } from "lucide-react";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import { procedimentosSemCategoriaProtocolo } from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-builders";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { AgendamentoResumoCard } from "./AgendamentoResumoCard";
import { AgendamentoSectionCard } from "./AgendamentoSectionCard";
import { CriarAgendamentoAdvancedSection } from "./CriarAgendamentoAdvancedSection";

type Props = Pick<
  UseCriarAgendamentoReturn,
  | "procedures"
  | "selectedProcedures"
  | "adicionarProcedimento"
  | "removerProcedimento"
  | "convenioId"
  | "precosMap"
  | "agendaEhProtocolo"
  | "taxaConsultaBase"
  | "totalEstimado"
  | "resumo"
  | "retornoInfo"
  | "notes"
  | "setNotes"
  | "showAdvanced"
  | "setShowAdvanced"
  | "retornoProcAtivo"
  | "regrasRetornoProc"
  | "patientId"
  | "retornoProcedureId"
  | "setRetornoProcedureId"
  | "verificandoRetorno"
  | "protocoloSelecionado"
  | "protocoloCliente"
>;

export function CriarAgendamentoDireitaSection({
  procedures,
  selectedProcedures,
  adicionarProcedimento,
  removerProcedimento,
  convenioId,
  precosMap,
  agendaEhProtocolo,
  taxaConsultaBase,
  totalEstimado,
  resumo,
  retornoInfo,
  notes,
  setNotes,
  showAdvanced,
  setShowAdvanced,
  retornoProcAtivo,
  regrasRetornoProc,
  patientId,
  retornoProcedureId,
  setRetornoProcedureId,
  verificandoRetorno,
  protocoloSelecionado,
  protocoloCliente,
}: Props) {
  const proceduresDoHorario = procedimentosSemCategoriaProtocolo(procedures);
  const taxaZerada = Boolean(retornoInfo?.elegivel);
  const retornoTexto =
    retornoInfo?.elegivel && retornoInfo.mensagem
      ? retornoInfo.mensagem
      : retornoInfo?.elegivel
        ? "Retorno gratuito"
        : "Não informado";

  const duracaoMinutos =
    protocoloCliente?.tempo_minutos ||
    protocoloSelecionado?.tempo_estimado ||
    resumo.duracao ||
    0;

  return (
    <div className="space-y-2.5">
      {!agendaEhProtocolo ? (
        <AgendamentoSectionCard icon={ClipboardList} title="Procedimentos">
          <ProcedureMultiSelect
            procedures={proceduresDoHorario}
            selectedIds={selectedProcedures}
            onAdd={adicionarProcedimento}
            onRemove={removerProcedimento}
            convenioId={convenioId}
            precosMap={precosMap}
            optional
            hideLabel
            hint="Opcional — pode agendar só a consulta."
          />
        </AgendamentoSectionCard>
      ) : null}

      <AgendamentoResumoCard
        taxaConsultaBase={taxaConsultaBase}
        taxaZerada={taxaZerada}
        procedimentosValor={agendaEhProtocolo ? 0 : resumo.valor}
        procedimentosCount={agendaEhProtocolo ? 0 : selectedProcedures.length}
        totalEstimado={totalEstimado}
        duracaoMinutos={Number(duracaoMinutos) || 0}
        retornoTexto={retornoTexto}
      >
        <CriarAgendamentoAdvancedSection
          showAdvanced={showAdvanced}
          setShowAdvanced={setShowAdvanced}
          retornoProcAtivo={retornoProcAtivo}
          regrasRetornoProc={regrasRetornoProc}
          patientId={patientId}
          retornoProcedureId={retornoProcedureId}
          setRetornoProcedureId={setRetornoProcedureId}
          verificandoRetorno={verificandoRetorno}
          retornoInfo={retornoInfo}
          notes={notes}
          setNotes={setNotes}
          protocoloSelecionado={protocoloSelecionado}
          protocoloCliente={protocoloCliente}
          hideNotes
        />
      </AgendamentoResumoCard>
    </div>
  );
}
