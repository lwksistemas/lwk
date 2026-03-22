export interface Hero {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
  botao_principal_ativo?: boolean;
  imagem?: string;
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

export interface HomepageData {
  hero: Hero | null;
  funcionalidades: Funcionalidade[];
  modulos: Modulo[];
}
