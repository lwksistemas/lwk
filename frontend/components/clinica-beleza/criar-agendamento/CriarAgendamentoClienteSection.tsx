import { PatientQuickRegisterField } from "@/components/clinica-beleza/patient-quick-register/PatientQuickRegisterField";
import type { PatientQuickOption } from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-types";
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
  | "aplicarConvenioDoPaciente"
  | "precosMap"
  | "createLoading"
  | "handleCreatePatient"
  | "onPatientsChange"
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
}: Props) {
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
    </div>
  );
}
