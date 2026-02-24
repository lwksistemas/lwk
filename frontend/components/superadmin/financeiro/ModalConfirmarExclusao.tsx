'use client';

import { formatCurrency, formatDate } from '@/lib/financeiro-helpers';

interface ModalConfirmarExclusaoProps {
  pagamento: {
    id: number | null;
    customer_name: string;
    value: string;
    due_date: string;
    status_display: string;
  };
  onClose: () => void;
  onConfirm: (paymentId: number) => void;
  loading: boolean;
}

export function ModalConfirmarExclusao({ pagamento, onClose, onConfirm, loading }: ModalConfirmarExclusaoProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
        <div className="flex items-center mb-4">
          <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center mr-4">
            <span className="text-2xl">⚠️</span>
          </div>
          <h3 className="text-lg font-semibold text-gray-900">
            Confirmar Exclusão
          </h3>
        </div>

        <div className="mb-6">
          <p className="text-gray-700 mb-4">
            Tem certeza que deseja excluir esta cobrança?
          </p>

          <div className="bg-gray-50 p-4 rounded-lg space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Cliente:</span>
              <span className="text-sm font-medium text-gray-900">{pagamento.customer_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Valor:</span>
              <span className="text-sm font-medium text-gray-900">{formatCurrency(pagamento.value)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Vencimento:</span>
              <span className="text-sm font-medium text-gray-900">{formatDate(pagamento.due_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">Status:</span>
              <span className="text-sm font-medium text-gray-900">{pagamento.status_display}</span>
            </div>
          </div>

          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">
              <strong>Atenção:</strong> Esta ação não pode ser desfeita. A cobrança será excluída do Asaas e do sistema.
            </p>
          </div>
        </div>

        {/* Botões */}
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => pagamento.id != null && onConfirm(pagamento.id)}
            disabled={loading || pagamento.id == null}
            className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Excluindo...' : 'Excluir Cobrança'}
          </button>
        </div>
      </div>
    </div>
  );
}
