'use client';

import { useEffect, useState } from 'react';
import apiClient from '@/lib/api-client';
import { getCrmApiErrorDetail } from '@/lib/crm-utils';
import { useToast } from '@/components/ui/Toast';

const TAMANHO_PADRAO = 100;
const INTENSIDADE_PADRAO = 25;

export function ModalLogoAssinatura({ onClose }: { onClose: () => void }) {
  const toast = useToast();
  const [tamanho, setTamanho] = useState(TAMANHO_PADRAO);
  const [intensidade, setIntensidade] = useState(INTENSIDADE_PADRAO);
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;
    apiClient.get<{ logo_assinatura_tamanho?: number; logo_assinatura_intensidade?: number }>(
      '/crm-vendas/config/',
    ).then((res) => {
      if (!ativo) return;
      const t = Number(res.data.logo_assinatura_tamanho);
      const i = Number(res.data.logo_assinatura_intensidade);
      if (t >= 30 && t <= 100) setTamanho(t);
      if (i >= 5 && i <= 80) setIntensidade(i);
    }).catch((err) => {
      if (ativo) setErro(getCrmApiErrorDetail(err, 'Não foi possível carregar a configuração.'));
    }).finally(() => {
      if (ativo) setCarregando(false);
    });
    return () => {
      ativo = false;
    };
  }, []);

  const salvar = async () => {
    setSalvando(true);
    setErro(null);
    try {
      await apiClient.patch('/crm-vendas/config/', {
        logo_assinatura_tamanho: tamanho,
        logo_assinatura_intensidade: intensidade,
      });
      toast.success('A logo da assinatura foi atualizada.');
      onClose();
    } catch (err) {
      setErro(getCrmApiErrorDetail(err, 'Não foi possível salvar.'));
    } finally {
      setSalvando(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-lg bg-white dark:bg-[#16325c] shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-labelledby="logo-assinatura-titulo"
      >
        <div className="border-b border-gray-200 dark:border-[#0d1f3c] px-5 py-4">
          <h2 id="logo-assinatura-titulo" className="text-base font-semibold text-gray-900 dark:text-white">
            Logo na assinatura digital
          </h2>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            A logo fica atrás dos dados do cliente e do vendedor, dentro do quadro da assinatura.
          </p>
        </div>
        <div className="px-5 py-4 space-y-5">
          {erro && (
            <p className="rounded-lg bg-red-50 dark:bg-red-900/20 px-3 py-2 text-sm text-red-700 dark:text-red-300">
              {erro}
            </p>
          )}
          <div className="grid grid-cols-2 overflow-hidden rounded border border-gray-300 dark:border-gray-600 text-[11px] text-gray-700 dark:text-gray-200">
            {['Vendedor', 'Cliente'].map((lado) => (
              <div key={lado} className="relative h-32 overflow-hidden border-r border-gray-200 p-2 last:border-r-0 dark:border-gray-600">
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div
                    className="text-gray-400"
                    style={{ width: `${tamanho}%`, height: `${tamanho}%`, opacity: intensidade / 100 }}
                  >
                    <svg viewBox="0 0 100 40" className="h-full w-full" preserveAspectRatio="none" aria-hidden>
                      <text
                        x="50"
                        y="34"
                        textAnchor="middle"
                        fontSize="36"
                        fontWeight="800"
                        fill="currentColor"
                        fontFamily="Arial, sans-serif"
                      >
                        LOGO
                      </text>
                    </svg>
                  </div>
                </div>
                <div className="relative">
                  <p className="font-semibold">{lado}</p>
                  <p>Nome</p>
                  <p>Assinado digitalmente</p>
                </div>
              </div>
            ))}
          </div>
          <label className="block text-sm text-gray-700 dark:text-gray-200">
            <span className="flex justify-between">
              Tamanho da logo no quadro
              <span className="font-medium">{tamanho}%</span>
            </span>
            <input
              type="range"
              min={30}
              max={100}
              value={tamanho}
              disabled={carregando || salvando}
              onChange={(e) => setTamanho(Number(e.target.value))}
              className="mt-2 w-full"
            />
          </label>
          <label className="block text-sm text-gray-700 dark:text-gray-200">
            <span className="flex justify-between">
              Intensidade atrás dos dados
              <span className="font-medium">{intensidade}%</span>
            </span>
            <input
              type="range"
              min={5}
              max={80}
              value={intensidade}
              disabled={carregando || salvando}
              onChange={(e) => setIntensidade(Number(e.target.value))}
              className="mt-2 w-full"
            />
          </label>
        </div>
        <div className="flex justify-end gap-2 border-t border-gray-200 dark:border-[#0d1f3c] px-5 py-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200 dark:hover:bg-[#0d1f3c]"
          >
            Cancelar
          </button>
          <button
            type="button"
            onClick={() => { void salvar(); }}
            disabled={carregando || salvando}
            className="rounded bg-[#0176d3] px-4 py-2 text-sm font-medium text-white hover:bg-[#0159a8] disabled:opacity-60"
          >
            {salvando ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  );
}
