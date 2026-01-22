'use client';

import { useState } from 'react';

export default function DiagnosticoPage() {
  const [resultado, setResultado] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const testarConexao = async () => {
    setLoading(true);
    setResultado(null);

    const testes: any = {
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      localStorage: {},
      apiTests: {}
    };

    // Verificar localStorage
    try {
      testes.localStorage = {
        access_token: localStorage.getItem('access_token') ? 'EXISTS' : 'NOT_FOUND',
        refresh_token: localStorage.getItem('refresh_token') ? 'EXISTS' : 'NOT_FOUND',
        keys: Object.keys(localStorage)
      };
    } catch (e) {
      testes.localStorage = { error: 'Cannot access localStorage' };
    }

    // Testar APIs
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://lwksistemas-38ad47519238.herokuapp.com';
    
    // Teste 1: API Root
    try {
      const response = await fetch(`${API_URL}/api/`);
      testes.apiTests.root = {
        status: response.status,
        ok: response.ok,
        data: await response.json()
      };
    } catch (e: any) {
      testes.apiTests.root = { error: e.message };
    }

    // Teste 2: Info pública da loja
    try {
      const response = await fetch(`${API_URL}/api/superadmin/lojas/info_publica/?slug=felix`);
      testes.apiTests.lojaInfo = {
        status: response.status,
        ok: response.ok,
        data: await response.json()
      };
    } catch (e: any) {
      testes.apiTests.lojaInfo = { error: e.message };
    }

    // Teste 3: Login de teste
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
      
      testes.apiTests.login = {
        status: response.status,
        ok: response.ok,
        data: response.ok ? await response.json() : await response.text()
      };
    } catch (e: any) {
      testes.apiTests.login = { error: e.message };
    }

    setResultado(testes);
    setLoading(false);
  };

  const limparCache = () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
      alert('✅ Cache limpo com sucesso! Recarregue a página.');
    } catch (e) {
      alert('❌ Erro ao limpar cache: ' + e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-6">
            🔧 Diagnóstico do Sistema - LWK Sistemas
          </h1>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <button
              onClick={testarConexao}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-6 rounded-lg disabled:opacity-50"
            >
              {loading ? '🔄 Testando...' : '🧪 Executar Diagnóstico'}
            </button>
            
            <button
              onClick={limparCache}
              className="bg-red-500 hover:bg-red-600 text-white font-bold py-3 px-6 rounded-lg"
            >
              🗑️ Limpar Cache
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <a
              href="/superadmin/login"
              className="bg-green-500 hover:bg-green-600 text-white font-bold py-3 px-6 rounded-lg text-center"
            >
              👑 Login Superadmin
            </a>
            
            <a
              href="/loja/felix/login"
              className="bg-purple-500 hover:bg-purple-600 text-white font-bold py-3 px-6 rounded-lg text-center"
            >
              🏥 Login Clínica Felix
            </a>
            
            <a
              href="/suporte/login"
              className="bg-orange-500 hover:bg-orange-600 text-white font-bold py-3 px-6 rounded-lg text-center"
            >
              🎧 Login Suporte
            </a>
          </div>

          {resultado && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h2 className="text-xl font-bold mb-4">📊 Resultado do Diagnóstico</h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-semibold text-gray-700">Informações do Sistema:</h3>
                  <p className="text-sm text-gray-600">Timestamp: {resultado.timestamp}</p>
                  <p className="text-sm text-gray-600">User Agent: {resultado.userAgent}</p>
                  <p className="text-sm text-gray-600">URL: {resultado.url}</p>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-700">LocalStorage:</h3>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(resultado.localStorage, null, 2)}
                  </pre>
                </div>

                <div>
                  <h3 className="font-semibold text-gray-700">Testes de API:</h3>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
                    {JSON.stringify(resultado.apiTests, null, 2)}
                  </pre>
                </div>
              </div>
            </div>
          )}

          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-semibold text-blue-800 mb-2">💡 Credenciais de Teste:</h3>
            <div className="text-sm text-blue-700 space-y-1">
              <p><strong>Superadmin:</strong> superadmin / super123</p>
              <p><strong>Clínica Felix:</strong> felipe / g$uR1t@!</p>
              <p><strong>Suporte:</strong> suporte / suporte123</p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-yellow-50 rounded-lg">
            <h3 className="font-semibold text-yellow-800 mb-2">⚠️ Problemas Comuns:</h3>
            <ul className="text-sm text-yellow-700 space-y-1">
              <li>• Cache do navegador corrompido → Limpe o cache</li>
              <li>• Tokens JWT expirados → Limpe o localStorage</li>
              <li>• Credenciais digitadas incorretamente → Verifique caps lock</li>
              <li>• Problemas de conectividade → Teste em aba anônima</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}