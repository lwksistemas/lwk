import { PatientQuickRegisterField } from "@/components/clinica-beleza/PatientQuickRegisterField";
import { ProcedureMultiSelect } from "@/components/clinica-beleza/ProcedureMultiSelect";
import type { UseCriarAgendamentoReturn } from "@/hooks/clinica-beleza/useCriarAgendamento";
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
  | "precosMap"
  | "createLoading"
  | "handleCreatePatient"
  | "onPatientsChange"
> & {
  onSearchPatients?: (query: string) => Promise<import("@/components/clinica-beleza/PatientQuickRegisterField").PatientQuickOption[]>;
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
  precosMap,
  createLoading,
  handleCreatePatient,
  onPatientsChange,
  onSearchPatients,
}: Props) {
  return (
    <div className="space-y-4">
      <SectionTitle>Cliente</SectionTitle>
      <PatientQuickRegisterField
        patients={patients}
        patientId={patientId}
        onSelect={setPatientId}
        onClear={() => setPatientId("")}
        onPatientCreated={(p) => onPatientsChange([...patients, p])}
        onCreatePatient={handleCreatePatient}
        onSearchPatients={onSearchPatients}
        disabled={createLoading}
      />
      <ProcedureMultiSelect
        procedures={procedures}
        selectedIds={selectedProcedures}
        onAdd={adicionarProcedimento}
        onRemove={removerProcedimento}
        convenioId={convenioId}
        precosMap={precosMap}
        optional
      />
    </div>
  );
}
