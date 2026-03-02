/**
 * Modal para salvar busca de logs
 * ✅ REFATORADO v777: Extraído da página de logs
 */
import { useState } from 'react';

interface SalvarBuscaModalProps {
  onSalvar: (nome: string) => void;
  onCancelar: () => void;
}

export function SalvarBuscaModal({ onSalvar, onCancelar }: SalvarBuscaModalProps) {
  const [nomeBusca, setNomeBusca] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (nomeBusca.trim()) {
      onSalvar(nomeBusca.trim());
      setNomeBusca('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-gray-100">Salvar Busca</h3>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={nomeBusca}
            onChange={(e) => setNomeBusca(e.target.value)}
            placeholder="Nome da busca..."
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md mb-4 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            autoFocus
          />
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onCancelar}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!nomeBusca.trim()}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400 transition-colors"
            >
              Salvar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
