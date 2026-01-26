'use client';

import { useEffect } from 'react';

export default function ForcarAtualizacaoPage() {
  useEffect(() => {
    const forcarAtualizacao = async () => {
      try {
        // 1. Limpar TUDO
        localStorage.clear();
        sessionStorage.clear();
        
        // 2. Limpar cookies
        document.cookie.split(";").forEach((c) => {
          document.cookie = c
            .replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
        
        // 3. Limpar cache
        if ('caches' in window) {
          const cacheNames = await caches.keys();
          await Promise.all(cacheNames.map(name => caches.delete(name)));
        }
        
        // 4. Desregistrar service workers
        if ('serviceWorker' in navigator) {
          const registrations = await navigator.serviceWorker.getRegistrations();
          await Promise.all(registrations.map(reg => reg.unregister()));
        }
        
        // 5. Adicionar timestamp na URL para forçar reload
        const timestamp = Date.now();
        
        // 6. Mostrar alerta
        alert('✅ Cache limpo! Você será redirecionado para o login.\n\nIMPORTANTE: Se ainda entrar direto no dashboard, FECHE O NAVEGADOR COMPLETAMENTE e abra novamente.');
        
        // 7. Redirecionar com timestamp
        window.location.href = `/loja/linda/login?v=${timestamp}`;
        
      } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao limpar cache. Feche o navegador e abra novamente.');
      }
    };

    forcarAtualizacao();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-600 to-orange-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center shadow-2xl">
        <div className="mb-6">
          <div className="mx-auto w-24 h-24 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <svg className="w-12 h-12 text-red-600 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            🔥 Forçando Atualização
          </h1>
          <p className="text-gray-600 text-lg">
            Limpando cache e forçando reload completo...
          </p>
        </div>

        <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-4 mb-6">
          <p className="text-yellow-800 font-bold text-sm">
            ⚠️ IMPORTANTE
          </p>
          <p className="text-yellow-700 text-sm mt-2">
            Se após isso você ainda entrar direto no dashboard:
          </p>
          <ol className="text-yellow-700 text-sm mt-2 text-left list-decimal list-inside">
            <li>Feche o navegador COMPLETAMENTE</li>
            <li>Aguarde 5 segundos</li>
            <li>Abra o navegador novamente</li>
            <li>Acesse o site</li>
          </ol>
        </div>

        <div className="space-y-2 text-gray-600 text-sm">
          <p>✅ Limpando localStorage</p>
          <p>✅ Limpando sessionStorage</p>
          <p>✅ Limpando cookies</p>
          <p>✅ Limpando cache do navegador</p>
          <p>✅ Removendo service workers</p>
          <p>✅ Forçando reload com timestamp</p>
        </div>

        <div className="mt-6 text-gray-500 text-xs">
          <p>Aguarde o redirecionamento automático...</p>
        </div>
      </div>
    </div>
  );
}
