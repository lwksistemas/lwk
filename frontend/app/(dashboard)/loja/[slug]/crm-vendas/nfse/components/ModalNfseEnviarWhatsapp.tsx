'use client';

import { useState } from 'react';
import { X } from 'lucide-react';
import { formatTelefone } from '@/lib/format-br';
import type { NFSe } from '../types';

type ModalNfseEnviarWhatsappProps = {
  nf: NFSe;
  onClose: () => void;
  onEnviar: (telefone: string) => Promise<void>;
};

export default function ModalNfseEnviarWhatsapp({ nf, onClose, onEnviar }: ModalNfseEnviarWhatsappProps) {
  const [telefone, setTelefone] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro(null);
    const digits = telefone.replace(/\D/g, '');
    if (digits.length < 10) {
      setErro('Informe um número de WhatsApp válido com DDD.');
      return;
    }
    setEnviando(true);
    try {
      await onEnviar(telefone);
      onClose();
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string; detail?: string } } };
      const data = ax.response?.data;
      setErro(data?.error || data?.detail || 'Erro ao enviar por WhatsApp.');
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center p-4 bg-black/50" onClick={() => !enviando && onClose()}>
      <div
        className="bg-white dark:bg-gray-800 rounded-xl shadow-xl border border-gray-200 dark:border-gray-700 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Enviar NFS-e por WhatsApp</h2>
          <button
            type="button"
            onClick={() => !enviando && onClose()}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500"
            aria-label="Fechar"
          >
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <p>
              <span className="font-medium text-gray-800 dark:text-gray-200">NF {nf.numero_nf || nf.id}</span>
              {' · '}
              {nf.tomador_nome}
            </p>
            <p>Valor: R$ {Number(nf.valor ?? 0).toFixed(2)}</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número do WhatsApp
            </label>
            <input
              type="tel"
              value={telefone}
              onChange={(e) => setTelefone(formatTelefone(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="(00) 00000-0000"
              autoFocus
              required
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Informe o número que receberá o link oficial da nota fiscal (portal da prefeitura).
            </p>
          </div>
          {erro && (
            <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 p-2 rounded-lg">
              {erro}
            </p>
          )}
          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => !enviando && onClose()}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={enviando}
              className="flex-1 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium"
            >
              {enviando ? 'Enviando...' : 'Enviar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
