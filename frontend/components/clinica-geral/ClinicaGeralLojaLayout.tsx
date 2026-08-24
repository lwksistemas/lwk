'use client';

import { useCallback, useEffect, useState, type ReactNode } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import { ClinicaGeralShell } from '@/components/clinica-geral/ClinicaGeralShell';
import {
  readLojaInfoPublicaCache,
  writeLojaInfoPublicaCache,
} from '@/lib/loja-info-publica-cache';
import { useClinicaGeralDark } from '@/hooks/useClinicaGeralDark';
import { TEAL } from '@/lib/clinica-geral-theme';
import type { LojaInfo } from '@/types/dashboard';

export function ClinicaGeralLojaLayout({ children }: { children: ReactNode }) {
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, handleLogout, isLoja, ready } = useLojaAuth(slug);
  useClinicaGeralDark();
  const [loja, setLoja] = useState<LojaInfo | null>(() => readLojaInfoPublicaCache(slug));
  const [lojaLoading, setLojaLoading] = useState(() => !readLojaInfoPublicaCache(slug));
  const [lojaError, setLojaError] = useState<string | null>(null);

  const loadLoja = useCallback(async () => {
    setLojaLoading(true);
    setLojaError(null);
    try {
      const res = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${encodeURIComponent(slug)}`);
      const data = res.data as LojaInfo;
      if (!data?.id) {
        setLoja(null);
        setLojaError('Não foi possível carregar os dados da loja.');
        return;
      }
      setLoja(data);
      writeLojaInfoPublicaCache(slug, data);
    } catch {
      setLoja(null);
      setLojaError('Falha ao carregar o consultório. Verifique a conexão e tente novamente.');
    } finally {
      setLojaLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    const cached = readLojaInfoPublicaCache(slug);
    if (cached) {
      setLoja(cached);
      setLojaLoading(false);
    }
    void loadLoja();
  }, [ready, isLoja, loadLoja, slug]);

  useEffect(() => {
    if (ready && !isLoja) window.location.href = loginPath;
  }, [ready, isLoja, loginPath]);

  if (!ready || !isLoja || (lojaLoading && !loja)) {
    return (
      <div className="clinica-geral-app flex min-h-screen items-center justify-center bg-[#F7F8FB] dark:bg-[#16152B] dark:text-slate-200">
        <p className="text-sm text-slate-500">Carregando consultório...</p>
      </div>
    );
  }

  if (!loja) {
    return (
      <div className="clinica-geral-app flex min-h-screen flex-col items-center justify-center gap-3 bg-[#F7F8FB] px-4 dark:bg-[#16152B] dark:text-slate-200">
        <p className="max-w-md text-center text-sm text-red-600">
          {lojaError || 'Não foi possível carregar o consultório.'}
        </p>
        <button
          type="button"
          onClick={() => void loadLoja()}
          className="rounded-md px-4 py-2 text-sm font-medium text-white"
          style={{ backgroundColor: TEAL }}
        >
          Tentar novamente
        </button>
      </div>
    );
  }

  return (
    <ClinicaGeralShell loja={loja} slug={slug} onLogout={handleLogout}>
      {children}
    </ClinicaGeralShell>
  );
}
