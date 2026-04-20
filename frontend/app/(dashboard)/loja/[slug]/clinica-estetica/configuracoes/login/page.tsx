'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, LogIn } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ImageUpload } from '@/components/ImageUpload';

interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

const CORES_PRE_DEFINIDAS = [
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
  { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
];

export default function ClinicaConfiguracoesLoginPage() {
  const params = useParams();
  const router = useRouter();
  const slug = (params?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-estetica/configuracoes`;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logo, setLogo] = useState('');
  const [loginBackground, setLoginBackground] = useState('');
  const [loginLogo, setLoginLogo] = useState('');
  const [corPrimaria, setCorPrimaria] = useState('#EC4899');
  const [corSecundaria, setCorSecundaria] = useState('#DB2777');

  const loadConfig = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<LoginConfigData>('/clinica/login-config/');
      setLogo((data.logo ?? '').toString());
      setLoginBackground((data.login_background ?? '').toString());
      setLoginLogo((data.login_logo ?? '').toString());
      setCorPrimaria((data.cor_primaria ?? '#EC4899').toString());
      setCorSecundaria((data.cor_secundaria ?? '#DB2777').toString());
    } catch (err) {
      console.error('Erro ao carregar config:', err);
      setLogo('');
      setLoginBackground('');
      setLoginLogo('');
      setCorPrimaria('#EC4899');
      setCorSecundaria('#DB2777');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await apiClient.patch('/clinica/login-config/', {
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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div>
              <h1 className="text-2xl font-bold">Configurar tela de login</h1>
              <p className="text-pink-100 text-sm">Personalize a aparência</p>
            </div>
            <Link
              href={base}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 rounded-md transition-colors flex items-center gap-2"
            >
              <ArrowLeft size={16} />
              Voltar
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2.5 rounded-lg bg-pink-100 text-pink-600">
                <LogIn size={24} />
              </div>
              <h2 className="text-xl font-semibold text-gray-900">
                Configurar tela de login
              </h2>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Personalize a aparência da tela de login da sua clínica (logo, cores e identidade visual).
            </p>

            {loading ? (
              <p className="text-sm text-gray-500">Carregando...</p>
            ) : (
              <div className="space-y-6">
                {/* Logo principal */}
                <ImageUpload
                  label="Logo da clínica (principal)"
                  description="Logo principal da clínica, usado no sistema (recomendado: PNG com fundo transparente)"
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
                  <label className="block text-sm font-medium text-gray-700 mb-2">
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
                            ? 'border-pink-500 bg-pink-50'
                            : 'border-gray-200 hover:border-pink-500/50'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <div
                            className="w-6 h-6 rounded-full shrink-0"
                            style={{ backgroundColor: cor.primaria }}
                          />
                          <span className="text-sm font-medium text-gray-900 truncate">
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
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cor primária
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={corPrimariaHex}
                        onChange={(e) => setCorPrimaria(e.target.value)}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={corPrimariaHex}
                        onChange={(e) => {
                          const v = e.target.value;
                          setCorPrimaria(v.startsWith('#') ? v : `#${v}`);
                        }}
                        placeholder="#EC4899"
                        className="flex-1 px-3 py-2 border border-gray-300 bg-white text-gray-900 rounded-md text-sm"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Cor secundária
                    </label>
                    <div className="flex gap-2">
                      <input
                        type="color"
                        value={corSecundariaHex}
                        onChange={(e) => setCorSecundaria(e.target.value)}
                        className="w-12 h-10 border border-gray-300 rounded cursor-pointer"
                      />
                      <input
                        type="text"
                        value={corSecundariaHex}
                        onChange={(e) => {
                          const v = e.target.value;
                          setCorSecundaria(v.startsWith('#') ? v : `#${v}`);
                        }}
                        placeholder="#DB2777"
                        className="flex-1 px-3 py-2 border border-gray-300 bg-white text-gray-900 rounded-md text-sm"
                      />
                    </div>
                  </div>
                </div>

                {/* Preview */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Prévia da tela de login
                  </label>
                  <div
                    className="rounded-lg border border-gray-200 overflow-hidden relative"
                    style={{
                      background: `linear-gradient(to bottom right, ${corPrimariaHex}, ${corSecundariaHex})`,
                      minHeight: '300px',
                    }}
                  >
                    {loginBackground && (
                      <>
                        <div
                          className="absolute inset-y-0 left-0 w-1/2"
                          style={{
                            background: `url(${loginBackground}) left center / auto 100% no-repeat`,
                          }}
                        />
                        <div
                          className="absolute inset-y-0 right-0 w-1/2"
                          style={{
                            background: `url(${loginBackground}) right center / auto 100% no-repeat`,
                          }}
                        />
                        <div className="absolute inset-0 bg-black/25" />
                      </>
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
                      <div className="w-full max-w-[200px] bg-white rounded-lg p-4 shadow-inner">
                        <div className="h-3 rounded bg-gray-200 mb-2" />
                        <div className="h-3 rounded bg-gray-200 mb-2 w-3/4" />
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
                    className="text-sm text-pink-600 hover:underline"
                  >
                    Ver tela de login →
                  </a>
                  <button
                    type="button"
                    onClick={saveConfig}
                    disabled={saving}
                    className="px-4 py-2 bg-pink-600 text-white rounded-lg hover:bg-pink-700 disabled:opacity-50"
                  >
                    {saving ? 'Salvando...' : 'Salvar'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
