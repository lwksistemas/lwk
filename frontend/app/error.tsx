'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[GlobalError]', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="text-6xl">⚠️</div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Algo deu errado
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Ocorreu um erro inesperado. Tente novamente ou recarregue a página.
        </p>
        {error.digest && (
          <p className="text-xs text-gray-400 font-mono">
            Código: {error.digest}
          </p>
        )}
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="px-4 py-2 bg-primary text-white rounded-md hover:opacity-90 transition"
          >
            Tentar novamente
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition"
          >
            Recarregar página
          </button>
        </div>
      </div>
    </div>
  );
}
