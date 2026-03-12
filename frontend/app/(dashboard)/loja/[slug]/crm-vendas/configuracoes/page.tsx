'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { Settings, Plus, Trash2, Edit2, Save, X } from 'lucide-react';

interface Origem {
  key: string;
  label: string;
  ativo: boolean;
}

interface CRMConfig {
  id: number;
  origens_leads: Origem[];
  etapas_pipeline: any[];
  colunas_leads: string[];
  modulos_ativos: Record<string, boolean>;
}

export default function ConfiguracoesPage() {
  const params = useParams();
  const slug = params?.slug as string;
  
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Estado para edição de origens
  const [editandoOrigem, setEditandoOrigem] = useState<string | null>(null);
  const [novaOrigem, setNovaOrigem] = useState({ key: '', label: '' });
  const [mostrarNovaOrigem, setMostrarNovaOrigem] = useState(false);

  useEffect(() => {
    carregarConfig();
  }, []);

  const carregarConfig = async () => {
    try {
      const res = await apiClient.get<CRMConfig>('/crm-vendas/config/');
      setConfig(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao carregar configurações.');
    } finally {
      setLoading(false);
    }
  };

  const salvarConfig = async (novaConfig: Partial<CRMConfig>) => {
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiClient.patch<CRMConfig>('/crm-vendas/config/', novaConfig);
      setConfig(res.data);
      setSuccess('Configurações salvas com sucesso!');
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Erro ao salvar configurações.');
    } finally {
      setSaving(false);
    }
  };

  const adicionarOrigem = () => {
    if (!novaOrigem.key || !novaOrigem.label) {
      setError('Preencha todos os campos da origem.');
      return;
    }
    
    const key = novaOrigem.key.toLowerCase().replace(/\s+/g, '_');
    const origens = config?.origens_leads || [];
    
    if (origens.some(o => o.key === key)) {
      setError('Já existe uma origem com essa chave.');
      return;
    }
    
    const novasOrigens = [...origens, { key, label: novaOrigem.label, ativo: true }];
    salvarConfig({ origens_leads: novasOrigens });
    setNovaOrigem({ key: '', label: '' });
    setMostrarNovaOrigem(false);
  };

  const removerOrigem = (key: string) => {
    if (!confirm('Tem certeza que deseja remover esta origem?')) return;
    
    const origens = config?.origens_leads || [];
    const novasOrigens = origens.filter(o => o.key !== key);
    salvarConfig({ origens_leads: novasOrigens });
  };

  const toggleOrigemAtiva = (key: string) => {
    const origens = config?.origens_leads || [];
    const novasOrigens = origens.map(o => 
      o.key === key ? { ...o, ativo: !o.ativo } : o
    );
    salvarConfig({ origens_leads: novasOrigens });
  };

  const editarOrigem = (key: string, novoLabel: string) => {
    const origens = config?.origens_leads || [];
    const novasOrigens = origens.map(o => 
      o.key === key ? { ...o, label: novoLabel } : o
    );
    salvarConfig({ origens_leads: novasOrigens });
    setEditandoOrigem(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500">Carregando configurações...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <Settings size={28} className="text-[#0176d3]" />
          Configurações do CRM
        </h1>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Personalize o sistema de acordo com suas necessidades
        </p>
      </div>

      {/* Mensagens */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}
      
      {success && (
        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
        </div>
      )}

      {/* Seção: Origens de Leads */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Origens de Leads
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Gerencie as origens disponíveis ao cadastrar novos leads
            </p>
          </div>
          <button
            onClick={() => setMostrarNovaOrigem(true)}
            className="px-4 py-2 bg-[#0176d3] hover:bg-[#0159a8] text-white rounded-lg text-sm font-medium flex items-center gap-2"
          >
            <Plus size={16} />
            Nova Origem
          </button>
        </div>

        {/* Formulário Nova Origem */}
        {mostrarNovaOrigem && (
          <div className="mb-4 p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Chave (identificador)
                </label>
                <input
                  type="text"
                  value={novaOrigem.key}
                  onChange={(e) => setNovaOrigem({ ...novaOrigem, key: e.target.value })}
                  placeholder="ex: linkedin"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Nome (exibição)
                </label>
                <input
                  type="text"
                  value={novaOrigem.label}
                  onChange={(e) => setNovaOrigem({ ...novaOrigem, label: e.target.value })}
                  placeholder="ex: LinkedIn"
                  className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button
                onClick={adicionarOrigem}
                disabled={saving}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium flex items-center gap-2 disabled:opacity-50"
              >
                <Save size={16} />
                Salvar
              </button>
              <button
                onClick={() => {
                  setMostrarNovaOrigem(false);
                  setNovaOrigem({ key: '', label: '' });
                }}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium flex items-center gap-2"
              >
                <X size={16} />
                Cancelar
              </button>
            </div>
          </div>
        )}

        {/* Lista de Origens */}
        <div className="space-y-2">
          {config?.origens_leads.map((origem) => (
            <div
              key={origem.key}
              className="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-3 flex-1">
                <input
                  type="checkbox"
                  checked={origem.ativo}
                  onChange={() => toggleOrigemAtiva(origem.key)}
                  className="w-4 h-4 text-[#0176d3] rounded"
                />
                {editandoOrigem === origem.key ? (
                  <input
                    type="text"
                    defaultValue={origem.label}
                    onBlur={(e) => editarOrigem(origem.key, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        editarOrigem(origem.key, e.currentTarget.value);
                      }
                    }}
                    autoFocus
                    className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                ) : (
                  <span className={`text-sm font-medium ${origem.ativo ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500 line-through'}`}>
                    {origem.label}
                  </span>
                )}
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  ({origem.key})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setEditandoOrigem(origem.key)}
                  className="p-2 text-gray-600 hover:text-[#0176d3] dark:text-gray-400 dark:hover:text-[#0176d3]"
                  title="Editar"
                >
                  <Edit2 size={16} />
                </button>
                <button
                  onClick={() => removerOrigem(origem.key)}
                  className="p-2 text-gray-600 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                  title="Remover"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Seção: Módulos Ativos (em breve) */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Módulos Ativos
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Em breve: Habilite ou desabilite módulos como Contas, Contatos, etc.
        </p>
      </div>

      {/* Seção: Etapas do Pipeline (em breve) */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Etapas do Pipeline
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Em breve: Personalize as etapas do seu pipeline de vendas
        </p>
      </div>
    </div>
  );
}
