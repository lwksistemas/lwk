'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { authService } from '@/lib/auth';
import apiClient from '@/lib/api-client';

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

  useEffect(() => {
    loadLojaInfo();
  }, [slug]);

  const loadLojaInfo = async () => {
    try {
      setLoadingInfo(true);
      // Buscar informações públicas da loja pelo slug (sem autenticação)
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
      await authService.login(credentials, 'loja', slug);
      
      // Verificar se precisa trocar senha
      try {
        const checkResponse = await apiClient.get('/superadmin/lojas/verificar_senha_provisoria/');
        if (checkResponse.data.precisa_trocar_senha) {
          router.push('/loja/trocar-senha');
          return;
        }
      } catch (checkErr) {
        console.error('Erro ao verificar senha:', checkErr);
      }
      
      // Redirecionar para dashboard da loja específica
      router.push(`/loja/${slug}/dashboard`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Usuário ou senha incorretos');
    } finally {
      setLoading(false);
    }
  };

  if (loadingInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-green-900 to-emerald-900">
        <div className="text-white text-xl">Carregando...</div>
      </div>
    );
  }

  if (!lojaInfo) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-900 to-red-700">
        <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Loja não encontrada</h2>
            <p className="text-gray-600 mb-6">A loja "{slug}" não existe ou não está ativa.</p>
            <Link
              href="/"
              className="inline-block px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700"
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
      className="min-h-screen flex items-center justify-center"
      style={{
        background: `linear-gradient(to bottom right, ${corPrimaria}, ${corSecundaria})`
      }}
    >
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow-2xl">
        <div>
          <div 
            className="mx-auto h-16 w-16 rounded-full flex items-center justify-center"
            style={{ backgroundColor: corPrimaria }}
          >
            {lojaInfo.logo ? (
              <img src={lojaInfo.logo} alt={lojaInfo.nome} className="h-12 w-12 rounded-full" />
            ) : (
              <svg className="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            )}
          </div>
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            {lojaInfo.nome}
          </h2>
          <p className="mt-2 text-center text-gray-600">
            {lojaInfo.tipo_loja_nome}
          </p>
          <p className="text-center text-sm text-gray-500 mt-1">
            Portal da Loja
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
                autoComplete="username"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-0"
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
                autoComplete="current-password"
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-0"
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
            className="w-full py-3 px-4 text-white font-semibold rounded-md disabled:opacity-50 transition-colors"
            style={{
              backgroundColor: corPrimaria
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = corSecundaria}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = corPrimaria}
          >
            {loading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>
        
        <div className="text-center text-sm text-gray-500">
          <a 
            href="/superadmin/login" 
            className="hover:underline"
            style={{ color: corPrimaria }}
          >
            Acesso Super Admin
          </a>
          {' | '}
          <a 
            href="/suporte/login" 
            className="hover:underline"
            style={{ color: corPrimaria }}
          >
            Acesso Suporte
          </a>
        </div>
      </div>
    </div>
  );
}
