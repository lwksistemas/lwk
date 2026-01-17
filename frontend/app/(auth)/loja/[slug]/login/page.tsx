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
  const [showRecuperarSenha, setShowRecuperarSenha] = useState(false);
  const [emailRecuperacao, setEmailRecuperacao] = useState('');
  const [loadingRecuperacao, setLoadingRecuperacao] = useState(false);
  const [mensagemRecuperacao, setMensagemRecuperacao] = useState('');

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

  const handleRecuperarSenha = async (e: React.FormEvent) => {
    e.preventDefault();
    setMensagemRecuperacao('');
    setLoadingRecuperacao(true);

    try {
      await apiClient.post('/superadmin/lojas/recuperar_senha/', {
        email: emailRecuperacao,
        slug: slug
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
        
        <div className="text-center">
          <button
            onClick={() => setShowRecuperarSenha(true)}
            className="text-sm hover:underline"
            style={{ color: corPrimaria }}
          >
            Esqueceu sua senha?
          </button>
        </div>
      </div>

      {/* Modal Recuperar Senha */}
      {showRecuperarSenha && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg p-8 max-w-md w-full">
            <h3 className="text-2xl font-bold mb-4" style={{ color: corPrimaria }}>
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-0"
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
                  className="px-6 py-2 text-white rounded-md hover:opacity-90 disabled:opacity-50"
                  style={{ backgroundColor: corPrimaria }}
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
