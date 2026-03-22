'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, LogIn } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';
import { ImageUpload } from '@/components/ImageUpload';

interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

const CORES_PRE_DEFINIDAS = [
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
];

export default function ConfiguracoesLoginPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/crm-vendas/configuracoes`;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logo, setLogo] = useState('');
  const [loginBackground, setLoginBackground] = useState('');
  const [loginLogo, setLoginLogo] = useState('');
  const [corPrimaria, setCorPrimaria] = useState('#10B981');
  const [corSecundaria, setCorSecundaria] = useState('#059669');

  const loadConfig = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<LoginConfigData>('/crm-vendas/login-config/');
      console.log('📥 Dados recebidos do backend:', data);
      console.log('  - logo:', data.logo);
      console.log('  - login_background:', data.login_background);
      console.log('  - login_logo:', data.login_logo);
      
      setLogo((data.logo ?? '').toString());
      setLoginBackground((data.login_background ?? '').toString());
      setLoginLogo((data.login_logo ?? '').toString());
      setCorPrimaria((data.cor_primaria ?? '#10B981').toString());
      setCorSecundaria((data.cor_secundaria ?? '#059669').toString());
      
      console.log('✅ Estados atualizados');
    } catch (err) {
      console.error('❌ Erro ao carregar config:', err);
      setLogo('');
      setLoginBackground('');
      setLoginLogo('');
      setCorPrimaria('#10B981');
      setCorSecundaria('#059669');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authService.isVendedor()) {
      router.replace(`/loja/${slug}/crm-vendas`);
      return;
    }
    loadConfig();
  }, [router, slug]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await apiClient.patch('/crm-vendas/login-config/', {
        logo: logo.trim(),
        login_background: loginBackground.trim(),
        login_logo: loginLogo.trim(),
        cor_primaria: corPrimaria.startsWith('#') ? corPrimaria : `#${corPrimaria}`,
        cor_secundaria: corSecundaria.startsWith('#') ? corSecundaria : `#${corSecundaria}`,
      });
      loadConfig();
      alert('Configurações da tela de login salvas com sucesso!');
    } catch (e) {
      const err = e as { response?: { data?: { error?: string; detail?: string } } };
      const msg =
        err?.response?.data?.error ||
        (typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : null) ||
        'Erro ao salvar. Tente novamente.';
      alert(msg);
    } finally {
      setSaving(false);
    }
  };

  const corPrimariaHex = corPrimaria.startsWith('#') ? corPrimaria : `#${corPrimaria}`;
  const corSecundariaHex = corSecundaria.startsWith('#') ? corSecundaria : `#${corSecundaria}`;

  return (
    <div className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:text-[#0176d3] dark:hover:text-[#0d9dda]"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg bg-[#e3f3ff] dark:bg-[#0176d3]/20 text-[#0176d3]">
            <LogIn size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
            Configurar tela de login
          </h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Personalize a aparência da tela de login da sua loja (logo, cores e identidade visual).
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-6">
            {/* Logo principal */}
            <ImageUpload
              label="Logo da loja (principal)"
              description="Logo principal da loja, usado no sistema (recomendado: PNG com fundo transparente)"
              value={logo}
              onChange={(url) => setLogo(url)}
              maxSize={2}
              aspectRatio="16:9"
            />

            {/* Imagem de fundo do login */}
            <ImageUpload
              label="Imagem de fundo da tela de login"
              description="Imagem de fundo exibida na tela de login (opcional, deixe vazio para usar gradiente de cores)"
              value={loginBackground}
              onChange={(url) => setLoginBackground(url)}
              maxSize={5}
              aspectRatio="16:9"
            />

            {/* Logo específico do login */}
            <ImageUpload
              label="Logo da tela de login"
              description="Logo específico para a tela de login (opcional, se não definido usa o logo principal)"
              value={loginLogo}
              onChange={(url) => setLoginLogo(url)}
              maxSize={2}
              aspectRatio="1:1"
            />

            {/* Cores pré-definidas */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Cores pré-definidas
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {CORES_PRE_DEFINIDAS.map((cor) => (
                  <button
                    key={cor.nome}
                    type="button"
                    onClick={() => {
                      setCorPrimaria(cor.primaria);
                      setCorSecundaria(cor.secundaria);
                    }}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      corPrimariaHex === cor.primaria
                        ? 'border-[#0176d3] bg-[#e3f3ff] dark:bg-[#0176d3]/20'
                        : 'border-gray-200 dark:border-[#0d1f3c] hover:border-[#0176d3]/50'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded-full shrink-0"
                        style={{ backgroundColor: cor.primaria }}
                      />
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {cor.nome}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Cores personalizadas */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cor primária
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={corPrimariaHex}
                    onChange={(e) => setCorPrimaria(e.target.value)}
                    className="w-12 h-10 border border-gray-300 dark:border-neutral-600 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={corPrimariaHex}
                    onChange={(e) => {
                      const v = e.target.value;
                      setCorPrimaria(v.startsWith('#') ? v : `#${v}`);
                    }}
                    placeholder="#10B981"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 rounded-md text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Cor secundária
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={corSecundariaHex}
                    onChange={(e) => setCorSecundaria(e.target.value)}
                    className="w-12 h-10 border border-gray-300 dark:border-neutral-600 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={corSecundariaHex}
                    onChange={(e) => {
                      const v = e.target.value;
                      setCorSecundaria(v.startsWith('#') ? v : `#${v}`);
                    }}
                    placeholder="#059669"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100 rounded-md text-sm"
                  />
                </div>
              </div>
            </div>

            {/* Preview */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Prévia da tela de login
              </label>
              <div
                className="rounded-lg border border-gray-200 dark:border-[#0d1f3c] overflow-hidden relative"
                style={{
                  background: loginBackground 
                    ? `url(${loginBackground}) center/cover no-repeat`
                    : `linear-gradient(to bottom right, ${corPrimariaHex}, ${corSecundariaHex})`,
                  minHeight: '300px',
                }}
              >
                {/* Overlay escuro se houver imagem de fundo */}
                {loginBackground && (
                  <div className="absolute inset-0 bg-black/40" />
                )}
                
                <div className="p-6 flex flex-col items-center relative z-10">
                  <div
                    className="w-14 h-14 rounded-full flex items-center justify-center mb-3 overflow-hidden"
                    style={{ backgroundColor: corPrimariaHex }}
                  >
                    {(loginLogo || logo) ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={loginLogo || logo}
                        alt="Logo"
                        className="w-10 h-10 rounded-full object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          const fallback = e.currentTarget.nextElementSibling as HTMLElement;
                          if (fallback) fallback.classList.remove('hidden');
                        }}
                      />
                    ) : null}
                    <svg
                      className={`h-8 w-8 text-white ${(loginLogo || logo) ? 'hidden' : ''}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                    </svg>
                  </div>
                  <div className="w-full max-w-[200px] bg-white dark:bg-gray-800 rounded-lg p-4 shadow-inner">
                    <div className="h-3 rounded bg-gray-200 dark:bg-gray-600 mb-2" />
                    <div className="h-3 rounded bg-gray-200 dark:bg-gray-600 mb-2 w-3/4" />
                    <div
                      className="h-8 rounded mt-3"
                      style={{ backgroundColor: corPrimariaHex }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3">
              <a
                href={`/loja/${slug}/login`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-[#0176d3] hover:underline"
              >
                Ver tela de login →
              </a>
              <button
                type="button"
                onClick={saveConfig}
                disabled={saving}
                className="px-4 py-2 bg-[#0176d3] text-white rounded-lg hover:bg-[#0176d3]/90 disabled:opacity-50"
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
