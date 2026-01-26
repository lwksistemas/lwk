'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LimparCachePage() {
  const router = useRouter();

  useEffect(() => {
    const clearAllCache = async () => {
      try {
        // 1. Limpar localStorage
        if (typeof window !== 'undefined') {
          localStorage.clear();
          sessionStorage.clear();
          
          // 2. Limpar cookies
          document.cookie.split(";").forEach((c) => {
            document.cookie = c
              .replace(/^ +/, "")
              .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
          });
          
          // 3. Limpar cache do navegador
          if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(cacheNames.map(name => caches.delete(name)));
          }
          
          // 4. Desregistrar service workers
          if ('serviceWorker' in navigator) {
            const registrations = await navigator.serviceWorker.getRegistrations();
            await Promise.all(registrations.map(reg => reg.unregister()));
          }
          
          // 5. Recarregar a página após 2 segundos
          setTimeout(() => {
            window.location.href = '/';
          }, 2000);
        }
      } catch (error) {
        console.error('Erro ao limpar cache:', error);
        setTimeout(() => {
          router.push('/');
        }, 2000);
      }
    };

    clearAllCache();
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 to-indigo-700 flex items-center justify-center p-4">
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
        <div className="mb-6">
          <div className="mx-auto w-20 h-20 bg-white/20 rounded-full flex items-center justify-center mb-4">
            <svg className="w-10 h-10 text-white animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">
            🧹 Limpando Cache
          </h1>
          <p className="text-white/80 text-lg">
            Removendo cache antigo do sistema...
          </p>
        </div>

        <div className="space-y-3 text-white/70 text-sm">
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Limpando localStorage</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <span>Limpando sessionStorage</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            <span>Limpando cookies</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.6s' }}></div>
            <span>Limpando cache do navegador</span>
          </div>
          <div className="flex items-center justify-center space-x-2">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.8s' }}></div>
            <span>Removendo service workers</span>
          </div>
        </div>

        <div className="mt-8 p-4 bg-white/10 rounded-lg">
          <p className="text-white/90 text-sm">
            ✅ Você será redirecionado automaticamente em alguns segundos...
          </p>
        </div>

        <div className="mt-6 text-white/60 text-xs">
          <p>Esta página limpa todo o cache do sistema</p>
          <p>para garantir que você veja a versão mais recente.</p>
        </div>
      </div>
    </div>
  );
}
