'use client';

import { useEffect } from 'react';
import { useParams } from 'next/navigation';

export default function LojaError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const params = useParams();
  const slug = params?.slug as string;

  useEffect(() => {
    console.error('[LojaError]', slug, error);
  }, [error, slug]);

  return (
    <div className="min-h-[60vh] flex items-center justify-center p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="text-5xl">😵</div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          Erro na página
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Ocorreu um erro ao carregar esta seção. Seus dados estão seguros.
        </p>
        {error.digest && (
          <p className="text-xs text-gray-400 font-mono">
            Ref: {error.digest}
          </p>
        )}
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition"
          >
            Tentar novamente
          </button>
          <a
            href={`/loja/${slug}/dashboard`}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            Ir para Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
