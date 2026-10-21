import { telefoneInternacionalBr } from '@/lib/format-br';

export interface CrmFuncionario {
  id: number | string;
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  comissao_padrao?: number;
  comissoes_categoria?: ComissaoCategoriaItem[];
  is_admin: boolean;
  is_active: boolean;
  tem_acesso?: boolean;
  usuario_login?: string;
  grupo_nome?: string;
  grupo_id?: number | null;
  permissoes_ids?: number[];
  controle_qualidade?: boolean;
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

export interface ComissaoCategoriaItem {
  categoria_id: number;
  tipo: 'fixo' | 'percentual';
  valor: string;
}

export interface CrmFuncionarioFormData {
  nome: string;
  email: string;
  telefone: string;
  cargo: string;
  comissao_padrao: string;
  comissoes_categoria: ComissaoCategoriaItem[];
  grupo_id: string;
  criar_acesso: boolean;
  username: string;
  usuario_login: string;
  permissoes_ids: number[];
  controle_qualidade: boolean;
}

export const EMPTY_FUNCIONARIO_FORM: CrmFuncionarioFormData = {
  nome: '',
  email: '',
  telefone: '',
  cargo: 'Vendedor',
  comissao_padrao: '0',
  comissoes_categoria: [],
  grupo_id: '',
  criar_acesso: false,
  username: '',
  usuario_login: '',
  permissoes_ids: [],
  controle_qualidade: false,
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
    comissoes_categoria: (form.comissoes_categoria || [])
      .filter((item) => item.valor.trim() !== '')
      .map((item) => ({
        categoria_id: item.categoria_id,
        tipo: item.tipo,
        valor: item.valor.replace(',', '.'),
      })),
    criar_acesso: form.criar_acesso,
    username: form.username?.trim() || '',
    permissoes_ids: form.permissoes_ids,
    controle_qualidade: form.controle_qualidade,
  };
  if (form.grupo_id) {
    payload.grupo_id = parseInt(form.grupo_id, 10);
  }
  return payload;
}
