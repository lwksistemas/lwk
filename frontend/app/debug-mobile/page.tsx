'use client';

import { useState } from 'react';

export default function DebugMobilePage() {
  const [resultado, setResultado] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testarLogin = async () => {
    setLoading(true);
    setResultado(null);

    const teste: any = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      isMobile: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent),
      localStorage: {},
      loginTest: {}
    };

    // Verificar localStorage
    try {
      teste.localStorage = {
        access_token: localStorage.getItem('access_token') ? 'EXISTS' : 'NOT_FOUND',
        refresh_token: localStorage.getItem('refresh_token') ? 'EXISTS' : 'NOT_FOUND',
        allKeys: Object.keys(localStorage)
      };
    } catch (e) {
      teste.localStorage = { error: 'Cannot access localStorage' };
    }

    // Testar login com felipe
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com';
    
    try {
      console.log('Tentando login com felipe...');
      
      const response = await fetch(`${API_URL}/api/auth/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'felipe',
          password: 'g$uR1t@!'
        })
      });
      
      const responseText = await response.text();
      
      teste.loginTest = {
        status: response.status,
        ok: response.ok,
        statusText: response.statusText,
        headers: Object.fromEntries(response.headers.entries()),
        responseText: responseText,
        data: null
      };
      
      if (response.ok) {
        try {
          teste.loginTest.data = JSON.parse(responseText);
        } catch (e) {
          teste.loginTest.parseError = 'Could not parse JSON';
        }
      }
      
    } catch (e: any) {
      teste.loginTest = { 
        error: e.message,
        stack: e.stack 
      };
    }

    setResultado(teste);
    setLoading(false);
  };

  const limparTudo = () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
      // Limpar cookies
      document.cookie.split(";").forEach(function(c) { 
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
      });
      alert('✅ Tudo limpo! Recarregue a página.');
    } catch (e) {
      alert('❌ Erro ao limpar: ' + e);
    }
  };

  const testarSuperadmin = async () => {
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com';
    
    try {
      const response = await fetch(`${API_URL}/api/auth/token/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: 'superadmin',
          password: 'super123'
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        alert('✅ Login superadmin OK! Tokens salvos.');
        window.location.href = '/superadmin/dashboard';
      } else {
        const error = await response.text();
        alert('❌ Erro superadmin: ' + error);
      }
    } catch (e) {
      alert('❌ Erro de conexão: ' + e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-6">
            📱 Debug Mobile - Login Felix
          </h1>
          
          <div className="grid grid-cols-1 gap-4 mb-6">
            <button
              onClick={testarLogin}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg disabled:opacity-50"
            >
              {loading ? '🔄 Testando Login Felipe...' : '🧪 Testar Login Felipe'}
            </button>
            
            <button
              onClick={testarSuperadmin}
              className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg"
            >
              🔑 Testar Login Superadmin
            </button>
            
            <button
              onClick={limparTudo}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg"
            >
              🗑️ Limpar Tudo (Cache + Cookies)
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <a
              href="/loja/felix/login"
              className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-3 px-6 rounded-lg text-center"
            >
              🏥 Ir para Login Felix
            </a>
            
            <a
              href="/superadmin/login"
              className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-6 rounded-lg text-center"
            >
              👑 Ir para Login Superadmin
            </a>
          </div>

          {resultado && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-xl font-bold mb-4">📊 Resultado do Teste</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-700">Informações do Dispositivo:</h3>
                  <p className="text-sm text-gray-600">Timestamp: {resultado.timestamp}</p>
                  <p className="text-sm text-gray-600">Mobile: {resultado.isMobile ? '✅ SIM' : '❌ NÃO'}</p>
                  <p className="text-sm text-gray-600 break-all">User Agent: {resultado.userAgent}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-700">LocalStorage:</h3>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(resultado.localStorage, null, 2)}
                  </pre>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-700">Teste de Login Felipe:</h3>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(resultado.loginTest, null, 2)}
                  </pre>
                </div>

                {resultado.loginTest.status === 401 && (
                  <div className="bg-red-50 border border-red-200 rounded p-4">
                    <h4 className="font-semibold text-red-800">❌ Erro 401 - Credenciais Inválidas</h4>
                    <p className="text-red-700 text-sm">Possíveis causas:</p>
                    <ul className="text-red-600 text-sm list-disc ml-4">
                      <li>Usuário felipe não existe no sistema</li>
                      <li>Senha incorreta</li>
                      <li>Usuário desativado</li>
                      <li>Problema no banco de dados</li>
                    </ul>
                  </div>
                )}

                {resultado.loginTest.status === 200 && (
                  <div className="bg-green-50 border border-green-200 rounded p-4">
                    <h4 className="font-semibold text-green-800">✅ Login Bem-sucedido!</h4>
                    <p className="text-green-700 text-sm">O login funcionou corretamente.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">💡 Credenciais de Teste:</h3>
            <div className="text-sm text-blue-700 space-y-1">
              <p><strong>Felix (Loja):</strong> felipe / g$uR1t@!</p>
              <p><strong>Superadmin:</strong> superadmin / super123</p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-2">🔧 Passos de Correção:</h3>
            <ol className="text-sm text-yellow-700 space-y-1 list-decimal ml-4">
              <li>Limpar tudo (cache + cookies)</li>
              <li>Testar login Felipe</li>
              <li>Se erro 401: usuário não existe ou senha incorreta</li>
              <li>Se erro 403: problema de permissões</li>
              <li>Se erro 500: problema no servidor</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}