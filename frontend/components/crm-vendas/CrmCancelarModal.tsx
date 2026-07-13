'use client';

import { useState } from 'react';
import { Ban, X } from 'lucide-react';

interface Props {
  titulo: string;
  tipo: 'proposta' | 'contrato';
  onConfirm: (motivo: string) => Promise<void>;
  onClose: () => void;
}

export default function CrmCancelarModal({ titulo, tipo, onConfirm, onClose }: Props) {
  const [motivo, setMotivo] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState('');

  const handleConfirm = async () => {
    if (!motivo.trim()) {
      setErro('Informe o motivo do cancelamento.');
      return;
    }
    setEnviando(true);
    setErro('');
    try {
      await onConfirm(motivo.trim());
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Erro ao cancelar.');
      setEnviando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md border border-gray-200 dark:border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Ban size={18} className="text-orange-500" />
            <h3 className="font-semibold text-gray-900 dark:text-white">
              Cancelar {tipo === 'proposta' ? 'Proposta' : 'Contrato'}
            </h3>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
            <X size={18} className="text-gray-500" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Cancelando: <span className="font-medium text-gray-900 dark:text-white">{titulo}</span>
          </p>
          <p className="text-xs text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg px-3 py-2">
            O cancelamento ficará registrado no histórico. Esta ação não pode ser desfeita.
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Motivo do cancelamento <span className="text-red-500">*</span>
            </label>
            <textarea
              value={motivo}
              onChange={e => { setMotivo(e.target.value); setErro(''); }}
              rows={3}
              placeholder="Ex.: Cliente desistiu, proposta fora do orçamento, negociação encerrada..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent resize-none"
              autoFocus
            />
            {erro && <p className="text-xs text-red-600 mt-1">{erro}</p>}
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-2 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            disabled={enviando}
            className="flex-1 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition disabled:opacity-50"
          >
            Voltar
          </button>
          <button
            onClick={handleConfirm}
            disabled={enviando || !motivo.trim()}
            className="flex-1 py-2 text-sm font-medium text-white bg-orange-500 hover:bg-orange-600 rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Ban size={15} />
            {enviando ? 'Cancelando...' : 'Confirmar Cancelamento'}
          </button>
        </div>
      </div>
    </div>
  );
}
