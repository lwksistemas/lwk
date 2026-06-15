'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { isTipoCRMVendas } from '@/lib/loja-tipo';
import PasswordInput from '@/components/auth/PasswordInput';
import { AuthScreenShell } from '@/components/auth/AuthScreenShell';
import { cacheLojaLoginContext } from '@/lib/login-default-backgrounds';
import { logger } from '@/lib/logger';
import { validatePasswordPolicy } from '@/lib/password-policy';

export default function TrocarSenhaLojaComSlugPage() {
  const router = useRouter();
  const params = useParams();
  const slug = (params?.slug as string) ?? '';
  const [loading, setLoading] = useState(false);
  const [loadingInfo, setLoadingInfo] = useState(true);
  const [lojaId, setLojaId] = useState<number | null>(null);
  const [tipoLojaNome, setTipoLojaNome] = useState<string>('');
  const [loginBackground, setLoginBackground] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    nova_senha: '',
    confirmar_senha: '',
  });
  const [erro, setErro] = useState('');

  const getDestinoAposTroca = useCallback(() => {
    return tipoLojaNome && isTipoCRMVendas(tipoLojaNome)
      ? `/loja/${slug}/crm-vendas`
      : `/loja/${slug}/dashboard`;
  }, [slug, tipoLojaNome]);

  const loadLojaInfo = useCallback(async () => {
    if (!slug) {
      setErro('Informações da loja não encontradas. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
      setLoadingInfo(false);
      return;
    }
    try {
      setLoadingInfo(true);
      const [infoRes, verificarRes] = await Promise.all([
        apiClient.get(`/superadmin/lojas/info_publica/?slug=${slug}`),
        apiClient.get(`/superadmin/lojas/verificar_senha_provisoria/?slug=${encodeURIComponent(slug)}`).catch(() => null),
      ]);
      const tipo = infoRes.data.tipo_loja_nome || '';
      setLojaId(infoRes.data.id);
      setTipoLojaNome(tipo);
      setLoginBackground(infoRes.data.login_background || null);
      cacheLojaLoginContext(slug, tipo, infoRes.data.login_background);

      if (verificarRes?.data?.precisa_trocar_senha === false) {
        const destino = tipo && isTipoCRMVendas(tipo)
          ? `/loja/${slug}/crm-vendas`
          : `/loja/${slug}/dashboard`;
        router.replace(destino);
      }
    } catch (error) {
      logger.warn('Erro ao carregar informações da loja:', error);
      setErro('Erro ao carregar informações. Faça login novamente.');
      setTimeout(() => router.push('/'), 2000);
    } finally {
      setLoadingInfo(false);
    }
  }, [slug, router]);

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
      const res = await apiClient.post(`/superadmin/lojas/${lojaId}/alterar_senha_primeiro_acesso/`, {
        nova_senha: formData.nova_senha,
        confirmar_senha: formData.confirmar_senha,
      });

      if (res.data?.ja_alterada) {
        router.replace(getDestinoAposTroca());
        return;
      }

      alert('✅ Senha alterada com sucesso!');
      router.push(getDestinoAposTroca());
    } catch (error: any) {
      logger.warn('Erro ao alterar senha:', error);
      const msg = error.response?.data?.error || 'Erro ao alterar senha';
      if (typeof msg === 'string' && msg.toLowerCase().includes('já foi alterada')) {
        router.replace(getDestinoAposTroca());
        return;
      }
      setErro(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthScreenShell
      slug={slug}
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
          Alterar Senha
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Por segurança, altere sua senha periodicamente.
        </p>
      </div>

      {erro && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md p-3 mb-6">
          <p className="text-sm text-red-800 dark:text-red-300">{erro}</p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
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

        <button
          type="submit"
          disabled={loading}
          className="w-full px-4 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? 'Alterando...' : 'Alterar Senha'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Após alterar a senha, você será redirecionado para o sistema.
        </p>
      </div>
    </AuthScreenShell>
  );
}
