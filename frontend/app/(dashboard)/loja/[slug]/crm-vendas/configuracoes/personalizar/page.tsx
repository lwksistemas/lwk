'use client';

import { useEffect, useState } from 'react';
import { Settings } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { formatApiErrorBody } from '@/lib/api-errors';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { OrigensSection } from './components/OrigensSection';
import { ModulosSection } from './components/ModulosSection';
import { EtapasSection } from './components/EtapasSection';
import { ColunasSection } from './components/ColunasSection';
import {
  COLUNAS_LEADS_DISPONIVEIS,
  COLUNAS_CONTAS_DISPONIVEIS,
  COLUNAS_CONTATOS_DISPONIVEIS,
  COLUNAS_PROPOSTAS_DISPONIVEIS,
  COLUNAS_CONTRATOS_DISPONIVEIS,
  DEFAULT_COLUNAS_LEADS,
  DEFAULT_COLUNAS_CONTAS,
  DEFAULT_COLUNAS_CONTATOS,
  DEFAULT_COLUNAS_PROPOSTAS,
  DEFAULT_COLUNAS_CONTRATOS,
} from '@/lib/crm-colunas-config';

const SECOES = [
  { id: 'origens', label: 'Origens de Leads' },
  { id: 'modulos', label: 'Módulos' },
  { id: 'etapas', label: 'Etapas do Pipeline' },
  { id: 'colunas-leads', label: 'Colunas — Leads' },
  { id: 'colunas-contas', label: 'Colunas — Empresas' },
  { id: 'colunas-contatos', label: 'Colunas — Contatos' },
  { id: 'colunas-propostas', label: 'Colunas — Propostas' },
  { id: 'colunas-contratos', label: 'Colunas — Contratos' },
] as const;

type SecaoId = (typeof SECOES)[number]['id'];

interface CRMConfig {
  id: number;
  origens_leads: Array<{ key: string; label: string; ativo: boolean }>;
  etapas_pipeline: Array<{ key: string; label: string; ativo: boolean; ordem: number }>;
  colunas_leads: string[];
  colunas_contas: string[];
  colunas_contatos: string[];
  colunas_propostas: string[];
  colunas_contratos: string[];
  modulos_ativos: Record<string, boolean>;
}

