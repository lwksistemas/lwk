'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { authService, markInternalNavigation } from '@/lib/auth';
import apiClient from '@/lib/api-client';
import PasswordInput from '@/components/auth/PasswordInput';
import ErrorAlert from '@/components/auth/ErrorAlert';
import RecuperarSenhaModal from '@/components/auth/RecuperarSenhaModal';

interface LojaInfo {
  nome: string;
  tipo_loja_nome: string;
  cor_primaria: string;
  cor_secundaria: string;
  logo?: string;
}

export default function LojaLoginDinamicoPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;
  
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [lojaInfo, setLojaInfo] = useState<LojaInfo | null>(null);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);

  useEffect(() => {
    loadLojaInfo();
  }, [slug]);

  const loadLojaInfo = async () => {
    try {
      setLoadingInfo(true);
      const response = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      setLojaInfo(response.data);
    } catch (err: any) {
      console.error('Erro ao carregar informações da loja:', err);
      if (err.response?.status === 404) {
        setError('Loja não encontrada');
      } else {
        setError('Erro ao carregar informações da loja');
      }
    } finally {
      setLoadingInfo(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const loginResponse = await authService.login(credentials, 'loja', slug);
      
      console.log('🔍 Login Response:', loginResponse);
      console.log('🔍 precisa_trocar_senha:', loginResponse.precisa_trocar_senha);
      
      // Verificar se precisa trocar senha
      const precisaTrocar = loginResponse.precisa_trocar_senha === true;
      
      if (precisaTrocar) {
        console.log('✅ Redirecionando para trocar senha...');
        markInternalNavigation();
        window.location.replace('/loja/trocar-senha');
        return;
      }
      
      console.log('✅ Redirecionando para dashboard...');
      markInternalNavigation();
      window.location.replace(`/loja/${slug}/dashboard`);
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      setError(err.message || 'Erro ao fazer login. Tente novamente.');
    } finally {
      setLoading(false);
    }
  };

  // Loading state
  if (loadingInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-900 to-emerald-900 p-4">
        <div className="text-white text-lg sm:text-xl flex items-center">
          <svg className="animate-spin -ml-1 mr-3 h-6 w-6 text-white" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Carregando...
        </div>
      </div>
    );
  }

  // Loja não encontrada
  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-900 to-red-700 p-4">
        <div className="max-w-md w-full space-y-6 sm:space-y-8 p-6 sm:p-8 bg-white rounded-lg shadow-2xl">
          <div className="text-center">
            <div className="mx-auto h-16 w-16 bg-red-600 rounded-full flex items-center justify-center mb-4">
              <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Loja não encontrada</h2>
            <p className="text-sm sm:text-base text-gray-600 mb-6">A loja "{slug}" não existe ou não está ativa.</p>
            <Link
              href="/"
              className="inline-block px-6 py-3 min-h-[44px] bg-red-600 text-white rounded-md hover:bg-red-700 active:scale-95 transition-transform"
            >
              Voltar para Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Usar cores da loja
  const corPrimaria = lojaInfo.cor_primaria;
  const corSecundaria = lojaInfo.cor_secundaria;

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: `linear-gradient(to bottom right, ${corPrimaria}, ${corSecundaria})`
      }}
    >
      <div className="max-w-md w-full space-y-6 sm:space-y-8 p-6 sm:p-8 bg-white rounded-lg shadow-2xl">
        {/* Header */}
        <div>
          <div 
            className="mx-auto h-14 w-14 sm:h-16 sm:w-16 rounded-full flex items-center justify-center"
            style={{ backgroundColor: corPrimaria }}
          >
            {lojaInfo.logo ? (
              <img src={lojaInfo.logo} alt={lojaInfo.nome} className="h-10 w-10 sm:h-12 sm:w-12 rounded-full object-cover" />
            ) : (
              <svg className="h-8 w-8 sm:h-10 sm:w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            )}
          </div>
          <h2 className="mt-4 sm:mt-6 text-center text-2xl sm:text-3xl font-bold text-gray-900">
            {lojaInfo.nome}
          </h2>
          <p className="mt-1 sm:mt-2 text-center text-sm sm:text-base text-gray-600">
            {lojaInfo.tipo_loja_nome}
          </p>
          <p className="text-center text-xs sm:text-sm text-gray-500 mt-1">
            Portal da Loja
          </p>
        </div>
        
        {/* Form */}
        <form className="mt-6 sm:mt-8 space-y-5 sm:space-y-6" onSubmit={handleSubmit}>
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
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
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
            className="w-full py-3.5 sm:py-3 px-4 min-h-[48px] text-white font-semibold rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            style={{
              backgroundColor: corPrimaria
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = corSecundaria}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = corPrimaria}
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
              'Entrar'
            )}
          </button>
        </form>
        
        {/* Forgot Password Link */}
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm hover:underline min-h-[44px] py-2 px-4 transition-colors"
            style={{ color: corPrimaria }}
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
        endpoint="/superadmin/lojas/recuperar_senha/"
        extraData={{ slug }}
        title="Recuperar Senha"
        description="Digite o email cadastrado para receber uma nova senha provisória."
        primaryColor={corPrimaria}
      />
    </div>
  );
}
