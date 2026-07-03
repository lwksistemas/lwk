import type { Dispatch, SetStateAction } from "react";
import type { ConvenioItem } from "@/lib/clinica-beleza-api";

export const PACIENTE_EMPTY_FORM = {
  name: "",
  phone: "",
  email: "",
  cpf: "",
  birth_date: "",
  cep: "",
  logradouro: "",
  numero: "",
  complemento: "",
  bairro: "",
  cidade: "",
  uf: "",
  notes: "",
  allow_whatsapp: true,
  convenio: "" as number | "",
  foto_url: "",
};

export type PacienteFormState = typeof PACIENTE_EMPTY_FORM;

export const UF_LIST = [
  "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA",
  "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
  "RS", "RO", "RR", "SC", "SP", "SE", "TO",
];

export interface PacienteCadastroFormProps {
  editing: boolean;
  form: PacienteFormState;
  setForm: Dispatch<SetStateAction<PacienteFormState>>;
  error: string;
  saving: boolean;
  convenios: ConvenioItem[];
  buscarCepLoading: boolean;
  onCepChange: (value: string) => void;
  onBuscarCep: () => void;
  onSave: () => void;
  onCancel: () => void;
  accentColor?: string;
  lojaSlug: string;
  /** Quando false, o cabeçalho fica só no ClinicaBelezaStandardPageHeader (topbar). */
  showHeader?: boolean;
}
