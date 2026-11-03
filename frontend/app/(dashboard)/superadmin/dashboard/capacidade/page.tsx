'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import apiClient from '@/lib/api-client';
import { authService } from '@/lib/auth';

type Snapshot = {
  ts?: string;
  cpus?: number | null;
  load_1m?: number | null;
  load_5m?: number | null;
  load_15m?: number | null;
  mem_total_mb?: number | null;
  mem_usada_mb?: number | null;
  mem_usada_pct?: number | null;
  disk_total_gb?: number | null;
  disk_livre_gb?: number | null;
  disk_usada_pct?: number | null;
  pg_conexoes?: number | null;
  pg_conexoes_max?: number | null;
  fila_pendente?: number | null;
  fila_workers?: number | null;
  fila_falhas_24h?: number | null;
  lojas_ativas?: number | null;
};

type MidiaCapacidade = {
  status?: string;
  free_gb?: number | null;
  total_gb?: number | null;
  used_gb?: number | null;
  used_pct?: number | null;
  tenants?: number | null;
  error?: string;
  media_server?: string;
};

function nivelAlerta(pct: number | null | undefined): 'ok' | 'warn' | 'crit' {
  if (pct == null || Number.isNaN(pct)) return 'ok';
  if (pct >= 85) return 'crit';
  if (pct >= 70) return 'warn';
  return 'ok';
}

function corNivel(n: 'ok' | 'warn' | 'crit'): string {
  if (n === 'crit') return 'border-red-300 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950/40 dark:text-red-100';
  if (n === 'warn') return 'border-amber-300 bg-amber-50 text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100';
  return 'border-gray-200 bg-white text-gray-900 dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100';
}

function fmt(v: number | null | undefined, suffix = '', digits = 1): string {
  if (v == null || Number.isNaN(v)) return '—';
  return `${Number(v).toFixed(digits)}${suffix}`;
}

function labelHora(ts?: string): string {
  if (!ts) return '';
  try {
    const d = new Date(ts);
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts.slice(0, 16);
  }
}

