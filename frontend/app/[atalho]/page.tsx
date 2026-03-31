/**
 * Página de Atalho de Loja
 * 
 * Esta página captura atalhos simples (ex: /felix-representacoes)
 * e redireciona para a página de login mantendo o atalho na URL através de query param.
 * 
 * ✅ NOVO v1431: Mantém URL amigável sem expor CNPJ
 * ✅ DINÂMICO: Busca slug automaticamente do backend
 * ✅ v1442: Client-Side Rendering para evitar problemas de SSR
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

interface AtalhoPageProps {
  params: Promise<{
    atalho: string;
  }>;
}

export default function AtalhoPage({ params }: AtalhoPageProps) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadAndRedirect() {
      try {
        const resolvedParams = await params;
        const { atalho } = resolvedParams;

        console.log(`[AtalhoPage] Buscando loja com atalho: ${atalho}`);

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com';
        const url = `${apiUrl}/api/superadmin/lojas/por-atalho/?atalho=${atalho}`;

        console.log(`[AtalhoPage] URL: ${url}`);

        const response = await fetch(url, {
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        console.log(`[AtalhoPage] Status: ${response.status}`);

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`[AtalhoPage] Erro: ${response.status} - ${errorText}`);
          setError('Loja não encontrada');
          setLoading(false);
          return;
        }

        const data = await response.json();
        console.log(`[AtalhoPage] Dados recebidos:`, data);

        if (!data.slug) {
          setError('Loja não encontrada');
          setLoading(false);
          return;
        }

        // Redirecionar para a página de login
        console.log(`[AtalhoPage] Redirecionando para: /loja/${data.slug}/login?from=${atalho}`);
        router.push(`/loja/${data.slug}/login?from=${atalho}`);
      } catch (err) {
        console.error('[AtalhoPage] Exceção:', err);
        setError('Erro ao carregar loja');
        setLoading(false);
      }
    }

    loadAndRedirect();
  }, [params, router]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Carregando...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
          <p className="text-gray-600 mb-4">{error}</p>
          <a
            href="/"
            className="text-emerald-600 hover:text-emerald-700 underline"
          >
            Voltar para a página inicial
          </a>
        </div>
      </div>
    );
  }

  return null;
}

