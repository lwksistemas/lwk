'use client';

import { FormEvent, Suspense, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import apiClient from '@/lib/api-client';

function Painel({ loginPath }: { loginPath: string }) {
  const params = useSearchParams();
  const token = params.get('token') || '';
  const [senha, setSenha] = useState('');
  const [usuario, setUsuario] = useState('');
  const [urlLogin, setUrlLogin] = useState(loginPath);
  const [erro, setErro] = useState('');
  const [loading, setLoading] = useState(false);
  const [pronto, setPronto] = useState(false);

  const confirmar = async (event: FormEvent) => {
    event.preventDefault();
    setErro('');
    setLoading(true);
    try {
      const res = await apiClient.post('/superadmin/usuarios/confirmar_recuperacao_senha/', { token });
      setSenha(res.data?.senha_provisoria || '');
      setUsuario(res.data?.usuario || '');
      setUrlLogin(res.data?.url_login || loginPath);
      setPronto(true);
    } catch {
      setErro('Link inválido ou expirado. Peça um novo na tela de login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 sm:p-8 max-w-md w-full">
        <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">Nova senha de acesso</h1>
        {!token ? (
          <p className="text-sm text-gray-600 dark:text-gray-300">Abra o link completo enviado por email.</p>
        ) : pronto ? (
          <div className="space-y-3 text-sm text-gray-700 dark:text-gray-200">
            <p>Anote a senha provisória. Ela aparece só nesta tela. No próximo login o sistema pede uma senha nova.</p>
            {usuario ? <p><strong>Usuário:</strong> {usuario}</p> : null}
            <p className="font-mono text-base break-all bg-gray-100 dark:bg-gray-700 rounded px-3 py-2">{senha}</p>
            <a href={urlLogin} className="inline-block text-purple-700 dark:text-purple-300 underline">
              Ir para o login
            </a>
          </div>
        ) : (
          <form onSubmit={confirmar} className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              A senha atual continua válida até você confirmar. Depois disso vale a senha provisória desta tela.
            </p>
            {erro ? (
              <p className="text-sm text-red-700 dark:text-red-300" role="alert">{erro}</p>
            ) : null}
            <button
              type="submit"
              disabled={loading}
              className="w-full min-h-[44px] rounded-md bg-purple-700 text-white disabled:opacity-50"
            >
              {loading ? 'Confirmando...' : 'Criar senha provisória'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}

export default function ConfirmarSenhaSistema({ loginPath }: { loginPath: string }) {
  return (
    <Suspense fallback={<p className="p-8 text-center text-gray-600">Carregando...</p>}>
      <Painel loginPath={loginPath} />
    </Suspense>
  );
}
