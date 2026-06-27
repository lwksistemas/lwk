/** Convênio (plano) */
export interface ConvenioItem {
  id: number;
  nome: string;
  codigo?: string;
  is_active?: boolean;
}

export type ConvenioPrecoModo = 'fixo' | 'percentual';

export interface ConvenioPrecoItem {
  id?: number;
  procedure: number;
  procedure_name?: string;
  preco_particular?: string | number;
  modo?: ConvenioPrecoModo;
  preco: string | number;
  preco_efetivo?: string | number;
}

export interface ConvenioDetailItem extends ConvenioItem {
  precos?: ConvenioPrecoItem[];
  created_at?: string;
  updated_at?: string;
}

export interface ProcedimentoConvenioPrecosMatrix {
  convenios: ConvenioItem[];
  precos: { procedure: number; convenio: number; preco: string }[];
}

export interface ProcedureConvenioPrecoItem {
  convenio: number;
  convenio_codigo?: string;
  convenio_nome?: string;
  modo?: ConvenioPrecoModo;
  preco: string | number | null;
  preco_efetivo?: number | null;
}

/** Local de atendimento para consultas */
export interface LocalAtendimentoItem {
  id: number;
  nome: string;
  valor_consulta: string | number;
  tempo_consulta_minutos?: number | null;
  is_padrao?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Nome de agenda (categoria do calendário) */
export interface NomeAgendaItem {
  id: number;
  nome: string;
  is_padrao?: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Configuração de retorno gratuito (isenção da taxa de consulta) */
export interface AgendaRetornoConfigItem {
  id: number;
  retorno_procedimento_ativo: boolean;
  retorno_consulta_ativo: boolean;
  dias_retorno_consulta: number;
  created_at: string;
  updated_at: string;
  loja_id?: number;
}

export interface RetornoProcedimentoRegraItem {
  id: number;
  procedure: number;
  procedure_name: string;
  dias_retorno: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  loja_id?: number;
}

export interface RetornoVerificacaoResult {
  elegivel: boolean;
  tipo?: 'procedimento' | 'consulta' | null;
  procedure_id?: number | null;
  procedure_nome?: string | null;
  dias_retorno?: number | null;
  dias_restantes?: number | null;
  consulta_origem_id?: number | null;
  mensagem?: string | null;
  config?: AgendaRetornoConfigItem;
  regras_procedimento?: RetornoProcedimentoRegraItem[];
}

/** Template de documento clínico */
export interface DocumentTemplateItem {
  id: number;
  professional: number;
  nome: string;
  tipo: string;
  conteudo: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

/** Documento clínico gerado durante consulta */
export interface DocumentoClinicoItem {
  id: number;
  consulta: number;
  patient: number;
  professional: number;
  professional_name: string | null;
  template: number | null;
  tipo: string;
  titulo: string;
  conteudo: string;
  created_at: string;
}

/** Dados do prontuário agrupado por seção */
export interface ProntuarioData {
  receituario: ProntuarioDocItem[];
  pedido_exame: ProntuarioDocItem[];
  atestado: ProntuarioDocItem[];
  documento_personalizado: ProntuarioDocItem[];
  evolucao: ProntuarioEvolucaoItem[];
  anamnese: ProntuarioAnamneseItem | null;
}

export interface ProntuarioDocItem {
  id: number;
  tipo: string;
  titulo: string;
  conteudo: string;
  professional_name: string | null;
  consulta_id: number | null;
  created_at: string | null;
  pdf_url?: string;
  source: 'documento_clinico' | 'memed';
}

export interface ProntuarioEvolucaoItem {
  id: number;
  descricao: string;
  procedimento_realizado: string;
  produtos_utilizados: string;
  orientacoes: string;
  professional_name: string | null;
  consulta_id: number | null;
  created_at: string | null;
}

export interface ProntuarioAnamneseItem {
  id: number;
  queixa_principal: string;
  historico_medico: string;
  medicamentos_uso: string;
  alergias: string;
  tipo_pele: string;
  observacoes: string;
  created_at: string | null;
  updated_at: string | null;
}
