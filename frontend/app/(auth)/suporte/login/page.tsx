'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import PasswordInput from '@/components/auth/PasswordInput';
import ErrorAlert from '@/components/auth/ErrorAlert';
import RecuperarSenhaModal from '@/components/auth/RecuperarSenhaModal';

export default function SuporteLoginPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);

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
      const loginResponse = await authService.login(credentials, 'suporte');
      
      console.log('🔍 Login Response:', loginResponse);
      console.log('🔍 precisa_trocar_senha:', loginResponse.precisa_trocar_senha);
      
      // Verificar se precisa trocar senha
      if (loginResponse.precisa_trocar_senha === true) {
        console.log('✅ Redirecionando para trocar senha...');
        window.location.href = '/suporte/trocar-senha';
        return;
      }
      
      console.log('✅ Redirecionando para dashboard...');
      window.location.href = '/suporte/dashboard';
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      setError(err.message || 'Erro ao fazer login. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-cyan-900 p-4">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        {/* Header */}
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

        {/* Form */}
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <ErrorAlert message={error} onClose={() => setError('')} />
          
          <div className="space-y-4">
            {/* Username */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Usuário
              </label>
              <input
                id="username"
                type="text"
                required
                autoComplete="username"
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 transition-colors"
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                placeholder="Digite seu usuário"
                disabled={loading}
              />
            </div>

            {/* Password */}
            <PasswordInput
              id="password"
              value={credentials.password}
              onChange={(value) => setCredentials({ ...credentials, password: value })}
              label="Senha"
              placeholder="Digite sua senha"
              autoComplete="current-password"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 min-h-[48px] bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors active:scale-[0.98]"
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
              'Entrar no Suporte'
            )}
          </button>
        </form>
        
        {/* Forgot Password Link */}
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm text-blue-600 hover:text-blue-700 hover:underline min-h-[44px] py-2 px-4 transition-colors"
            disabled={loading}
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      {/* Modal Recuperar Senha */}
      <RecuperarSenhaModal
        isOpen={showRecuperarSenha}
        onClose={() => setShowRecuperarSenha(false)}
        endpoint="/suporte/usuarios/recuperar_senha/"
        extraData={{ tipo: 'suporte' }}
        title="Recuperar Senha - Suporte"
        primaryColor="#2563eb"
      />
    </div>
  );
}
