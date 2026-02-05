'use client';

import { useState } from 'react';

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
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
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

        {/* Conteúdo */}
        <div className="p-6">
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
