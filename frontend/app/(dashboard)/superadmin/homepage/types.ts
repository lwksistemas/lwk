export interface HeroData {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
  ativo?: boolean;
}

export interface FuncionalidadeData {
  id?: number;
  titulo: string;
  descricao: string;
  icone: string;
  imagem?: string;
  ordem?: number;
  ativo?: boolean;
}

export interface ModuloData {
  id?: number;
  nome: string;
  descricao: string;
  slug: string;
  icone: string;
  imagem?: string;
  ordem?: number;
  ativo?: boolean;
}

export interface WhyUsData {
  id?: number;
  titulo: string;
  descricao?: string;
  icone?: string;
  ordem?: number;
  ativo?: boolean;
}

export interface HeroImagemData {
  id?: number;
  imagem: string;
  titulo: string;
  ordem?: number;
  ativo?: boolean;
}

export interface EmpresaFormData {
  nome_empresa: string;
  cnpj: string;
  endereco: string;
  telefone_whatsapp: string;
  mensagem_whatsapp: string;
  email_contato: string;
}

export type FilterAtivo = 'all' | 'ativo' | 'inativo';
export type ItemType = 'func' | 'mod' | 'whyus' | 'heroimg';
export type BulkActionType = 'ativar' | 'desativar' | 'excluir';

export interface DeleteConfirm {
  type: ItemType;
  id: number;
  nome: string;
}

export const API = {
  hero: '/superadmin/homepage/hero/',
  funcionalidades: '/superadmin/homepage/funcionalidades/',
  modulos: '/superadmin/homepage/modulos/',
  whyus: '/superadmin/homepage/whyus/',
  heroImagens: '/superadmin/homepage/hero-imagens/',
  empresa: '/superadmin/homepage/empresa/',
};
