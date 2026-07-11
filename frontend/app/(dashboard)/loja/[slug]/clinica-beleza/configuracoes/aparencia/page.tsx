'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft, Palette, RotateCcw } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { logger } from '@/lib/logger';
import { useToast } from '@/components/ui/Toast';
import { ClinicaBelezaPageContent } from '@/components/clinica-beleza/ClinicaBelezaPageContent';
import {
  useClinicaBelezaTheme,
  useClinicaBelezaThemeActions,
} from '@/components/clinica-beleza/ClinicaBelezaThemeContext';
import { LoginConfigColorSection } from '@/components/clinica-beleza/login-config-page/LoginConfigColorSection';
import type { LoginColorPreset } from '@/components/clinica-beleza/login-config-page/login-config-page-types';
import {
  CLINICA_AGENDA_STATUS_COLORS,
  CLINICA_AGENDA_STATUS_COLOR_EDITABLE,
  CLINICA_AGENDA_STATUS_LABEL,
  type AgendaStatusColorMap,
  mergeAgendaStatusColors,
} from '@/lib/clinica-beleza-constants';
import { lightenHex, normalizeHexColor } from '@/lib/clinica-beleza-theme-utils';
import { ColunasSection } from '@/components/ui/ColunasSection';
import {
  COLUNAS_CONSULTAS_DISPONIVEIS,
  DEFAULT_COLUNAS_CONSULTAS,
} from '@/lib/clinica-consultas-colunas-config';
import {
  COLUNAS_ESTOQUE_DISPONIVEIS,
  DEFAULT_COLUNAS_ESTOQUE,
} from '@/lib/clinica-estoque-colunas-config';

const CORES_PRE_DEFINIDAS: LoginColorPreset[] = [
  { nome: 'Burgundy', primaria: '#8B3D52', secundaria: '#6B2F40' },
  { nome: 'Rosa', primaria: '#EC4899', secundaria: '#DB2777' },
  { nome: 'Roxo', primaria: '#8B5CF6', secundaria: '#7C3AED' },
  { nome: 'Verde', primaria: '#10B981', secundaria: '#059669' },
  { nome: 'Azul', primaria: '#3B82F6', secundaria: '#2563EB' },
  { nome: 'Laranja', primaria: '#F97316', secundaria: '#EA580C' },
];

const FUNDOS_PRE_DEFINIDOS = [
  { nome: 'Automático', value: '' },
  { nome: 'Cinza claro', value: '#f3f4f6' },
  { nome: 'Gelo', value: '#eef2f7' },
  { nome: 'Verde suave', value: '#e8f5ef' },
  { nome: 'Azul suave', value: '#e8f0fe' },
  { nome: 'Bege', value: '#f5f0e8' },
  { nome: 'Lavanda', value: '#f3eef8' },
] as const;

type LoginConfigResponse = {
  cor_primaria?: string;
  cor_secundaria?: string;
  cor_fundo_pagina?: string;
  agenda_status_colors?: Record<string, { bg?: string; border?: string }> | null;
  colunas_consultas?: string[] | null;
  colunas_estoque?: string[] | null;
};

function toHexInput(value: string, fallback: string): string {
  return normalizeHexColor(value) || fallback;
}

