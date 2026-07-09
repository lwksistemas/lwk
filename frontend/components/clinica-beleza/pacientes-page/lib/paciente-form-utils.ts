/**
 * Utilitários de formulário para o cadastro de pacientes.
 * Extraído de pacientes/page.tsx para reduzir o tamanho do componente principal.
 */

import {
  entityEmail,
  entityName,
  entityPhone,
  patientAddress,
  patientBirthDate,
  patientCpf,
  patientNotes,
} from '@/lib/clinica-beleza-entities';
import { formatTelefone, formatCpf, formatCep } from '@/lib/format-br';
import type { PacienteFormState } from '@/components/clinica-beleza/paciente-cadastro/paciente-cadastro-types';

export interface Patient {
  id: number;
  name?: string;
  nome?: string;
  phone?: string;
  telefone?: string;
  email?: string | null;
  cpf?: string | null;
  birth_date?: string | null;
  data_nascimento?: string | null;
  address?: string | null;
  endereco?: string | null;
  cidade?: string | null;
  estado?: string | null;
  city?: string | null;
  state?: string | null;
  notes?: string | null;
  observacoes?: string | null;
  active?: boolean;
  is_active?: boolean;
  allow_whatsapp?: boolean;
  convenio?: number | null;
  convenio_name?: string | null;
  foto_url?: string | null;
}

/**
 * Monta a string de endereço completa a partir do formulário.
 */
export function montarEnderecoPaciente(form: PacienteFormState): string {
  const partes: string[] = [];
  if (form.logradouro.trim()) partes.push(form.logradouro.trim());
  if (form.numero.trim()) partes.push(`Nº ${form.numero.trim()}`);
  if (form.complemento.trim()) partes.push(form.complemento.trim());
  if (form.bairro.trim()) partes.push(form.bairro.trim());
  if (form.cep.trim()) partes.push(`CEP ${form.cep.trim()}`);
  return partes.join(', ');
}

/**
 * Converte um objeto Patient nos campos de formulário PacienteFormState.
 */
export function patientToForm(p: Patient): PacienteFormState {
  const endereco = patientAddress(p) || '';
  const cepMatch = endereco.match(/CEP\s*(\d{5}-?\d{3})/i);
  const enderecoSemCep = endereco.replace(/,?\s*CEP\s*\d{5}-?\d{3}/i, '').trim();
  const partes = enderecoSemCep.split(',').map((s) => s.trim()).filter(Boolean);
  let logradouro = partes[0] || '';
  let numero = '';
  let complemento = '';
  let bairro = '';
  for (let i = 1; i < partes.length; i += 1) {
    const parte = partes[i];
    const numMatch = parte.match(/^N[º°o\.]?\s*(.+)$/i);
    if (numMatch && !numero) {
      numero = numMatch[1].trim();
    } else if (!bairro) {
      bairro = parte;
    } else if (!complemento) {
      complemento = parte;
    }
  }
  if (!logradouro && enderecoSemCep) {
    logradouro = enderecoSemCep;
  }
  return {
    name: entityName(p),
    phone: formatTelefone(entityPhone(p)),
    email: entityEmail(p) || '',
    cpf: formatCpf(patientCpf(p) || ''),
    birth_date: patientBirthDate(p) ? patientBirthDate(p)!.slice(0, 10) : '',
    cep: cepMatch ? formatCep(cepMatch[1]) : '',
    logradouro,
    numero,
    complemento,
    bairro,
    cidade: (p.cidade || p.city || '').trim(),
    uf: (p.estado || p.state || '').trim(),
    notes: patientNotes(p) || '',
    allow_whatsapp: p.allow_whatsapp !== false,
    convenio: p.convenio ?? '',
    foto_url: p.foto_url || '',
  };
}
