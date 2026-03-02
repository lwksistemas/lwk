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
}

export function PagamentosTab({
  pagamentos,
  loading,
  filtroStatus,
  setFiltroStatus,
  onDownloadBoleto,
  onCopyPix,
  onUpdateStatusAsaas,
  onExcluirAsaas
}: PagamentosTabProps) {
  if (loading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>;
  }

  return (
    <div>
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
