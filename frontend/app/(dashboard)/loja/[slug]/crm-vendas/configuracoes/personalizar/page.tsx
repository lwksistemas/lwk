'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import apiClient from '@/lib/api-client';
import { Settings, Plus, Trash2, Edit2, Save, X, ChevronUp, ChevronDown } from 'lucide-react';
import { useCRMConfig } from '@/contexts/CRMConfigContext';

interface Origem {
  key: string;
  label: string;
  ativo: boolean;
}

interface Etapa {
  key: string;
  label: string;
  ativo: boolean;
  ordem: number;
}

interface CRMConfig {
  id: number;
  origens_leads: Origem[];
  etapas_pipeline: Etapa[];
  colunas_leads: string[];
  modulos_ativos: Record<string, boolean>;
}

export default function ConfiguracoesPage() {
  const params = useParams();
  const slug = params?.slug as string;
  const { recarregar } = useCRMConfig();
  
  const [config, setConfig] = useState<CRMConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Estado para edição de origens
  const [editandoOrigem, setEditandoOrigem] = useState<string | null>(null);
  const [novaOrigem, setNovaOrigem] = useState({ key: '', label: '' });
  const [mostrarNovaOrigem, setMostrarNovaOrigem] = useState(false);
  
  // Estado para edição de etapas
  const [editandoEtapa, setEditandoEtapa] = useState<string | null>(null);
  
  // Colunas disponíveis para leads
  const colunasDisponiveis = [
    { key: 'nome', label: 'Nome' },
    { key: 'empresa', label: 'Empresa' },
    { key: 'email', label: 'E-mail' },
    { key: 'telefone', label: 'Telefone' },
    { key: 'origem', label: 'Origem' },
    { key: 'status', label: 'Status' },
    { key: 'valor_estimado', label: 'Valor Estimado' },
    { key: 'created_at', label: 'Data de Criação' },
  ];

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
      
      // Recarregar o context global para atualizar todas as páginas
      await recarregar();
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

  // Funções para gerenciar etapas
  const toggleEtapaAtiva = (key: string) => {
    const etapas = config?.etapas_pipeline || [];
    
    // Não permitir desabilitar closed_won e closed_lost
    if (['closed_won', 'closed_lost'].includes(key)) {
      setError('As etapas de fechamento não podem ser desabilitadas.');
      setTimeout(() => setError(null), 3000);
      return;
    }
    
    const novasEtapas = etapas.map(e => 
      e.key === key ? { ...e, ativo: !e.ativo } : e
    );
    salvarConfig({ etapas_pipeline: novasEtapas });
  };

  const editarEtapa = (key: string, novoLabel: string) => {
    const etapas = config?.etapas_pipeline || [];
    const novasEtapas = etapas.map(e => 
      e.key === key ? { ...e, label: novoLabel } : e
    );
    salvarConfig({ etapas_pipeline: novasEtapas });
    setEditandoEtapa(null);
  };

  const moverEtapa = (key: string, direcao: 'up' | 'down') => {
    const etapas = [...(config?.etapas_pipeline || [])];
    const index = etapas.findIndex(e => e.key === key);
    
    if (index === -1) return;
    if (direcao === 'up' && index === 0) return;
    if (direcao === 'down' && index === etapas.length - 1) return;
    
    const newIndex = direcao === 'up' ? index - 1 : index + 1;
    [etapas[index], etapas[newIndex]] = [etapas[newIndex], etapas[index]];
    
    // Atualizar ordem
    const novasEtapas = etapas.map((e, i) => ({ ...e, ordem: i + 1 }));
    salvarConfig({ etapas_pipeline: novasEtapas });
  };

  // Funções para gerenciar colunas de leads
  const toggleColuna = (key: string) => {
    const colunas = config?.colunas_leads || [];
    
    if (colunas.includes(key)) {
      // Remover coluna (mínimo 3 colunas)
      if (colunas.length <= 3) {
        setError('Mantenha pelo menos 3 colunas visíveis.');
        setTimeout(() => setError(null), 3000);
        return;
      }
      const novasColunas = colunas.filter(c => c !== key);
      salvarConfig({ colunas_leads: novasColunas });
    } else {
      // Adicionar coluna
      const novasColunas = [...colunas, key];
      salvarConfig({ colunas_leads: novasColunas });
    }
  };

  const moverColuna = (key: string, direcao: 'up' | 'down') => {
    const colunas = [...(config?.colunas_leads || [])];
    const index = colunas.indexOf(key);
    
    if (index === -1) return;
    if (direcao === 'up' && index === 0) return;
    if (direcao === 'down' && index === colunas.length - 1) return;
    
    const newIndex = direcao === 'up' ? index - 1 : index + 1;
    [colunas[index], colunas[newIndex]] = [colunas[newIndex], colunas[index]];
    
    salvarConfig({ colunas_leads: colunas });
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

      {/* Seção: Módulos Ativos */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Módulos Ativos
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Habilite ou desabilite módulos do CRM. Módulos desabilitados não aparecerão no menu.
          </p>
        </div>

        <div className="space-y-3">
          {/* Leads - sempre ativo */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={true}
                disabled
                className="w-4 h-4 text-[#0176d3] rounded opacity-50 cursor-not-allowed"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Leads
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Módulo principal (sempre ativo)
                </p>
              </div>
            </div>
          </div>

          {/* Contas */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config?.modulos_ativos?.contas !== false}
                onChange={() => {
                  const novosModulos = { ...config?.modulos_ativos, contas: !config?.modulos_ativos?.contas };
                  salvarConfig({ modulos_ativos: novosModulos });
                }}
                className="w-4 h-4 text-[#0176d3] rounded"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Contas (Empresas)
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Gerenciar empresas/organizações clientes
                </p>
              </div>
            </div>
          </div>

          {/* Contatos */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={config?.modulos_ativos?.contatos !== false}
                onChange={() => {
                  const novosModulos = { ...config?.modulos_ativos, contatos: !config?.modulos_ativos?.contatos };
                  salvarConfig({ modulos_ativos: novosModulos });
                }}
                className="w-4 h-4 text-[#0176d3] rounded"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Contatos
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Gerenciar pessoas de contato das empresas
                </p>
              </div>
            </div>
          </div>

          {/* Pipeline - sempre ativo */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={true}
                disabled
                className="w-4 h-4 text-[#0176d3] rounded opacity-50 cursor-not-allowed"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Pipeline de Vendas
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Módulo principal (sempre ativo)
                </p>
              </div>
            </div>
          </div>

          {/* Atividades - sempre ativo */}
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={true}
                disabled
                className="w-4 h-4 text-[#0176d3] rounded opacity-50 cursor-not-allowed"
              />
              <div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  Calendário / Atividades
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Módulo principal (sempre ativo)
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Seção: Etapas do Pipeline */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Etapas do Pipeline
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Personalize as etapas do seu pipeline de vendas. Arraste para reordenar.
          </p>
        </div>

        <div className="space-y-2">
          {config?.etapas_pipeline
            .sort((a, b) => a.ordem - b.ordem)
            .map((etapa, index) => {
              const isFirst = index === 0;
              const isLast = index === config.etapas_pipeline.length - 1;
              const isFechamento = ['closed_won', 'closed_lost'].includes(etapa.key);
              
              return (
                <div
                  key={etapa.key}
                  className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700"
                >
                  {/* Ordem */}
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => moverEtapa(etapa.key, 'up')}
                      disabled={isFirst}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Mover para cima"
                    >
                      <ChevronUp size={16} />
                    </button>
                    <button
                      onClick={() => moverEtapa(etapa.key, 'down')}
                      disabled={isLast}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Mover para baixo"
                    >
                      <ChevronDown size={16} />
                    </button>
                  </div>

                  {/* Checkbox e Nome */}
                  <div className="flex items-center gap-3 flex-1">
                    <input
                      type="checkbox"
                      checked={etapa.ativo}
                      onChange={() => toggleEtapaAtiva(etapa.key)}
                      disabled={isFechamento}
                      className="w-4 h-4 text-[#0176d3] rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      title={isFechamento ? 'Etapas de fechamento não podem ser desabilitadas' : ''}
                    />
                    {editandoEtapa === etapa.key ? (
                      <input
                        type="text"
                        defaultValue={etapa.label}
                        onBlur={(e) => editarEtapa(etapa.key, e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            editarEtapa(etapa.key, e.currentTarget.value);
                          }
                        }}
                        autoFocus
                        className="px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    ) : (
                      <span className={`text-sm font-medium ${etapa.ativo ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500 line-through'}`}>
                        {etapa.label}
                      </span>
                    )}
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      ({etapa.key})
                    </span>
                    {isFechamento && (
                      <span className="text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-1 rounded">
                        Obrigatória
                      </span>
                    )}
                  </div>

                  {/* Ações */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setEditandoEtapa(etapa.key)}
                      className="p-2 text-gray-600 hover:text-[#0176d3] dark:text-gray-400 dark:hover:text-[#0176d3]"
                      title="Editar nome"
                    >
                      <Edit2 size={16} />
                    </button>
                  </div>
                </div>
              );
            })}
        </div>

        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>💡 Dica:</strong> As etapas desabilitadas não aparecerão no pipeline, mas oportunidades existentes nessas etapas continuarão visíveis.
          </p>
        </div>
      </div>

      {/* Seção: Colunas Visíveis nos Leads */}
      <div className="bg-white dark:bg-[#16325c] rounded-lg border border-gray-200 dark:border-[#0d1f3c] shadow-sm p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Colunas Visíveis nos Leads
          </h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Escolha quais informações aparecem na listagem de leads. Mínimo de 3 colunas.
          </p>
        </div>

        <div className="space-y-2">
          {colunasDisponiveis.map((coluna, index) => {
            const isVisible = config?.colunas_leads.includes(coluna.key);
            const colunaIndex = config?.colunas_leads.indexOf(coluna.key) ?? -1;
            const isFirst = colunaIndex === 0;
            const isLast = colunaIndex === (config?.colunas_leads.length ?? 0) - 1;
            
            return (
              <div
                key={coluna.key}
                className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#0d1f3c] rounded-lg border border-gray-200 dark:border-gray-700"
              >
                {/* Ordem (só aparece se visível) */}
                {isVisible && (
                  <div className="flex flex-col gap-1">
                    <button
                      onClick={() => moverColuna(coluna.key, 'up')}
                      disabled={isFirst}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Mover para esquerda"
                    >
                      <ChevronUp size={16} />
                    </button>
                    <button
                      onClick={() => moverColuna(coluna.key, 'down')}
                      disabled={isLast}
                      className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed"
                      title="Mover para direita"
                    >
                      <ChevronDown size={16} />
                    </button>
                  </div>
                )}

                {/* Checkbox e Nome */}
                <div className="flex items-center gap-3 flex-1">
                  <input
                    type="checkbox"
                    checked={isVisible}
                    onChange={() => toggleColuna(coluna.key)}
                    className="w-4 h-4 text-[#0176d3] rounded"
                  />
                  <span className={`text-sm font-medium ${isVisible ? 'text-gray-900 dark:text-white' : 'text-gray-400 dark:text-gray-500'}`}>
                    {coluna.label}
                  </span>
                  {isVisible && (
                    <span className="text-xs bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 px-2 py-1 rounded">
                      Posição {colunaIndex + 1}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-700 dark:text-blue-300">
            <strong>💡 Dica:</strong> As colunas aparecerão na ordem definida. Use as setas para reordenar as colunas visíveis.
          </p>
        </div>
      </div>
    </div>
  );
}
