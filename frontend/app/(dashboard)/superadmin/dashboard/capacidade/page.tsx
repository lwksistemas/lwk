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

type ServidorInfo = {
  id: string;
  nome: string;
  papel: string;
  tipo_magalu: string;
  ipv4: string;
};

type Snapshot = {
  ts?: string;
  servidor?: string;
  nome?: string;
  papel?: string;
  tipo_magalu?: string;
  ipv4?: string;
  status?: string;
  error?: string;
  dica?: string;
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
  tenants?: number | null;
};

const SERVIDORES_FALLBACK: ServidorInfo[] = [
  {
    id: 'lwksistemas-nova',
    nome: 'lwksistemas-nova',
    papel: 'API, ERP, Postgres e frontends',
    tipo_magalu: 'BV8-16-150',
    ipv4: '201.23.81.50',
  },
  {
    id: 'midia01',
    nome: 'midia01',
    papel: 'Servidor de mídia (imagens/PDFs)',
    tipo_magalu: 'BV1-4-100',
    ipv4: '201.23.87.251',
  },
  {
    id: 'whatsappnova',
    nome: 'whatsappnova',
    papel: 'Evolution API (WhatsApp)',
    tipo_magalu: 'BV2-4-100',
    ipv4: '169.150.0.111',
  },
];

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
  const [servidores, setServidores] = useState<ServidorInfo[]>(SERVIDORES_FALLBACK);
  const [servidorId, setServidorId] = useState('lwksistemas-nova');
  const [dias, setDias] = useState(7);
  const [atual, setAtual] = useState<Snapshot | null>(null);
  const [historico, setHistorico] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizadoEm, setAtualizadoEm] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && authService.getUserType() !== 'superadmin') {
      router.push('/superadmin/login');
    }
  }, [router]);

  useEffect(() => {
    void apiClient
      .get('/superadmin/capacidade/servidores/')
      .then((r) => {
        if (Array.isArray(r.data?.servidores) && r.data.servidores.length) {
          setServidores(r.data.servidores);
        }
      })
      .catch(() => undefined);
  }, []);

  const servidorAtivo = useMemo(
    () => servidores.find((s) => s.id === servidorId) || servidores[0],
    [servidores, servidorId],
  );

  const carregar = useCallback(async () => {
    try {
      setErro(null);
      const [rAtual, rHist] = await Promise.all([
        apiClient.get(`/superadmin/capacidade/atual/?servidor=${encodeURIComponent(servidorId)}`),
        apiClient.get(
          `/superadmin/capacidade/historico/?dias=${dias}&servidor=${encodeURIComponent(servidorId)}`,
        ),
      ]);
      setAtual(rAtual.data);
      setHistorico(Array.isArray(rHist.data?.pontos) ? rHist.data.pontos : []);
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
  }, [dias, servidorId]);

  useEffect(() => {
    setLoading(true);
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
      })),
    [historico],
  );

  const loadPct =
    atual?.cpus && atual.load_5m != null
      ? Math.min(100, Math.round((atual.load_5m / atual.cpus) * 1000) / 10)
      : null;

  const isApi = servidorId === 'lwksistemas-nova';

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
              Nomes iguais às instâncias Magalu Cloud. Escolha a VM para ver CPU, RAM e disco.
              {atualizadoEm ? ` · Atualizado às ${atualizadoEm}` : null}
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
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

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {servidores.map((s) => {
            const ativo = s.id === servidorId;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setServidorId(s.id)}
                className={`text-left rounded-xl border p-4 transition-colors ${
                  ativo
                    ? 'border-violet-500 bg-violet-50 dark:bg-violet-950/40 ring-1 ring-violet-400'
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-violet-300'
                }`}
              >
                <p className="font-semibold text-gray-900 dark:text-white font-mono text-sm">
                  {s.nome}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{s.papel}</p>
                <p className="text-[11px] text-gray-400 mt-2">
                  {s.tipo_magalu} · {s.ipv4}
                </p>
              </button>
            );
          })}
        </section>

        {servidorAtivo ? (
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
            Monitorando{' '}
            <span className="font-mono font-semibold text-gray-900 dark:text-white">
              {servidorAtivo.nome}
            </span>{' '}
            ({servidorAtivo.tipo_magalu} · {servidorAtivo.ipv4})
          </div>
        ) : null}

        {erro ? (
          <div className="rounded-lg border border-red-300 bg-red-50 text-red-800 px-4 py-3 text-sm">
            {erro}
          </div>
        ) : null}

        {atual?.status === 'unavailable' || atual?.error ? (
          <div className="rounded-lg border border-amber-300 bg-amber-50 text-amber-900 px-4 py-3 text-sm">
            {atual.error || 'Servidor sem resposta de métricas.'}
            {atual.dica ? <span className="block mt-1 opacity-90">{atual.dica}</span> : null}
          </div>
        ) : null}

        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(loadPct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">Processador</p>
            <p className="text-2xl font-semibold mt-1">
              {fmt(atual?.load_5m, '', 2)}
              <span className="text-sm font-normal opacity-70"> / {atual?.cpus ?? '—'} vCPU</span>
            </p>
            <p className="text-xs mt-1 opacity-80">
              load 5m · ~{fmt(loadPct, '%', 0)} da capacidade
            </p>
          </div>
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(atual?.mem_usada_pct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">Memória RAM</p>
            <p className="text-2xl font-semibold mt-1">{fmt(atual?.mem_usada_pct, '%')}</p>
            <p className="text-xs mt-1 opacity-80">
              {fmt(atual?.mem_usada_mb, '', 0)} / {fmt(atual?.mem_total_mb, ' MB', 0)}
            </p>
          </div>
          <div className={`rounded-xl border p-4 ${corNivel(nivelAlerta(atual?.disk_usada_pct))}`}>
            <p className="text-xs uppercase tracking-wide opacity-70">Espaço em disco</p>
            <p className="text-2xl font-semibold mt-1">{fmt(atual?.disk_usada_pct, '%')}</p>
            <p className="text-xs mt-1 opacity-80">
              livre {fmt(atual?.disk_livre_gb, ' GB')} de {fmt(atual?.disk_total_gb, ' GB')}
            </p>
          </div>
        </section>

        {isApi ? (
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
                {fmt(atual?.fila_workers, '', 0)} workers · falhas 24h{' '}
                {fmt(atual?.fila_falhas_24h, '', 0)}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Lojas ativas</p>
              <p className="text-xl font-semibold mt-1">{fmt(atual?.lojas_ativas, '', 0)}</p>
            </div>
          </section>
        ) : null}

        {servidorId === 'midia01' && atual?.tenants != null ? (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 text-sm">
            Tenants de mídia: <strong>{fmt(atual.tenants, '', 0)}</strong>
          </div>
        ) : null}

        <section className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
            Histórico — {servidorAtivo?.nome} ({dias === 1 ? '24h' : `${dias} dias`})
          </h2>
          {chartData.length === 0 ? (
            <p className="text-sm text-gray-500 py-10 text-center">
              Sem amostras deste servidor no período. O cron grava as três VMs a cada ~15 min.
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
          Amarelo ≥ 70% · Vermelho ≥ 85%. Instâncias: lwksistemas-nova, midia01, whatsappnova
          (console Magalu).
        </p>
      </div>
    </div>
  );
}
