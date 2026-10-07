import { PatientQuickRegisterField } from "@/components/clinica-beleza/patient-quick-register/PatientQuickRegisterField";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
import { rotuloIntervaloProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
import { formatCurrency } from "@/lib/financeiro-helpers";
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
}: Props) {
  return (
    <div className={protocoloCliente ? "flex h-full flex-col gap-4" : "space-y-4"}>
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
        <div className="flex flex-1 flex-col rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-neutral-700 dark:bg-neutral-900/50">
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
          <p className="mt-auto pt-3 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
            Depois de Cliente presente, o recebimento escolhe o valor total ou o parcelamento por sessão.
          </p>
        </div>
      ) : (
        <ProcedureMultiSelect
          procedures={procedures}
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
