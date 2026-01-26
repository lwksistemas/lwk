'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';

export default function SuperAdminLoginPage() {
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
    
    if (userType && userType !== 'superadmin') {
      console.log(`🚨 BLOQUEIO: Usuário tipo "${userType}" tentou acessar login de Super Admin`);
      
      // Redirecionar para o dashboard correto
      if (userType === 'suporte') {
        router.push('/suporte/dashboard');
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
      // Login retorna precisa_trocar_senha diretamente
      const loginResponse = await authService.login(credentials, 'superadmin');
      
      console.log('🔍 Login Response:', loginResponse);
      console.log('🔍 precisa_trocar_senha:', loginResponse.precisa_trocar_senha);
      
      // Verificar se precisa trocar senha (vem na resposta do login)
      if (loginResponse.precisa_trocar_senha === true) {
        console.log('✅ Redirecionando para trocar senha...');
        window.location.href = '/superadmin/trocar-senha';
        return;
      }
      
      console.log('✅ Redirecionando para dashboard...');
      window.location.href = '/superadmin/dashboard';
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      let errorMessage = 'Erro ao fazer login';
      
      if (err.response?.data?.error) {
        errorMessage = err.response.data.error;
      } else if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
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
        tipo: 'superadmin'
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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 to-indigo-900">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        <div>
          <div className="mx-auto h-16 w-16 bg-purple-600 rounded-full flex items-center justify-center">
            <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Super Admin
          </h2>
          <p className="mt-2 text-center text-gray-600">
            Acesso restrito ao sistema
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
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
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
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
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
            className="w-full py-3 px-4 bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-md disabled:opacity-50 transition-colors"
          >
            {loading ? 'Entrando...' : 'Entrar como Super Admin'}
          </button>
        </form>
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm text-purple-600 hover:text-purple-700 hover:underline"
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      {/* Modal Recuperar Senha */}
      {showRecuperarSenha && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h3 className="text-2xl font-bold mb-4 text-purple-600">
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
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
                  className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-md disabled:opacity-50"
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
