"use client";

/**
 * Modo Tablet (Recepção) - Agenda de Hoje
 * UX pensada para tablet: timeline do dia, FAB "+ Novo", sessão curta e logout por inatividade.
 * Rota: /loja/[slug]/tablet
 * Acesso: admin | recepção | profissional (mesmo auth da loja).
 */

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getClinicaBelezaBaseUrl, getClinicaBelezaHeaders } from "@/lib/clinica-beleza-api";

/** Sessão curta: logout automático por inatividade (recepção) */
const INACTIVITY_MINUTES = 3;
const INACTIVITY_MS = INACTIVITY_MINUTES * 60 * 1000;

const STATUS_LABEL: Record<string, string> = {
  SCHEDULED: "Agendado",
  PENDING: "Pendente",
  CONFIRMED: "Confirmado",
  IN_PROGRESS: "Em atendimento",
  COMPLETED: "Concluído",
  CANCELLED: "Cancelado",
  NO_SHOW: "Faltou",
};

export interface AgendaHojeItem {
  id: number;
  start: string;
  end: string;
  status: string;
  patient_name: string;
  professional_name: string;
  procedure_name: string;
  procedure_duration: number;
  title?: string;
}

function useAgendaHoje() {
  const [data, setData] = useState<AgendaHojeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const baseURL = getClinicaBelezaBaseUrl();
      const headers = getClinicaBelezaHeaders();
      const res = await fetch(`${baseURL}/agenda/hoje/`, { headers });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.error || `Erro ${res.status}`);
      }
      const raw = await res.json();
      const list: AgendaHojeItem[] = (raw || []).map((e: any) => ({
        id: e.id,
        start: e.start,
        end: e.end,
        status: e.status || "",
        patient_name: e.patient_name || "",
        professional_name: e.professional_name || "",
        procedure_name: e.procedure_name || "",
        procedure_duration: e.procedure_duration ?? 0,
        title: e.title,
      }));
      setData(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar agenda.");
      setData([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}

function formatHora(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

function AgendaTimeline({
  data,
  loading,
  error,
}: {
  data: AgendaHojeItem[];
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-gray-500 dark:text-gray-400 text-lg">
        Carregando agenda…
      </div>
    );
  }
  if (error) {
    return (
      <div className="rounded-xl bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-4 text-center">
        {error}
      </div>
    );
  }
  if (data.length === 0) {
    return (
      <div className="rounded-xl bg-gray-100 dark:bg-gray-800 p-8 text-center text-gray-600 dark:text-gray-400 text-lg">
        Nenhum agendamento para hoje.
      </div>
    );
  }
  return (
    <div className="space-y-4">
      {data.map((item) => (
        <div
          key={item.id}
          className="bg-white dark:bg-gray-800 rounded-xl p-4 shadow-md flex justify-between items-center gap-4 border border-gray-200 dark:border-gray-700"
        >
          <div className="min-w-0 flex-1">
            <p className="text-xl font-semibold text-gray-900 dark:text-white tablet-text">
              {formatHora(item.start)}
            </p>
            <p className="font-medium text-gray-800 dark:text-gray-200 tablet-text">
              {item.patient_name}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 tablet-text">
              {item.procedure_name}
              {item.professional_name ? ` · ${item.professional_name}` : ""}
            </p>
          </div>
          <span className="text-green-600 dark:text-green-400 font-bold tablet-text shrink-0">
            {STATUS_LABEL[item.status] || item.status}
          </span>
        </div>
      ))}
    </div>
  );
}

/** Fullscreen automático: em tablet (≤1024px) e sem PWA, tenta tela cheia (cara de app). */
function useTabletFullscreen() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as any).standalone === true;
    if (isStandalone) return;
    if (window.innerWidth > 1024) return;
    const enter = () => {
      const el = document.documentElement;
      if (el.requestFullscreen) el.requestFullscreen().catch(() => {});
    };
    const t = setTimeout(enter, 500);
    return () => clearTimeout(t);
  }, []);
}

export default function TabletAgendaPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params.slug as string;
  const { data, loading, error, refetch } = useAgendaHoje();
  const [lastActivity, setLastActivity] = useState(Date.now());

  useTabletFullscreen();

  // Logout por inatividade
  useEffect(() => {
    const checkInactivity = () => {
      if (Date.now() - lastActivity >= INACTIVITY_MS) {
        sessionStorage.removeItem("access_token");
        sessionStorage.removeItem("current_loja_id");
        router.push(`/loja/${slug}/login?reason=inactivity`);
      }
    };
    const t = setInterval(checkInactivity, 30_000);
    return () => clearInterval(t);
  }, [lastActivity, slug, router]);

  useEffect(() => {
    const onActivity = () => setLastActivity(Date.now());
    window.addEventListener("click", onActivity);
    window.addEventListener("touchstart", onActivity);
    window.addEventListener("keydown", onActivity);
    return () => {
      window.removeEventListener("click", onActivity);
      window.removeEventListener("touchstart", onActivity);
      window.removeEventListener("keydown", onActivity);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 p-4 tablet-mode">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            📅 Agenda de Hoje
          </h1>
          <Link
            href={`/loja/${slug}/agenda`}
            className="text-sm text-gray-600 dark:text-gray-400 hover:underline"
          >
            Ver agenda completa
          </Link>
        </div>

        {/* Cadastros rápidos para recepção */}
        <div className="flex flex-wrap gap-3 mb-6">
          <Link
            href={`/loja/${slug}/clinica-beleza/pacientes?novo=1`}
            className="flex-1 min-w-[140px] py-3 px-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm text-center font-medium text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            👤 Novo paciente
          </Link>
          <Link
            href={`/loja/${slug}/clinica-beleza/profissionais?novo=1`}
            className="flex-1 min-w-[140px] py-3 px-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-sm text-center font-medium text-gray-800 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
          >
            🧑‍⚕️ Novo profissional
          </Link>
        </div>

        <AgendaTimeline data={data} loading={loading} error={error} />

        <button
          type="button"
          onClick={() => refetch()}
          className="mt-4 w-full py-2 text-gray-600 dark:text-gray-400 text-sm"
        >
          Atualizar
        </button>
      </div>

      <Link
        href={`/loja/${slug}/agenda?novo=1`}
        className="fixed bottom-6 right-6 bg-pink-600 hover:bg-pink-700 text-white px-6 py-4 rounded-full text-lg font-semibold shadow-lg transition"
        aria-label="Novo agendamento"
      >
        + Novo
      </Link>
    </div>
  );
}
