/**
 * Componente da tab de assinaturas
 * ✅ REFATORADO v780: Extraído da página de financeiro
 */
import { useState } from 'react';
import type { Assinatura, Pagamento } from '@/hooks/useAssinaturas';
import { AssinaturasTabela } from './AssinaturasTabela';

interface AssinaturasTabProps {
  assinaturas: Assinatura[];
  loading: boolean;
  filtroProvedor: 'todos' | 'asaas' | 'mercadopago' | 'cora';
  setFiltroProvedor: (filtro: 'todos' | 'asaas' | 'mercadopago' | 'cora') => void;
  // Asaas actions
  onDownloadBoletoAsaas: (payment: Pagamento) => void;
  onCopyPixAsaas: (pixCode: string) => void;
  onUpdateStatusAsaas: (paymentId: number) => void;
  onNovaCobranca: (assinatura: Assinatura) => void;
  onExcluirAsaas: (payment: Pagamento) => void;
  gerandoCobranca: number | null;
  // Mercado Pago actions
  onDownloadBoletoMP: (payment: Pagamento) => void;
  onCopyPixMP: (pixCode: string) => void;
  onGerarPixMP: (payment: Pagamento) => void;
  onUpdateStatusMP: (lojaSlug: string) => void;
  onNovaCobrancaMP: (assinatura: Assinatura) => void;
  onExcluirMP: (payment: Pagamento) => void;
  gerandoPix: number | null;
  atualizandoMP: string | null;
  gerandoCobrancaMP: string | number | null;
  excluindoPagamentoMP: boolean;
  onAtualizar: () => void;
  onLojaHistorico?: (loja: { slug: string; nome: string } | null) => void;
  fecharHistorico?: number;
}

const FILTRO_OPTIONS = [
  { value: 'todos' as const, label: 'Todos', icon: '🏪' },
  { value: 'asaas' as const, label: 'Asaas', icon: '🔵' },
  { value: 'mercadopago' as const, label: 'Mercado Pago', icon: '🟢' },
  { value: 'cora' as const, label: 'Cora', icon: '🟣' },
];

export function AssinaturasTab({
  assinaturas,
  loading,
  filtroProvedor,
  setFiltroProvedor,
  onDownloadBoletoAsaas,
  onCopyPixAsaas,
  onUpdateStatusAsaas,
  onNovaCobranca,
  onExcluirAsaas,
  gerandoCobranca,
  onDownloadBoletoMP,
  onCopyPixMP,
  onGerarPixMP,
  onUpdateStatusMP,
  onNovaCobrancaMP,
  onExcluirMP,
  gerandoPix,
  atualizandoMP,
  gerandoCobrancaMP,
  excluindoPagamentoMP,
  onAtualizar,
  onLojaHistorico,
  fecharHistorico,
}: AssinaturasTabProps) {
  const [soLoja, setSoLoja] = useState(false);

  if (loading) {
    return <div className="text-center py-12 text-gray-500 dark:text-gray-400">Carregando...</div>;
  }

  return (
    <div>
      {!soLoja && (
      <div className="mb-4 flex items-center space-x-4">
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          Filtrar por provedor:
        </span>
        <div className="flex flex-wrap gap-2">
          {FILTRO_OPTIONS.map(({ value, label, icon }) => (
            <button
              key={value}
              onClick={() => setFiltroProvedor(value)}
              className={`px-3 py-1 rounded text-sm transition-colors ${
                filtroProvedor === value
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>
      </div>
      )}

      {/* Lista de Assinaturas */}
      {assinaturas.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 text-center py-8">
          Nenhuma assinatura encontrada.
        </p>
      ) : (
        <>
        {!soLoja && (
        <p className="mb-3 text-sm text-gray-500 dark:text-gray-400">
          Histórico abre só essa loja. Em cada nota, Baixar e Reenviar. Com o histórico aberto, a aba Pagamentos mostra só os pagamentos dessa loja. Enviar comprovante lê o PDF ou a foto e só baixa se o nome e o CPF ou CNPJ forem os do cadastro. PDF e Reenviar só aparecem enquanto o boleto está em aberto.
        </p>
        )}
        <AssinaturasTabela
          assinaturas={assinaturas}
          onAtualizar={onAtualizar}
          onDownloadBoletoAsaas={onDownloadBoletoAsaas}
          onCopyPixAsaas={onCopyPixAsaas}
          onUpdateStatusAsaas={onUpdateStatusAsaas}
          onNovaCobranca={onNovaCobranca}
          onExcluirAsaas={onExcluirAsaas}
          gerandoCobranca={gerandoCobranca}
          onDownloadBoletoMP={onDownloadBoletoMP}
          onCopyPixMP={onCopyPixMP}
          onGerarPixMP={onGerarPixMP}
          onUpdateStatusMP={onUpdateStatusMP}
          onNovaCobrancaMP={onNovaCobrancaMP}
          onExcluirMP={onExcluirMP}
          gerandoPix={gerandoPix}
          atualizandoMP={atualizandoMP}
          gerandoCobrancaMP={gerandoCobrancaMP}
          excluindoPagamentoMP={excluindoPagamentoMP}
          fecharHistorico={fecharHistorico}
          onHistoricoAberto={(loja) => {
            setSoLoja(loja != null);
            onLojaHistorico?.(loja);
          }}
        />
        </>
      )}
    </div>
  );
}
