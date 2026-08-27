"use client";

import { useEffect, useMemo } from "react";
import { createPortal } from "react-dom";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import type { ClinicaProfessional } from "@/lib/clinica-beleza-entities";
import { formatClinicaHora } from "@/lib/clinica-beleza-datetime";
import {
  addDaysIso,
  colunasProfissionaisDia,
  eventosDoDiaNaColuna,
  horasGradeAgenda,
  minutesToHm,
  parseHmToMinutes,
  sameDayIso,
  slotDateFromMinutes,
  snapMinutos,
  estiloCardStatusAgenda,
  estiloInlineCardAgenda,
  rotuloStatusCardAgenda,
  capitalizarAgenda,
  tituloCardAgenda,
  toAgendaDiaIso,
} from "@/hooks/clinica-beleza/agenda-data/agenda-dia-colunas-utils";
import { AlcaLarguraColuna, useAgendaColunaLargura } from "./useAgendaColunaLargura";
import { useAgendaDiaArrasto } from "./useAgendaDiaArrasto";
import { AgendaLateralDireita } from "./AgendaLateralDireita";

const PX_PER_HOUR = 72;
const COL_MIN_WIDTH = 280;
const TIME_COL_W = 44;
const DIA_ACCENT = "#7c3aed";

function subtituloCard(evt: AgendaEventData): string {
  const p = evt.extendedProps || {};
  if (p.isBloqueio) return "Bloqueio";
  if (p.isIntervalo) return "Intervalo";
  return p.procedure_name || "";
}

