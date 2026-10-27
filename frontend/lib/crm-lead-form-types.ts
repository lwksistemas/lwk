/**
 * Tipos do formulário de lead CRM.
 */

import { formatCep } from '@/lib/format-br';

export interface FormDataLead {
  nome: string;
  empresa: string;
  conta: string;
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
  conta: '',
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

export interface ContaDoLead {
  id: number;
  nome?: string;
  razao_social?: string;
  cnpj?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
}

function preencherSeVazio(atual: string, vindo?: string | null): string {
  if (atual.trim()) return atual;
  return (vindo || '').trim();
}

/** Liga o lead a uma conta já cadastrada e completa o endereço que ainda estiver vazio. */
export function leadComEmpresa(form: FormDataLead, conta: ContaDoLead | null): FormDataLead {
  if (!conta) {
    return { ...form, conta: '', empresa: '' };
  }
  return {
    ...form,
    conta: String(conta.id),
    empresa: (conta.nome || conta.razao_social || form.empresa).toUpperCase(),
    cep: preencherSeVazio(form.cep, conta.cep ? formatCep(conta.cep) : ''),
    logradouro: preencherSeVazio(form.logradouro, (conta.logradouro || '').toUpperCase()),
    numero: preencherSeVazio(form.numero, conta.numero || ''),
    complemento: preencherSeVazio(form.complemento, (conta.complemento || '').toUpperCase()),
    bairro: preencherSeVazio(form.bairro, (conta.bairro || '').toUpperCase()),
    cidade: preencherSeVazio(form.cidade, (conta.cidade || '').toUpperCase()),
    uf: preencherSeVazio(form.uf, (conta.uf || '').toUpperCase()),
  };
}
