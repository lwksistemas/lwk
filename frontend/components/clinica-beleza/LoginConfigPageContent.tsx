'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, LogIn } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ImageUpload } from '@/components/ImageUpload';
import { cloudinaryLojaLogin, useLojaCloudinaryDocument } from '@/lib/cloudinary-folders';
import { logger } from '@/lib/logger';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';

interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

export interface LoginColorPreset {
  nome: string;
  primaria: string;
  secundaria: string;
}

export interface LoginConfigPageContentProps {
  slug: string;
  apiPath: string;
  backHref: string;
  accentColor: string;
  defaultPrimary: string;
  defaultSecondary: string;
  colorPresets: LoginColorPreset[];
  backgroundDescription?: string;
  title?: string;
}

export function LoginConfigPageContent({
  slug,
  apiPath,
  backHref,
  accentColor,
  defaultPrimary,
  defaultSecondary,
  colorPresets,
  backgroundDescription = 'Opcional — se vazio, usa a imagem padrão do tipo de loja',
  title = 'Configurar tela de login',
}: LoginConfigPageContentProps) {
  const { documento: lojaDoc, ready: lojaDocReady, loading: lojaDocLoading } =
    useLojaCloudinaryDocument(slug);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logo, setLogo] = useState('');
  const [loginBackground, setLoginBackground] = useState('');
  const [loginLogo, setLoginLogo] = useState('');
  const [corPrimaria, setCorPrimaria] = useState(defaultPrimary);
  const [corSecundaria, setCorSecundaria] = useState(defaultSecondary);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<LoginConfigData>(apiPath);
      setLogo((data.logo ?? '').toString());
      setLoginBackground((data.login_background ?? '').toString());
      setLoginLogo((data.login_logo ?? '').toString());
      setCorPrimaria((data.cor_primaria ?? defaultPrimary).toString());
      setCorSecundaria((data.cor_secundaria ?? defaultSecondary).toString());
    } catch (err) {
      logger.warn('Erro ao carregar config login:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiPath]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await apiClient.patch(apiPath, {
        logo: logo.trim(),
        login_background: loginBackground.trim(),
        login_logo: loginLogo.trim(),
        cor_primaria: corPrimaria.startsWith('#') ? corPrimaria : `#${corPrimaria}`,
        cor_secundaria: corSecundaria.startsWith('#') ? corSecundaria : `#${corSecundaria}`,
      });
      await loadConfig();
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
    <ClinicaBelezaPageContent className="space-y-6">
      <Link
        href={backHref}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: accentColor }}>
            <LogIn size={24} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 dark:text-white">{title}</h1>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
          Personalize logo, cores e identidade visual da tela de login.
        </p>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-6">
            <ImageUpload
              label="Logo da clínica (principal)"
              description="Usado no sistema (PNG com fundo transparente recomendado)"
              value={logo}
              onChange={setLogo}
              maxSize={2}
              aspectRatio="16:9"
              folder={cloudinaryLojaLogin(lojaDoc)}
              disabled={lojaDocLoading || !lojaDocReady}
            />
            <ImageUpload
              label="Imagem de fundo da tela de login"
              description={backgroundDescription}
              value={loginBackground}
              onChange={setLoginBackground}
              maxSize={5}
              aspectRatio="16:9"
              folder={cloudinaryLojaLogin(lojaDoc)}
              disabled={lojaDocLoading || !lojaDocReady}
            />
            <ImageUpload
              label="Logo da tela de login"
              description="Opcional — se vazio, usa o logo principal"
              value={loginLogo}
              onChange={setLoginLogo}
              maxSize={2}
              aspectRatio="1:1"
              folder={cloudinaryLojaLogin(lojaDoc)}
              disabled={lojaDocLoading || !lojaDocReady}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Cores pré-definidas
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {colorPresets.map((cor) => (
                  <button
                    key={cor.nome}
                    type="button"
                    onClick={() => {
                      setCorPrimaria(cor.primaria);
                      setCorSecundaria(cor.secundaria);
                    }}
                    className={`p-3 rounded-lg border-2 transition-all ${
                      corPrimariaHex === cor.primaria
                        ? 'border-current bg-opacity-10'
                        : 'border-gray-200 dark:border-gray-600'
                    }`}
                    style={
                      corPrimariaHex === cor.primaria
                        ? { borderColor: accentColor, backgroundColor: `${accentColor}15` }
                        : undefined
                    }
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
                    className="w-12 h-10 border rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={corPrimariaHex}
                    onChange={(e) =>
                      setCorPrimaria(e.target.value.startsWith('#') ? e.target.value : `#${e.target.value}`)
                    }
                    className="flex-1 px-3 py-2 border rounded-md text-sm dark:bg-gray-700 dark:border-gray-600"
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
                    className="w-12 h-10 border rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={corSecundariaHex}
                    onChange={(e) =>
                      setCorSecundaria(
                        e.target.value.startsWith('#') ? e.target.value : `#${e.target.value}`,
                      )
                    }
                    className="flex-1 px-3 py-2 border rounded-md text-sm dark:bg-gray-700 dark:border-gray-600"
                  />
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3">
              <a
                href={`/loja/${slug}/login`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm hover:underline"
                style={{ color: accentColor }}
              >
                Ver tela de login →
              </a>
              <button
                type="button"
                onClick={saveConfig}
                disabled={saving}
                className="px-4 py-2 text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: accentColor }}
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </div>
        )}
      </div>
    </ClinicaBelezaPageContent>
  );
}
