'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Palette, RotateCcw } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useToast } from '@/components/ui/Toast';
import { LoginConfigColorSection } from '@/components/clinica-beleza/login-config-page/LoginConfigColorSection';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';
import { SALAO_PRIMARY } from '@/components/cabeleireiro/salao-nav';
import {
  mergeSalaoAgendaStatusColors,
  SALAO_AGENDA_STATUS_COLOR_EDITABLE,
  SALAO_STATUS_COLORS,
  SALAO_STATUS_LABEL,
  type SalaoStatusColorMap,
} from '@/components/cabeleireiro/salao-agenda-mappers';
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
  const [statusColors, setStatusColors] = useState<SalaoStatusColorMap>(() =>
    mergeSalaoAgendaStatusColors(),
  );

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<{
        cor_primaria?: string;
        cor_secundaria?: string;
        cor_fundo_pagina?: string;
        agenda_status_colors?: Record<string, { bg?: string; border?: string }> | null;
      }>('/crm-vendas/login-config/');
      setCorPrimaria(normalizeHexColor(data.cor_primaria || '') || SALAO_PRIMARY);
      setCorSecundaria(normalizeHexColor(data.cor_secundaria || '') || '#6B4560');
      setCorFundoPagina(normalizeHexColor(data.cor_fundo_pagina || '') || '');
      setStatusColors(mergeSalaoAgendaStatusColors(data.agenda_status_colors));
    } catch {
      /* endpoint pode falhar em loja nova */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const updateStatusColor = (key: string, field: 'bg' | 'border', value: string) => {
    const hex = normalizeHexColor(value);
    if (!hex) return;
    setStatusColors((prev) => ({
      ...prev,
      [key]: { ...prev[key], [field]: hex, text: '#ffffff' },
    }));
  };

  const resetStatusColors = () => {
    setStatusColors(mergeSalaoAgendaStatusColors());
  };

  const save = async () => {
    const primaria = normalizeHexColor(corPrimaria);
    const secundaria = normalizeHexColor(corSecundaria);
    if (!primaria || !secundaria) {
      toast.error('Informe cores válidas (#RRGGBB)');
      return;
    }

    const agendaPayload: Record<string, { bg: string; border: string }> = {};
    for (const key of SALAO_AGENDA_STATUS_COLOR_EDITABLE) {
      const entry = statusColors[key];
      const def = SALAO_STATUS_COLORS[key];
      if (!entry || !def) continue;
      if (entry.bg !== def.bg || entry.border !== def.border) {
        agendaPayload[key] = { bg: entry.bg, border: entry.border };
      }
    }

    setSaving(true);
    try {
      await apiClient.patch('/crm-vendas/login-config/', {
        cor_primaria: primaria,
        cor_secundaria: secundaria,
        cor_fundo_pagina: normalizeHexColor(corFundoPagina) || '',
        agenda_status_colors: agendaPayload,
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

      <div className="bg-white rounded-xl border border-[#E8D5DC] p-6 space-y-8">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: corPrimaria || SALAO_PRIMARY }}>
            <Palette size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Identidade visual</h1>
            <p className="text-sm text-gray-500">
              Cores do menu, fundo das páginas e status da agenda (como na clínica)
            </p>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <>
            <section className="space-y-4">
              <h2 className="text-sm font-semibold text-gray-900">Cores do menu</h2>
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
            </section>

            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-gray-900">Fundo das páginas</h2>
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
              <div className="flex items-center gap-2">
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
            </section>

            <section className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-gray-900">Cores dos status na agenda</h2>
                  <p className="text-xs text-gray-500 mt-1">
                    Defina fundo e borda de cada status no calendário — igual à clínica da beleza.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={resetStatusColors}
                  className="inline-flex items-center gap-1.5 text-xs text-gray-600 hover:underline"
                >
                  <RotateCcw size={14} />
                  Restaurar padrão
                </button>
              </div>

              <div className="space-y-3">
                {SALAO_AGENDA_STATUS_COLOR_EDITABLE.map((key) => {
                  const entry = statusColors[key] || SALAO_STATUS_COLORS[key];
                  return (
                    <div
                      key={key}
                      className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-lg border border-[#E8D5DC] p-3"
                    >
                      <div className="flex items-center gap-3 min-w-0 sm:w-56">
                        <span
                          className="w-10 h-8 rounded-md shrink-0 border-2"
                          style={{ backgroundColor: entry.bg, borderColor: entry.border }}
                          aria-hidden
                        />
                        <span className="text-sm font-medium text-gray-800 truncate">
                          {SALAO_STATUS_LABEL[key] || key}
                        </span>
                      </div>
                      <div className="flex flex-1 flex-wrap gap-3">
                        <label className="flex items-center gap-2 text-xs text-gray-500">
                          Fundo
                          <input
                            type="color"
                            value={entry.bg}
                            onChange={(e) => updateStatusColor(key, 'bg', e.target.value)}
                            className="w-10 h-8 border rounded cursor-pointer"
                          />
                          <input
                            type="text"
                            value={entry.bg}
                            onChange={(e) => updateStatusColor(key, 'bg', e.target.value)}
                            className="w-24 px-2 py-1 border rounded text-xs"
                          />
                        </label>
                        <label className="flex items-center gap-2 text-xs text-gray-500">
                          Borda
                          <input
                            type="color"
                            value={entry.border}
                            onChange={(e) => updateStatusColor(key, 'border', e.target.value)}
                            className="w-10 h-8 border rounded cursor-pointer"
                          />
                          <input
                            type="text"
                            value={entry.border}
                            onChange={(e) => updateStatusColor(key, 'border', e.target.value)}
                            className="w-24 px-2 py-1 border rounded text-xs"
                          />
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <div className="flex justify-end pt-2 border-t border-[#F3E4EA]">
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
