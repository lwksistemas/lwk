/**
 * Tipos do formulário de lead CRM.
 */

export interface FormDataLead {
  nome: string;
  empresa: string;
  cpf_cnpj: string;
  email: string;
  telefone: string;
  origem: string;
  status: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  observacoes: string;
}

export const EMPTY_FORM_LEAD: FormDataLead = {
  nome: '',
  empresa: '',
  cpf_cnpj: '',
  email: '',
  telefone: '',
  origem: 'site',
  status: 'novo',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  observacoes: '',
};
