/**
 * Página de Atalho de Loja
 * 
 * Esta página captura atalhos simples (ex: /felix-representacoes)
 * e renderiza a página de login da loja mantendo a URL amigável.
 * 
 * ✅ NOVO v1431: Mantém URL amigável sem expor CNPJ
 * ✅ DINÂMICO: Busca slug automaticamente do backend
 */

import { notFound } from 'next/navigation';
import LoginPage from '@/app/(auth)/loja/[slug]/login/page';

interface AtalhoPageProps {
  params: {
    atalho: string;
  };
}

/**
 * Busca o slug da loja pelo atalho no backend
 */
async function getSlugByAtalho(atalho: string): Promise<string | null> {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com';
    const response = await fetch(
      `${apiUrl}/api/superadmin/lojas/por-atalho/?atalho=${atalho}`,
      {
        cache: 'no-store', // Não cachear para sempre ter dados atualizados
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      console.error(`Erro ao buscar loja por atalho ${atalho}: ${response.status}`);
      return null;
    }

    const data = await response.json();
    return data.slug || null;
  } catch (error) {
    console.error(`Erro ao buscar loja por atalho ${atalho}:`, error);
    return null;
  }
}

export default async function AtalhoPage({ params }: AtalhoPageProps) {
  const { atalho } = params;

  // Buscar slug dinamicamente do backend
  const slug = await getSlugByAtalho(atalho);
  
  if (!slug) {
    // Se não encontrar a loja, retornar 404
    notFound();
  }

  // Renderizar a página de login usando o slug, mas mantendo a URL com atalho
  return <LoginPage params={{ slug }} />;
}

