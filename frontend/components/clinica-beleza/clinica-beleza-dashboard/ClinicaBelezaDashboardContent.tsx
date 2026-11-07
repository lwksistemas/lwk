"use client";

import dynamic from "next/dynamic";
import { Activity, AlertTriangle, CalendarDays, TrendingUp, Users } from "lucide-react";
import { ClinicaBelezaPageHeader } from "@/components/clinica-beleza/ClinicaBelezaPageHeaderContext";
import { useClinicaBelezaUserDisplayName } from "@/components/clinica-beleza/ClinicaBelezaTopBar";
import { ClinicaBelezaShell } from "@/components/clinica-beleza/clinica-beleza-shell/ClinicaBelezaShell";
import {
  ClinicaBelezaThemeProvider,
  useClinicaBelezaTheme,
} from "@/components/clinica-beleza/ClinicaBelezaThemeContext";
import { useClinicaBelezaDark } from "@/hooks/useClinicaBelezaDark";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { LojaInfo } from "@/types/dashboard";
import {
  AppointmentItem,
  DashboardGreeting,
  LinkPainel,
  PainelCard,
  ProcedureBars,
  ResumoFinanceiroLista,
  StatCard,
} from "./ClinicaBelezaDashboardCards";
import {
  getDashboardChartColors,
  parseDashboardMesAno,
  pctChangeDashboard,
  primeiroNomeDashboard,
  rotuloPeriodoDashboard,
  saudacaoDashboard,
} from "./clinica-beleza-dashboard-utils";
import { useClinicaBelezaDashboard } from "./useClinicaBelezaDashboard";

const ClinicaBelezaDashboardCharts = dynamic(
  () =>
    import("./ClinicaBelezaDashboardCharts").then((m) => m.ClinicaBelezaDashboardCharts),
  {
    ssr: false,
    loading: () => (
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4">
        <div className="xl:col-span-3 h-72 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
        <div className="xl:col-span-2 h-72 rounded-2xl bg-gray-100 dark:bg-gray-800 animate-pulse" />
      </div>
    ),
  },
);

