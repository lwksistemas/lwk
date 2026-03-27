'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import PasswordInput from '@/components/auth/PasswordInput';
import ErrorAlert from '@/components/auth/ErrorAlert';
import RecuperarSenhaModal from '@/components/auth/RecuperarSenhaModal';
import apiClient from '@/lib/api-client';

interface LoginConfig {
  logo: string;
  login_background: string;
  cor_primaria: string;
  cor_secundaria: string;
  titulo: string;
  subtitulo: string;
}

export default function SuperAdminLoginPage() {
  const router = useRouter();
  const [credentials, setCredentials] = useState({ username: '', password: '', cpf_cnpj: '' });
  const [lembrarCpf, setLembrarCpf] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);
  const [config, setConfig] = useState<LoginConfig>({
    logo: '',
    login_background: '',
    cor_primaria: '#9333ea',
    cor_secundaria: '#7e22ce',
    titulo: 'Super Admin',
    subtitulo: 'Acesso restrito ao sistema',
  });
  const [configLoading, setConfigLoading] = useState(true);

  const STORAGE_KEY = 'login_lembrar_cpf_superadmin';

  // Carregar configurações personalizadas
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const res = await apiClient.get('/superadmin/public/login-config-sistema/superadmin/');
        setConfig(res.data);
      } catch (err) {
        console.error('Erro ao carregar configurações de login:', err);
      } finally {
        setConfigLoading(false);
      }
    };
    loadConfig();
  }, []);

  // Limpar sessões antigas e carregar CPF salvo
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        setCredentials((c) => ({ ...c, cpf_cnpj: saved }));
        setLembrarCpf(true);
      }
      sessionStorage.removeItem('access_token');
      sessionStorage.removeItem('refresh_token');
      sessionStorage.removeItem('user_type');
      sessionStorage.removeItem('loja_slug');
      sessionStorage.removeItem('session_id');
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

  // Mostrar loading enquanto carrega configurações
  if (configLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 to-indigo-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-white"></div>
          <p className="mt-4 text-white">Carregando...</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        backgroundImage: config.login_background ? `url(${config.login_background})` : 'none',
        backgroundColor: config.login_background ? 'transparent' : `${config.cor_primaria}`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      <div className="max-w-md w-full space-y-8 p-8 bg-white/95 backdrop-blur-sm rounded-lg shadow-2xl">
        <div>
          {config.logo ? (
            <div className="mx-auto h-16 flex items-center justify-center">
              <img src={config.logo} alt="Logo" className="max-h-16 object-contain" />
            </div>
          ) : (
            <div 
              className="mx-auto h-16 w-16 rounded-full flex items-center justify-center"
              style={{ backgroundColor: config.cor_primaria }}
            >
              <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
          )}
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            {config.titulo}
          </h2>
          <p className="mt-2 text-center text-gray-600">
            {config.subtitulo}
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
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
                style={{ 
                  '--tw-ring-color': config.cor_primaria,
                } as React.CSSProperties}
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
                className="block w-full px-3 py-3 sm:py-2.5 min-h-[44px] text-base sm:text-sm text-gray-900 placeholder:text-gray-400 border border-gray-300 rounded-md bg-white focus:outline-none focus:ring-2 focus:ring-offset-0 transition-colors"
                style={{ 
                  '--tw-ring-color': config.cor_primaria,
                } as React.CSSProperties}
                value={credentials.cpf_cnpj}
                onChange={handleCpfChange}
                placeholder="000.000.000-00"
                disabled={loading}
                maxLength={14}
              />
              <label className="mt-2 flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={lembrarCpf}
                  onChange={(e) => setLembrarCpf(e.target.checked)}
                  className="rounded border-gray-300 text-gray-900 focus:ring-2 focus:ring-offset-0"
                  style={{ 
                    '--tw-ring-color': config.cor_primaria,
                  } as React.CSSProperties}
                  disabled={loading}
                />
                <span className="text-sm text-gray-600">Lembrar CPF neste dispositivo</span>
              </label>
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
            className="w-full py-3 px-4 min-h-[48px] text-white font-semibold rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors active:scale-[0.98]"
            style={{
              backgroundColor: config.cor_primaria,
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.backgroundColor = config.cor_secundaria;
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = config.cor_primaria;
            }}
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
              `Entrar como ${config.titulo}`
            )}
          </button>
        </form>
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm hover:underline min-h-[44px] py-2 px-4 transition-colors"
            style={{ color: config.cor_primaria }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = config.cor_secundaria;
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = config.cor_primaria;
            }}
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
        title={`Recuperar Senha - ${config.titulo}`}
        primaryColor={config.cor_primaria}
      />
    </div>
  );
}
