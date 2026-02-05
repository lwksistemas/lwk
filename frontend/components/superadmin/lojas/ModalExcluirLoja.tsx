'use client';

import { useState } from 'react';

interface Loja {
  id: number;
  nome: string;
  database_created: boolean;
}

interface ModalExcluirLojaProps {
  loja: Loja;
  onClose: () => void;
  onConfirm: () => void;
}

export function ModalExcluirLoja({ loja, onClose, onConfirm }: ModalExcluirLojaProps) {
  const [confirmacaoTexto, setConfirmacaoTexto] = useState('');
  const [loading, setLoading] = useState(false);

  const temBancoCriado = loja.database_created;
  const textoConfirmacao = 'EXCLUIR';
  const confirmacaoCorreta = confirmacaoTexto === textoConfirmacao;

  const handleConfirmar = async () => {
    if (!confirmacaoCorreta) return;
    
    setLoading(true);
    await onConfirm();
    setLoading(false);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
            <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.268 15.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Excluir Loja
          </h3>
          <p className="text-sm text-gray-500">
            Você está prestes a excluir a loja <strong>"{loja.nome}"</strong>
          </p>
        </div>

        <div className="mb-6">
          <div className={`border rounded-md p-4 mb-4 ${temBancoCriado ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className={`h-5 w-5 ${temBancoCriado ? 'text-red-400' : 'text-yellow-400'}`} viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className={`text-sm font-medium ${temBancoCriado ? 'text-red-800' : 'text-yellow-800'}`}>
                  {temBancoCriado ? '🔥 EXCLUSÃO TOTAL - Banco de Dados Será Deletado!' : '⚠️ EXCLUSÃO COMPLETA - Esta ação é irreversível'}
                </h3>
                <div className={`mt-2 text-sm ${temBancoCriado ? 'text-red-700' : 'text-yellow-700'}`}>
                  <p className="font-medium mb-2">Será removido PERMANENTEMENTE:</p>
                  <ul className="list-disc list-inside space-y-1">
                    <li><strong>Loja completa</strong> - Todos os dados e configurações</li>
                    {temBancoCriado && (
                      <>
                        <li className="text-red-800 font-bold">🗄️ Banco de dados isolado - Arquivo físico será DELETADO</li>
                        <li><strong>Usuários e funcionários</strong> - Todos os acessos da loja</li>
                        <li><strong>Produtos e serviços</strong> - Todo o catálogo</li>
                        <li><strong>Pedidos e vendas</strong> - Histórico completo</li>
                      </>
                    )}
                    <li><strong>Dados financeiros</strong> - Assinatura e pagamentos</li>
                    <li><strong>Usuário proprietário</strong> - Será removido se não tiver outras lojas</li>
                    <li><strong>Configurações personalizadas</strong> - Cores, logos, etc.</li>
                  </ul>
                  <p className="font-bold mt-3 text-red-800">
                    ⚠️ IMPOSSÍVEL RECUPERAR após a exclusão!
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Para confirmar, digite <strong className="text-red-600">{textoConfirmacao}</strong>:
            </label>
            <input
              type="text"
              value={confirmacaoTexto}
              onChange={(e) => setConfirmacaoTexto(e.target.value.toUpperCase())}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-red-500 focus:border-red-500"
              placeholder={textoConfirmacao}
              autoFocus
            />
          </div>
        </div>

        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            disabled={!confirmacaoCorreta || loading}
            className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Excluindo...' : 'Excluir Loja Permanentemente'}
          </button>
        </div>
      </div>
    </div>
  );
}
