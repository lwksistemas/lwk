export type SexoPaciente = '' | 'M' | 'F' | 'I';

export type TipoConsulta = 'consulta' | 'primeira' | 'retorno';

export type ModalidadeConsulta = 'presencial' | 'tele';

export type StatusConsulta =
  | 'agendado'
  | 'confirmado'
  | 'recepcionado'
  | 'desmarcado'
  | 'faltou';

export interface Responsavel {
  id?: number;
  nome: string;
  profissao: string;
  parentesco: string;
  telefone: string;
}

export interface ConvenioPaciente {
  id?: number;
  convenio: string;
  plano: string;
  carteirinha: string;
  validade: string | null;
}

export interface PacienteLista {
  id: number;
  nome: string;
  nome_social: string;
  telefone: string;
  email: string;
  cpf: string;
}

export interface Paciente extends PacienteLista {
  numero_prontuario: string;
  medico_referencia: string;
  data_nascimento: string | null;
  sexo: SexoPaciente;
  estado_civil: string;
  rg: string;
  passaporte: string;
  nome_mae: string;
  tipo_sanguineo: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  observacoes: string;
  responsaveis: Responsavel[];
  convenios: ConvenioPaciente[];
  created_at?: string;
}

export interface Consulta {
  id: number;
  paciente: number;
  paciente_nome: string;
  paciente_telefone: string;
  paciente_email: string;
  data: string;
  hora: string;
  tipo: TipoConsulta;
  modalidade: ModalidadeConsulta;
  convenio: string;
  status: StatusConsulta;
  observacoes: string;
}

export interface DiaHorariosLivres {
  data: string;
  horarios: string[];
}

export const TIPO_CONSULTA_LABEL: Record<TipoConsulta, string> = {
  consulta: 'Consulta',
  primeira: 'Primeira consulta',
  retorno: 'Retorno',
};

export const MODALIDADE_LABEL: Record<ModalidadeConsulta, string> = {
  presencial: 'Consulta presencial',
  tele: 'Teleconsulta',
};

export const STATUS_LABEL: Record<StatusConsulta, string> = {
  agendado: 'Agendado',
  confirmado: 'Confirmado',
  recepcionado: 'Recepcionado',
  desmarcado: 'Desmarcado',
  faltou: 'Faltou',
};

export const SEXO_LABEL: Record<SexoPaciente, string> = {
  '': 'Não informado',
  M: 'Masculino',
  F: 'Feminino',
  I: 'Indefinido',
};

export const EMPTY_RESPONSAVEL: Responsavel = {
  nome: '',
  profissao: '',
  parentesco: '',
  telefone: '',
};

export const EMPTY_CONVENIO: ConvenioPaciente = {
  convenio: '',
  plano: '',
  carteirinha: '',
  validade: null,
};

export function emptyPaciente(): Paciente {
  return {
    id: 0,
    numero_prontuario: '',
    medico_referencia: '',
    nome: '',
    nome_social: '',
    data_nascimento: null,
    sexo: '',
    estado_civil: '',
    cpf: '',
    rg: '',
    passaporte: '',
    nome_mae: '',
    tipo_sanguineo: '',
    telefone: '',
    email: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    observacoes: '',
    responsaveis: [],
    convenios: [],
  };
}
