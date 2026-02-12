'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ForcarAtualizacaoPage() {
  const router = useRouter();

  useEffect(() => {
    // Limpar todo o storage
    if (typeof window !== 'undefined') {
      // Limpar sessionStorage
      sessionStorage.clear();
      
      // Limpar localStorage
      localStorage.clear();
      
      // Limpar cookies
      document.cookie.split(";").forEach((c) => {
        document.cookie = c
          .replace(/^ +/, "")
          .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
      
      // Limpar cache do service worker se existir
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then((registrations) => {
          registrations.forEach((registration) => registration.unregister());
        });
      }
      
      // Limpar cache do navegador
      if ('caches' in window) {
        caches.keys().then((names) => {
          names.forEach((name) => caches.delete(name));
        });
      }
      
      // Aguardar 1 segundo e redirecionar
      setTimeout(() => {
        window.location.href = '/';
      }, 1000);
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-purple-900">
      <div className="text-center text-white">
        <div className="mb-4">
          <svg className="animate-spin h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <h1 className="text-2xl font-bold mb-2">Limpando cache...</h1>
        <p className="text-gray-300">Aguarde, você será redirecionado em instantes.</p>
      </div>
    </div>
  );
}
