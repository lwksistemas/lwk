'use client';

import { useState, useEffect } from 'react';
import { setBackendServer } from '@/lib/api-client';
import { getPrimaryApiRoot, getBackupApiRoot } from '@/lib/api-base';

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
    nome: 'Render',
    url: BACKUP_BACKEND_URL,
    cor: 'blue',
    icone: '🔵',
  },
};

/** Timeout do health check (Render free pode demorar no cold start). */
const HEALTH_TIMEOUT_MS = 15000;

/** URL base sem /api para montar o path do health (evita /api/api/ quando env já tem /api). */
function healthBaseUrl(url: string): string {
  return url.replace(/\/api\/?$/, '');
}

export default function SeletorServidorBackend() {
  const [servidorAtivo, setServidorAtivo] = useState<Servidor>('heroku');
  const [mostrarMenu, setMostrarMenu] = useState(false);
  const [verificando, setVerificando] = useState(false);
  const [statusServidores, setStatusServidores] = useState<Record<Servidor, 'online' | 'offline' | 'verificando'>>({
    heroku: 'verificando',
    render: BACKUP_BACKEND_URL ? 'verificando' : 'offline',
  });

  useEffect(() => {
    // Carregar servidor ativo do localStorage
    const servidorSalvo = localStorage.getItem('backend_servidor') as Servidor;
    if (servidorSalvo && SERVIDORES[servidorSalvo]) {
      setServidorAtivo(servidorSalvo);
      // Atualizar a URL base da API usando a função do api-client
      setBackendServer(SERVIDORES[servidorSalvo].url);
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
        
        const response = await fetch(`${healthBaseUrl(base)}/api/superadmin/health/`, {
          method: 'GET',
          signal: controller.signal,
          mode: 'cors',
        });
        
        clearTimeout(timeoutId);
        return response.ok ? 'online' : 'offline';
      } catch (error) {
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
    
    try {
      // Verificar se o servidor está online (timeout maior para Render cold start)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), HEALTH_TIMEOUT_MS);
      
      const targetBase = SERVIDORES[novoServidor].url;
      if (!targetBase) {
        alert('URL do servidor de backup não configurada.');
        setVerificando(false);
        return;
      }

      const response = await fetch(`${healthBaseUrl(targetBase)}/api/superadmin/health/`, {
        method: 'GET',
        signal: controller.signal,
        mode: 'cors',
      });
      
      clearTimeout(timeoutId);

      if (response.ok) {
        // Salvar no localStorage
        localStorage.setItem('backend_servidor', novoServidor);
        
        // Atualizar a URL base da API usando a função do api-client
        setBackendServer(targetBase);
        
        setServidorAtivo(novoServidor);
        setMostrarMenu(false);
        
        // Recarregar a página para aplicar as mudanças
        window.location.reload();
      } else {
        alert(`Servidor ${SERVIDORES[novoServidor].nome} está offline. Não é possível trocar.`);
      }
    } catch (error) {
      alert(`Erro ao conectar com ${SERVIDORES[novoServidor].nome}. Servidor pode estar offline.`);
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
                    render: BACKUP_BACKEND_URL ? 'verificando' : 'offline',
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
    </div>
  );
}
