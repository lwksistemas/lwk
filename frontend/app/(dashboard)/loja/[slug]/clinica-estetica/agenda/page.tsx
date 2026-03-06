'use client';

/**
 * Página de Agenda - Clínica de Estética
 * Página dedicada do app (não overlay), com layout próprio e menu superior.
 * Boas práticas: rota específica, responsabilidade única, sem código duplicado.
 */

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import apiClient from '@/lib/api-client';
import { useLojaAuth } from '@/hooks/useLojaAuth';
import CalendarioAgendamentos from '@/components/calendario/CalendarioAgendamentos';

interface LojaInfo {
  id: number;
  nome: string;
  slug: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
}

/** Legenda de status do calendário (fonte única para evitar repetição) */
const LEGENDA_STATUS = [
  { cor: '#3b82f6', label: 'Agendado' },
  { cor: '#22c55e', label: 'Confirmado' },
  { cor: '#b45309', label: 'Faltou' },
  { cor: '#6b7280', label: 'Cancelado' },
] as const;

export default function AgendaClinicaEsteticaPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  const { loginPath, isLoja, ready } = useLojaAuth(slug);

  const [loja, setLoja] = useState<LojaInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [viewTitle, setViewTitle] = useState('');

  const carregarLoja = useCallback(async () => {
    if (!slug) return;
    try {
      setLoading(true);
      const { data } = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      if (data?.id) {
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('current_loja_id', String(data.id));
          if (data.slug) sessionStorage.setItem('loja_slug', data.slug);
        }
        setLoja(data);
      }
    } catch (err) {
      console.error('Erro ao carregar loja:', err);
      const ax = err && typeof err === 'object' && 'response' in err ? (err as { response?: { status?: number } }).response : undefined;
      if (ax?.status === 401) router.push(loginPath);
    } finally {
      setLoading(false);
    }
  }, [slug, loginPath, router]);

  useEffect(() => {
    if (!ready || !isLoja) return;
    carregarLoja();
  }, [ready, isLoja, carregarLoja]);

  useEffect(() => {
    if (ready && !isLoja) router.push(loginPath);
  }, [ready, isLoja, loginPath, router]);

  const handleLogout = () => {
    sessionStorage.clear();
    router.push(`/loja/${slug}/login`);
  };

  if (!ready || loading || !loja) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="w-10 h-10 border-2 border-purple-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900">
      {/* Menu superior: cor da loja (roxo para clínica de estética), título, período e legenda */}
      <header
        className="text-white shadow-lg flex-shrink-0 px-3 sm:px-4 py-2 sm:py-3"
        style={{ backgroundColor: loja.cor_primaria }}
      >
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2 sm:gap-3 min-w-0">
              <Link
                href={`/loja/${slug}/dashboard`}
                className="flex items-center justify-center min-w-[44px] min-h-[44px] rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                aria-label="Voltar ao dashboard"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </Link>
              <span className="text-lg sm:text-xl font-bold">📅 Calendário</span>
              {viewTitle && (
                <span className="text-xs sm:text-sm text-white/95 truncate max-w-[200px] sm:max-w-none">
                  {viewTitle}
                </span>
              )}
            </div>
            <div className="flex items-center gap-1 sm:gap-2">
              <Link
                href={`/loja/${slug}/suporte`}
                className="min-w-[44px] min-h-[44px] flex items-center justify-center rounded-lg bg-white/20 hover:bg-white/30 transition-colors"
                title="Chamados"
                aria-label="Chamados"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                className="min-w-[44px] min-h-[44px] sm:px-3 flex items-center justify-center rounded-lg bg-red-600 hover:bg-red-700 transition-colors text-sm font-medium"
                aria-label="Sair"
              >
                <span className="hidden sm:inline">Sair</span>
                <svg className="w-5 h-5 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
          {/* Legenda de status na barra superior */}
          <div className="flex flex-wrap items-center gap-3 sm:gap-4 text-xs sm:text-sm text-white/95">
            {LEGENDA_STATUS.map(({ cor, label }) => (
              <span key={label} className="flex items-center gap-1.5">
                <span
                  className="w-2.5 h-2.5 sm:w-3 sm:h-3 rounded-full shrink-0"
                  style={{ backgroundColor: cor }}
                  aria-hidden
                />
                {label}
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* Conteúdo: apenas o calendário (cabeçalho duplicado omitido via headerInBar) */}
      <main className="flex-1 min-h-0 flex flex-col overflow-hidden px-2 sm:px-4 lg:px-8 py-2 sm:py-4">
        <CalendarioAgendamentos
          loja={loja}
          headerInBar
          onViewTitleChange={setViewTitle}
        />
      </main>
    </div>
  );
}
