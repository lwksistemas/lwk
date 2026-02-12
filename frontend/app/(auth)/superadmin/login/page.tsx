'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import PasswordInput from '@/components/auth/PasswordInput';
import ErrorAlert from '@/components/auth/ErrorAlert';
import RecuperarSenhaModal from '@/components/auth/RecuperarSenhaModal';

export default function SuperAdminLoginPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', password: '', cpf_cnpj: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);

  // Limpar sessões antigas ao carregar a página de login
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Limpar sessionStorage
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('user_type');
      sessionStorage.removeItem('loja_slug');
      sessionStorage.removeItem('session_id');
      
      // Limpar cookies
      document.cookie = 'user_type=; path=/; max-age=0';
      document.cookie = 'loja_slug=; path=/; max-age=0';
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('🔐 [SuperAdmin] Iniciando login...', { username: credentials.username });
      const loginResponse = await authService.login(credentials, 'superadmin');
      
      console.log('✅ [SuperAdmin] Login bem-sucedido:', loginResponse);
      
      if (loginResponse.precisa_trocar_senha === true) {
        console.log('🔄 [SuperAdmin] Redirecionando para trocar senha...');
        window.location.replace('/superadmin/trocar-senha');
        return;
      }
      
      console.log('🚀 [SuperAdmin] Redirecionando para dashboard...');
      // Aguardar um pouco para garantir que os cookies foram setados
      await new Promise(resolve => setTimeout(resolve, 100));
      window.location.replace('/superadmin/dashboard');
    } catch (err: any) {
      console.error('❌ [SuperAdmin] Erro no login:', err);
      setError(err.message || 'Erro ao fazer login. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  // Função para formatar CPF automaticamente
  const formatarCpf = (valor: string) => {
    // Remove tudo que não é número
    const numeros = valor.replace(/\D/g, '');
    
    // Limita a 11 dígitos (CPF)
    const limitado = numeros.slice(0, 11);
    
    // Formata CPF: 000.000.000-00
    return limitado
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  };

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const valorFormatado = formatarCpf(e.target.value);
    setCredentials({ ...credentials, cpf_cnpj: valorFormatado });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 to-indigo-900 p-4">
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
          <ErrorAlert message={error} onClose={() => setError('')} />
          
          <div className="space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Usuário
              </label>
              <input
                id="username"
                type="text"
                required
                autoComplete="username"
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-0 transition-colors"
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                placeholder="Digite seu usuário"
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="cpf" className="block text-sm font-medium text-gray-700 mb-1">
                CPF
              </label>
              <input
                id="cpf"
                type="text"
                required
                autoComplete="off"
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-0 transition-colors"
                value={credentials.cpf_cnpj}
                onChange={handleCpfChange}
                placeholder="000.000.000-00"
                disabled={loading}
                maxLength={14}
              />
            </div>

            <PasswordInput
              id="password"
              value={credentials.password}
              onChange={(value) => setCredentials({ ...credentials, password: value })}
              label="Senha"
              placeholder="Digite sua senha"
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 min-h-[48px] bg-purple-600 hover:bg-purple-700 text-white font-semibold rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors active:scale-[0.98]"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Entrando...
              </span>
            ) : (
              'Entrar como Super Admin'
            )}
          </button>
        </form>
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm text-purple-600 hover:text-purple-700 hover:underline min-h-[44px] py-2 px-4 transition-colors"
            disabled={loading}
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      <RecuperarSenhaModal
        isOpen={showRecuperarSenha}
        onClose={() => setShowRecuperarSenha(false)}
        endpoint="/superadmin/usuarios/recuperar_senha/"
        extraData={{ tipo: 'superadmin' }}
        title="Recuperar Senha - Super Admin"
        primaryColor="#9333ea"
      />
    </div>
  );
}
