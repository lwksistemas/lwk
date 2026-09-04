export type SexoPaciente = '' | 'M' | 'F' | 'I';

export type TipoConsulta = string;

export type ModalidadeConsulta = 'presencial' | 'tele';

export type StatusConsulta =
  | 'agendado'
  | 'confirmado'
  | 'checkin'
  | 'recepcionado'
  | 'atendido'
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
  numero_prontuario?: string;
  alergias?: string;
}

export interface Paciente extends PacienteLista {
  numero_prontuario: string;
  medico_referencia: string;
  data_nascimento: string | null;
  sexo: SexoPaciente;
  estado_civil: string;
  rg: string;
  passaporte: string;
  rne: string;
  pais_emissor: string;
  nome_mae: string;
  tipo_sanguineo: string;
  nacionalidade: string;
  profissao: string;
  foto_url: string;
  telefone_fixo: string;
  quem_indicou: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  observacoes: string;
  alergias: string;
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
  paciente_idade: number | null;
  paciente_prontuario: string;
  paciente_alergias: string;
  paciente_foto_url?: string;
  data: string;
  hora: string;
  tipo: TipoConsulta;
  modalidade: ModalidadeConsulta;
  convenio: string;
  status: StatusConsulta;
  duracao_minutos: number;
  valor: string | null;
  tele_sala_url: string;
  tele_token?: string;
  tele_link?: string;
  tele_minutos: number;
  agendado_por: string;
  minutos_espera: number;
  observacoes: string;
}

export interface ConfiguracaoConsultorio {
  hora_inicio: string;
  hora_fim: string;
  duracao_minutos: number;
  endereco: string;
  cep: string;
  logradouro: string;
  numero: string;
  complemento: string;
  bairro: string;
  cidade: string;
  uf: string;
  telefone: string;
  especialidade: string;
  crm: string;
  medico_nome: string;
  teto_tele_minutos: number;
  prontuario_prefixo: string;
  prontuario_abas_ocultas: string[];
}

export interface UsuarioConsultorio {
  username: string;
  nome: string;
  email: string;
  tratamento?: string;
  celular?: string;
  telefone?: string;
  conselho?: string;
  uf?: string;
  rg?: string;
  cpf?: string;
  data_nascimento?: string;
  nacionalidade?: string;
  sexo?: string;
  sexo_label?: string;
  cbo?: string;
  estado_civil?: string;
  estado_civil_label?: string;
  foto_url?: string;
}

export const RECURSOS_MENU: { label: string; path: (slug: string) => string }[] = [
  { label: 'faturamento', path: (s) => `/loja/${s}/clinica/faturamento` },
  { label: 'lotes TISS', path: (s) => `/loja/${s}/clinica/tiss` },
];

export interface Tarefa {
  id: number;
  data: string;
  texto: string;
  concluida: boolean;
}

export type TipoRelatorio = 'atendimentos' | 'indicacao' | 'financeiro' | 'status' | 'outros';

export const RELATORIOS_MENU: { tipo: TipoRelatorio; label: string }[] = [
  { tipo: 'atendimentos', label: 'atendimentos' },
  { tipo: 'indicacao', label: 'indicação' },
  { tipo: 'financeiro', label: 'relatório financeiro' },
  { tipo: 'status', label: 'status de agendamento' },
  { tipo: 'outros', label: 'outros relatórios' },
];

export const RELATORIO_TITULO: Record<TipoRelatorio, string> = {
  atendimentos: 'Atendimentos',
  indicacao: 'Indicação',
  financeiro: 'Relatório financeiro',
  status: 'Status de agendamento',
  outros: 'Outros relatórios',
};

export interface RelatorioResposta {
  de: string;
  ate: string;
  total?: number;
  sem_indicacao?: number;
  faltas?: number;
  desmarcados?: number;
  primeiras?: number;
  retornos?: number;
  pacientes_novos?: number;
  pacientes_ativos?: number;
  valor_total?: string;
  itens?: Array<
    Consulta & {
      indicacao?: string;
      convenio?: string;
      status?: string;
      total?: number;
      valor?: string;
    }
  >;
}

export interface ItemFicha {
  nome: string;
  status?: string;
  duracao?: string;
  nota?: string;
}

export interface ExameFisicoFicha {
  peso: string;
  altura: string;
  sc: string;
  temperatura: string;
  imc: string;
  circ_abdominal: string;
  pas_sentado: string;
  pad_sentado: string;
  pas_deitado: string;
  pad_deitado: string;
  aspecto_geral: string;
  mucosas: string;
  olhos_face: string;
  pescoco: string;
  cardiorespiratorio: string;
  pele: string;
  abdome_superior: string;
  abdome_inferior: string;
  osteomuscular: string;
  membros: string;
  neurologico: string;
  outras: string;
}

export interface FichaAtendimento {
  queixas: ItemFicha[];
  historia_doenca: string;
  tratamentos: ItemFicha[];
  antecedentes_clinicos: ItemFicha[];
  antecedentes_cirurgicos: ItemFicha[];
  exame: ExameFisicoFicha;
  diagnostico: string;
  terapeutica: string;
  encaminhamento: string;
  laudos: string;
  sumario: string;
  atestado: string;
}

