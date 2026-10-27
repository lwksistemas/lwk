import { PatientQuickRegisterField } from "@/components/clinica-beleza/patient-quick-register/PatientQuickRegisterField";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { rotuloIntervaloProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import { procedimentosSemCategoriaProtocolo } from "@/hooks/clinica-beleza/criar-agendamento/criar-agendamento-builders";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { ProtocoloCobrancaBox } from "./CriarAgendamentoAgendaSection";
import { SectionTitle } from "./CriarAgendamentoFormFields";

type Props = Pick<
  UseCriarAgendamentoReturn,
  | "patients"
  | "patientId"
  | "setPatientId"
  | "procedures"
  | "selectedProcedures"
  | "adicionarProcedimento"
  | "removerProcedimento"
  | "convenioId"
  | "aplicarConvenioDoPaciente"
  | "precosMap"
  | "createLoading"
  | "handleCreatePatient"
  | "onPatientsChange"
  | "protocoloCliente"
  | "protocoloSelecionado"
  | "agendaEhProtocolo"
  | "valorProtocolo"
  | "formaCobranca"
  | "setFormaCobranca"
  | "isConsulta"
  | "totalEstimado"
> & {
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
};

export function CriarAgendamentoClienteSection({
  patients,
  patientId,
  setPatientId,
  procedures,
  selectedProcedures,
  adicionarProcedimento,
  removerProcedimento,
  convenioId,
  aplicarConvenioDoPaciente,
  precosMap,
  createLoading,
  handleCreatePatient,
  onPatientsChange,
  onSearchPatients,
  protocoloCliente,
  protocoloSelecionado,
  agendaEhProtocolo,
  valorProtocolo,
  formaCobranca,
  setFormaCobranca,
  isConsulta,
  totalEstimado,
}: Props) {
  const proceduresDoHorario = procedimentosSemCategoriaProtocolo(procedures);
  return (
    <div className="space-y-4">
      <SectionTitle>Cliente</SectionTitle>
      <PatientQuickRegisterField
        patients={patients}
        patientId={patientId}
        onSelect={setPatientId}
        onSelectPatient={(p) => {
          const demais = patients.filter((item) => item.id !== p.id);
          onPatientsChange([...demais, p]);
          aplicarConvenioDoPaciente(p);
        }}
        onClear={() => setPatientId("")}
        onPatientCreated={(p) => onPatientsChange([...patients, p])}
        onCreatePatient={handleCreatePatient}
        onSearchPatients={onSearchPatients}
        disabled={createLoading}
      />
      {protocoloCliente ? (
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-neutral-700 dark:bg-neutral-900/50">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Protocolo desta cliente</p>
          <p className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-gray-100">{protocoloCliente.nome}</p>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Sessões</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">{protocoloCliente.sessoes}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Duração</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">{protocoloCliente.tempo_minutos} min</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Intervalo</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">
                {rotuloIntervaloProtocolo(protocoloCliente.intervalo_quantidade, protocoloCliente.intervalo_unidade)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Valor com desconto</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">{formatCurrency(protocoloCliente.valor_total)}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            Depois de Cliente presente, o recebimento escolhe o valor total ou o parcelamento por sessão.
          </p>
        </div>
      ) : agendaEhProtocolo && protocoloSelecionado ? (
        <div className="rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-neutral-700 dark:bg-neutral-900/50">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Modelo da clínica</p>
          <p className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-gray-100">{protocoloSelecionado.nome}</p>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Sessões</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">{protocoloSelecionado.sessoes || 1}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500 dark:text-gray-400">Duração</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">{protocoloSelecionado.tempo_estimado} min</dd>
            </div>
            <div className="col-span-2">
              <dt className="text-xs text-gray-500 dark:text-gray-400">Intervalo</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100">
                {rotuloIntervaloProtocolo(
                  protocoloSelecionado.intervalo_quantidade || 1,
                  protocoloSelecionado.intervalo_unidade || "dias",
                )}
              </dd>
            </div>
          </dl>
          <p className="mt-3 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            Ao salvar, este modelo vira o protocolo desta cliente e as sessões entram na agenda.
          </p>
          <div className="mt-3 border-t border-gray-200 pt-3 dark:border-neutral-700">
            <ProtocoloCobrancaBox
              nome={protocoloSelecionado.nome}
              sessoes={protocoloSelecionado.sessoes || 1}
              intervaloQuantidade={protocoloSelecionado.intervalo_quantidade || 1}
              intervaloUnidade={protocoloSelecionado.intervalo_unidade || "dias"}
              valorPacote={valorProtocolo}
              forma={formaCobranca}
              onForma={setFormaCobranca}
              isConsulta={isConsulta}
              totalDestaVisita={totalEstimado}
              ocultarResumo
            />
          </div>
        </div>
      ) : agendaEhProtocolo ? (
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {patientId
            ? "Escolha o protocolo na coluna Agendamento."
            : "Selecione a cliente. O protocolo é escolhido na coluna Agendamento."}
        </p>
      ) : (
        <ProcedureMultiSelect
          procedures={proceduresDoHorario}
          selectedIds={selectedProcedures}
          onAdd={adicionarProcedimento}
          onRemove={removerProcedimento}
          convenioId={convenioId}
          precosMap={precosMap}
          showSummary={selectedProcedures.length > 1}
          optional
        />
      )}
    </div>
  );
}
