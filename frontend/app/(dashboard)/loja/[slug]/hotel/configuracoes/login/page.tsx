'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { LogIn, ArrowLeft, Palette, Image, Check } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ImageUpload } from '@/components/ImageUpload';

interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

const CORES = [
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Vermelho', primaria: '#EF4444', secundaria: '#DC2626' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Cyan', primaria: '#06B6D4', secundaria: '#0891B2' },
  { nome: 'Índigo', primaria: '#6366F1', secundaria: '#4F46E5' },
];

export default function HotelLoginConfigPage() {
  const params = useParams();
  const slug = (params?.slug as string) ?? '';

  const [config, setConfig] = useState<LoginConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await apiClient.get('/crm-vendas/login-config/');
        setConfig(data);
      } catch { /* endpoint pode não existir */ }
      setLoading(false);
    })();
  }, []);

  const salvar = async () => {
    if (!config) return;
    setSaving(true);
    setMsg(null);
    try {
      await apiClient.put('/crm-vendas/login-config/', config);
      setMsg('Salvo com sucesso!');
    } catch {
      setMsg('Erro ao salvar.');
    }
    setSaving(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-white to-cyan-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-cyan-600 text-white shadow-lg">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-white/15 rounded-lg">
                <LogIn className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Configurar Tela de Login</h1>
                <p className="text-white/80 text-sm">Personalize a aparência da tela de login</p>
              </div>
            </div>
            <Link href={`/loja/${slug}/hotel/configuracoes`} className="px-3 py-2 bg-white/15 hover:bg-white/25 rounded-md transition-colors text-sm flex items-center gap-1">
              <ArrowLeft className="w-4 h-4" /> Voltar
            </Link>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {config ? (
          <>
            {/* Logo */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
              <div className="h-1.5 bg-gradient-to-r from-purple-500 to-violet-600" />
              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300">
                    <Image className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Logo do Login</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
                      Imagem que aparece no topo da tela de login.
                    </p>
                    <ImageUpload value={config.login_logo} onChange={(v) => setConfig({ ...config, login_logo: v })} />
                  </div>
                </div>
              </div>
            </div>

            {/* Background */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
              <div className="h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600" />
              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                    <Image className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Background do Login</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
                      Imagem de fundo da tela de login.
                    </p>
                    <ImageUpload value={config.login_background} onChange={(v) => setConfig({ ...config, login_background: v })} />
                  </div>
                </div>
              </div>
            </div>

            {/* Cores */}
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-sm">
              <div className="h-1.5 bg-gradient-to-r from-amber-500 to-orange-600" />
              <div className="p-6">
                <div className="flex items-start gap-4">
                  <div className="p-3 rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
                    <Palette className="w-6 h-6" />
                  </div>
                  <div className="flex-1">
                    <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Cores do Sistema</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1 mb-4">
                      Escolha a cor principal do sistema.
                    </p>
                    <div className="flex gap-3 flex-wrap">
                      {CORES.map((c) => (
                        <button
                          key={c.nome}
                          type="button"
                          onClick={() => setConfig({ ...config, cor_primaria: c.primaria, cor_secundaria: c.secundaria })}
                          className="group relative"
                          title={c.nome}
                        >
                          <div
                            className={`w-12 h-12 rounded-xl border-2 transition-all ${config.cor_primaria === c.primaria ? 'border-gray-900 dark:border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105 hover:shadow-md'}`}
                            style={{ backgroundColor: c.primaria }}
                          >
                            {config.cor_primaria === c.primaria && (
                              <div className="absolute inset-0 flex items-center justify-center">
                                <Check className="w-5 h-5 text-white drop-shadow" />
                              </div>
                            )}
                          </div>
                          <p className="text-[10px] text-center text-gray-500 dark:text-gray-400 mt-1">{c.nome}</p>
                        </button>
                      ))}
                    </div>

                    {/* Preview */}
                    <div className="mt-5 p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Pré-visualização:</p>
                      <div className="flex items-center gap-3">
                        <div className="h-8 w-24 rounded-md" style={{ backgroundColor: config.cor_primaria }} />
                        <div className="h-8 w-24 rounded-md" style={{ backgroundColor: config.cor_secundaria }} />
                        <span className="text-xs text-gray-500">{config.cor_primaria} / {config.cor_secundaria}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Salvar */}
            <div className="flex items-center justify-between gap-4 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
              {msg && (
                <p className={`text-sm font-medium ${msg.includes('Erro') ? 'text-red-600' : 'text-green-600'}`}>
                  {msg.includes('Erro') ? '❌' : '✅'} {msg}
                </p>
              )}
              {!msg && <div />}
              <button
                onClick={salvar}
                disabled={saving}
                className="px-6 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg disabled:opacity-50 font-medium transition-colors shadow-sm"
              >
                {saving ? 'Salvando...' : 'Salvar Configurações'}
              </button>
            </div>
          </>
        ) : (
          <div className="text-center py-20">
            <LogIn className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-lg font-medium text-gray-600 dark:text-gray-400">Configuração de login não disponível para esta loja.</p>
          </div>
        )}
      </div>
    </div>
  );
}
