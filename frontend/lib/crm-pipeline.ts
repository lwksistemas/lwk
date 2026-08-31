import { fetchAllPaginatedResults, getCrmApiErrorDetail } from '@/lib/crm-utils';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';

const ETAPAS_FECHADAS = new Set(['closed_won', 'closed_lost']);

/** YYYY-MM-DD no fuso local. Datas ISO só-dia (`2026-08-31`) não passam por `new Date`,
 * que interpreta como UTC e corta o último dia do mês no Brasil. */
export function diaCalendarioLocal(value: string): string {
  const trimmed = value.trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) return trimmed;
  const d = new Date(trimmed);
  if (Number.isNaN(d.getTime())) return trimmed.slice(0, 10);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function dataRefOportunidade(op: Oportunidade): string {
  if (op.etapa === 'closed_won') {
    return op.data_fechamento_ganho || op.data_fechamento || op.created_at || '';
  }
  if (op.etapa === 'closed_lost') {
    return op.data_fechamento_perdido || op.created_at || '';
  }
  return op.created_at || '';
}

/** Período filtra por data de criação (abertas) ou data de fechamento (ganho/perdido). */
export function oportunidadeNoPeriodo(
  op: Oportunidade,
  dataInicio: string,
  dataFim: string,
): boolean {
  if (!dataInicio && !dataFim) return true;

  const dataRef = dataRefOportunidade(op);
  if (!dataRef) return true;

  const dia = diaCalendarioLocal(dataRef);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dia)) return true;
  if (dataInicio && dia < dataInicio) return false;
  if (dataFim && dia > dataFim) return false;
  return true;
}

export function filtrarOportunidadesPipeline(
  oportunidades: Oportunidade[],
  opts: { etapa?: string; vendedor?: string; dataInicio: string; dataFim: string },
): Oportunidade[] {
  return oportunidades.filter((op) => {
    if (opts.etapa && op.etapa !== opts.etapa) return false;
    if (opts.vendedor && String(op.vendedor) !== opts.vendedor) return false;
    return oportunidadeNoPeriodo(op, opts.dataInicio, opts.dataFim);
  });
}

export function dataReferenciaOportunidade(op: Oportunidade): string {
  if (op.etapa === 'closed_won') {
    return (op.data_fechamento_ganho || op.data_fechamento || op.created_at || '').slice(0, 10);
  }
  if (op.etapa === 'closed_lost') {
    return (op.data_fechamento_perdido || op.created_at || '').slice(0, 10);
  }
  return (op.created_at || '').slice(0, 10);
}

export function loadOportunidades(
  setOportunidades: (o: Oportunidade[]) => void,
  setError: (e: string | null) => void,
  filters: Record<string, string | number> = {},
) {
  return fetchAllPaginatedResults<Oportunidade>('/crm-vendas/oportunidades/', {
    _t: Date.now(),
    ...filters,
  })
    .then((items) => {
      setOportunidades(items);
      setError(null);
    })
    .catch((err: unknown) => {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar oportunidades.'));
    });
}

export { ETAPAS_FECHADAS };
