'use client';

import { useState, useEffect } from 'react';
import { setBackendServer } from '@/lib/api-client';
import { getPrimaryApiRoot, getBackupApiRoot } from '@/lib/api-base';
import { wakeUpRenderServer, type WakeUpProgress } from '@/lib/wake-up-render';

const PRIMARY_BACKEND_URL = getPrimaryApiRoot();
const BACKUP_BACKEND_URL = getBackupApiRoot();

type Servidor = 'heroku' | 'render';

interface ServidorConfig {
  nome: string;
  url: string;
  cor: string;
  icone: string;
}

const SERVIDORES: Record<Servidor, ServidorConfig> = {
  heroku: {
    nome: 'Heroku',
    url: PRIMARY_BACKEND_URL,
    cor: 'purple',
    icone: '🟣',
  },
  render: {
    nome: 'Render (Desabilitado)',
    url: '', // Desabilitado - Plano Free insuficiente. Reativar quando fizer upgrade para plano pago
    cor: 'blue',
    icone: '🔵',
  },
};

/** Timeout do health check (Render free: cold start pode passar de 15s). */
const HEALTH_TIMEOUT_MS = 45000;

/** Health via rota Next.js — evita CORS do browser ao chamar Render direto da Vercel. */
async function fetchBackendHealth(
  servidor: Servidor,
  signal: AbortSignal
): Promise<{ ok: boolean; status?: number; configured?: boolean }> {
  const res = await fetch(`/api/backend-health?server=${servidor}`, {
    method: 'GET',
    signal,
    cache: 'no-store',
  });
  const data = (await res.json()) as {
    ok?: boolean;
    status?: number;
    configured?: boolean;
    error?: string;
  };
  if (!res.ok) {
    return { ok: false };
  }
  return {
    ok: Boolean(data.ok),
    status: data.status,
    configured: data.configured !== false,
  };
}