export default function ConfiguracoesPage() {
  const { recarregar } = useCRMConfig();
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [secao, setSecao] = useState<SecaoId | null>(null);

  useEffect(() => {
    const hash = window.location.hash.replace('#', '') as SecaoId;
    if (SECOES.some((item) => item.id === hash)) setSecao(hash);
  }, []);

  const escolherSecao = (id: SecaoId) => {
    setSecao(id);
    window.history.replaceState(null, '', `#${id}`);
  };

  useEffect(() => {
    apiClient.get<CRMConfig>('/crm-vendas/config/')
      .then((res) => setConfig(res.data))
      .catch((e) => setError(formatApiErrorBody(e) || 'Erro ao carregar configurações.'))
      .finally(() => setLoading(false));
  }, []);

  const salvarConfig = async (patch: Partial<CRMConfig>) => {
    setSaving(true); setError(null); setSuccess(null);
    try {
      const res = await apiClient.patch<CRMConfig>('/crm-vendas/config/', patch);
      setConfig(res.data);
      setSuccess('Configurações salvas com sucesso!');
      setTimeout(() => setSuccess(null), 3000);
      await recarregar();
    } catch (e) {
      setError(formatApiErrorBody(e) || 'Erro ao salvar configurações.');
    } finally {
      setSaving(false);
    }
  };

  const handleError = (msg: string) => { setError(msg); setTimeout(() => setError(null), 3000); };

  if (loading) {
    return <div className="flex items-center justify-center min-h-[400px]"><div className="text-gray-500">Carregando configurações...</div></div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Settings size={28} className="text-[#0176d3]" /> Configurações do CRM
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Personalize o sistema de acordo com suas necessidades</p>
      </div>

      {error && <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4"><p className="text-sm text-red-600 dark:text-red-400">{error}</p></div>}
      {success && <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4"><p className="text-sm text-green-600 dark:text-green-400">{success}</p></div>}

      <nav className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-4" aria-label="Atalhos da personalização">
        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">Ir para</p>
        <div className="flex flex-wrap gap-2">
          {SECOES.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => escolherSecao(item.id)}
              aria-pressed={secao === item.id}
              className={`text-sm px-3 py-1.5 rounded-full border transition-colors ${
                secao === item.id
                  ? 'bg-[#0176d3] border-[#0176d3] text-white'
                  : 'border-[#0176d3]/30 text-[#0176d3] hover:bg-[#e3f3ff] dark:hover:bg-[#0176d3]/20'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      {secao === 'origens' && (
        <OrigensSection origens={config?.origens_leads || []} saving={saving} onSave={(o) => salvarConfig({ origens_leads: o })} onError={handleError} />
      )}
      {secao === 'modulos' && (
        <ModulosSection modulos={config?.modulos_ativos || {}} onSave={(m) => salvarConfig({ modulos_ativos: m })} />
      )}
      {secao === 'etapas' && (
        <EtapasSection etapas={config?.etapas_pipeline || []} onSave={(e) => salvarConfig({ etapas_pipeline: e })} onError={handleError} />
      )}
      {secao === 'colunas-leads' && (
        <ColunasSection
          sectionId="colunas-leads"
          title="Colunas Visíveis nos Leads"
          colunasDisponiveis={COLUNAS_LEADS_DISPONIVEIS}
          colunas={config?.colunas_leads?.length ? config.colunas_leads : DEFAULT_COLUNAS_LEADS}
          onSave={(c) => salvarConfig({ colunas_leads: c })}
          onError={handleError}
        />
      )}
      {secao === 'colunas-contas' && (
        <ColunasSection
          sectionId="colunas-contas"
          title="Colunas Visíveis nas Empresas"
          description="Escolha quais informações aparecem na listagem de empresas."
          colunasDisponiveis={COLUNAS_CONTAS_DISPONIVEIS}
          colunas={config?.colunas_contas?.length ? config.colunas_contas : DEFAULT_COLUNAS_CONTAS}
          onSave={(c) => salvarConfig({ colunas_contas: c })}
          onError={handleError}
        />
      )}
      {secao === 'colunas-contatos' && (
        <ColunasSection
          sectionId="colunas-contatos"
          title="Colunas Visíveis nos Contatos"
          description="Escolha quais informações aparecem na listagem de contatos (pessoas vinculadas às contas)."
          colunasDisponiveis={COLUNAS_CONTATOS_DISPONIVEIS}
          colunas={config?.colunas_contatos?.length ? config.colunas_contatos : DEFAULT_COLUNAS_CONTATOS}
          onSave={(c) => salvarConfig({ colunas_contatos: c })}
          onError={handleError}
        />
      )}
      {secao === 'colunas-propostas' && (
        <ColunasSection
          sectionId="colunas-propostas"
          title="Colunas Visíveis nas Propostas"
          description="Escolha quais informações aparecem na listagem de propostas."
          colunasDisponiveis={COLUNAS_PROPOSTAS_DISPONIVEIS}
          colunas={config?.colunas_propostas?.length ? config.colunas_propostas : DEFAULT_COLUNAS_PROPOSTAS}
          onSave={(c) => salvarConfig({ colunas_propostas: c })}
          onError={handleError}
        />
      )}
      {secao === 'colunas-contratos' && (
        <ColunasSection
          sectionId="colunas-contratos"
          title="Colunas Visíveis nos Contratos"
          description="Escolha quais informações aparecem na listagem de contratos."
          colunasDisponiveis={COLUNAS_CONTRATOS_DISPONIVEIS}
          colunas={config?.colunas_contratos?.length ? config.colunas_contratos : DEFAULT_COLUNAS_CONTRATOS}
          onSave={(c) => salvarConfig({ colunas_contratos: c })}
          onError={handleError}
        />
      )}
    </div>
  );
}
