'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

export default function SuporteLoginPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);
  const [emailRecuperacao, setEmailRecuperacao] = useState('');
  const [loadingRecuperacao, setLoadingRecuperacao] = useState(false);
  const [mensagemRecuperacao, setMensagemRecuperacao] = useState('');

  // Verificar se usuário já está logado como outro tipo
  useEffect(() => {
    const userType = authService.getUserType();
    const lojaSlug = authService.getLojaSlug();
    
    if (userType && userType !== 'suporte') {
      console.log(`🚨 BLOQUEIO: Usuário tipo "${userType}" tentou acessar login de Suporte`);
      
      // Redirecionar para o dashboard correto
      if (userType === 'superadmin') {
        router.push('/superadmin/dashboard');
      } else if (userType === 'loja' && lojaSlug) {
        router.push(`/loja/${lojaSlug}/dashboard`);
      }
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(credentials, 'suporte');
      
      // Aguardar um momento para garantir que o token foi salvo
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Verificar se precisa trocar senha
      try {
        const apiClient = (await import('@/lib/api-client')).default;
        const checkResponse = await apiClient.get('/superadmin/usuarios/verificar_senha_provisoria/');
        console.log('Verificação senha Suporte:', checkResponse.data);
        
        if (checkResponse.data.precisa_trocar_senha) {
          router.push('/suporte/trocar-senha');
          return;
        }
      } catch (checkErr) {
        console.error('Erro ao verificar senha:', checkErr);
      }
      
      router.push('/suporte/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  const handleRecuperarSenha = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensagemRecuperacao('');
    setLoadingRecuperacao(true);

    try {
      const apiClient = (await import('@/lib/api-client')).default;
      await apiClient.post('/superadmin/usuarios/recuperar_senha/', {
        email: emailRecuperacao,
        tipo: 'suporte'
      });
      setMensagemRecuperacao('✅ Senha provisória enviada para o email cadastrado!');
      setTimeout(() => {
        setShowRecuperarSenha(false);
        setEmailRecuperacao('');
        setMensagemRecuperacao('');
      }, 3000);
    } catch (err: any) {
      setMensagemRecuperacao(err.response?.data?.detail || '❌ Erro ao recuperar senha. Verifique o email.');
    } finally {
      setLoadingRecuperacao(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-cyan-900">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        <div>
          <div className="mx-auto h-16 w-16 bg-blue-600 rounded-full flex items-center justify-center">
            <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Portal de Suporte
          </h2>
          <p className="mt-2 text-center text-gray-600">
            Gerenciamento de chamados e tickets
          </p>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded">
              {error}
            </div>
          )}
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Usuário
              </label>
              <input
                id="username"
                type="text"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={credentials.username}
                onChange={(e) =>
                  setCredentials({ ...credentials, username: e.target.value })
                }
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Senha
              </label>
              <input
                id="password"
                type="password"
                required
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={credentials.password}
                onChange={(e) =>
                  setCredentials({ ...credentials, password: e.target.value })
                }
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md disabled:opacity-50 transition-colors"
          >
            {loading ? 'Entrando...' : 'Entrar no Suporte'}
          </button>
        </form>
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      {/* Modal Recuperar Senha */}
      {showRecuperarSenha && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h3 className="text-2xl font-bold mb-4 text-blue-600">
              Recuperar Senha
            </h3>
            <p className="text-gray-600 mb-6">
              Digite o email cadastrado para receber uma nova senha provisória.
            </p>
            
            <form onSubmit={handleRecuperarSenha} className="space-y-4">
              {mensagemRecuperacao && (
                <div className={`p-3 rounded ${mensagemRecuperacao.includes('✅') ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                  {mensagemRecuperacao}
                </div>
              )}
              
              <div>
                <label htmlFor="email-recuperacao" className="block text-sm font-medium text-gray-700 mb-1">
                  Email
                </label>
                <input
                  id="email-recuperacao"
                  type="email"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={emailRecuperacao}
                  onChange={(e) => setEmailRecuperacao(e.target.value)}
                  placeholder="seu@email.com"
                />
              </div>
              
              <div className="flex justify-end space-x-4 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowRecuperarSenha(false);
                    setEmailRecuperacao('');
                    setMensagemRecuperacao('');
                  }}
                  disabled={loadingRecuperacao}
                  className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={loadingRecuperacao}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
                >
                  {loadingRecuperacao ? 'Enviando...' : 'Enviar'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
