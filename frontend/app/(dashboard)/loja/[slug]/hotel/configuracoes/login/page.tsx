'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { LogIn } from 'lucide-react';
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

  if (loading) return <div className="max-w-3xl mx-auto p-6 text-sm text-gray-500">Carregando...</div>;

  return (
    <div className="max-w-3xl mx-auto p-4 sm:p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-3">
          <LogIn size={24} className="text-sky-600" /> Configurar Tela de Login
        </h1>
        <Link href={`/loja/${slug}/hotel/configuracoes`} className="text-sm text-sky-700 hover:underline">← Voltar</Link>
      </div>

      {config && (
        <div className="space-y-6 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-6">
          <div>
            <label className="block text-sm font-medium mb-2">Logo do Login</label>
            <ImageUpload value={config.login_logo} onChange={(v) => setConfig({ ...config, login_logo: v })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Background do Login</label>
            <ImageUpload value={config.login_background} onChange={(v) => setConfig({ ...config, login_background: v })} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Cor Primária</label>
            <div className="flex gap-2 flex-wrap">
              {CORES.map((c) => (
                <button
                  key={c.nome}
                  type="button"
                  onClick={() => setConfig({ ...config, cor_primaria: c.primaria, cor_secundaria: c.secundaria })}
                  className={`w-10 h-10 rounded-full border-2 ${config.cor_primaria === c.primaria ? 'border-gray-900 dark:border-white' : 'border-transparent'}`}
                  style={{ backgroundColor: c.primaria }}
                  title={c.nome}
                />
              ))}
            </div>
          </div>

          {msg && <p className={`text-sm ${msg.includes('Erro') ? 'text-red-600' : 'text-green-600'}`}>{msg}</p>}

          <button
            onClick={salvar}
            disabled={saving}
            className="px-6 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-lg disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      )}

      {!config && <p className="text-sm text-gray-500">Configuração de login não disponível para esta loja.</p>}
    </div>
  );
}
