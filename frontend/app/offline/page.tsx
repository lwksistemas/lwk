'use client';

import { useEffect, useState } from 'react';

export default function OfflinePage() {
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    // Verificar se está online
    setIsOnline(navigator.onLine);

    // Listener para mudanças de conectividade
    const handleOnline = () => {
      setIsOnline(true);
      // Recarregar página quando voltar online
      window.location.reload();
    };

    const handleOffline = () => {
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-600 to-blue-600 p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full text-center">
        <div className="mb-6">
          {isOnline ? (
            <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
          ) : (
            <div className="w-20 h-20 mx-auto bg-red-100 rounded-full flex items-center justify-center">
              <svg
                className="w-10 h-10 text-red-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
                />
              </svg>
            </div>
          )}
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          {isOnline ? 'Conectado!' : 'Sem Conexão'}
        </h1>

        <p className="text-gray-600 mb-6">
          {isOnline
            ? 'Sua conexão foi restaurada. Recarregando...'
            : 'Você está offline. Verifique sua conexão com a internet e tente novamente.'}
        </p>

        {!isOnline && (
          <div className="space-y-4">
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Tentar Novamente
            </button>

            <button
              onClick={() => window.history.back()}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              Voltar
            </button>
          </div>
        )}

        <div className="mt-6 pt-6 border-t border-gray-200">
          <p className="text-sm text-gray-500">
            Status da conexão:{' '}
            <span className={isOnline ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
              {isOnline ? 'Online' : 'Offline'}
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}
