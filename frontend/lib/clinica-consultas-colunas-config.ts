/** Definições de colunas configuráveis na listagem de Consultas (clínica). */

import {
  colunasVisiveisFromConfig,
  type CrmColunaDef,
} from '@/lib/crm-colunas-config';

export type ConsultasColunaDef = CrmColunaDef;

export const COLUNAS_CONSULTAS_DISPONIVEIS: ConsultasColunaDef[] = [
  { key: 'patient', label: 'Cliente' },
  { key: 'agenda', label: 'Agenda' },
  { key: 'procedure', label: 'Procedimento' },
  { key: 'date', label: 'Data' },
  { key: 'professional', label: 'Profissional' },
  { key: 'pagamento', label: 'Pagamento' },
  { key: 'status', label: 'Status' },
];

/** Padrão sem AGENDA (pedido Harmonis / listagem mais limpa). */
export const DEFAULT_COLUNAS_CONSULTAS = [
  'patient',
  'procedure',
  'date',
  'professional',
  'pagamento',
  'status',
];

export function resolveColunasConsultas(
  keys: string[] | undefined | null,
): ConsultasColunaDef[] {
  return colunasVisiveisFromConfig(
    keys,
    COLUNAS_CONSULTAS_DISPONIVEIS,
    DEFAULT_COLUNAS_CONSULTAS,
  );
}