export default function SeletorServidorBackend() {
  const [servidorAtivo, setServidorAtivo] = useState<Servidor>('heroku');
  const [mostrarMenu, setMostrarMenu] = useState(false);
  const [verificando, setVerificando] = useState(false);
  const [statusServidores, setStatusServidores] = useState<Record<Servidor, 'online' | 'offline' | 'verificando'>>({
    heroku: 'verificando',
    render: 'offline', // Render desabilitado temporariamente
  });
  
  // Estados para o modal de acordar servidor
  const [mostrarModalAcordar, setMostrarModalAcordar] = useState(false);
  const [progressoAcordar, setProgressoAcordar] = useState<WakeUpProgress>({
    status: 'checking',
    message: 'Iniciando...',
    progress: 0,
  });

  useEffect(() => {
    // Carregar servidor ativo do localStorage
    const servidorSalvo = localStorage.getItem('backend_servidor') as Servidor;
    
    // ✅ FALLBACK: Se Render estiver com problemas, forçar Heroku
    // Verificar se há parâmetro na URL para forçar servidor
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const forceServer = urlParams.get('forceServer') as Servidor;
      
      if (forceServer === 'heroku' || forceServer === 'render') {
        localStorage.setItem('backend_servidor', forceServer);
        setServidorAtivo(forceServer);
        setBackendServer(SERVIDORES[forceServer].url);
        // Remover parâmetro da URL
        window.history.replaceState({}, '', window.location.pathname);
      } else if (servidorSalvo && SERVIDORES[servidorSalvo]) {
        setServidorAtivo(servidorSalvo);
        setBackendServer(SERVIDORES[servidorSalvo].url);
      } else {
        // Padrão: Heroku
        setServidorAtivo('heroku');
        setBackendServer(SERVIDORES.heroku.url);
      }
    }
    
    // Verificar status dos servidores
    verificarStatusServidores();
  }, []);

  const verificarStatusServidores = async () => {
    const verificarServidor = async (servidor: Servidor): Promise<'online' | 'offline'> => {
      const base = SERVIDORES[servidor].url;
      if (!base) {
        return 'offline';
      }
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);

        const data = await fetchBackendHealth(servidor, controller.signal);
        clearTimeout(timeoutId);
        if (servidor === 'render' && data.configured === false) {
          return 'offline';
        }
        return data.ok ? 'online' : 'offline';
      } catch {
        return 'offline';
      }
    };

    // Verificar ambos os servidores em paralelo
    const [herokuStatus, renderStatus] = await Promise.all([
      verificarServidor('heroku'),
      verificarServidor('render'),
    ]);

    setStatusServidores({
      heroku: herokuStatus,
      render: renderStatus,
    });
  };

  const trocarServidor = async (novoServidor: Servidor) => {
    if (novoServidor === servidorAtivo) {
      setMostrarMenu(false);
      return;
    }

    if (novoServidor === 'render' && !SERVIDORES.render.url) {
      alert('Servidor de backup não configurado. Defina NEXT_PUBLIC_API_BACKUP_URL no deploy.');
      return;
    }

    setVerificando(true);
    setMostrarMenu(false);
    
    try {
      // Se for trocar para Render, acordar o servidor primeiro
      if (novoServidor === 'render') {
        setMostrarModalAcordar(true);
        
        const acordou = await wakeUpRenderServer((progress) => {
          setProgressoAcordar(progress);
        });
        
        if (!acordou) {
          setMostrarModalAcordar(false);
          alert('Não foi possível acordar o servidor Render. Tente novamente em alguns minutos.');
          setVerificando(false);
          return;
        }
        
        // Aguardar mais 2 segundos para garantir
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      // Verificar se o servidor está online
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);
      
      const targetBase = SERVIDORES[novoServidor].url;
      if (!targetBase) {
        alert('URL do servidor de backup não configurada.');
        setVerificando(false);
        setMostrarModalAcordar(false);
        return;
      }

      const data = await fetchBackendHealth(novoServidor, controller.signal);

      clearTimeout(timeoutId);

      if (novoServidor === 'render' && data.configured === false) {
        alert('Servidor de backup não configurado. Defina NEXT_PUBLIC_API_BACKUP_URL no deploy.');
        setMostrarModalAcordar(false);
        return;
      }

      if (data.ok) {
        // Salvar no localStorage
        localStorage.setItem('backend_servidor', novoServidor);
        
        // Atualizar a URL base da API usando a função do api-client
        setBackendServer(targetBase);
        
        setServidorAtivo(novoServidor);
        setMostrarModalAcordar(false);
        
        // Recarregar a página para aplicar as mudanças
        window.location.reload();
      } else {
        setMostrarModalAcordar(false);
        const status = data.status ?? '—';
        const hint =
          novoServidor === 'render' && data.status === 400
            ? ' (no Render: faça deploy com settings atual — ALLOWED_HOSTS deve incluir o hostname onrender.com.)'
            : '';
        alert(
          `Servidor ${SERVIDORES[novoServidor].nome} respondeu ${status}. Não é possível trocar.${hint}`,
        );
      }
    } catch {
      setMostrarModalAcordar(false);
      alert(
        `Erro de rede ao contactar ${SERVIDORES[novoServidor].nome} (timeout ou URL errada). Confira no Vercel: NEXT_PUBLIC_API_BACKUP_URL = URL HTTPS exata do serviço no Render (redeploy após alterar).`,
      );
    } finally {
      setVerificando(false);
    }
  };

  const config = SERVIDORES[servidorAtivo];
  const statusAtual = statusServidores[servidorAtivo];

  return (
    <div className="relative">
      {/* Botão Principal */}
      <button
        onClick={() => setMostrarMenu(!mostrarMenu)}
        className="flex items-center space-x-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        title="Trocar servidor backend"
      >
        <span className="text-lg">{config.icone}</span>
        <div className="flex flex-col items-start">
          <span className="text-xs text-gray-500 dark:text-gray-400">Backend</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100">{config.nome}</span>
        </div>
        <div className={`w-2 h-2 rounded-full ${
          statusAtual === 'online' ? 'bg-green-500' : 
          statusAtual === 'offline' ? 'bg-red-500' : 
          'bg-yellow-500 animate-pulse'
        }`} />
      </button>

      {/* Menu Dropdown */}
      {mostrarMenu && (
        <>
          {/* Overlay para fechar ao clicar fora */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setMostrarMenu(false)}
          />
          
          {/* Menu */}
          <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20">
            <div className="p-3 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                Selecionar Servidor Backend
              </h3>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Escolha qual servidor usar para as requisições
              </p>
            </div>

            <div className="p-2">
              {(Object.keys(SERVIDORES) as Servidor[]).map((servidor) => {
                const servidorConfig = SERVIDORES[servidor];
                const status = statusServidores[servidor];
                const isAtivo = servidor === servidorAtivo;

                return (
                  <button
                    key={servidor}
                    onClick={() => trocarServidor(servidor)}
                    disabled={
                      verificando ||
                      status === 'offline' ||
                      (servidor === 'render' && !servidorConfig.url)
                    }
                    className={`w-full flex items-center justify-between p-3 rounded-md mb-2 transition-colors ${
                      isAtivo
                        ? 'bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-500'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-700 border-2 border-transparent'
                    } ${
                      status === 'offline' ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{servidorConfig.icone}</span>
                      <div className="flex flex-col items-start">
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {servidorConfig.nome}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {servidorConfig.url
                            ? servidorConfig.url.replace('https://', '')
                            : '(defina NEXT_PUBLIC_API_BACKUP_URL)'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {isAtivo && (
                        <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                          Ativo
                        </span>
                      )}
                      <div className={`w-3 h-3 rounded-full ${
                        status === 'online' ? 'bg-green-500' : 
                        status === 'offline' ? 'bg-red-500' : 
                        'bg-yellow-500 animate-pulse'
                      }`} title={status === 'online' ? 'Online' : status === 'offline' ? 'Offline' : 'Verificando...'} />
                    </div>
                  </button>
                );
              })}
            </div>

            <div className="p-3 border-t border-gray-200 dark:border-gray-700">
              <button
                onClick={() => {
                  setStatusServidores({
                    heroku: 'verificando',
                    render: 'offline', // Render desabilitado temporariamente
                  });
                  verificarStatusServidores();
                }}
                className="w-full text-xs text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-medium"
              >
                🔄 Verificar Status Novamente
              </button>
            </div>
          </div>
        </>
      )}
      
      {/* Modal de Acordar Servidor */}
      {mostrarModalAcordar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="flex items-start space-x-4">
              {/* Ícone de loading */}
              <div className="flex-shrink-0">
                {progressoAcordar.status === 'error' ? (
                  <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                    <span className="text-2xl">❌</span>
                  </div>
                ) : progressoAcordar.status === 'ready' ? (
                  <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/20 flex items-center justify-center">
                    <span className="text-2xl">✅</span>
                  </div>
                ) : (
                  <div className="w-12 h-12 rounded-full bg-blue-100 dark:bg-blue-900/20 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  </div>
                )}
              </div>
              
              {/* Conteúdo */}
              <div className="flex-1">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {progressoAcordar.status === 'error' ? 'Erro' :
                   progressoAcordar.status === 'ready' ? 'Pronto!' :
                   'Acordando Servidor Render'}
                </h3>
                
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {progressoAcordar.message}
                </p>
                
                {/* Barra de progresso */}
                {progressoAcordar.status !== 'error' && progressoAcordar.status !== 'ready' && (
                  <div className="mb-4">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${progressoAcordar.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
                      {Math.round(progressoAcordar.progress)}%
                    </p>
                  </div>
                )}
                
                {/* Informação adicional */}
                {progressoAcordar.status === 'waking' && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-3">
                    <p className="text-xs text-blue-800 dark:text-blue-200">
                      ⏱️ O servidor está no plano Free e pode demorar até 90 segundos para acordar completamente (inicialização + banco de dados).
                    </p>
                  </div>
                )}
                
                {progressoAcordar.status === 'error' && (
                  <button
                    onClick={() => setMostrarModalAcordar(false)}
                    className="w-full mt-4 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-md transition-colors"
                  >
                    Fechar
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
