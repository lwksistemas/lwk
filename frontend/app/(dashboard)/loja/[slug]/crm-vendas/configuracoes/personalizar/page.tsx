'use client';

import { useEffect, useState } from 'react';
import { Settings } from 'lucide-react';
import apiClient from '@/lib/api-client';
import { useCRMConfig } from '@/contexts/CRMConfigContext';
import { OrigensSection } from './components/OrigensSection';
import { ModulosSection } from './components/ModulosSection';
import { EtapasSection } from './components/EtapasSection';
import { ColunasSection } from './components/ColunasSection';

interface CRMConfig {
  id: number;
  origens_leads: Array<{ key: string; label: string; ativo: boolean }>;
  etapas_pipeline: Array<{ key: string; label: string; ativo: boolean; ordem: number }>;
  colunas_leads: string[];
  modulos_ativos: Record<string, boolean>;
}

export default function ConfiguracoesPage() {
  const { recarregar } = useCRMConfig();
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get<CRMConfig>('/crm-vendas/config/')
      .then((res) => setConfig(res.data))
      .catch((e: any) => setError(e.response?.data?.detail || 'Erro ao carregar configurações.'))
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
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao salvar configurações.');
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

      <OrigensSection origens={config?.origens_leads || []} saving={saving} onSave={(o) => salvarConfig({ origens_leads: o })} onError={handleError} />
      <ModulosSection modulos={config?.modulos_ativos || {}} onSave={(m) => salvarConfig({ modulos_ativos: m })} />
      <EtapasSection etapas={config?.etapas_pipeline || []} onSave={(e) => salvarConfig({ etapas_pipeline: e })} onError={handleError} />
      <ColunasSection colunas={config?.colunas_leads || []} onSave={(c) => salvarConfig({ colunas_leads: c })} onError={handleError} />
    </div>
  );
}
