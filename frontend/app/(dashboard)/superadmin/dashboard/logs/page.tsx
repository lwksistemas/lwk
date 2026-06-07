/**
 * Página de Busca de Logs
 * ✅ REFATORADO v777: Código reduzido de 691 para ~120 linhas usando hooks e componentes
 */
'use client';

import { Suspense, useEffect, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { authService } from '@/lib/auth';
import { useLogsList } from '@/hooks/useLogsList';
import { useLogActions } from '@/hooks/useLogActions';
import { LogFilters, LogTable, LogDetalhesModal, SalvarBuscaModal } from '@/components/superadmin/logs';
import type { Log } from '@/hooks/useLogsList';

function BuscaLogsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { logs, loading, filtros, setFiltros, buscarLogs, buscarComFiltros, limparFiltros } = useLogsList();
  const {
    buscasSalvas,
    contextoTemporal,
    exportarCSV,
    exportarJSON,
    carregarContextoTemporal,
    limparContextoTemporal,
    salvarBusca,
    excluirBusca
  } = useLogActions();

  const [logSelecionado, setLogSelecionado] = useState<Log | null>(null);
  const [mostrarDetalhes, setMostrarDetalhes] = useState(false);
  const [mostrarSalvarBusca, setMostrarSalvarBusca] = useState(false);
  const urlFiltrosAplicados = useRef(false);
  const emailParam = searchParams.get('usuario_email');
  const qParam = searchParams.get('q');

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
      return;
    }
    if (urlFiltrosAplicados.current || (!emailParam && !qParam)) return;

    urlFiltrosAplicados.current = true;
    const novosFiltros = {
      ...(emailParam ? { usuario_email: emailParam } : {}),
      ...(qParam ? { q: qParam } : {}),
    };
    setFiltros(novosFiltros);
    buscarComFiltros(novosFiltros);
  }, [router, emailParam, qParam, setFiltros, buscarComFiltros]);

  const handleVerDetalhes = async (log: Log) => {
    setLogSelecionado(log);
    setMostrarDetalhes(true);
    await carregarContextoTemporal(log.id);
  };

  const handleFecharDetalhes = () => {
    setMostrarDetalhes(false);
    setLogSelecionado(null);
    limparContextoTemporal();
  };

  const handleSalvarBusca = (nome: string) => {
    const sucesso = salvarBusca(nome, filtros);
    if (sucesso) {
      setMostrarSalvarBusca(false);
    }
  };

  const handleCarregarBusca = (busca: { nome: string; filtros: typeof filtros }) => {
    setFiltros(busca.filtros);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <nav className="bg-purple-900 dark:bg-purple-950 text-white shadow-lg">
        <div className="w-full max-w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center space-x-4">
              <a
                href="/superadmin/dashboard"
                className="text-purple-200 hover:text-white transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
              </a>
              <h1 className="text-2xl font-bold">Busca de Logs</h1>
            </div>
          </div>
        </div>
      </nav>

      <main className="w-full max-w-full py-6 px-4 sm:px-6 lg:px-8">
        <LogFilters
          filtros={filtros}
          setFiltros={setFiltros}
          onBuscar={buscarLogs}
          onLimpar={limparFiltros}
          onExportarCSV={() => exportarCSV(filtros)}
          onExportarJSON={() => exportarJSON(filtros)}
          onSalvarBusca={() => setMostrarSalvarBusca(true)}
          buscasSalvas={buscasSalvas}
          onCarregarBusca={handleCarregarBusca}
          onExcluirBusca={excluirBusca}
          loading={loading}
          hasResults={logs.length > 0}
        />

        <LogTable
          logs={logs}
          loading={loading}
          searchQuery={filtros.q}
          onVerDetalhes={handleVerDetalhes}
        />
      </main>

      {mostrarDetalhes && logSelecionado && (
        <LogDetalhesModal
          log={logSelecionado}
          contextoTemporal={contextoTemporal}
          onClose={handleFecharDetalhes}
        />
      )}

      {mostrarSalvarBusca && (
        <SalvarBuscaModal
          onSalvar={handleSalvarBusca}
          onCancelar={() => setMostrarSalvarBusca(false)}
        />
      )}
    </div>
  );
}

export default function BuscaLogsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 text-gray-700 dark:text-gray-200">
        Carregando logs...
      </div>
    }>
      <BuscaLogsContent />
    </Suspense>
  );
}
