/**
 * Componente da tab de pagamentos
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import type { Pagamento } from '@/hooks/useAssinaturas';
import { PagamentosFiltros } from './PagamentosFiltros';
import { PagamentosTable } from './PagamentosTable';

interface PagamentosTabProps {
  pagamentos: Pagamento[];
  loading: boolean;
  filtroStatus: string;
  setFiltroStatus: (status: string) => void;
  onDownloadBoleto: (payment: Pagamento) => void;
  onCopyPix: (pixCode: string) => void;
  onUpdateStatusAsaas?: (paymentId: number) => void;
  onExcluirAsaas?: (payment: Pagamento) => void;
  lojaNome?: string;
  onVerTodas?: () => void;
}

export function PagamentosTab({
  pagamentos,
  loading,
  filtroStatus,
  setFiltroStatus,
  onDownloadBoleto,
  onCopyPix,
  onUpdateStatusAsaas,
  onExcluirAsaas,
  lojaNome,
  onVerTodas,
}: PagamentosTabProps) {
  if (loading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>;
  }

  return (
    <div>
      {lojaNome && (
        <div className="mb-4 flex flex-wrap items-center gap-3 text-sm text-gray-700 dark:text-gray-200">
          <span>Pagamentos de {lojaNome}.</span>
          {onVerTodas && (
            <button
              type="button"
              onClick={onVerTodas}
              className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded"
            >
              Ver todas as lojas
            </button>
          )}
        </div>
      )}
      <PagamentosFiltros
        filtroStatus={filtroStatus}
        setFiltroStatus={setFiltroStatus}
      />
      
      <PagamentosTable
        pagamentos={pagamentos}
        onDownloadBoleto={onDownloadBoleto}
        onCopyPix={onCopyPix}
        onUpdateStatusAsaas={onUpdateStatusAsaas}
        onExcluirAsaas={onExcluirAsaas}
      />
    </div>
  );
}