export function AgendaDiaColunas({
  dateIso,
  onDateChange,
  eventos,
  professionals,
  selectedProfessional,
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
  professionals: ClinicaProfessional[];
  selectedProfessional: string;
  slotMinTime: string;
  slotMaxTime: string;
  onOpenEvent: (evt: AgendaEventData) => void;
  onSlotClick: (date: Date, professionalId: number) => void;
  onMudarVisao: (view: "week" | "month") => void;
  onMover?: (evt: AgendaEventData, start: Date, professionalId: number) => void;
  onRedimensionar?: (evt: AgendaEventData, duracaoMinutos: number) => void;
  onArrastoAtivo?: (ativo: boolean) => void;
}) {
  const minMin = parseHmToMinutes(slotMinTime);
  const maxMin = Math.max(minMin + 60, parseHmToMinutes(slotMaxTime));
  const totalMin = maxMin - minMin;
  const pxPerMin = PX_PER_HOUR / 60;
  const gridH = totalMin * pxPerMin;
  const colunas = useMemo(
    () => colunasProfissionaisDia(professionals, selectedProfessional),
    [professionals, selectedProfessional],
  );

  const horas = useMemo(() => horasGradeAgenda(minMin, maxMin), [minMin, maxMin]);

  const agora = new Date();
  const mostrarAgora = sameDayIso(agora, dateIso);
  const agoraMin = agora.getHours() * 60 + agora.getMinutes();
  const agoraTop = (agoraMin - minMin) * pxPerMin;
  const agoraVisivel = mostrarAgora && agoraMin >= minMin && agoraMin <= maxMin;

  const { tituloData, weekday } = useMemo(() => {
    const [y, mo, d] = dateIso.split("-").map(Number);
    const ref = new Date(y, (mo || 1) - 1, d || 1);
    return {
      tituloData: ref.toLocaleDateString("pt-BR", {
        day: "numeric",
        month: "long",
        year: "numeric",
      }),
            weekday: capitalizarAgenda(ref.toLocaleDateString("pt-BR", { weekday: "long" })),
    };
  }, [dateIso]);

  const hojeIso = toAgendaDiaIso(new Date());
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
  } = useAgendaColunaLargura("agenda-col-w-dia", COL_MIN_WIDTH);
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
            onClick={() => onDateChange(addDaysIso(dateIso, -1))}
            aria-label="Dia anterior"
          >
            ‹
          </button>
          <button
            type="button"
            className="w-8 h-8 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
            onClick={() => onDateChange(addDaysIso(dateIso, 1))}
            aria-label="Próximo dia"
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
            {tituloData}
          </h2>
          <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{weekday}</p>
        </div>
        <div className="flex justify-end">
          <div className="inline-flex items-center rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 text-sm">
            <span
              className="px-3 py-1.5 font-medium text-white"
              style={{ backgroundColor: DIA_ACCENT }}
            >
              Dia
            </span>
            <button
              type="button"
              className="px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50"
              onClick={() => onMudarVisao("week")}
            >
              Semana
            </button>
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

      {colunas.length === 0 ? (
        <p className="text-center text-sm text-gray-500 py-12">Nenhum profissional na agenda.</p>
      ) : (
        <div className="flex flex-1 min-h-0">
          <div className="flex-1 min-h-0 overflow-auto agenda-scroll-root">
            <div
              className="grid h-full min-w-full"
              style={{
                gridTemplateColumns: colunas.map((col) => template(`prof-${col.id}`)).join(" "),
              }}
            >
              {colunas.map((col) => {
                const items = eventosDoDiaNaColuna(eventos, dateIso, col.id);
                const colKey = `prof-${col.id}`;
                return (
                  <div
                    key={col.id}
                    data-agenda-col-wrap
                    className="relative flex flex-col border-r border-gray-200 dark:border-gray-700 min-w-0"
                  >
                    <AlcaLarguraColuna onPointerDown={(e) => iniciarLargura(colKey, e)} />
                    <div className="sticky top-0 z-20 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-3 py-2.5">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <span
                          className="shrink-0 w-9 h-9 rounded-full text-white text-xs font-bold flex items-center justify-center"
                          style={{ backgroundColor: col.cor }}
                        >
                          {col.iniciais}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-[11px] sm:text-xs font-semibold text-gray-900 dark:text-gray-100 truncate uppercase tracking-wide">
                            {col.nome}
                          </p>
                          {col.especialidade ? (
                            <p className="text-[11px] text-gray-500 dark:text-gray-400 truncate flex items-center gap-1.5">
                              <span
                                className="inline-block w-1.5 h-1.5 rounded-full shrink-0"
                                style={{ backgroundColor: col.cor }}
                              />
                              {col.especialidade}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    </div>
                    <div
                      className={`relative bg-white dark:bg-gray-800 cursor-pointer ${
                        arrasto?.modo === "mover" && arrasto.hoverProfessionalId === col.id
                          ? "bg-violet-50/60 dark:bg-violet-950/20"
                          : ""
                      }`}
                      data-agenda-coluna={col.id}
                      data-agenda-grade
                      style={{ height: gridH }}
                      onClick={(e) => {
                        if (deveIgnorarClick()) return;
                        if ((e.target as HTMLElement).closest("[data-agenda-card]")) return;
                        const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
                        const y = e.clientY - rect.top;
                        const mins = snapMinutos(minMin + y / pxPerMin);
                        onSlotClick(slotDateFromMinutes(dateIso, mins), col.id);
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
                      {agoraVisivel ? (
                        <div
                          className="absolute z-10 h-px bg-red-500 pointer-events-none"
                          style={{ top: agoraTop, left: TIME_COL_W, right: 0 }}
                        />
                      ) : null}
                      {items.map(({ evt, start, end }) => {
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
                              iniciarMover(evt, start, end, e);
                            }}
                            onClick={(e) => {
                              e.stopPropagation();
                              if (deveIgnorarClick() || intervalo) return;
                              onOpenEvent(evt);
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                if (!intervalo) onOpenEvent(evt);
                              }
                            }}
                            className={`absolute z-[1] rounded-lg text-left overflow-hidden px-2.5 py-1.5 touch-none ${
                              arrastandoEste ? "opacity-40" : ""
                            }`}
                            style={{
                              top,
                              height,
                              left: TIME_COL_W,
                              right: 6,
                              ...estiloInlineCardAgenda(evt),
                              cursor: intervalo || bloqueio ? "default" : "grab",
                            }}
                          >
                            <div className="flex items-start justify-between gap-1">
                              <p className="text-[11px] tabular-nums text-gray-600 dark:text-gray-700">
                                {formatClinicaHora(start)} - {formatClinicaHora(fimPreview)}
                              </p>
                              {height > 42 || bloqueio ? (
                                <span
                                  className="text-[10px] font-semibold leading-none px-1.5 py-0.5 rounded-full text-white shrink-0 max-w-[6.5rem] truncate"
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
                            <p className="text-xs font-semibold text-gray-900 truncate leading-tight">
                              {tituloCardAgenda(evt)}
                            </p>
                            {height > 56 ? (
                              <p className="text-[11px] text-gray-500 truncate">
                                {subtituloCard(evt)}
                              </p>
                            ) : null}
                            {!intervalo && !bloqueio ? (
                              <span
                                className="absolute left-0 right-0 bottom-0 h-2.5 cursor-ns-resize flex items-end justify-center pb-0.5"
                                title="Arraste para alterar a duração"
                                onPointerDown={(e) => {
                                  if (e.button !== 0) return;
                                  e.preventDefault();
                                  iniciarResize(evt, start, end, e);
                                }}
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
          />
        </div>
      )}
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
