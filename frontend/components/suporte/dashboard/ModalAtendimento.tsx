'use client';

import { useState, useEffect } from 'react';
import apiClient from '@/lib/api-client';
import { formatDateTime } from '@/lib/financeiro-helpers';

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

// ---- Logs de diagnóstico (navegador / frontend / backend) ----
type Severidade = 'erro' | 'falha' | 'timeout';

interface LogCliente {
  created_at: string | null;
  mensagem: string;
  stack: string;
  url: string;
  user_agent: string;
  severidade: Severidade;
}

interface LogBackend {
  created_at: string | null;
  url: string;
  metodo_http: string;
  erro: string;
  usuario_email: string;
  severidade: Severidade;
}

type LogItem = LogCliente | LogBackend;

const SEVERIDADES: { chave: Severidade; titulo: string; cor: string; borda: string; badge: string }[] = [
  { chave: 'erro', titulo: '🔴 Erros', cor: 'bg-red-50', borda: 'border-red-200', badge: 'bg-red-100 text-red-800' },
  { chave: 'falha', titulo: '🟠 Falhas', cor: 'bg-amber-50', borda: 'border-amber-200', badge: 'bg-amber-100 text-amber-800' },
  { chave: 'timeout', titulo: '⏱️ Tempo esgotado', cor: 'bg-sky-50', borda: 'border-sky-200', badge: 'bg-sky-100 text-sky-800' },
];

function textoDoLog(item: LogItem): string {
  return 'erro' in item ? item.erro : item.mensagem;
}

// Remove o bloco de logs automáticos concatenado na descrição — esses logs já aparecem
// estruturados nas abas de diagnóstico, então na descrição fica só o texto do cliente.
function descricaoLimpa(descricao: string): string {
  if (!descricao) return '';
  const marcadores = [
    'LOGS DE DIAGNÓSTICO AUTOMÁTICO',
    '📋 LOGS DE DIAGNÓSTICO',
    'ERROS NAVEGADOR:',
    'ERROS FRONTEND',
    'ERROS API/BACKEND',
    'INFORMAÇÕES DO SISTEMA',
  ];
  let corte = descricao.length;
  for (const m of marcadores) {
    const idx = descricao.indexOf(m);
    if (idx !== -1 && idx < corte) corte = idx;
  }
  // Remove também a linha de "===" que costuma preceder o bloco de logs.
  let texto = descricao.slice(0, corte);
  texto = texto.replace(/\n*=+\s*$/,'').trimEnd();
  return texto || descricao.trim();
}

function ColunaSeveridade({ sev, itens }: { sev: typeof SEVERIDADES[number]; itens: LogItem[] }) {
  return (
    <div className={`flex flex-col rounded-lg border ${sev.borda} ${sev.cor} overflow-hidden min-h-0`}>
      <div className={`flex items-center justify-between px-3 py-2 text-xs font-semibold uppercase ${sev.badge} border-b ${sev.borda}`}>
        <span>{sev.titulo}</span>
        <span className="tabular-nums">{itens.length}</span>
      </div>
      <div className="p-2 space-y-2 overflow-y-auto max-h-[46vh]">
        {itens.map((item, i) => {
            const isBackend = 'erro' in item;
            return (
              <div key={i} className="bg-white rounded border border-gray-200 p-2 text-xs">
                <div className="text-gray-500 mb-1">
                  {item.created_at ? formatDateTime(item.created_at) : ''}
                  {isBackend && (item as LogBackend).metodo_http ? ` · ${(item as LogBackend).metodo_http}` : ''}
                </div>
                <p className="font-mono text-gray-900 break-all whitespace-pre-wrap">{textoDoLog(item)}</p>
                {item.url && <p className="text-gray-400 break-all mt-1">URL: {item.url}</p>}
                {isBackend && (item as LogBackend).usuario_email && (
                  <p className="text-gray-400 mt-0.5">Usuário: {(item as LogBackend).usuario_email}</p>
                )}
                {!isBackend && (item as LogCliente).stack && (
                  <pre className="mt-1 text-gray-500 whitespace-pre-wrap break-all max-h-24 overflow-y-auto bg-gray-50 p-1 rounded">
                    {(item as LogCliente).stack}
                  </pre>
                )}
              </div>
            );
          })}
      </div>
    </div>
  );
}