export interface Evolucao {
  id: number;
  consulta: number;
  paciente: number;
  especialidade: string;
  subjetivo: string;
  objetivo: string;
  avaliacao: string;
  plano: string;
  ficha?: FichaAtendimento;
  updated_at?: string;
}

export interface PrescricaoItem {
  id?: number;
  medicamento: string;
  dosagem: string;
  posologia: string;
  quantidade: string;
  alerta_alergia?: boolean;
}

export interface Prescricao {
  id: number;
  consulta: number;
  paciente: number;
  itens: PrescricaoItem[];
  created_at?: string;
}

export interface LoteTiss {
  id: number;
  numero: string;
  competencia: string;
  status: 'aberto' | 'fechado';
  guias_count?: number;
}

export interface GuiaTiss {
  id: number;
  lote: number | null;
  consulta: number;
  numero_guia: string;
  codigo_procedimento: string;
  valor: string | null;
  paciente_nome: string;
  consulta_data: string;
}

export interface CaixaDia {
  data: string;
  total_particular: string;
  total_convenio: string;
  consultas?: number;
}

export interface DiaHorariosLivres {
  data: string;
  horarios: string[];
}

export const TIPO_CONSULTA_LABEL: Record<string, string> = {
  consulta: 'Consulta',
  primeira: 'Primeira consulta',
  retorno: 'Retorno',
};

export function labelTipoConsulta(tipo?: string | null): string {
  const codigo = (tipo || '').trim();
  if (!codigo) return '—';
  return TIPO_CONSULTA_LABEL[codigo] || codigo;
}

export const MODALIDADE_LABEL: Record<ModalidadeConsulta, string> = {
  presencial: 'Consulta presencial',
  tele: 'Teleconsulta',
};

export const STATUS_LABEL: Record<StatusConsulta, string> = {
  agendado: 'Agendado',
  confirmado: 'Confirmado',
  checkin: 'Check-in',
  recepcionado: 'Recepcionado',
  atendido: 'Atendido',
  desmarcado: 'Desmarcado',
  faltou: 'Faltou',
};

export const SEXO_LABEL: Record<SexoPaciente, string> = {
  '': 'Não informado',
  M: 'Masculino',
  F: 'Feminino',
  I: 'Indefinido',
};

export const ESTADO_CIVIL_OPCOES = [
  '',
  'Solteiro(a)',
  'Casado(a)',
  'União estável',
  'Divorciado(a)',
  'Viúvo(a)',
  'Separado(a)',
] as const;

export const TIPO_SANGUINEO_OPCOES = ['', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'] as const;

export interface PacienteAnexo {
  id: number;
  paciente: number;
  nome: string;
  url: string;
  created_at?: string;
}

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
    rne: '',
    pais_emissor: '',
    nome_mae: '',
    telefone_fixo: '',
    quem_indicou: '',
    tipo_sanguineo: '',
    nacionalidade: 'Brasileira',
    profissao: '',
    foto_url: '',
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
    alergias: '',
    responsaveis: [],
    convenios: [],
  };
}

export type CargoFuncionario = 'recepcao' | 'administracao' | 'financeiro' | 'outros';

export const CARGO_FUNCIONARIO: { id: CargoFuncionario; label: string }[] = [
  { id: 'recepcao', label: 'Recepção' },
  { id: 'administracao', label: 'Administração' },
  { id: 'financeiro', label: 'Financeiro' },
  { id: 'outros', label: 'Outros' },
];

export interface ProfissionalEquipe {
  id: number;
  especialidade: number;
  especialidade_nome: string;
  nome: string;
  conselho: string;
  registro: string;
  uf: string;
  email: string;
  telefone: string;
  cbo: string;
}

export interface EspecialidadeEquipe {
  id: number;
  nome: string;
  profissionais: ProfissionalEquipe[];
}

export interface FuncionarioLoja {
  id: number;
  nome: string;
  cargo: CargoFuncionario;
  cargo_label: string;
  email: string;
  telefone: string;
}

export type TipoConvenioConsultorio = 'particular' | 'convenio' | 'empresa' | 'adm';

export const TIPO_CONVENIO_CONSULTORIO: { id: TipoConvenioConsultorio; label: string }[] = [
  { id: 'particular', label: 'Particular' },
  { id: 'convenio', label: 'Convênio' },
  { id: 'empresa', label: 'Empresa' },
  { id: 'adm', label: 'Adm. de benefícios' },
];

export interface TipoConsultaCatalogo {
  id: number;
  codigo: string;
  nome: string;
  duracao_minutos: number;
  valor: string | null;
  ordem: number;
}

export interface ConvenioConsultorio {
  id: number;
  nome: string;
  tipo: TipoConvenioConsultorio;
  tipo_label: string;
  registro_ans: string;
  telefone: string;
  observacoes: string;
  ordem: number;
}
