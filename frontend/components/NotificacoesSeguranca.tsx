'use client';

import { useEffect, useRef, useState } from 'react';
import apiClient from '@/lib/api-client';
import { formatDateTime } from '@/lib/financeiro-helpers';

interface Violacao {
  id: number;
  tipo: string;
  tipo_display: string;
  criticidade: string;
  criticidade_display: string;
  usuario_nome: string;
  descricao: string;
  created_at: string;
}

interface NotificacoesSegurancaProps {
  onNovaViolacao?: (violacao: Violacao) => void;
}

/** Visível: poll a cada 45s. Com aba em background o intervalo pausa. */
const INTERVALO_POLLING_MS = 45000;

export default function NotificacoesSeguranca({ onNovaViolacao }: NotificacoesSegurancaProps) {
  const [violacoesNaoLidas, setViolacoesNaoLidas] = useState<Violacao[]>([]);
  const [mostrarDropdown, setMostrarDropdown] = useState(false);
  const desdeRef = useRef<Date>(new Date());

  const verificarNovasViolacoes = async () => {
    try {
      const desde = desdeRef.current.toISOString();
      const response = await apiClient.get('/superadmin/violacoes-seguranca/', {
        params: {
          status: 'nova',
          criticidade__in: 'alta,critica',
          created_at__gte: desde,
          ordering: '-created_at',
          page_size: 10,
        }
      });

      const novasViolacoes = response.data.results || [];
      
      if (novasViolacoes.length > 0) {
        // Não chamar onNovaViolacao / setState do pai dentro do updater deste setState
        // (React: "Cannot update a component while rendering a different component").
        let novasParaToast: Violacao[] = [];
        setViolacoesNaoLidas((prev) => {
          const ids = new Set(prev.map((v) => v.id));
          novasParaToast = novasViolacoes.filter((v: Violacao) => !ids.has(v.id));
          if (novasParaToast.length === 0) {
            return prev;
          }
          return [...novasParaToast, ...prev].slice(0, 10);
        });
        if (novasParaToast.length > 0) {
          queueMicrotask(() => {
            novasParaToast.forEach((v: Violacao) => {
              try {
                mostrarNotificacaoNativa(v);
                onNovaViolacao?.(v);
              } catch {
                // Silenciosamente ignorar erros de notificação
              }
            });
          });
        }
      }
      
      desdeRef.current = new Date();
    } catch {
      // Silenciosamente ignorar erros de rede
    }
  };

  const verificarRef = useRef(verificarNovasViolacoes);
  verificarRef.current = verificarNovasViolacoes;

  useEffect(() => {
    const run = () => void verificarRef.current();
    let intervalId: ReturnType<typeof setInterval> | null = null;
    const clear = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
    const schedule = () => {
      clear();
      intervalId = setInterval(run, INTERVALO_POLLING_MS);
    };
    const onVisibility = () => {
      if (document.hidden) {
        clear();
      } else {
        run();
        schedule();
      }
    };

    document.addEventListener('visibilitychange', onVisibility);
    if (!document.hidden) {
      run();
      schedule();
    }

    return () => {
      document.removeEventListener('visibilitychange', onVisibility);
      clear();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- montagem única; ref sempre aponta para a última verificação
  }, []);

  const mostrarNotificacaoNativa = (violacao: Violacao) => {
    // Desabilitar notificações nativas no mobile para evitar erros
    if (typeof window === 'undefined') return;
    
    // Detectar se é mobile
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) return; // Não mostrar notificações nativas no mobile
    
    // Verificar permissão para notificações (apenas desktop)
    try {
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('🚨 Alerta de Segurança', {
          body: `${violacao.tipo_display}: ${violacao.usuario_nome}`,
          icon: '/favicon.ico',
          tag: `violacao-${violacao.id}`,
        });
      }
    } catch (error) {
      // Silenciosamente ignorar erros de notificação
    }
  };

  const solicitarPermissaoNotificacoes = async () => {
    // Desabilitar no mobile
    if (typeof window === 'undefined') return;
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    if (isMobile) return;
    
    try {
      if ('Notification' in window && Notification.permission === 'default') {
        await Notification.requestPermission();
      }
    } catch (error) {
      // Silenciosamente ignorar erros
    }
  };

  const marcarComoLida = (id: number) => {
    setViolacoesNaoLidas(prev => prev.filter(v => v.id !== id));
  };

  const marcarTodasComoLidas = () => {
    setViolacoesNaoLidas([]);
    setMostrarDropdown(false);
  };

  const getCriticidadeColor = (criticidade: string) => {
    const colors: Record<string, string> = {
      'critica': 'bg-red-600',
      'alta': 'bg-orange-500',
      'media': 'bg-yellow-500',
      'baixa': 'bg-green-500',
    };
    return colors[criticidade] || 'bg-gray-500';
  };

  const getCriticidadeBadgeColor = (criticidade: string) => {
    const colors: Record<string, string> = {
      'critica': 'bg-red-100 text-red-800',
      'alta': 'bg-orange-100 text-orange-800',
      'media': 'bg-yellow-100 text-yellow-800',
      'baixa': 'bg-green-100 text-green-800',
    };
    return colors[criticidade] || 'bg-gray-100 text-gray-800';
  };

  useEffect(() => {
    solicitarPermissaoNotificacoes();
  }, []);

  return (
    <div className="relative">
      {/* Botão de Notificações */}
      <button
        onClick={() => setMostrarDropdown(!mostrarDropdown)}
        className="relative p-2 text-white hover:bg-purple-800 rounded-md transition-colors"
        title="Alertas de Segurança"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        
        {/* Badge de contador */}
        {violacoesNaoLidas.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
            {violacoesNaoLidas.length > 9 ? '9+' : violacoesNaoLidas.length}
          </span>
        )}
      </button>

      {/* Dropdown de Notificações */}
      {mostrarDropdown && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setMostrarDropdown(false)}
          />
          
          <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl z-20 max-h-[600px] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">
                Alertas de Segurança
              </h3>
              {violacoesNaoLidas.length > 0 && (
                <button
                  onClick={marcarTodasComoLidas}
                  className="text-sm text-purple-600 hover:text-purple-800"
                >
                  Limpar tudo
                </button>
              )}
            </div>

            {/* Lista de Notificações */}
            <div className="overflow-y-auto flex-1">
              {violacoesNaoLidas.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="text-sm">Nenhum alerta novo</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {violacoesNaoLidas.map((violacao) => (
                    <div
                      key={violacao.id}
                      className="p-4 hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2 h-2 rounded-full ${getCriticidadeColor(violacao.criticidade)}`} />
                          <span className={`text-xs font-medium px-2 py-1 rounded ${getCriticidadeBadgeColor(violacao.criticidade)}`}>
                            {violacao.criticidade_display}
                          </span>
                        </div>
                        <button
                          onClick={() => marcarComoLida(violacao.id)}
                          className="text-gray-400 hover:text-gray-600"
                          title="Marcar como lida"
                        >
                          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </button>
                      </div>
                      
                      <h4 className="text-sm font-semibold text-gray-900 mb-1">
                        {violacao.tipo_display}
                      </h4>
                      
                      <p className="text-sm text-gray-600 mb-2">
                        {violacao.descricao}
                      </p>
                      
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{violacao.usuario_nome}</span>
                        <span>{formatDateTime(violacao.created_at)}</span>
                      </div>
                      
                      <a
                        href={`/superadmin/dashboard/alertas?violacao_id=${violacao.id}`}
                        className="mt-2 inline-block text-xs text-purple-600 hover:text-purple-800 font-medium"
                        onClick={() => setMostrarDropdown(false)}
                      >
                        Ver detalhes →
                      </a>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-gray-200 bg-gray-50">
              <a
                href="/superadmin/dashboard/alertas"
                className="block text-center text-sm text-purple-600 hover:text-purple-800 font-medium"
                onClick={() => setMostrarDropdown(false)}
              >
                Ver todos os alertas
              </a>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
