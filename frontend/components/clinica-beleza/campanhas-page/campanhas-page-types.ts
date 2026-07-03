export interface Campanha {
  id: number;
  titulo: string;
  mensagem: string;
  data_inicio: string | null;
  data_fim: string | null;
  ativa: boolean;
  enviada_em: string | null;
  total_enviados: number;
  created_at: string;
}

export interface CampanhaFormState {
  titulo: string;
  mensagem: string;
  data_inicio: string;
  data_fim: string;
  ativa: boolean;
}

export const EMPTY_CAMPANHA_FORM: CampanhaFormState = {
  titulo: "",
  mensagem: "",
  data_inicio: "",
  data_fim: "",
  ativa: true,
};
