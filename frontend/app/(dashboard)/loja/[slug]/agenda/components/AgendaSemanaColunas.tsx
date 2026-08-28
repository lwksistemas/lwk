"use client";

import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import { formatClinicaHora } from "@/lib/clinica-beleza-datetime";
import {
  addDaysIso,
  diasSemanaIso,
  estiloCardStatusAgenda,
  estiloInlineCardAgenda,
  eventosDoDiaFiltrados,
  faixasSobrepostas,
  horasGradeAgenda,
  minutesToHm,
  parseHmToMinutes,
  rotuloStatusCardAgenda,
  sameDayIso,
  slotDateFromMinutes,
  snapMinutos,
  capitalizarAgenda,
  tituloCardAgenda,
  toAgendaDiaIso,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import { AlcaLarguraColuna, useAgendaColunaLargura } from "./useAgendaColunaLargura";
import { useAgendaDiaArrasto } from "./useAgendaDiaArrasto";
import { AgendaLateralDireita } from "./AgendaLateralDireita";

const PX_PER_HOUR = 72;
const COL_MIN_WIDTH = 168;
const TIME_COL_W = 44;
const DIA_ACCENT = "#7c3aed";

function subtituloCard(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return "Bloqueio";
  if (p.isIntervalo) return "Intervalo";
  return [p.procedure_name, p.professional_name].filter(Boolean).join(" · ");
}

function rotuloDia(iso: string): { semana: string; data: string } {
  const [y, mo, d] = iso.split("-").map(Number);
  const ref = new Date(y, (mo || 1) - 1, d || 1);
  return {
    semana: capitalizarAgenda(ref.toLocaleDateString("pt-BR", { weekday: "short" })).replace(".", ""),
    data: ref.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
  };
}

function chaveColunaSemana(iso: string): string {
  const [y, mo, d] = iso.split("-").map(Number);
  return `dow-${new Date(y, (mo || 1) - 1, d || 1).getDay()}`;
}

export function AgendaSemanaColunas({
  dateIso,
  onDateChange,
  eventos,
  selectedProfessional,
  hiddenDays,
  slotMinTime,
  slotMaxTime,
  onOpenEvent,
  onSlotClick,
  onMudarVisao,
  onMover,
  onRedimensionar,
  onArrastoAtivo,
}: {
  dateIso: string;
  onDateChange: (iso: string) => void;
  eventos: AgendaEventData[];
  selectedProfessional: string;
  hiddenDays: number[];
  slotMinTime: string;
  slotMaxTime: string;
  onOpenEvent: (evt: AgendaEventData) => void;
  onSlotClick: (date: Date, professionalId: number) => void;
  onMudarVisao: (view: "day" | "month") => void;
  onMover?: (evt: AgendaEventData, start: Date, professionalId: number) => void;
  onRedimensionar?: (evt: AgendaEventData, duracaoMinutos: number) => void;
  onArrastoAtivo?: (ativo: boolean) => void;
}) {
  const minMin = parseHmToMinutes(slotMinTime);
  const maxMin = Math.max(minMin + 60, parseHmToMinutes(slotMaxTime));
  const pxPerMin = PX_PER_HOUR / 60;
  const gridH = (maxMin - minMin) * pxPerMin;
  const colunas = useMemo(() => diasSemanaIso(dateIso, hiddenDays), [dateIso, hiddenDays]);
  const profSlot = selectedProfessional ? Number(selectedProfessional) : 0;

  const horas = useMemo(() => horasGradeAgenda(minMin, maxMin), [minMin, maxMin]);

  const agora = new Date();
  const hojeIso = toAgendaDiaIso(agora);
  const agoraMin = agora.getHours() * 60 + agora.getMinutes();
  const agoraTop = (agoraMin - minMin) * pxPerMin;
  const agoraVisivel = agoraMin >= minMin && agoraMin <= maxMin;

  const tituloFaixa = useMemo(() => {
    const primeiro = colunas[0];
    const ultimo = colunas[colunas.length - 1] || primeiro;
    const [y1, m1, d1] = primeiro.split("-").map(Number);
    const [y2, m2, d2] = ultimo.split("-").map(Number);
    const a = new Date(y1, (m1 || 1) - 1, d1 || 1);
    const b = new Date(y2, (m2 || 1) - 1, d2 || 1);
    if (a.getMonth() === b.getMonth()) {
      return `${a.getDate()} – ${b.getDate()} de ${capitalizarAgenda(
        a.toLocaleDateString("pt-BR", { month: "long", year: "numeric" }),
      )}`;
    }
    return `${a.toLocaleDateString("pt-BR", { day: "numeric", month: "short" })} – ${b.toLocaleDateString("pt-BR", {
      day: "numeric",
      month: "short",
      year: "numeric",
    })}`;
  }, [colunas]);

  const { arrasto, iniciarMover, iniciarResize, deveIgnorarClick: deveIgnorarArrasto } = useAgendaDiaArrasto({
    dateIso,
    minMin,
    maxMin,
    pxPerMin,
    onMover,
    onRedimensionar,
    onDateChange,
  });
  const {
    template,
    iniciar: iniciarLargura,
    arrastando: arrastandoLargura,
    deveIgnorarClick: deveIgnorarLargura,
    hasCustomWidths,
  } = useAgendaColunaLargura("agenda-col-w-semana", COL_MIN_WIDTH);
  const deveIgnorarClick = () => deveIgnorarArrasto() || deveIgnorarLargura();

  useEffect(() => {
    onArrastoAtivo?.(Boolean(arrasto) || arrastandoLargura);
    return () => onArrastoAtivo?.(false);
  }, [arrasto, arrastandoLargura, onArrastoAtivo]);

  return (
    <div className={`flex flex-col min-h-0 flex-1 bg-white dark:bg-gray-800 ${arrasto?.moved || arrastandoLargura ? "select-none" : ""}`}>
      <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 px-3 sm:px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
            onClick={() => onDateChange(addDaysIso(dateIso, -7))}
            aria-label="Semana anterior"
          >
            ‹
          </button>
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
            onClick={() => onDateChange(addDaysIso(dateIso, 7))}
            aria-label="Próxima semana"
          >
            ›
          </button>
          <button
            type="button"
            className="ml-1 px-3 h-8 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 hover:bg-gray-50"
            onClick={() => onDateChange(hojeIso)}
          >
            Hoje
          </button>
        </div>
        <div className="text-center min-w-[12rem]">
          <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-50 capitalize leading-tight">
            {tituloFaixa}
          </h2>
        </div>
        <div className="flex justify-end">
          <div className="inline-flex items-center rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 text-sm">
            <button
              type="button"
              className="px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
              onClick={() => onMudarVisao("day")}
            >
              Dia
            </button>
            <span className="px-3 py-1.5 font-medium text-white" style={{ backgroundColor: DIA_ACCENT }}>
              Semana
            </span>
            <button
              type="button"
              className="px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 border-l border-gray-200 dark:border-gray-600"
              onClick={() => onMudarVisao("month")}
            >
              Mês
            </button>
          </div>
        </div>
      </div>

      <div className="flex flex-1 min-h-0">
        <div
          className={`min-h-0 overflow-auto agenda-scroll-root flex-1 ${
            hasCustomWidths ? "lg:flex-none lg:max-w-[calc(100%-16rem)]" : ""
          }`}
        >
          <div
            className={`grid h-full ${hasCustomWidths ? "w-max min-w-full lg:min-w-0" : "min-w-full"}`}
            style={{
              gridTemplateColumns: colunas.map((colIso) => template(chaveColunaSemana(colIso))).join(" "),
            }}
          >
            {colunas.map((colIso) => {
              const rotulo = rotuloDia(colIso);
              const ehHoje = colIso === hojeIso;
              const ehFoco = colIso === dateIso;
              const items = faixasSobrepostas(eventosDoDiaFiltrados(eventos, colIso, selectedProfessional));
              const colKey = chaveColunaSemana(colIso);
              return (
                <div
                  key={colIso}
                  data-agenda-col-wrap
                  data-agenda-col-id={colKey}
                  className="relative flex flex-col border-r border-gray-200 dark:border-gray-700 min-w-0"
                >
                  <AlcaLarguraColuna onPointerDown={(e) => iniciarLargura(colKey, e)} />
                  <div
                    className={`sticky top-0 z-20 border-b border-gray-200 dark:border-gray-700 px-2 py-2 text-center ${
                      ehHoje ? "bg-violet-50 dark:bg-violet-950/30" : "bg-white dark:bg-gray-800"
                    }`}
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">{rotulo.semana}</p>
                    <p
                      className={`text-sm font-semibold ${
                        ehFoco ? "text-violet-700 dark:text-violet-300" : "text-gray-900 dark:text-gray-100"
                      }`}
                    >
                      {rotulo.data}
                    </p>
                  </div>
                  <div
                    className={`relative cursor-pointer ${
                      arrasto?.modo === "mover" && arrasto.hoverDiaIso === colIso
                        ? "bg-violet-50/60 dark:bg-violet-950/20"
                        : ehHoje
                          ? "bg-amber-50/40 dark:bg-amber-950/10"
                          : "bg-white dark:bg-gray-800"
                    }`}
                    data-agenda-semana-dia={colIso}
                    data-agenda-grade
                    style={{ height: gridH }}
                    onClick={(e) => {
                      if (deveIgnorarClick()) return;
                      if ((e.target as HTMLElement).closest("[data-agenda-card]")) return;
                      const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                      const y = e.clientY - rect.top;
                      const mins = snapMinutos(minMin + y / pxPerMin);
                      onSlotClick(slotDateFromMinutes(colIso, mins), profSlot);
                    }}
                  >
                    {horas.map((m) => (
                      <div
                        key={m}
                        className="absolute left-0 right-0 pointer-events-none"
                        style={{ top: (m - minMin) * pxPerMin }}
                      >
                        <span
                          className={`absolute left-1.5 text-[10px] tabular-nums text-gray-400 dark:text-gray-500 leading-none ${
                            m >= maxMin ? "-translate-y-full" : "pt-0.5"
                          }`}
                        >
                          {minutesToHm(m)}
                        </span>
                        <div
                          className="border-t border-gray-100 dark:border-gray-700/80"
                          style={{ marginLeft: TIME_COL_W }}
                        />
                      </div>
                    ))}
                    {agoraVisivel && sameDayIso(agora, colIso) ? (
                      <div
                        className="absolute z-10 h-px bg-red-500 pointer-events-none"
                        style={{ top: agoraTop, left: TIME_COL_W, right: 0 }}
                      />
                    ) : null}
                    {items.map(({ item: { evt, start, end }, lane, lanes }) => {
                      const startMin = start.getHours() * 60 + start.getMinutes();
                      const endMin = Math.max(startMin + 15, end.getHours() * 60 + end.getMinutes());
                      const top = (startMin - minMin) * pxPerMin;
                      const resizing = arrasto?.modo === "resize" && arrasto.evt.id === evt.id;
                      const durationMin = resizing ? arrasto.durationMin : Math.max(15, endMin - startMin);
                      const height = Math.max(36, durationMin * pxPerMin - 4);
                      const intervalo = Boolean(evt.extendedProps?.isIntervalo);
                      const bloqueio = Boolean(evt.extendedProps?.isBloqueio);
                      const estilo = estiloCardStatusAgenda(evt);
                      const arrastandoEste = arrasto?.modo === "mover" && arrasto.evt.id === evt.id && arrasto.moved;
                      const fimPreview = new Date(start.getTime() + durationMin * 60_000);
                      return (
                        <div
                          key={evt.id}
                          role="button"
                          tabIndex={0}
                          data-agenda-card
                          data-agenda-card-id={evt.id}
                          onPointerDown={(e) => {
                            if (e.button !== 0) return;
                            if (intervalo || bloqueio) return;
                            if ((e.target as HTMLElement).closest("[data-agenda-resize]")) return;
                            iniciarMover(evt, start, end, e);
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            if (deveIgnorarClick() || intervalo) return;
                            if ((e.target as HTMLElement).closest("[data-agenda-resize]")) return;
                            onOpenEvent(evt);
                          }}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              if (!intervalo) onOpenEvent(evt);
                            }
                          }}
                          className={`absolute z-[1] rounded-lg text-left overflow-hidden px-2 py-1.5 touch-none ${
                            arrastandoEste ? "opacity-40" : ""
                          }`}
                          style={{
                            top,
                            height,
                            left: `calc(${TIME_COL_W}px + ${lane} * ((100% - ${TIME_COL_W + 6}px) / ${lanes}))`,
                            width: `calc((100% - ${TIME_COL_W + 6}px) / ${lanes} - 4px)`,
                            ...estiloInlineCardAgenda(evt),
                            cursor: intervalo || bloqueio ? "default" : "grab",
                          }}
                        >
                          <div className="flex items-start justify-between gap-1">
                            <p className="text-[11px] tabular-nums text-gray-600">
                              {formatClinicaHora(start)} - {formatClinicaHora(fimPreview)}
                            </p>
                            {height > 42 || bloqueio ? (
                              <span
                                className="text-[10px] font-semibold leading-none px-1.5 py-0.5 rounded-full text-white shrink-0 max-w-[5.5rem] truncate"
                                style={{ backgroundColor: estilo.cor }}
                              >
                                {rotuloStatusCardAgenda(evt)}
                              </span>
                            ) : (
                              <span
                                className="mt-0.5 w-2.5 h-2.5 rounded-full shrink-0 ring-2 ring-white"
                                style={{ backgroundColor: estilo.cor }}
                                title={rotuloStatusCardAgenda(evt)}
                              />
                            )}
                          </div>
                          <p className="text-xs font-semibold text-gray-900 truncate leading-tight">{tituloCardAgenda(evt)}</p>
                          {height > 56 ? (
                            <p className="text-[11px] text-gray-500 truncate">{subtituloCard(evt)}</p>
                          ) : null}
                          {!intervalo && !bloqueio ? (
                            <span
                              data-agenda-resize
                              className="absolute left-0 right-0 bottom-0 h-4 cursor-ns-resize flex items-end justify-center pb-0.5"
                              title="Arraste para alterar a duração"
                              onPointerDown={(e) => {
                                if (e.button !== 0) return;
                                e.preventDefault();
                                e.stopPropagation();
                                iniciarResize(evt, start, end, e);
                              }}
                              onClick={(e) => e.stopPropagation()}
                            >
                              <span className="block w-8 h-1 rounded-full bg-black/20" />
                            </span>
                          ) : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <AgendaLateralDireita
          dateIso={dateIso}
          onDateChange={onDateChange}
          eventos={eventos}
          selectedProfessional={selectedProfessional}
          hoverDiaIso={arrasto?.modo === "mover" ? arrasto.hoverDiaIso : null}
          deveIgnorarClick={deveIgnorarClick}
          onOpenEvent={onOpenEvent}
          expandToFill={hasCustomWidths}
        />
      </div>

      {arrasto?.modo === "mover" && arrasto.moved && typeof document !== "undefined"
        ? createPortal(
            <div
              data-agenda-ghost
              className="pointer-events-none fixed z-[80] w-56 rounded-lg px-2.5 py-1.5 shadow-lg border border-violet-200"
              style={{
                left: arrasto.x + 12,
                top: arrasto.y - 8,
                backgroundColor: estiloCardStatusAgenda(arrasto.evt).backgroundColor,
                borderLeft: estiloCardStatusAgenda(arrasto.evt).borderLeft,
              }}
            >
              <p className="text-[11px] tabular-nums text-gray-600">
                {formatClinicaHora(arrasto.start)} - {formatClinicaHora(arrasto.end)}
              </p>
              <p className="text-xs font-semibold text-gray-900 truncate">{tituloCardAgenda(arrasto.evt)}</p>
              {arrasto.hoverDiaIso && arrasto.hoverDiaIso !== dateIso ? (
                <p className="text-[11px] text-violet-700 mt-0.5">
                  Mover para {arrasto.hoverDiaIso.split("-").reverse().join("/")}
                </p>
              ) : null}
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