function PainelLogs({ itens }: { itens: LogItem[] }) {
  // Só mostra as colunas de severidade que têm registros; as visíveis dividem a largura.
  const colunas = SEVERIDADES
    .map((sev) => ({ sev, itens: itens.filter((it) => it.severidade === sev.chave) }))
    .filter((c) => c.itens.length > 0);

  if (colunas.length === 0) {
    return <p className="text-gray-400 text-sm py-4 text-center">Nenhum registro nesta origem.</p>;
  }

  const gridCols = colunas.length === 1
    ? 'lg:grid-cols-1'
    : colunas.length === 2
      ? 'lg:grid-cols-2'
      : 'lg:grid-cols-3';

  return (
    <div className={`grid grid-cols-1 ${gridCols} gap-4`}>
      {colunas.map(({ sev, itens: itensCol }) => (
        <ColunaSeveridade key={sev.chave} sev={sev} itens={itensCol} />
      ))}
    </div>
  );
}

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
  const [abaLog, setAbaLog] = useState<'navegador' | 'frontend' | 'backend'>('navegador');
  const [detalhes, setDetalhes] = useState<{
    erros_navegador: LogCliente[];
    erros_frontend: LogCliente[];
    erros_backend: LogBackend[];
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
          erros_navegador: [],
          erros_frontend: [],
          erros_backend: [],
          periodo_exibido: 'Não foi possível carregar.',
          limite_por_tipo: 50,
        });
      })
      .finally(() => {
        if (!cancelled) setDetalhesLoading(false);
      });
    return () => { cancelled = true; };
    // chamado omitido: usar chamado?.id evita reexecução quando o objeto muda sem mudar id
  // eslint-disable-next-line react-hooks/exhaustive-deps
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-3 sm:p-5">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-[96vw] h-[94vh] flex flex-col">
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
          {/* Informações do Chamado — ocultadas quando os logs de diagnóstico estão expandidos (mais espaço) */}
          {!detalhesAberto && (
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
                {formatDateTime(chamado.created_at)}
              </p>
            </div>
          </div>
          )}

          {/* Descrição — também oculta quando os logs estão expandidos */}
          {!detalhesAberto && (
          <div className="mb-6">
            <label className="text-sm font-medium text-gray-500 block mb-2">Descrição</label>
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <p className="text-gray-900 whitespace-pre-wrap">{descricaoLimpa(chamado.descricao)}</p>
            </div>
          </div>
          )}

          {/* Logs de diagnóstico — 3 abas (navegador/frontend/backend), 3 colunas por severidade */}
          <div className="mb-6">
            <button
              type="button"
              onClick={() => setDetalhesAberto(!detalhesAberto)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600"
            >
              {detalhesAberto ? '▼' : '▶'} Logs de diagnóstico da loja (navegador · frontend · backend)
            </button>
            {detalhesAberto && (
              <div className="mt-3">
                {detalhesLoading ? (
                  <p className="text-gray-500 text-sm">Carregando...</p>
                ) : detalhes ? (
                  <div className="rounded-lg border border-gray-200 overflow-hidden">
                    {/* Abas */}
                    <div className="flex border-b border-gray-200 bg-gray-50">
                      {([
                        { chave: 'navegador', rotulo: '🌐 Navegador do cliente', itens: detalhes.erros_navegador },
                        { chave: 'frontend', rotulo: '⚛️ Frontend', itens: detalhes.erros_frontend },
                        { chave: 'backend', rotulo: '🖥️ Backend (API)', itens: detalhes.erros_backend },
                      ] as const).map((aba) => (
                        <button
                          key={aba.chave}
                          type="button"
                          onClick={() => setAbaLog(aba.chave)}
                          className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
                            abaLog === aba.chave
                              ? 'border-blue-600 text-blue-700 bg-white'
                              : 'border-transparent text-gray-500 hover:text-gray-700'
                          }`}
                        >
                          {aba.rotulo}
                          <span className="ml-1.5 text-xs text-gray-400">({aba.itens.length})</span>
                        </button>
                      ))}
                    </div>
                    {/* Conteúdo da aba: 3 colunas por severidade */}
                    <div className="p-4 bg-white">
                      {detalhes.periodo_exibido && (
                        <p className="text-xs text-gray-400 mb-3">{detalhes.periodo_exibido}</p>
                      )}
                      {abaLog === 'navegador' && <PainelLogs itens={detalhes.erros_navegador} />}
                      {abaLog === 'frontend' && <PainelLogs itens={detalhes.erros_frontend} />}
                      {abaLog === 'backend' && <PainelLogs itens={detalhes.erros_backend} />}
                    </div>
                  </div>
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
                        {formatDateTime(resp.created_at)}
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
