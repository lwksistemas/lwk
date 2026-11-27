import { UserRound } from "lucide-react";
import { PatientQuickRegisterField } from "@/components/clinica-beleza/patient-quick-register/PatientQuickRegisterField";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { rotuloIntervaloProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { CRIAR_AGENDAMENTO_INPUT_CLASS } from "@/components/clinica-beleza/criar-agendamento/criar-agendamento-utils";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { formatCurrency } from "@/lib/financeiro-helpers";
import { AgendamentoSectionCard } from "./AgendamentoSectionCard";
import { CriarAgendamentoProtocoloEscolha, ProtocoloCobrancaBox } from "./CriarAgendamentoAgendaSection";

type Props = Pick<
  UseCriarAgendamentoReturn,
  | "patients"
  | "patientId"
  | "setPatientId"
  | "aplicarConvenioDoPaciente"
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
  | "protocolosClienteCarregando"
  | "protocolosDaCliente"
  | "protocolos"
  | "protocoloClienteId"
  | "setProtocoloClienteId"
  | "protocoloModeloId"
  | "setProtocoloModeloId"
  | "setSelectedProcedures"
> & {
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
};

export function CriarAgendamentoClienteSection({
  patients,
  patientId,
  setPatientId,
  aplicarConvenioDoPaciente,
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
  protocolosClienteCarregando,
  protocolosDaCliente,
  protocolos,
  protocoloClienteId,
  setProtocoloClienteId,
  protocoloModeloId,
  setProtocoloModeloId,
  setSelectedProcedures,
}: Props) {
  return (
    <div className="space-y-4">
      <AgendamentoSectionCard icon={UserRound} title="Paciente">
        <PatientQuickRegisterField
          variant="agenda"
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
      </AgendamentoSectionCard>

      {protocoloCliente ? (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-3.5 shadow-sm">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Protocolo desta cliente</p>
          <p className="mt-0.5 text-sm font-semibold text-gray-900 dark:text-gray-100">{protocoloCliente.nome}</p>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-500">Sessões</dt>
              <dd className="font-medium">{protocoloCliente.sessoes}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Duração</dt>
              <dd className="font-medium">{protocoloCliente.tempo_minutos} min</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Intervalo</dt>
              <dd className="font-medium">
                {rotuloIntervaloProtocolo(protocoloCliente.intervalo_quantidade, protocoloCliente.intervalo_unidade)}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Valor com desconto</dt>
              <dd className="font-medium">{formatCurrency(protocoloCliente.valor_total)}</dd>
            </div>
          </dl>
          <div className="mt-3 border-t border-gray-200 pt-3 dark:border-neutral-700">
            <ProtocoloCobrancaBox
              nome={protocoloCliente.nome}
              sessoes={protocoloCliente.sessoes || 1}
              intervaloQuantidade={protocoloCliente.intervalo_quantidade || 1}
              intervaloUnidade={protocoloCliente.intervalo_unidade || "dias"}
              valorPacote={Number(protocoloCliente.valor_total) || 0}
              forma={formaCobranca}
              onForma={setFormaCobranca}
              isConsulta={isConsulta}
              totalDestaVisita={totalEstimado}
              ocultarResumo
            />
          </div>
        </div>
      ) : agendaEhProtocolo && protocoloSelecionado ? (
        <div className="rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-3.5 shadow-sm">
          <p className="text-xs font-medium text-gray-500">Modelo da clínica</p>
          <p className="mt-0.5 text-sm font-semibold">{protocoloSelecionado.nome}</p>
          <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-gray-500">Sessões</dt>
              <dd className="font-medium">{protocoloSelecionado.sessoes || 1}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Duração</dt>
              <dd className="font-medium">{protocoloSelecionado.tempo_estimado} min</dd>
            </div>
          </dl>
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
      ) : agendaEhProtocolo && patientId ? (
        <CriarAgendamentoProtocoloEscolha
          inputClass={CRIAR_AGENDAMENTO_INPUT_CLASS}
          protocolosClienteCarregando={protocolosClienteCarregando}
          protocolosDaCliente={protocolosDaCliente}
          protocolos={protocolos}
          protocoloClienteId={protocoloClienteId}
          setProtocoloClienteId={setProtocoloClienteId}
          protocoloModeloId={protocoloModeloId}
          setProtocoloModeloId={setProtocoloModeloId}
          setSelectedProcedures={setSelectedProcedures}
          protocoloSelecionado={protocoloSelecionado}
        />
      ) : agendaEhProtocolo ? (
        <p className="text-sm text-gray-500 dark:text-gray-400 px-1">
          Selecione a cliente para escolher o protocolo.
        </p>
      ) : null}
    </div>
  );
}
