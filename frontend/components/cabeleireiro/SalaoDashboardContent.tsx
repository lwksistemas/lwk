'use client';

import { useCallback, useEffect, useState, type CSSProperties } from 'react';
import type { LojaInfo } from '@/types/dashboard';
import { CabeleireiroAPI, type SalaoAgendamento, type SalaoDashboard } from '@/lib/cabeleireiro-api';
import { SALAO_PRIMARY } from './salao-nav';
import { SalaoShell } from './SalaoShell';
import { Parisienne } from 'next/font/google';

const scriptFont = Parisienne({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-salao-script',
  display: 'swap',
});

function formatHora(h: string) {
  return (h || '').slice(0, 5);
}

export function SalaoDashboardContent({
  loja,
  onLogout,
  wrapShell = true,
}: {
  loja: LojaInfo;
  onLogout?: () => void;
  wrapShell?: boolean;
}) {
  const [data, setData] = useState<SalaoDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [confirmingId, setConfirmingId] = useState<number | null>(null);
  const primary = loja.cor_primaria || SALAO_PRIMARY;

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await CabeleireiroAPI.dashboard());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const confirmar = async (ag: SalaoAgendamento) => {
    setConfirmingId(ag.id);
    try {
      await CabeleireiroAPI.confirmarChegada(ag.id);
      await load();
    } finally {
      setConfirmingId(null);
    }
  };

  const body = (
    <div
      className={`${scriptFont.variable} relative min-h-[calc(100vh-0px)] overflow-hidden`}
      style={
        {
          '--salao-primary': primary,
        } as CSSProperties
      }
    >
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage:
            "url('https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1600&q=80')",
        }}
      />
      <div className="absolute inset-0 bg-[#F7F0F3]/55 backdrop-blur-[1px]" />

      <div className="relative z-10 flex flex-col items-center px-4 py-10 md:py-16 max-w-3xl mx-auto">
        <h1
          className="text-5xl md:text-6xl text-[var(--salao-primary)] drop-shadow-sm"
          style={{ fontFamily: 'var(--font-salao-script), cursive' }}
        >
          {loja.nome?.split(' ')[0] || 'Lumina'}
        </h1>
        <p className="mt-2 text-[11px] md:text-xs tracking-[0.2em] uppercase text-[var(--salao-primary)]/80 font-medium text-center">
          Gestão que realça a beleza do seu salão
        </p>

        <div className="mt-8 w-full rounded-2xl bg-white/85 backdrop-blur-md border border-white/60 shadow-lg p-5 md:p-6">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h2 className="text-sm font-semibold text-gray-800">Próximos 3 agendamentos de hoje</h2>
            {!loading && data && (
              <span className="text-xs text-gray-500">
                {data.concluidos_hoje}/{data.total_hoje} concluídos
              </span>
            )}
          </div>

          {loading && <p className="text-sm text-gray-500 text-center py-6">Carregando...</p>}
          {!loading && (!data?.proximos || data.proximos.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-6">Nenhum agendamento pendente para hoje.</p>
          )}

          <ul className="space-y-3">
            {data?.proximos?.map((ag) => (
              <li
                key={ag.id}
                className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl bg-white/90 border border-[#E8D5DC] px-3 py-3"
              >
                <div
                  className="shrink-0 w-16 rounded-lg text-center py-1.5 text-[var(--salao-primary)]"
                  style={{ backgroundColor: '#F3E4EA' }}
                >
                  <div className="text-sm font-bold leading-tight">{formatHora(ag.hora_inicio)}</div>
                  <div className="text-[10px] uppercase">Hoje</div>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{ag.cliente_nome}</p>
                  <p className="text-xs text-gray-500 truncate">
                    {ag.servico_nome || 'Serviço'}
                    {ag.profissional_nome ? ` · ${ag.profissional_nome}` : ''}
                  </p>
                </div>
                {ag.status === 'SCHEDULED' || ag.status === 'ARRIVED' ? (
                  <button
                    type="button"
                    disabled={confirmingId === ag.id || ag.status === 'ARRIVED'}
                    onClick={() => void confirmar(ag)}
                    className="shrink-0 px-3 py-2 rounded-lg text-xs font-medium text-white disabled:opacity-60"
                    style={{ backgroundColor: primary }}
                  >
                    {ag.status === 'ARRIVED'
                      ? 'Chegada confirmada'
                      : confirmingId === ag.id
                        ? 'Confirmando...'
                        : 'Confirmar chegada'}
                  </button>
                ) : (
                  <span className="text-xs text-gray-500 shrink-0">{ag.status_display || ag.status}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );

  if (!wrapShell) return body;
  return (
    <div className={scriptFont.variable}>
      <SalaoShell loja={loja} onLogout={onLogout}>
        {body}
      </SalaoShell>
    </div>
  );
}
