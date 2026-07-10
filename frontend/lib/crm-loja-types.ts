/**
 * Tipos de loja e lead partilhados pelos formulários CRM (proposta, contrato, emitente).
 */

export interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  cor_primaria?: string;
  endereco?: string | null;
  cpf_cnpj?: string | null;
  admin_nome?: string | null;
  admin_email?: string | null;
}

export interface LeadInfo {
  id: number;
  nome: string;
  empresa?: string;
  cpf_cnpj?: string;
  email?: string;
  telefone?: string;
  cep?: string;
  logradouro?: string;
  numero?: string;
  complemento?: string;
  bairro?: string;
  cidade?: string;
  uf?: string;
  conta_info?: {
    id: number;
    nome: string;
    razao_social?: string;
    cnpj?: string;
    inscricao_estadual?: string;
    email?: string;
    telefone?: string;
    site?: string;
    cep?: string;
    logradouro?: string;
    numero?: string;
    complemento?: string;
    bairro?: string;
    cidade?: string;
    uf?: string;
  } | null;
}
