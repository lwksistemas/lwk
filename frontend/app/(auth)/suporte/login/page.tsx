'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { FormLogin, ModalRecuperarSenha } from '@/components/suporte/login';

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
      // Login retorna precisa_trocar_senha diretamente
      const loginResponse = await authService.login(credentials, 'suporte');
      
      console.log('🔍 Login Response:', loginResponse);
      console.log('🔍 precisa_trocar_senha:', loginResponse.precisa_trocar_senha);
      
      // Verificar se precisa trocar senha (vem na resposta do login)
      if (loginResponse.precisa_trocar_senha === true) {
        console.log('✅ Redirecionando para trocar senha...');
        window.location.href = '/suporte/trocar-senha';
        return;
      }
      
      console.log('✅ Redirecionando para dashboard...');
      window.location.href = '/suporte/dashboard';
    } catch (err: any) {
      console.error('❌ Erro no login:', err);
      setError(err.response?.data?.error || err.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
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
        
        <FormLogin
          credentials={credentials}
          onChange={setCredentials}
          onSubmit={handleSubmit}
          loading={loading}
          error={error}
        />
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      <ModalRecuperarSenha
        isOpen={showRecuperarSenha}
        onClose={() => setShowRecuperarSenha(false)}
      />
    </div>
  );
}
