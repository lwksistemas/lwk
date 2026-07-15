'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Palette } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { LoginConfigColorSection } from '@/components/clinica-beleza/login-config-page/LoginConfigColorSection';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import { normalizeHexColor } from '@/lib/clinica-beleza-theme-utils';

const CORES_PRE_DEFINIDAS: LoginColorPreset[] = [
  { nome: 'Lumina', primaria: '#4A3042', secundaria: '#6B4560' },
  { nome: 'Blush', primaria: '#C4A4B0', secundaria: '#A88494' },
  { nome: 'Burgundy', primaria: '#8B3D52', secundaria: '#6B2F40' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
];

const FUNDOS = [
  { nome: 'Automático (blush)', value: '' },
  { nome: 'Blush', value: '#F7F0F3' },
  { nome: 'Cinza claro', value: '#f3f4f6' },
  { nome: 'Gelo', value: '#eef2f7' },
  { nome: 'Bege', value: '#f5f0e8' },
] as const;

export default function SalaoAparenciaPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/cabeleireiro/configuracoes`;
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [corPrimaria, setCorPrimaria] = useState(SALAO_PRIMARY);
  const [corSecundaria, setCorSecundaria] = useState('#6B4560');
  const [corFundoPagina, setCorFundoPagina] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{
        cor_primaria?: string;
        cor_secundaria?: string;
        cor_fundo_pagina?: string;
      }>('/crm-vendas/login-config/');
      setCorPrimaria(normalizeHexColor(data.cor_primaria || '') || SALAO_PRIMARY);
      setCorSecundaria(normalizeHexColor(data.cor_secundaria || '') || '#6B4560');
      setCorFundoPagina(normalizeHexColor(data.cor_fundo_pagina || '') || '');
    } catch {
      /* endpoint pode falhar em loja nova */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    const primaria = normalizeHexColor(corPrimaria);
    const secundaria = normalizeHexColor(corSecundaria);
    if (!primaria || !secundaria) {
      toast.error('Informe cores válidas (#RRGGBB)');
      return;
    }
    setSaving(true);
    try {
      await apiClient.patch('/crm-vendas/login-config/', {
        cor_primaria: primaria,
        cor_secundaria: secundaria,
        cor_fundo_pagina: normalizeHexColor(corFundoPagina) || '',
      });
      toast.success('Identidade visual salva.');
    } catch {
      toast.error('Erro ao salvar.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <Link href={base} className="inline-flex items-center gap-2 text-sm text-gray-600 hover:underline">
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white rounded-xl border border-[#E8D5DC] p-6 space-y-6">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: corPrimaria || SALAO_PRIMARY }}>
            <Palette size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Identidade visual</h1>
            <p className="text-sm text-gray-500">Cores do menu (sidebar) e fundo das páginas do salão</p>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <>
            <LoginConfigColorSection
              colorPresets={CORES_PRE_DEFINIDAS}
              corPrimaria={corPrimaria}
              corSecundaria={corSecundaria}
              accentColor={corPrimaria || SALAO_PRIMARY}
              onApplyPreset={(primaria, secundaria) => {
                setCorPrimaria(primaria);
                setCorSecundaria(secundaria);
              }}
              onCorPrimariaChange={setCorPrimaria}
              onCorSecundariaChange={setCorSecundaria}
            />

            <div>
              <p className="text-sm font-medium text-gray-800 mb-2">Fundo das páginas</p>
              <div className="flex flex-wrap gap-2">
                {FUNDOS.map((f) => (
                  <button
                    key={f.nome}
                    type="button"
                    onClick={() => setCorFundoPagina(f.value)}
                    className={`px-3 py-1.5 rounded-lg text-xs border ${
                      corFundoPagina === f.value
                        ? 'border-[#4A3042] bg-[#F7F0F3] font-medium'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    {f.nome}
                  </button>
                ))}
              </div>
              <div className="mt-3 flex items-center gap-2">
                <input
                  type="color"
                  value={corFundoPagina || '#F7F0F3'}
                  onChange={(e) => setCorFundoPagina(e.target.value)}
                  className="h-10 w-14 border rounded"
                />
                <input
                  value={corFundoPagina}
                  onChange={(e) => setCorFundoPagina(e.target.value)}
                  placeholder="#F7F0F3 (vazio = automático)"
                  className="flex-1 border rounded-lg px-3 py-2 text-sm"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="button"
                disabled={saving}
                onClick={() => void save()}
                className="px-5 py-2.5 rounded-lg text-sm font-medium text-white disabled:opacity-60"
                style={{ backgroundColor: corPrimaria || SALAO_PRIMARY }}
              >
                {saving ? 'Salvando...' : 'Salvar identidade visual'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
