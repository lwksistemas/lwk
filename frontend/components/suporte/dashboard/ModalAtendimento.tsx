'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';

interface Resposta {
  id: number;
  usuario_nome: string;
  mensagem: string;
  is_suporte: boolean;
  created_at: string;
}

interface Chamado {
  id: number;
  titulo: string;
  descricao: string;
  tipo: string;
  loja_nome: string;
  loja_slug: string;
  usuario_nome: string;
  usuario_email: string;
  status: string;
  prioridade: string;
  respostas?: Resposta[];
  created_at: string;
  updated_at: string;
}

interface ModalAtendimentoProps {
  chamado: Chamado | null;
  isOpen: boolean;
  onClose: () => void;
  onIniciarAtendimento: (id: number) => Promise<void>;
  onResolver: (id: number) => Promise<void>;
  onEnviarResposta: (id: number, mensagem: string) => Promise<void>;
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    'aberto': 'bg-yellow-100 text-yellow-800',
    'em_andamento': 'bg-blue-100 text-blue-800',
    'resolvido': 'bg-green-100 text-green-800',
    'fechado': 'bg-gray-100 text-gray-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
};

const getPrioridadeColor = (prioridade: string) => {
  const colors: Record<string, string> = {
    'baixa': 'text-gray-600',
    'media': 'text-yellow-600',
    'alta': 'text-orange-600',
    'urgente': 'text-red-600',
  };
  return colors[prioridade] || 'text-gray-600';
};

const getTipoDisplay = (tipo: string) => {
  const tipos: Record<string, string> = {
    'duvida': 'Dúvida',
    'treinamento': 'Treinamento',
    'problema': 'Problema Técnico',
    'sugestao': 'Sugestão',
    'outro': 'Outro'
  };
  return tipos[tipo] || tipo;
};

