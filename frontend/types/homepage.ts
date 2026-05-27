export interface Hero {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
}

export interface Funcionalidade {
  id: number;
  titulo: string;
  descricao: string;
  icone?: string;
  imagem?: string;
}

export interface Modulo {
  id: number;
  nome: string;
  descricao: string;
  slug?: string;
  icone?: string;
  imagem?: string;
}

export interface WhyUsBenefit {
  id: number;
  titulo: string;
  descricao?: string;
  icone?: string;
}

export interface HeroImagem {
  id: number;
  imagem: string;
  titulo: string;
}

export interface EmpresaConfig {
  id?: number;
  nome_empresa: string;
  cnpj: string;
  endereco: string;
  telefone_whatsapp: string;
  mensagem_whatsapp: string;
  email_contato: string;
}

export interface HomepageData {
  hero: Hero | null;
  hero_imagens: HeroImagem[];
  funcionalidades: Funcionalidade[];
  modulos: Modulo[];
  whyus: WhyUsBenefit[];
  empresa: EmpresaConfig | null;
}
