// Constantes compartilhadas - Estados do Brasil
export const ESTADOS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
] as const;

export type EstadoBrasil = typeof ESTADOS_BRASIL[number];

// Status de agendamento
export const STATUS_AGENDAMENTO = [
  { value: 'agendado', label: 'Agendado', color: 'bg-blue-100 text-blue-800' },
  { value: 'confirmado', label: 'Confirmado', color: 'bg-green-100 text-green-800' },
  { value: 'em_atendimento', label: 'Em Atendimento', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'concluido', label: 'Concluído', color: 'bg-gray-100 text-gray-800' },
  { value: 'cancelado', label: 'Cancelado', color: 'bg-red-100 text-red-800' },
  { value: 'nao_compareceu', label: 'Não Compareceu', color: 'bg-orange-100 text-orange-800' },
] as const;

// Tipos de campo de anamnese
export const TIPOS_CAMPO_ANAMNESE = [
  { value: 'texto', label: 'Texto Curto' },
  { value: 'textarea', label: 'Texto Longo' },
  { value: 'numero', label: 'Número' },
  { value: 'data', label: 'Data' },
  { value: 'sim_nao', label: 'Sim/Não' },
  { value: 'multipla_escolha', label: 'Múltipla Escolha' },
  { value: 'selecao_unica', label: 'Seleção Única' },
] as const;