export default function CapacidadeServidoresPage() {
  const router = useRouter();
  const [dias, setDias] = useState(7);
  const [atual, setAtual] = useState<Snapshot | null>(null);
  const [midia, setMidia] = useState<MidiaCapacidade | null>(null);
  const [historico, setHistorico] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizadoEm, setAtualizadoEm] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  const carregar = useCallback(async () => {
    try {
      setErro(null);
      const [rAtual, rHist, rMidia] = await Promise.all([
        apiClient.get('/superadmin/capacidade/atual/'),
        apiClient.get(`/superadmin/capacidade/historico/?dias=${dias}`),
        apiClient.get('/superadmin/capacidade/midia/').catch((e) => ({
          data: {
            status: 'unavailable',
            error: e?.response?.data?.error || e?.message || 'Mídia indisponível',
          },
        })),
      ]);
      setAtual(rAtual.data);
      setHistorico(Array.isArray(rHist.data?.pontos) ? rHist.data.pontos : []);
      setMidia(rMidia.data);
      setAtualizadoEm(new Date().toLocaleTimeString('pt-BR'));
    } catch (e: unknown) {
      const msg =
        e && typeof e === 'object' && 'message' in e
          ? String((e as { message?: string }).message)
          : 'Falha ao carregar capacidade';
      setErro(msg);
    } finally {
      setLoading(false);
    }
  }, [dias]);

  useEffect(() => {
    void carregar();
    const id = window.setInterval(() => {
      void carregar();
    }, 45000);
    return () => window.clearInterval(id);
  }, [carregar]);

  const chartData = useMemo(
    () =>
      historico.map((p) => ({
        t: labelHora(p.ts),
        load5: p.load_5m ?? null,
        ram: p.mem_usada_pct ?? null,
        disco: p.disk_usada_pct ?? null,
        fila: p.fila_pendente ?? null,
        pg: p.pg_conexoes ?? null,
      })),
    [historico],
  );

  const loadPct =
    atual?.cpus && atual.load_5m != null
      ? Math.min(100, Math.round((atual.load_5m / atual.cpus) * 1000) / 10)
      : null;

  if (loading && !atual) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500 dark:text-gray-400">
        Carregando capacidade…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-4 sm:p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <button
              type="button"
              onClick={() => router.push('/superadmin/dashboard')}
              className="text-sm text-violet-600 dark:text-violet-400 hover:underline mb-1"
            >
              ← Voltar ao dashboard
            </button>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Capacidade dos servidores
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              API (produção) em tempo quase real + histórico do coletor. Mídia via health.
              {atualizadoEm ? ` · Atualizado às ${atualizadoEm}` : null}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {[1, 7, 30].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => setDias(d)}
                className={`px-3 py-1.5 rounded-lg text-sm border ${
                  dias === d
                    ? 'bg-violet-600 text-white border-violet-600'
                    : 'bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-200'
                }`}
              >
                {d === 1 ? '24h' : `${d}d`}
              </button>
            ))}
            <button
              type="button"
              onClick={() => void carregar()}
              className="px-3 py-1.5 rounded-lg text-sm border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
            >
              Atualizar
            </button>
          </div>
        </header>

        {erro ? (
          <div className="rounded-lg border border-red-300 bg-red-50 text-red-800 px-4 py-3 text-sm">
            {erro}
          </div>
        ) : null}

        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(loadPct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">CPU (API)</p>
            <p className="text-2xl font-semibold mt-1">
              {fmt(atual?.load_5m, '', 2)}
              <span className="text-sm font-normal opacity-70"> / {atual?.cpus ?? '—'} vCPU</span>
            </p>
            <p className="text-xs mt-1 opacity-80">
              load 5m · ~{fmt(loadPct, '%', 0)} da capacidade
            </p>
          </div>
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(atual?.mem_usada_pct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">RAM (API)</p>
            <p className="text-2xl font-semibold mt-1">{fmt(atual?.mem_usada_pct, '%')}</p>
            <p className="text-xs mt-1 opacity-80">
              {fmt(atual?.mem_usada_mb, '', 0)} / {fmt(atual?.mem_total_mb, ' MB', 0)}
            </p>
          </div>
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(atual?.disk_usada_pct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">Disco (API)</p>
            <p className="text-2xl font-semibold mt-1">{fmt(atual?.disk_usada_pct, '%')}</p>
            <p className="text-xs mt-1 opacity-80">
              livre {fmt(atual?.disk_livre_gb, ' GB')} de {fmt(atual?.disk_total_gb, ' GB')}
            </p>
          </div>
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(midia?.used_pct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">Disco (Mídia)</p>
            <p className="text-2xl font-semibold mt-1">
              {midia?.used_pct != null ? fmt(midia.used_pct, '%') : fmt(midia?.free_gb, ' GB livre')}
            </p>
            <p className="text-xs mt-1 opacity-80">
              {midia?.status === 'unavailable' || midia?.error
                ? midia.error || 'Indisponível'
                : `livre ${fmt(midia?.free_gb, ' GB')} · ${fmt(midia?.tenants, '', 0)} tenants`}
            </p>
          </div>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Postgres</p>
            <p className="text-xl font-semibold mt-1">
              {fmt(atual?.pg_conexoes, '', 0)} / {fmt(atual?.pg_conexoes_max, '', 0)}
            </p>
          </div>
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Fila django-q</p>
            <p className="text-xl font-semibold mt-1">
              {fmt(atual?.fila_pendente, '', 0)} pendente
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {fmt(atual?.fila_workers, '', 0)} workers · falhas 24h {fmt(atual?.fila_falhas_24h, '', 0)}
            </p>
          </div>
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
            <p className="text-xs uppercase tracking-wide text-gray-500">Lojas ativas</p>
            <p className="text-xl font-semibold mt-1">{fmt(atual?.lojas_ativas, '', 0)}</p>
          </div>
        </section>

        <section className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Histórico — load, RAM e disco ({dias === 1 ? '24h' : `${dias} dias`})
          </h2>
          {chartData.length === 0 ? (
            <p className="text-sm text-gray-500 py-10 text-center">
              Sem amostras no período. O cron grava a cada ~15 min após o deploy.
            </p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="t" tick={{ fontSize: 11 }} minTickGap={28} />
                  <YAxis tick={{ fontSize: 11 }} domain={[0, 'auto']} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="load5" name="Load 5m" stroke="#8b5cf6" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="ram" name="RAM %" stroke="#3b82f6" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="disco" name="Disco %" stroke="#10b981" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <p className="text-xs text-gray-500 dark:text-gray-400 pb-6">
          Amarelo ≥ 70% · Vermelho ≥ 85%. Use picos sustentados de RAM/disco/load para decidir
          upgrade de vCPU, memória ou volume na Magalu.
        </p>
      </div>
    </div>
  );
}
