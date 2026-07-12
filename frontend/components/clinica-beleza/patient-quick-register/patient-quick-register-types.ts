export interface PatientQuickOption {
  id: number;
  nome?: string;
  name?: string;
  telefone?: string;
  phone?: string;
  cpf?: string | null;
  email?: string | null;
  convenio?: number | null;
  foto_url?: string | null;
}

export interface PatientQuickRegisterFieldProps {
  patients: PatientQuickOption[];
  patientId: number | "";
  onSelect: (id: number) => void;
  onClear: () => void;
  onPatientCreated: (patient: PatientQuickOption) => void;
  onCreatePatient: (data: { nome: string; telefone: string; cpf: string }) => Promise<PatientQuickOption>;
  onSearchPatients?: (query: string) => Promise<PatientQuickOption[]>;
  disabled?: boolean;
}
