import { telefoneInternacionalBr } from '@/lib/format-br';

export interface CrmFuncionario {
  id: number | string;
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  comissao_padrao?: number;
  is_admin: boolean;
  is_active: boolean;
  tem_acesso?: boolean;
  grupo_nome?: string;
  grupo_id?: number | null;
  permissoes_ids?: number[];
}

export interface CrmFuncionarioGrupo {
  id: number;
  name: string;
  permissoes_ids?: number[];
}

export interface CrmPermissaoItem {
  id: number;
  codename: string;
  nome: string;
}

export interface CrmPermissaoCategoria {
  categoria: string;
  permissoes: CrmPermissaoItem[];
}

export interface CrmFuncionarioFormData {
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  comissao_padrao: string;
  grupo_id: string;
  criar_acesso: boolean;
  username: string;
  permissoes_ids: number[];
}

export const EMPTY_FUNCIONARIO_FORM: CrmFuncionarioFormData = {
  nome: '',
  email: '',
  telefone: '',
  cargo: 'Vendedor',
  comissao_padrao: '0',
  grupo_id: '',
  criar_acesso: false,
  username: '',
  permissoes_ids: [],
};

export function suggestLoginFromNome(nome: string): string {
  const first = nome.trim().split(/\s+/)[0] || '';
  return first
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9._-]/g, '');
}

export function buildFuncionarioPayload(form: CrmFuncionarioFormData): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    nome: form.nome,
    email: form.email,
    telefone: form.telefone.trim() ? telefoneInternacionalBr(form.telefone) : '',
    cargo: form.cargo,
    comissao_padrao: parseFloat(form.comissao_padrao) || 0,
    criar_acesso: form.criar_acesso,
    username: form.username?.trim() || '',
    permissoes_ids: form.permissoes_ids,
  };
  if (form.grupo_id) {
    payload.grupo_id = parseInt(form.grupo_id, 10);
  }
  return payload;
}