export function ModalAtendimento({
  chamado,
  isOpen,
  onClose,
  onIniciarAtendimento,
  onResolver,
  onEnviarResposta,
}: ModalAtendimentoProps) {
  const [resposta, setResposta] = useState('');
  const [enviandoResposta, setEnviandoResposta] = useState(false);
  const [detalhesAberto, setDetalhesAberto] = useState(false);
  const [detalhes, setDetalhes] = useState<{
    erros_backend: Array<{ created_at: string | null; url: string; metodo_http: string; erro: string; usuario_email: string }>;
    erros_frontend: Array<{ created_at: string | null; mensagem: string; stack: string; url: string; user_agent: string }>;
    periodo_exibido?: string;
    limite_por_tipo?: number;
  } | null>(null);
  const [detalhesLoading, setDetalhesLoading] = useState(false);

  useEffect(() => {
    if (!isOpen || !chamado || !detalhesAberto) return;
    let cancelled = false;
    setDetalhesLoading(true);
    apiClient
      .get(`/suporte/chamados/${chamado.id}/detalhes-contexto/`)
      .then((res) => {
        if (!cancelled) setDetalhes(res.data);
      })
      .catch(() => {
        if (!cancelled) setDetalhes({
          erros_backend: [],
          erros_frontend: [],
          periodo_exibido: 'Não foi possível carregar.',
          limite_por_tipo: 50,
        });
      })
      .finally(() => {
        if (!cancelled) setDetalhesLoading(false);
      });
    return () => { cancelled = true; };
  }, [isOpen, chamado?.id, detalhesAberto]);

  if (!isOpen || !chamado) return null;

  const handleEnviarResposta = async () => {
    if (!resposta.trim()) return;
    
    try {
      setEnviandoResposta(true);
      await onEnviarResposta(chamado.id, resposta);
      setResposta('');
    } finally {
      setEnviandoResposta(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl min-h-[85vh] max-h-[95vh] flex flex-col">
        {/* Header */}
        <div className="bg-blue-900 text-white px-6 py-4 rounded-t-lg">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-xl font-bold">Chamado #{chamado.id}</h3>
              <p className="text-blue-200 text-sm mt-1">{chamado.titulo}</p>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Conteúdo - área rolável em tela grande */}
        <div className="p-6 overflow-y-auto flex-1">
          {/* Informações do Chamado */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="text-sm font-medium text-gray-500">Loja</label>
              <p className="text-gray-900">{chamado.loja_nome}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Tipo</label>
              <p className="text-gray-900">{getTipoDisplay(chamado.tipo)}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Usuário</label>
              <p className="text-gray-900">{chamado.usuario_nome}</p>
              <p className="text-sm text-gray-500">{chamado.usuario_email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Status</label>
              <p>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(chamado.status)}`}>
                  {chamado.status.replace('_', ' ')}
                </span>
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Prioridade</label>
              <p className={`font-semibold ${getPrioridadeColor(chamado.prioridade)}`}>
                {chamado.prioridade.toUpperCase()}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-500">Criado em</label>
              <p className="text-gray-900">
                {new Date(chamado.created_at).toLocaleString('pt-BR')}
              </p>
            </div>
          </div>

          {/* Descrição */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-500 block mb-2">Descrição</label>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <p className="text-gray-900 whitespace-pre-wrap">{chamado.descricao}</p>
            </div>
          </div>

          {/* Detalhes técnicos (erros backend + frontend da loja) */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setDetalhesAberto(!detalhesAberto)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
            >
              {detalhesAberto ? '▼' : '▶'} Detalhes técnicos (erros da loja)
            </button>
            {detalhesAberto && (
              <div className="mt-2 p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
                {detalhesLoading ? (
                  <p className="text-gray-500 text-sm">Carregando...</p>
                ) : detalhes ? (
                  <>
                    {/* Quando é exibido: período/limite */}
                    {detalhes.periodo_exibido && (
                      <div className="text-xs text-gray-500 bg-white/80 rounded px-3 py-2 border border-gray-200">
                        <span className="font-medium text-gray-600">Quando é exibido:</span>{' '}
                        {detalhes.periodo_exibido}
                        {detalhes.limite_por_tipo != null && (
                          <span> (máx. {detalhes.limite_por_tipo} por tipo)</span>
                        )}
                      </div>
                    )}

                    {/* Backend: cor vermelha */}
                    <div className="rounded-lg border-2 border-red-200 bg-red-50/70 overflow-hidden">
                      <h4 className="text-xs font-semibold uppercase px-3 py-2 bg-red-100 text-red-800 border-b border-red-200">
                        🔴 Erros no backend (Heroku / API)
                      </h4>
                      <div className="p-3">
                        {detalhes.erros_backend.length === 0 ? (
                          <p className="text-gray-500 text-sm">Nenhum erro recente.</p>
                        ) : (
                          <ul className="space-y-2 max-h-48 overflow-y-auto">
                            {detalhes.erros_backend.map((e, i) => (
                              <li key={i} className="text-sm border-l-4 border-red-500 pl-2 py-1.5 bg-white rounded pr-2">
                                <span className="text-gray-500 text-xs block">
                                  {e.created_at ? new Date(e.created_at).toLocaleString('pt-BR') : ''} — {e.metodo_http} {e.url}
                                </span>
                                <p className="text-red-900 font-mono text-xs break-all mt-0.5">{e.erro}</p>
                                {e.usuario_email && (
                                  <p className="text-gray-500 text-xs">Usuário: {e.usuario_email}</p>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>

                    {/* Frontend: cor azul/laranja para diferenciar */}
                    <div className="rounded-lg border-2 border-amber-300 bg-amber-50/70 overflow-hidden">
                      <h4 className="text-xs font-semibold uppercase px-3 py-2 bg-amber-100 text-amber-900 border-b border-amber-200">
                        🟠 Erros no navegador / frontend (Vercel)
                      </h4>
                      <div className="p-3">
                        {detalhes.erros_frontend.length === 0 ? (
                          <p className="text-gray-500 text-sm">Nenhum erro reportado pelo navegador da loja.</p>
                        ) : (
                          <ul className="space-y-2 max-h-48 overflow-y-auto">
                            {detalhes.erros_frontend.map((e, i) => (
                              <li key={i} className="text-sm border-l-4 border-amber-500 pl-2 py-1.5 bg-white rounded pr-2">
                                <span className="text-gray-500 text-xs block">
                                  {e.created_at ? new Date(e.created_at).toLocaleString('pt-BR') : ''}
                                </span>
                                <p className="text-amber-900 font-mono text-xs mt-0.5">{e.mensagem}</p>
                                {e.url && <p className="text-gray-500 text-xs">URL: {e.url}</p>}
                                {e.stack && (
                                  <pre className="mt-1 text-xs text-gray-600 whitespace-pre-wrap break-all max-h-24 overflow-y-auto bg-gray-50 p-1 rounded">
                                    {e.stack}
                                  </pre>
                                )}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
            )}
          </div>

          {/* Ações Rápidas */}
          <div className="flex gap-3 mb-6">
            {chamado.status === 'aberto' && (
              <button
                onClick={() => onIniciarAtendimento(chamado.id)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Iniciar Atendimento
              </button>
            )}
            {chamado.status !== 'resolvido' && chamado.status !== 'fechado' && (
              <button
                onClick={() => onResolver(chamado.id)}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Marcar como Resolvido
              </button>
            )}
          </div>

          {/* Histórico de Respostas */}
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-700 block mb-3">
              Histórico de Respostas ({chamado.respostas?.length || 0})
            </label>
            {chamado.respostas && chamado.respostas.length > 0 ? (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {chamado.respostas.map((resp) => (
                  <div
                    key={resp.id}
                    className={`p-4 rounded-lg ${
                      resp.is_suporte
                        ? 'bg-blue-50 border-l-4 border-blue-500'
                        : 'bg-gray-50 border-l-4 border-gray-300'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        {resp.is_suporte ? (
                          <span className="text-blue-600 font-semibold">🎧 Suporte - {resp.usuario_nome}</span>
                        ) : (
                          <span className="text-gray-700 font-semibold">👤 Cliente - {resp.usuario_nome}</span>
                        )}
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(resp.created_at).toLocaleString('pt-BR')}
                      </span>
                    </div>
                    <p className="text-gray-900 whitespace-pre-wrap">{resp.mensagem}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-500">Nenhuma resposta ainda</p>
                <p className="text-sm text-gray-400 mt-1">
                  Seja o primeiro a responder este chamado
                </p>
              </div>
            )}
          </div>

          {/* Área de Resposta */}
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">
              Adicionar Resposta
            </label>
            <textarea
              value={resposta}
              onChange={(e) => setResposta(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              placeholder="Digite sua resposta ao cliente..."
            />
            <div className="mt-3 flex justify-end">
              <button
                onClick={handleEnviarResposta}
                disabled={!resposta.trim() || enviandoResposta}
                className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {enviandoResposta ? 'Enviando...' : 'Enviar Resposta'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
