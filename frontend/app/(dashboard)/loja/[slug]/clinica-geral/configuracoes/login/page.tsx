'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Check, Image, LogIn, Palette } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { ImageUploadMedia as ImageUpload } from '@/components/ImageUploadMedia';

const NAVY = '#2F2E5B';
const TEAL = '#0D9B9B';

interface LoginConfigData {
  logo: string;
  login_background: string;
  login_logo: string;
  cor_primaria: string;
  cor_secundaria: string;
}

const CORES = [
  { nome: 'Navy', primaria: NAVY, secundaria: '#232247' },
  { nome: 'Teal', primaria: TEAL, secundaria: '#0A7F7F' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Índigo', primaria: '#6366F1', secundaria: '#4F46E5' },
];

export default function ClinicaGeralLoginConfigPage() {
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
      } catch {
        /* endpoint pode não existir */
      }
      setLoading(false);
    })();
  }, []);

  const salvar = async () => {
    if (!config) return;
    setSaving(true);
    setMsg(null);
    try {
      await apiClient.patch('/crm-vendas/login-config/', config);
      setMsg('Salvo com sucesso!');
    } catch {
      setMsg('Erro ao salvar.');
    }
    setSaving(false);
  };

  if (loading) {
    return <p className="p-8 text-sm text-slate-500">Carregando tela de login...</p>;
  }

  return (
    <div className="min-h-full bg-[#F7F8FB]">
      <div className="text-white shadow-sm" style={{ backgroundColor: NAVY }}>
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-4 py-5 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-white/15 p-2">
              <LogIn className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold">Tela de login</h1>
              <p className="text-sm text-white/80">Logo, fundo e cores da entrada</p>
            </div>
          </div>
          <Link
            href={`/loja/${slug}/clinica-geral/configuracoes`}
            className="flex items-center gap-1 rounded-md bg-white/15 px-3 py-2 text-sm hover:bg-white/25"
          >
            <ArrowLeft className="h-4 w-4" /> Voltar
          </Link>
        </div>
      </div>

      <div className="mx-auto max-w-4xl space-y-6 px-4 py-8 sm:px-6">
        {config ? (
          <>
            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-xl bg-indigo-100 p-2.5 text-indigo-700">
                  <Image className="h-5 w-5" aria-hidden="true" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">Logo do login</h2>
              </div>
              <ImageUpload
                value={config.login_logo}
                onChange={(v) => setConfig({ ...config, login_logo: v })}
                folder="fotos"
              />
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-xl bg-sky-100 p-2.5 text-sky-700">
                  <Image className="h-5 w-5" aria-hidden="true" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">Fundo do login</h2>
              </div>
              <ImageUpload
                value={config.login_background}
                onChange={(v) => setConfig({ ...config, login_background: v })}
                folder="fotos"
              />
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-xl bg-amber-100 p-2.5 text-amber-700">
                  <Palette className="h-5 w-5" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">Cores</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                {CORES.map((c) => (
                  <button
                    key={c.nome}
                    type="button"
                    onClick={() => setConfig({ ...config, cor_primaria: c.primaria, cor_secundaria: c.secundaria })}
                    title={c.nome}
                    className="group relative"
                  >
                    <div
                      className={`h-12 w-12 rounded-xl border-2 ${
                        config.cor_primaria === c.primaria ? 'scale-110 border-slate-900' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: c.primaria }}
                    >
                      {config.cor_primaria === c.primaria && (
                        <div className="absolute inset-0 flex items-center justify-center">
                          <Check className="h-5 w-5 text-white drop-shadow" />
                        </div>
                      )}
                    </div>
                    <p className="mt-1 text-center text-[10px] text-slate-500">{c.nome}</p>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-6">
              {msg ? (
                <p className={`text-sm font-medium ${msg.includes('Erro') ? 'text-red-600' : 'text-emerald-600'}`}>
                  {msg}
                </p>
              ) : (
                <div />
              )}
              <button
                type="button"
                onClick={() => void salvar()}
                disabled={saving}
                className="rounded-lg px-6 py-2.5 font-medium text-white disabled:opacity-50"
                style={{ backgroundColor: TEAL }}
              >
                {saving ? 'Salvando...' : 'Salvar'}
              </button>
            </div>
          </>
        ) : (
          <p className="py-16 text-center text-sm text-slate-500">
            Configuração de login não disponível para esta loja.
          </p>
        )}
      </div>
    </div>
  );
}
