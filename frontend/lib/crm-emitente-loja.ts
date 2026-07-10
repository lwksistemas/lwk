import type { LojaInfo } from '@/lib/crm-loja-types';

export interface EmitenteLojaFields {
  emitente_personalizado: boolean;
  emitente_nome: string;
  emitente_endereco: string;
  emitente_cpf_cnpj: string;
  emitente_responsavel: string;
  emitente_email: string;
}

export const EMPTY_EMITENTE_LOJA: EmitenteLojaFields = {
  emitente_personalizado: false,
  emitente_nome: '',
  emitente_endereco: '',
  emitente_cpf_cnpj: '',
  emitente_responsavel: '',
  emitente_email: '',
};

export interface EmitenteLojaApi {
  emitente_nome?: string | null;
  emitente_endereco?: string | null;
  emitente_cpf_cnpj?: string | null;
  emitente_responsavel?: string | null;
  emitente_email?: string | null;
}

export function lojaInfoParaEmitente(loja: LojaInfo | null): Omit<EmitenteLojaFields, 'emitente_personalizado'> {
  return {
    emitente_nome: loja?.nome ?? '',
    emitente_endereco: loja?.endereco ?? '',
    emitente_cpf_cnpj: loja?.cpf_cnpj ?? '',
    emitente_responsavel: loja?.admin_nome ?? '',
    emitente_email: loja?.admin_email ?? '',
  };
}

export function emitenteFieldsFromApi(data: EmitenteLojaApi): EmitenteLojaFields {
  const nome = (data.emitente_nome ?? '').trim();
  return {
    emitente_personalizado: Boolean(nome),
    emitente_nome: data.emitente_nome ?? '',
    emitente_endereco: data.emitente_endereco ?? '',
    emitente_cpf_cnpj: data.emitente_cpf_cnpj ?? '',
    emitente_responsavel: data.emitente_responsavel ?? '',
    emitente_email: data.emitente_email ?? '',
  };
}

export function emitentePayloadFromForm(fields: EmitenteLojaFields): EmitenteLojaApi {
  if (!fields.emitente_personalizado) {
    return {
      emitente_nome: '',
      emitente_endereco: '',
      emitente_cpf_cnpj: '',
      emitente_responsavel: '',
      emitente_email: '',
    };
  }
  return {
    emitente_nome: fields.emitente_nome.trim(),
    emitente_endereco: fields.emitente_endereco.trim(),
    emitente_cpf_cnpj: fields.emitente_cpf_cnpj.trim(),
    emitente_responsavel: fields.emitente_responsavel.trim(),
    emitente_email: fields.emitente_email.trim(),
  };
}

export function resumoEmitenteLoja(lojaInfo: LojaInfo | null, emitente: EmitenteLojaFields): string {
  if (emitente.emitente_personalizado && emitente.emitente_nome.trim()) {
    const doc = emitente.emitente_cpf_cnpj.trim();
    return doc ? `${emitente.emitente_nome.trim()} · ${doc}` : emitente.emitente_nome.trim();
  }
  if (!lojaInfo) return 'Carregando dados da loja...';
  const doc = lojaInfo.cpf_cnpj?.trim();
  const base = lojaInfo.nome || 'Loja';
  return doc ? `${base} · ${doc} · padrão da loja` : `${base} · padrão da loja`;
}