export default function ClinicaBelezaAparenciaPage() {
  const slug = (useParams()?.slug as string) ?? '';
  const base = `/loja/${slug}/clinica-beleza/configuracoes`;
  const toast = useToast();
  const theme = useClinicaBelezaTheme();
  const { applyColors } = useClinicaBelezaThemeActions();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [corPrimaria, setCorPrimaria] = useState('#8B3D52');
  const [corSecundaria, setCorSecundaria] = useState('#6B2F40');
  /** Vazio = automático (tom claro da primária). */
  const [corFundoPagina, setCorFundoPagina] = useState('');
  const [statusColors, setStatusColors] = useState<AgendaStatusColorMap>(
    () => mergeAgendaStatusColors(),
  );
  const [colunasConsultas, setColunasConsultas] = useState<string[]>(
    () => [...DEFAULT_COLUNAS_CONSULTAS],
  );
  const [colunasEstoque, setColunasEstoque] = useState<string[]>(
    () => [...DEFAULT_COLUNAS_ESTOQUE],
  );

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get<LoginConfigResponse>('/crm-vendas/login-config/');
      setCorPrimaria(toHexInput(data.cor_primaria || '', '#8B3D52'));
      setCorSecundaria(toHexInput(data.cor_secundaria || '', '#6B2F40'));
      setCorFundoPagina(normalizeHexColor(data.cor_fundo_pagina || '') || '');
      setStatusColors(mergeAgendaStatusColors(data.agenda_status_colors));
      setColunasConsultas(
        data.colunas_consultas && data.colunas_consultas.length > 0
          ? data.colunas_consultas
          : [...DEFAULT_COLUNAS_CONSULTAS],
      );
      setColunasEstoque(
        data.colunas_estoque && data.colunas_estoque.length > 0
          ? data.colunas_estoque
          : [...DEFAULT_COLUNAS_ESTOQUE],
      );
    } catch (err) {
      logger.warn('Erro ao carregar identidade visual:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadConfig();
  }, [loadConfig]);

  const previewPrimary = useMemo(
    () => normalizeHexColor(corPrimaria) || theme.primary,
    [corPrimaria, theme.primary],
  );

  const previewPageBg = useMemo(() => {
    const custom = normalizeHexColor(corFundoPagina);
    if (custom) return custom;
    return lightenHex(previewPrimary, 0.96) || '#f7f2f4';
  }, [corFundoPagina, previewPrimary]);

  /** Preview ao vivo no menu/fundo — só CSS vars (sem re-render do shell). */
  useEffect(() => {
    if (loading) return;
    applyColors(
      {
        corPrimaria: normalizeHexColor(corPrimaria) || corPrimaria,
        corSecundaria: normalizeHexColor(corSecundaria) || corSecundaria,
        corFundoPagina: normalizeHexColor(corFundoPagina) || '',
      },
      { commit: false },
    );
  }, [loading, corPrimaria, corSecundaria, corFundoPagina, applyColors]);

  const updateStatusColor = (key: string, field: 'bg' | 'border', value: string) => {
    const hex = normalizeHexColor(value);
    if (!hex) return;
    setStatusColors((prev) => {
      const next = { ...prev, [key]: { ...prev[key], [field]: hex } };
      if (key === 'SCHEDULED') {
        next.PENDING = next.SCHEDULED;
      }
      return next;
    });
  };

  const resetStatusColors = () => {
    setStatusColors(mergeAgendaStatusColors());
  };

  const saveConfig = async () => {
    const primaria = normalizeHexColor(corPrimaria);
    const secundaria = normalizeHexColor(corSecundaria);
    if (!primaria || !secundaria) {
      toast.error('Informe cores válidas (#RRGGBB) para o menu.');
      return;
    }

    const agendaPayload: Record<string, { bg: string; border: string }> = {};
    for (const key of CLINICA_AGENDA_STATUS_COLOR_EDITABLE) {
      const entry = statusColors[key];
      const def = CLINICA_AGENDA_STATUS_COLORS[key];
      if (!entry || !def) continue;
      if (entry.bg !== def.bg || entry.border !== def.border) {
        agendaPayload[key] = { bg: entry.bg, border: entry.border };
      }
    }

    setSaving(true);
    try {
      const fundo = normalizeHexColor(corFundoPagina) || '';
      await apiClient.patch('/crm-vendas/login-config/', {
        cor_primaria: primaria,
        cor_secundaria: secundaria,
        cor_fundo_pagina: fundo,
        agenda_status_colors: agendaPayload,
        colunas_consultas: colunasConsultas,
        colunas_estoque: colunasEstoque,
      });
      applyColors(
        {
          corPrimaria: primaria,
          corSecundaria: secundaria,
          corFundoPagina: fundo,
          agendaStatusColors: agendaPayload,
        },
        { commit: true },
      );
      toast.success('Identidade visual salva.');
    } catch (e) {
      const err = e as { response?: { data?: { error?: string; detail?: string } } };
      toast.error(
        err?.response?.data?.error ||
          (typeof err?.response?.data?.detail === 'string' ? err.response.data.detail : null) ||
          'Erro ao salvar. Tente novamente.',
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <ClinicaBelezaPageContent className="space-y-6">
      <Link
        href={base}
        className="inline-flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 hover:underline"
      >
        <ArrowLeft size={16} />
        Voltar às configurações
      </Link>

      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg text-white" style={{ backgroundColor: previewPrimary }}>
            <Palette size={24} />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
              Identidade visual
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Cores do menu, fundo das páginas, status da agenda e colunas de Consultas e Estoque.
            </p>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Carregando...</p>
        ) : (
          <div className="space-y-8">
            <section className="space-y-4">
              <div>
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
                  Cores do menu e do sistema
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  A cor primária destaca itens ativos no menu e botões principais. Também vale para
                  a tela de login. O menu e o fundo atualizam na hora enquanto você escolhe.
                </p>
              </div>
              <LoginConfigColorSection
                colorPresets={CORES_PRE_DEFINIDAS}
                corPrimaria={corPrimaria}
                corSecundaria={corSecundaria}
                accentColor={previewPrimary}
                onApplyPreset={(p, s) => {
                  setCorPrimaria(p);
                  setCorSecundaria(s);
                }}
                onCorPrimariaChange={setCorPrimaria}
                onCorSecundariaChange={setCorSecundaria}
              />
              <div className="rounded-lg border border-dashed border-gray-200 dark:border-gray-600 p-3">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">Prévia do menu</p>
                <div className="flex gap-2">
                  <span
                    className="px-3 py-1.5 rounded-lg text-sm font-medium text-white"
                    style={{ backgroundColor: previewPrimary }}
                  >
                    Item ativo
                  </span>
                  <span className="px-3 py-1.5 rounded-lg text-sm text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-gray-700">
                    Item inativo
                  </span>
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <div>
                <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
                  Fundo das páginas
                </h2>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Cor de fundo atrás dos formulários e listas (ex.: cadastro de cliente). Em
                  automático, usa um tom claro da cor primária.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {FUNDOS_PRE_DEFINIDOS.map((f) => {
                  const selected =
                    f.value === ''
                      ? !corFundoPagina
                      : normalizeHexColor(corFundoPagina) === f.value;
                  return (
                    <button
                      key={f.nome}
                      type="button"
                      onClick={() => setCorFundoPagina(f.value)}
                      className={`px-3 py-2 rounded-lg border text-xs font-medium transition-colors ${
                        selected
                          ? 'border-current'
                          : 'border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300'
                      }`}
                      style={
                        selected
                          ? {
                              borderColor: previewPrimary,
                              backgroundColor: `${previewPrimary}15`,
                              color: previewPrimary,
                            }
                          : undefined
                      }
                    >
                      <span className="inline-flex items-center gap-2">
                        <span
                          className="w-4 h-4 rounded border border-gray-300 shrink-0"
                          style={{
                            backgroundColor:
                              f.value || lightenHex(previewPrimary, 0.96) || '#f7f2f4',
                          }}
                        />
                        {f.nome}
                      </span>
                    </button>
                  );
                })}
              </div>
              <div className="flex flex-wrap items-end gap-3">
                <label className="block text-xs text-gray-500">
                  Cor personalizada
                  <div className="mt-1 flex gap-2">
                    <input
                      type="color"
                      value={previewPageBg}
                      onChange={(e) => setCorFundoPagina(e.target.value)}
                      className="w-12 h-10 border rounded cursor-pointer"
                    />
                    <input
                      type="text"
                      value={corFundoPagina || previewPageBg}
                      onChange={(e) => {
                        const v = e.target.value.trim();
                        if (!v) {
                          setCorFundoPagina('');
                          return;
                        }
                        const hex = normalizeHexColor(v);
                        if (hex) setCorFundoPagina(hex);
                        else setCorFundoPagina(v);
                      }}
                      placeholder="#eef2f7"
                      className="w-28 px-2 py-2 border rounded text-sm dark:bg-gray-700 dark:border-gray-600"
                    />
                  </div>
                </label>
                {corFundoPagina ? (
                  <button
                    type="button"
                    onClick={() => setCorFundoPagina('')}
                    className="text-xs text-gray-600 dark:text-gray-300 hover:underline inline-flex items-center gap-1"
                  >
                    <RotateCcw size={12} />
                    Voltar ao automático
                  </button>
                ) : null}
              </div>
              <div
                className="rounded-lg border border-gray-200 dark:border-gray-600 p-4"
                style={{ backgroundColor: previewPageBg }}
              >
                <div className="rounded-lg bg-white/90 dark:bg-neutral-800/90 border border-gray-200 dark:border-gray-600 p-3 text-xs text-gray-600 dark:text-gray-300">
                  Prévia: área de conteúdo sobre o fundo da página
                </div>
              </div>
            </section>

            <section className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
                    Cores dos status na agenda
                  </h2>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Defina fundo e borda de cada status no calendário. Deixe no padrão LWK ou
                    ajuste para bater com o sistema anterior.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={resetStatusColors}
                  className="inline-flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-300 hover:underline"
                >
                  <RotateCcw size={14} />
                  Restaurar padrão
                </button>
              </div>

              <div className="space-y-3">
                {CLINICA_AGENDA_STATUS_COLOR_EDITABLE.map((key) => {
                  const entry = statusColors[key] || CLINICA_AGENDA_STATUS_COLORS[key];
                  return (
                    <div
                      key={key}
                      className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-lg border border-gray-200 dark:border-gray-600 p-3"
                    >
                      <div className="flex items-center gap-3 min-w-0 sm:w-56">
                        <span
                          className="w-10 h-8 rounded-md shrink-0 border-2"
                          style={{
                            backgroundColor: entry.bg,
                            borderColor: entry.border,
                          }}
                          aria-hidden
                        />
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-100 truncate">
                          {CLINICA_AGENDA_STATUS_LABEL[key] || key}
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
                            className="w-24 px-2 py-1 border rounded text-xs dark:bg-gray-700 dark:border-gray-600"
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
                            className="w-24 px-2 py-1 border rounded text-xs dark:bg-gray-700 dark:border-gray-600"
                          />
                        </label>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>

            <ColunasSection
              sectionId="colunas-consultas"
              title="Colunas da listagem de Consultas"
              description="Escolha quais informações aparecem em Clínica → Consultas."
              colunasDisponiveis={COLUNAS_CONSULTAS_DISPONIVEIS}
              colunas={colunasConsultas}
              onSave={setColunasConsultas}
              onError={(msg) => toast.error(msg)}
              minColunas={3}
              className="!border-0 !shadow-none !p-0 !bg-transparent dark:!bg-transparent"
            />

            <ColunasSection
              sectionId="colunas-estoque"
              title="Colunas da listagem de Estoque"
              description="Escolha quais informações aparecem em Clínica → Estoque. A coluna Ações permanece sempre visível."
              colunasDisponiveis={COLUNAS_ESTOQUE_DISPONIVEIS}
              colunas={colunasEstoque}
              onSave={setColunasEstoque}
              onError={(msg) => toast.error(msg)}
              minColunas={3}
              className="!border-0 !shadow-none !p-0 !bg-transparent dark:!bg-transparent"
            />

            <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-gray-100 dark:border-gray-700">
              <Link
                href={`${base}/login`}
                className="text-sm hover:underline"
                style={{ color: previewPrimary }}
              >
                Configurar tela de login (logo e fundo) →
              </Link>
              <button
                type="button"
                onClick={() => void saveConfig()}
                disabled={saving}
                className="px-4 py-2 text-white rounded-lg disabled:opacity-50"
                style={{ backgroundColor: previewPrimary }}
              >
                {saving ? 'Salvando...' : 'Salvar identidade visual'}
              </button>
            </div>
          </div>
        )}
      </div>
    </ClinicaBelezaPageContent>
  );
}
