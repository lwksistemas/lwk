'use client';

import { useState } from 'react';
import { formatCurrency } from '@/lib/financeiro-helpers';

interface ModalNovaCobrancaProps {
  assinatura: {
    id: number | string;
    loja_nome: string;
    plano_valor: string;
  };
  onClose: () => void;
  onConfirm: (assinaturaId: number | string, dueDate?: string) => void;
  loading: boolean;
}

export function ModalNovaCobranca({ assinatura, onClose, onConfirm, loading }: ModalNovaCobrancaProps) {
  const [tipoCobranca, setTipoCobranca] = useState<'automatica' | 'manual'>('automatica');
  const [dataVencimento, setDataVencimento] = useState('');

  const handleConfirm = () => {
    if (tipoCobranca === 'manual') {
      if (!dataVencimento) {
        alert('Por favor, selecione uma data de vencimento');
        return;
      }
      onConfirm(assinatura.id, dataVencimento);
    } else {
      onConfirm(assinatura.id);
    }
  };

  // Calcular data mínima (amanhã)
  const getMinDate = () => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Nova Cobrança - {assinatura.loja_nome}
        </h3>

        <div className="space-y-4 mb-6">
          {/* Tipo de Cobrança */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Tipo de Cobrança
            </label>
            <div className="space-y-2">
              <label className="flex items-center p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <input
                  type="radio"
                  name="tipo"
                  value="automatica"
                  checked={tipoCobranca === 'automatica'}
                  onChange={() => setTipoCobranca('automatica')}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">Automática</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Próximo mês, dia configurado</div>
                </div>
              </label>

              <label className="flex items-center p-3 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <input
                  type="radio"
                  name="tipo"
                  value="manual"
                  checked={tipoCobranca === 'manual'}
                  onChange={() => setTipoCobranca('manual')}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium text-gray-900 dark:text-gray-100">Manual</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">Escolher data personalizada</div>
                </div>
              </label>
            </div>
          </div>

          {/* Data de Vencimento (apenas se manual) */}
          {tipoCobranca === 'manual' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Data de Vencimento
              </label>
              <input
                type="date"
                value={dataVencimento}
                onChange={(e) => setDataVencimento(e.target.value)}
                min={getMinDate()}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
          )}

          {/* Valor */}
          <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded-lg">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Valor da Cobrança:</span>
              <span className="text-lg font-bold text-purple-600 dark:text-purple-400">
                {formatCurrency(assinatura.plano_valor)}
              </span>
            </div>
          </div>
        </div>

        {/* Botões */}
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={onClose}
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Criando...' : 'Criar Cobrança'}
          </button>
        </div>
      </div>
    </div>
  );
}
