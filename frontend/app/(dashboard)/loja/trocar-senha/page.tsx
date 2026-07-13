'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { formatApiErrorBody } from '@/lib/api-errors';
import { authService } from '@/lib/auth';
import { isTipoCRMVendas } from '@/lib/loja-tipo';
import PasswordInput from '@/components/auth/PasswordInput';
import { AuthScreenShell } from '@/components/auth/AuthScreenShell';
import { cacheLojaLoginContext } from '@/lib/login-default-backgrounds';
import { logger } from '@/lib/logger';
import { validatePasswordPolicy, checkPasswordRules } from '@/lib/password-policy';

export default function TrocarSenhaLojaPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [lojaId, setLojaId] = useState<number | null>(null);
  const [lojaSlug, setLojaSlug] = useState<string | null>(null);
  const [tipoLojaNome, setTipoLojaNome] = useState<string>('');
  const [loginBackground, setLoginBackground] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const loadLojaInfo = useCallback(async () => {
    try {
      const slug = authService.getLojaSlug();
      if (!slug) {
        setErro('Informações da loja não encontradas. Faça login novamente.');
        setTimeout(() => router.push('/'), 2000);
        return;
      }
      setLojaSlug(slug);
      const response = await apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`);
      const tipo = response.data.tipo_loja_nome || '';
      setLojaId(response.data.id);
      setTipoLojaNome(tipo);
      setLoginBackground(response.data.login_background || null);
      cacheLojaLoginContext(slug, tipo, response.data.login_background);
    } catch (error) {
      logger.warn('Erro ao carregar informações da loja:', error);
      setErro('Erro ao carregar informações. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
    } finally {
      setLoadingInfo(false);
    }
  }, [router]);

  useEffect(() => {
    loadLojaInfo();
  }, [loadLojaInfo]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro('');

    const policyError = validatePasswordPolicy(formData.nova_senha);
    if (policyError) {
      setErro(policyError);
      return;
    }

    if (formData.nova_senha !== formData.confirmar_senha) {
      setErro('As senhas não coincidem');
      return;
    }

    if (!lojaId) {
      setErro('ID da loja não encontrado');
      return;
    }

    setLoading(true);

    try {
      await apiClient.post(`/superadmin/lojas/${lojaId}/alterar_senha_primeiro_acesso/`, {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha,
      });

      alert('✅ Senha alterada com sucesso!');
      const destino = tipoLojaNome && isTipoCRMVendas(tipoLojaNome)
        ? `/loja/${lojaSlug}/crm-vendas`
        : `/loja/${lojaSlug}/dashboard`;
      router.push(destino);
    } catch (error) {
      logger.warn('Erro ao alterar senha:', error);
      setErro(formatApiErrorBody(error) || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthScreenShell
      slug={lojaSlug || undefined}
      tipoLojaNome={tipoLojaNome || undefined}
      loginBackground={loginBackground}
      loading={loadingInfo}
    >
      <div className="text-center mb-8">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-yellow-100 dark:bg-yellow-900/30 mb-4">
          <svg className="h-8 w-8 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Alterar Senha Provisória
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Por segurança, você precisa alterar sua senha provisória antes de continuar.
        </p>
      </div>

      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-4 mb-6">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400 dark:text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-200">Primeiro Acesso</h3>
            <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
              Esta é sua senha provisória. Escolha uma senha forte e única.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {erro && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3">
            <p className="text-sm text-red-800 dark:text-red-300">{erro}</p>
          </div>
        )}

        <PasswordInput
          id="nova_senha"
          value={formData.nova_senha}
          onChange={(v) => { setFormData(prev => ({ ...prev, nova_senha: v })); setErro(''); }}
          label="Nova Senha *"
          placeholder="Mínimo 6 caracteres"
          autoComplete="new-password"
          required
        />
        <PasswordInput
          id="confirmar_senha"
          value={formData.confirmar_senha}
          onChange={(v) => { setFormData(prev => ({ ...prev, confirmar_senha: v })); setErro(''); }}
          label="Confirmar Nova Senha *"
          placeholder="Digite a senha novamente"
          autoComplete="new-password"
          required
        />

        <div className="bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-md p-4">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-200 mb-2">
            Requisitos da senha:
          </h4>
          <ul className="text-xs space-y-1.5">
            {checkPasswordRules(formData.nova_senha).map(({ rule, passed }) => (
              <li key={rule.id} className="flex items-center gap-2">
                <span className={`flex-shrink-0 w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  formData.nova_senha
                    ? passed
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                }`}>
                  {formData.nova_senha ? (passed ? '✓' : '✗') : '•'}
                </span>
                <span className={`${
                  formData.nova_senha
                    ? passed
                      ? 'text-green-700 dark:text-green-400'
                      : 'text-red-700 dark:text-red-400'
                    : 'text-gray-600 dark:text-gray-400'
                }`}>
                  {rule.texto}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? 'Alterando...' : 'Alterar Senha e Continuar'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Após alterar a senha, você será redirecionado para o dashboard.
        </p>
      </div>
    </AuthScreenShell>
  );
}
