/** Definições de colunas configuráveis na listagem de Consultas (clínica). */

import {
  colunasVisiveisFromConfig,
  type CrmColunaDef,
} from '@/lib/crm-colunas-config';

export type ConsultasColunaDef = CrmColunaDef;

export const COLUNAS_CONSULTAS_DISPONIVEIS: ConsultasColunaDef[] = [
  { key: 'numero', label: 'Nº' },
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
  'numero',
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
  // Preferências antigas sem "numero": inclui Nº no início da listagem.
  let resolvedKeys = keys;
  if (keys && keys.length > 0 && !keys.includes("numero")) {
    resolvedKeys = ["numero", ...keys];
  }
  return colunasVisiveisFromConfig(
    resolvedKeys,
    COLUNAS_CONSULTAS_DISPONIVEIS,
    DEFAULT_COLUNAS_CONSULTAS,
  );
}
