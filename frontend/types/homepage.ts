export interface Hero {
  id?: number;
  titulo: string;
  subtitulo: string;
  selo?: string;
  botao_texto: string;
  botao_url?: string;
  botao_principal_ativo?: boolean;
  botao_secundario_texto?: string;
  botao_secundario_url?: string;
  botao_secundario_ativo?: boolean;
  intervalo_carrossel?: number;
  titulo_destaque?: string;
  fonte_familia?: string;
  fonte_tamanho?: string;
  rotulos_botoes?: Record<string, string>;
}

export interface Funcionalidade {
  id: number;
  titulo: string;
  descricao: string;
  icone?: string;
  imagem?: string;
  link?: string;
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
  link?: string;
}

export interface ItemMenu {
  id?: number;
  rotulo: string;
  url: string;
  grupo?: string;
}

export interface MenuSite {
  solucoes: ItemMenu[];
  segmentos: ItemMenu[];
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
  menu?: MenuSite;
  paginas?: PaginaHome[];
}

export interface PaginaHome {
  slug: string;
  titulo: string;
  resumo: string;
  corpo: string;
  itens: string;
  imagem?: string;
  ativo?: boolean;
}
