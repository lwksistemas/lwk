'use client';

import { useState } from 'react';
import { AlertCircle, Loader2, X } from 'lucide-react';
import apiClient from '@/lib/api-client';

interface ModalRecuperarNFSeProps {
  onClose: () => void;
  onSuccess: (message: string) => void;
}

export function ModalRecuperarNFSe({ onClose, onSuccess }: ModalRecuperarNFSeProps) {
  const [numeroNf, setNumeroNf] = useState('');
  const [numeroRps, setNumeroRps] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    const nf = numeroNf.trim();
    const rps = numeroRps.trim();
    if (!nf && !rps) {
      setError('Informe o número da NFS-e ou do RPS.');
      return;
    }
    setLoading(true);
    try {
      const payload: { numero_nf?: string; numero_rps?: number } = {};
      if (nf) payload.numero_nf = nf;
      if (rps) payload.numero_rps = Number(rps);
      const res = await apiClient.post<{ message?: string; error?: string }>(
        '/nfse/recuperar-issnet/',
        payload,
      );
      onSuccess(res.data.message || 'NFS-e recuperada com sucesso.');
    } catch (err: unknown) {
      const ax = err as { response?: { data?: { error?: string } } };
      setError(ax.response?.data?.error || 'Não foi possível recuperar a NFS-e.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-[#16325c] rounded-lg max-w-md w-full p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">Recuperar do ISSNet</h2>
          <button type="button" onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={22} />
          </button>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Use quando a nota foi emitida na prefeitura mas não aparece na lista (ex.: falha ao gravar no
          sistema). Informe o <strong>número da NFS-e</strong> (ex.: 151) ou o <strong>RPS</strong> da
          tentativa.
        </p>
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-800 dark:text-red-200 flex gap-2">
            <AlertCircle size={18} className="shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número da NFS-e
            </label>
            <input
              type="text"
              inputMode="numeric"
              value={numeroNf}
              onChange={(e) => setNumeroNf(e.target.value)}
              placeholder="Ex.: 151"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-[#0d1f3c] dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Número do RPS (opcional)
            </label>
            <input
              type="text"
              inputMode="numeric"
              value={numeroRps}
              onChange={(e) => setNumeroRps(e.target.value)}
              placeholder="Ex.: 155"
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-[#0d1f3c] dark:text-white"
            />
          </div>
          <div className="flex gap-2 justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#0d1f3c] rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50"
            >
              {loading ? <Loader2 size={16} className="animate-spin" /> : null}
              Recuperar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
