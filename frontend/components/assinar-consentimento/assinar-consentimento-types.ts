import type { TermoConsentimentoSecao } from "@/lib/clinica-beleza-api";

export interface RespostaTcleInterativo {
  sim_nao?: string;
  duvidas?: string;
  dum?: string;
  nao_me_recordo?: boolean;
  consinto?: string;
}

export interface TermoConsentimentoData {
  tipo_documento: string;
  tipo_termo?: "simples" | "interativo";
  titulo: string;
  procedimentos_nomes?: string;
  nome_assinante: string;
  tipo_assinante: string;
  tipo_assinante_display: string;
  paciente_nome: string;
  profissional_nome: string;
  clinica_nome: string;
  conteudo_termo: string;
  introducao?: string;
  secoes?: TermoConsentimentoSecao[];
}