export function ClinicaBelezaDashboardContent({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  return (
    <ClinicaBelezaThemeProvider
      corPrimaria={loja.cor_primaria}
      corSecundaria={loja.cor_secundaria}
      corFundoPagina={loja.cor_fundo_pagina}
      agendaStatusColors={loja.agenda_status_colors}
    >
      <ClinicaBelezaDashboardInner loja={loja} onLogout={onLogout} />
    </ClinicaBelezaThemeProvider>
  );
}

function ClinicaBelezaDashboardInner({ loja, onLogout }: { loja: LojaInfo; onLogout?: () => void }) {
  const { primary } = useClinicaBelezaTheme();
  const chartColors = getDashboardChartColors(primary);
  const { slug, data, financial, loading, mesAno, setMesAno, mesAnoMax, fetchData } =
    useClinicaBelezaDashboard(loja);
  const [darkMode] = useClinicaBelezaDark();
  const nomeUsuario = useClinicaBelezaUserDisplayName();

  const stats = data?.statistics;
  const filterLabel = data?.filter?.label ?? "Este mês";
  const appointments = data?.next_appointments || [];
  const revenueData = data?.revenue_last_7_days || [];
  const revenueComValor = revenueData.some((d) => d.value > 0);
  const topProcedures = data?.top_procedures || [];

  const apptChange =
    stats?.appointments_yesterday != null
      ? pctChangeDashboard(stats.appointments_today, stats.appointments_yesterday)
      : null;
  const apptCaiu = Boolean(apptChange?.startsWith("-"));
  const inadimplentes = stats?.inadimplentes_count ?? 0;

  const faturamento = financial?.faturamento ?? stats?.revenue_month ?? 0;
  const despesas = financial?.despesas ?? 0;
  const lucro = financial?.lucro ?? faturamento - despesas;
  const periodoDashboard = parseDashboardMesAno(mesAno);
  const faturamentoChartTitle = `Faturamento — ${filterLabel}`;

  return (
    <ClinicaBelezaShell loja={loja} onLogout={onLogout}>
      <ClinicaBelezaPageHeader>
        <DashboardGreeting
          saudacao={saudacaoDashboard(new Date().getHours())}
          primeiroNome={primeiroNomeDashboard(nomeUsuario)}
          mesAno={mesAno}
          mesAnoMax={mesAnoMax}
          rotuloPeriodo={rotuloPeriodoDashboard(mesAno)}
          loading={loading}
          onMesAno={setMesAno}
          onAtualizar={() => void fetchData(true)}
        />
      </ClinicaBelezaPageHeader>
      <div className="@container p-4 lg:p-5 space-y-4 w-full min-w-0">

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div
              className="w-8 h-8 border-4 rounded-full animate-spin"
              style={{
                borderColor: "color-mix(in srgb, var(--cb-primary, #8B3D52) 20%, transparent)",
                borderTopColor: "var(--cb-primary, #8B3D52)",
              }}
            />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 @min-[520px]:grid-cols-2 @min-[1040px]:grid-cols-5 gap-3">
              <StatCard
                title="Atendimentos hoje"
                value={stats?.appointments_today ?? 0}
                icon={CalendarDays}
                changeLabel={apptChange ? `${apptChange} vs. ontem` : undefined}
                hintTone={apptChange ? (apptCaiu ? "alert" : "positive") : "muted"}
              />
              <StatCard
                title="Faturamento hoje"
                value={formatCurrency(stats?.revenue_today ?? 0)}
                icon={TrendingUp}
                changeLabel="Hoje"
              />
              <StatCard
                title="Clientes ativos"
                value={stats?.patients_total ?? 0}
                icon={Users}
                changeLabel="Cadastrados"
                valueTone="positive"
                hintTone="positive"
              />
              <StatCard
                title="Sessões realizadas"
                value={stats?.sessions_month ?? 0}
                icon={Activity}
                changeLabel={filterLabel}
                valueTone="positive"
                hintTone="positive"
              />
              <StatCard
                title="Inadimplência"
                value={formatCurrency(stats?.inadimplencia_total ?? 0)}
                icon={AlertTriangle}
                changeLabel={
                  inadimplentes > 0
                    ? `${inadimplentes} ${inadimplentes === 1 ? "cliente em atraso" : "clientes em atraso"}`
                    : "Em dia"
                }
                valueTone={inadimplentes > 0 ? "alert" : "positive"}
                hintTone={inadimplentes > 0 ? "alert" : "positive"}
                href={`/loja/${slug}/clinica-beleza/financeiro`}
              />
            </div>

            <div className="grid grid-cols-1 @min-[760px]:grid-cols-2 @min-[1100px]:grid-cols-3 gap-3 items-stretch">
              <PainelCard
                title="Próximos agendamentos"
                action={<LinkPainel href={`/loja/${slug}/agenda`}>Ver agenda</LinkPainel>}
              >
                {appointments.length > 0 ? (
                  appointments
                    .slice(0, 5)
                    .map((appt) => (
                      <AppointmentItem
                        key={appt.id}
                        appt={appt}
                        href={`/loja/${slug}/agenda?agendamento=${appt.id}`}
                      />
                    ))
                ) : (
                  <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-6">
                    Nenhum agendamento próximo
                  </p>
                )}
              </PainelCard>

              <PainelCard
                title={`Procedimentos realizados — ${filterLabel}`}
                action={
                  <LinkPainel
                    href={`/loja/${slug}/clinica-beleza/procedimentos-realizados?mes=${periodoDashboard.mes}&ano=${periodoDashboard.ano}`}
                  >
                    Ver relatório
                  </LinkPainel>
                }
              >
                {topProcedures.length > 0 ? (
                  <ProcedureBars procedures={topProcedures.slice(0, 5)} colors={chartColors} />
                ) : (
                  <p className="text-sm text-gray-400 dark:text-gray-500 text-center py-6">
                    Sem atendimentos concluídos no período
                  </p>
                )}
              </PainelCard>

              <PainelCard
                title={`Resumo financeiro — ${filterLabel}`}
                action={<LinkPainel href={`/loja/${slug}/clinica-beleza/financeiro`}>Ver financeiro</LinkPainel>}
              >
                <ResumoFinanceiroLista
                  faturamento={faturamento}
                  desconto={financial?.desconto ?? 0}
                  despesas={despesas}
                  lucro={lucro}
                  aReceber={financial?.a_receber ?? 0}
                  aPrazo={financial?.a_prazo ?? 0}
                />
              </PainelCard>
            </div>

            <ClinicaBelezaDashboardCharts
              faturamentoChartTitle={faturamentoChartTitle}
              filterLabel={filterLabel}
              revenueData={revenueData}
              revenueComValor={revenueComValor}
              topProcedures={topProcedures}
              chartColors={chartColors}
              primary={primary}
              darkMode={darkMode}
            />
          </>
        )}
      </div>
    </ClinicaBelezaShell>
  );
}
