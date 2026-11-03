'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  CartesianGrid,
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
  pg_ativas?: number | null;
  pg_ociosas?: number | null;
  pg_idle_in_transaction?: number | null;
  pg_tamanho_gb?: number | null;
  pg_lentas_disponivel?: boolean;
  fila_pendente?: number | null;
  fila_workers?: number | null;
  fila_falhas_24h?: number | null;
  fila_em_execucao?: number | null;
  fila_sucesso_24h?: number | null;
  fila_tempo_medio_s?: number | null;
  fila_idade_pendente_s?: number | null;
  lojas_ativas?: number | null;
  tenants?: number | null;
  wa_instancias?: number | null;
  wa_conectadas?: number | null;
  wa_desconectadas?: number | null;
  api_latency_media_ms?: number | null;
  api_latency_p95_ms?: number | null;
  api_5xx?: number | null;
  api_rpm_estimado?: number | null;
  api_amostras?: number | null;
  cpu_pct?: number | null;
};

type ResumoCampo = { atual?: number | null; media?: number | null; max?: number | null };
type HistMeta = {
  parcial?: boolean;
  desatualizado?: boolean;
  dias_disponiveis?: number;
  periodo_inicio?: string | null;
  periodo_fim?: string | null;
  amostras?: number;
  resumo?: Record<string, ResumoCampo>;
};
type Alerta = { servidor: string; tipo: string; nivel: string; mensagem: string; ts?: string };

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
    return new Date(ts).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return ts.slice(0, 16);
  }
}

