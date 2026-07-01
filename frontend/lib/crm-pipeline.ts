import { fetchAllPaginatedResults, getCrmApiErrorDetail } from '@/lib/crm-utils';
import type { Oportunidade } from '@/components/crm-vendas/PipelineBoard';

const ETAPAS_FECHADAS = new Set(['closed_won', 'closed_lost']);

/** Período filtra por data de criação (abertas) ou data de fechamento (ganho/perdido). */
export function oportunidadeNoPeriodo(
  op: Oportunidade,
  dataInicio: string,
  dataFim: string,
): boolean {
  if (!dataInicio && !dataFim) return true;

  let dataRef = '';
  if (op.etapa === 'closed_won') {
    dataRef = op.data_fechamento_ganho || op.data_fechamento || op.created_at || '';
  } else if (op.etapa === 'closed_lost') {
    dataRef = op.data_fechamento_perdido || op.created_at || '';
  } else {
    dataRef = op.created_at || '';
  }

  if (!dataRef) return true;
  const dataOp = new Date(dataRef);
  if (Number.isNaN(dataOp.getTime())) return true;
  if (dataInicio && dataOp < new Date(dataInicio)) return false;
  if (dataFim) {
    const dataFimDate = new Date(dataFim);
    dataFimDate.setHours(23, 59, 59, 999);
    if (dataOp > dataFimDate) return false;
  }
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
) {
  fetchAllPaginatedResults<Oportunidade>('/crm-vendas/oportunidades/', { _t: Date.now() })
    .then((items) => {
      setOportunidades(items);
      setError(null);
    })
    .catch((err: unknown) => {
      setError(getCrmApiErrorDetail(err, 'Erro ao carregar oportunidades.'));
    });
}

export { ETAPAS_FECHADAS };
