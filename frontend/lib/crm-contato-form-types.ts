export interface CrmContatoFormData {
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  conta: string;
  observacoes: string;
}

export const EMPTY_CONTATO_FORM: CrmContatoFormData = {
  nome: '',
  email: '',
  telefone: '',
  cargo: '',
  conta: '',
  observacoes: '',
};