function MiniChart({
  data,
  dataKey,
  color,
  nome,
}: {
  data: { t: string; v: number | null }[];
  dataKey: string;
  color: string;
  nome: string;
}) {
  if (data.length === 0) {
    return <p className="text-sm text-gray-500 py-8 text-center">Sem amostras.</p>;
  }
  return (
    <div className="h-52 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
          <XAxis dataKey="t" tick={{ fontSize: 10 }} minTickGap={28} />
          <YAxis tick={{ fontSize: 10 }} domain={[0, 'auto']} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey={dataKey}
            name={nome}
            stroke={color}
            dot={data.length < 8}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function ResumoTrio({ titulo, campo }: { titulo: string; campo?: ResumoCampo }) {
  return (
    <div className="rounded-lg border border-gray-100 dark:border-gray-800 px-3 py-2 text-xs">
      <p className="uppercase tracking-wide text-gray-500 mb-1">{titulo}</p>
      <p className="text-gray-800 dark:text-gray-100">
        atual <strong>{fmt(campo?.atual, '', 1)}</strong>
        {' · '}média <strong>{fmt(campo?.media, '', 1)}</strong>
        {' · '}máx <strong>{fmt(campo?.max, '', 1)}</strong>
      </p>
    </div>
  );
}

export default function CapacidadeServidoresPage() {
  const router = useRouter();
  const [servidores, setServidores] = useState<ServidorInfo[]>(SERVIDORES_FALLBACK);
  const [servidorId, setServidorId] = useState('lwksistemas-nova');
  const [dias, setDias] = useState(7);
  const [atual, setAtual] = useState<Snapshot | null>(null);
  const [historico, setHistorico] = useState<Snapshot[]>([]);
  const [histMeta, setHistMeta] = useState<HistMeta>({});
  const [alertas, setAlertas] = useState<Alerta[]>([]);
  const [crescimento, setCrescimento] = useState<{ ts?: string; lojas_ativas?: number; disk_usada_pct?: number; wa_conectadas?: number }[]>([]);
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
      const [rAtual, rHist, rAlert, rCresc] = await Promise.all([
        apiClient.get(`/superadmin/capacidade/atual/?servidor=${encodeURIComponent(servidorId)}`),
        apiClient.get(
          `/superadmin/capacidade/historico/?dias=${dias}&servidor=${encodeURIComponent(servidorId)}`,
        ),
        apiClient.get('/superadmin/capacidade/alertas/').catch(() => ({ data: { ativos: [] } })),
        apiClient
          .get(`/superadmin/capacidade/crescimento/?dias=${Math.max(dias, 7)}`)
          .catch(() => ({ data: { lwksistemas_nova: [] } })),
      ]);
      setAtual(rAtual.data);
      setHistorico(Array.isArray(rHist.data?.pontos) ? rHist.data.pontos : []);
      setHistMeta({
        parcial: rHist.data?.parcial,
        desatualizado: rHist.data?.desatualizado,
        dias_disponiveis: rHist.data?.dias_disponiveis,
        periodo_inicio: rHist.data?.periodo_inicio,
        periodo_fim: rHist.data?.periodo_fim,
        amostras: rHist.data?.amostras,
        resumo: rHist.data?.resumo,
      });
      setAlertas(Array.isArray(rAlert.data?.ativos) ? rAlert.data.ativos : []);
      const cres = Array.isArray(rCresc.data?.lwksistemas_nova) ? rCresc.data.lwksistemas_nova : [];
      const wa = Array.isArray(rCresc.data?.whatsappnova) ? rCresc.data.whatsappnova : [];
      const waByTs = new Map(wa.map((p: { ts?: string; wa_conectadas?: number }) => [p.ts, p.wa_conectadas]));
      setCrescimento(
        cres.map((p: { ts?: string; lojas_ativas?: number; disk_usada_pct?: number }) => ({
          ...p,
          wa_conectadas: waByTs.get(p.ts) ?? null,
        })),
      );
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

  const chartCpu = useMemo(
    () =>
      historico.map((p) => ({
        t: labelHora(p.ts),
        v:
          p.cpu_pct ??
          (p.cpus && p.load_5m != null
            ? Math.min(100, Math.round((p.load_5m / p.cpus) * 1000) / 10)
            : null),
      })),
    [historico],
  );
  const chartRam = useMemo(
    () => historico.map((p) => ({ t: labelHora(p.ts), v: p.mem_usada_pct ?? null })),
    [historico],
  );
  const chartDisk = useMemo(
    () => historico.map((p) => ({ t: labelHora(p.ts), v: p.disk_usada_pct ?? null })),
    [historico],
  );
  const chartCresc = useMemo(
    () =>
      crescimento.map((p) => ({
        t: labelHora(p.ts),
        lojas: p.lojas_ativas ?? null,
        disco: p.disk_usada_pct ?? null,
        wa: p.wa_conectadas ?? null,
      })),
    [crescimento],
  );

  const loadPct =
    atual?.cpus && atual.load_5m != null
      ? Math.min(100, Math.round((atual.load_5m / atual.cpus) * 1000) / 10)
      : null;

  const isApi = servidorId === 'lwksistemas-nova';
  const isWa = servidorId === 'whatsappnova';

  const tituloHist = useMemo(() => {
    const pedido = dias === 1 ? '24h' : `${dias}d`;
    if (histMeta.parcial && histMeta.dias_disponiveis != null) {
      const disp =
        histMeta.dias_disponiveis < 1
          ? `${Math.round(histMeta.dias_disponiveis * 24)}h disponíveis`
          : `${histMeta.dias_disponiveis.toFixed(1)} dias disponíveis`;
      return `Histórico — ${servidorAtivo?.nome} (${disp} · pedido ${pedido})`;
    }
    return `Histórico — ${servidorAtivo?.nome} (${pedido})`;
  }, [dias, histMeta, servidorAtivo?.nome]);

  if (loading && !atual) {
    return (
      <div className="min-h-screen flex items-center justify-center text-gray-500 dark:text-gray-400">
        Carregando capacidade…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="w-full max-w-full px-4 sm:px-6 lg:px-8 py-6 space-y-6">
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

        {alertas.length > 0 ? (
          <div className="space-y-2">
            {alertas.map((a, i) => (
              <div
                key={`${a.servidor}-${a.tipo}-${i}`}
                className={`rounded-lg border px-4 py-3 text-sm ${
                  a.nivel === 'critico'
                    ? 'border-red-300 bg-red-50 text-red-900'
                    : 'border-amber-300 bg-amber-50 text-amber-900'
                }`}
              >
                <span className="font-semibold uppercase text-xs mr-2">{a.nivel}</span>
                {a.mensagem}
              </div>
            ))}
          </div>
        ) : null}

        {histMeta.desatualizado ? (
          <div className="rounded-lg border border-amber-300 bg-amber-50 text-amber-900 px-4 py-3 text-sm">
            Coleta desatualizada (&gt;45 min). Verifique o worker django-q e o schedule de capacidade.
          </div>
        ) : null}

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

        <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <ResumoTrio titulo="CPU % no período" campo={histMeta.resumo?.cpu_pct} />
          <ResumoTrio titulo="RAM % no período" campo={histMeta.resumo?.mem_usada_pct} />
          <ResumoTrio titulo="Disco % no período" campo={histMeta.resumo?.disk_usada_pct} />
        </section>

        {isApi ? (
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Postgres</p>
              <p className="text-xl font-semibold mt-1">
                {fmt(atual?.pg_conexoes, '', 0)} / {fmt(atual?.pg_conexoes_max, '', 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                ativas {fmt(atual?.pg_ativas, '', 0)} · ociosas {fmt(atual?.pg_ociosas, '', 0)}
                {atual?.pg_tamanho_gb != null ? ` · ${fmt(atual.pg_tamanho_gb, ' GB')}` : ''}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Fila django-q</p>
              <p className="text-xl font-semibold mt-1">
                {fmt(atual?.fila_pendente, '', 0)} pendente
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {fmt(atual?.fila_workers, '', 0)} workers · exec {fmt(atual?.fila_em_execucao, '', 0)}
                {' · '}falhas 24h {fmt(atual?.fila_falhas_24h, '', 0)}
                {atual?.fila_sucesso_24h != null ? ` · ok 24h ${fmt(atual.fila_sucesso_24h, '', 0)}` : ''}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">API Django</p>
              <p className="text-xl font-semibold mt-1">
                p95 {fmt(atual?.api_latency_p95_ms, ' ms', 0)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                média {fmt(atual?.api_latency_media_ms, ' ms', 0)} · ~{fmt(atual?.api_rpm_estimado, ' rpm', 0)}
                {' · '}5xx {fmt(atual?.api_5xx, '', 0)}
              </p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Lojas ativas</p>
              <p className="text-xl font-semibold mt-1">{fmt(atual?.lojas_ativas, '', 0)}</p>
            </div>
          </section>
        ) : null}

        {isWa ? (
          <section className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Instâncias WhatsApp</p>
              <p className="text-xl font-semibold mt-1">{fmt(atual?.wa_instancias, '', 0)}</p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Conectadas</p>
              <p className="text-xl font-semibold mt-1 text-emerald-700">{fmt(atual?.wa_conectadas, '', 0)}</p>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
              <p className="text-xs uppercase tracking-wide text-gray-500">Desconectadas</p>
              <p className="text-xl font-semibold mt-1">{fmt(atual?.wa_desconectadas, '', 0)}</p>
            </div>
          </section>
        ) : null}

        {servidorId === 'midia01' && atual?.tenants != null ? (
          <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 text-sm">
            Tenants de mídia: <strong>{fmt(atual.tenants, '', 0)}</strong>
          </div>
        ) : null}

        <section className="space-y-4">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">{tituloHist}</h2>
          {historico.length === 0 ? (
            <p className="text-sm text-gray-500 py-10 text-center">
              Sem amostras deste servidor no período. O cron grava as três VMs a cada ~15 min.
            </p>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                <p className="text-xs font-medium text-violet-700 mb-2">CPU % (load/vCPU)</p>
                <MiniChart data={chartCpu} dataKey="v" color="#8b5cf6" nome="CPU %" />
              </div>
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                <p className="text-xs font-medium text-blue-700 mb-2">Memória RAM %</p>
                <MiniChart data={chartRam} dataKey="v" color="#3b82f6" nome="RAM %" />
              </div>
              <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4">
                <p className="text-xs font-medium text-emerald-700 mb-2">Disco %</p>
                <MiniChart data={chartDisk} dataKey="v" color="#10b981" nome="Disco %" />
              </div>
            </div>
          )}
        </section>

        <section className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 space-y-3">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-white">
            Capacidade e crescimento
          </h2>
          <p className="text-xs text-gray-500">
            Compara lojas ativas, disco da API e instâncias WhatsApp conectadas no período.
          </p>
          {chartCresc.length === 0 ? (
            <p className="text-sm text-gray-500 py-6 text-center">Aguardando histórico de crescimento.</p>
          ) : (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartCresc}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="t" tick={{ fontSize: 10 }} minTickGap={28} />
                  <YAxis tick={{ fontSize: 10 }} domain={[0, 'auto']} />
                  <Tooltip />
                  <Line type="monotone" dataKey="lojas" name="Lojas ativas" stroke="#7c3aed" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="disco" name="Disco API %" stroke="#10b981" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="wa" name="WA conectadas" stroke="#0ea5e9" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <p className="text-xs text-gray-500 dark:text-gray-400 pb-6">
          Amarelo ≥ 70% · Vermelho ≥ 85%. Alertas de CPU/RAM exigem ~45 min sustentados. Coleta a
          cada 15 min (django-q).
        </p>
      </div>
    </div>
  );
}
