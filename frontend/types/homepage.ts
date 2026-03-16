export interface Hero {
  id?: number;
  titulo: string;
  subtitulo: string;
  botao_texto: string;
}

export interface Funcionalidade {
  id: number;
  titulo: string;
  descricao: string;
  icone?: string;
}

export interface Modulo {
  id: number;
  nome: string;
  descricao: string;
  slug?: string;
  icone?: string;
}

export interface HomepageData {
  hero: Hero | null;
  funcionalidades: Funcionalidade[];
  modulos: Modulo[];
}
