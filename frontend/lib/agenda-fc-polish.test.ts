import { describe, expect, it, beforeEach } from "vitest";
import {
  idsEventosSimultaneosOutrosProf,
  idsEventosSobrepostosMesmoProf,
} from "@/hooks/clinica-beleza/agenda-data/agenda-fc-event-content";
import type { AgendaEventData } from "@/lib/clinica-beleza-agenda-types";
import {
  defaultAgendaFetchRange,
  getAgendaFetchRange,
  resetAgendaFetchRange,
  syncAgendaFetchRangeToVisible,
} from "@/lib/clinica-beleza-cadastros-api";
import { normalizeAgendaVisual, AGENDA_VISUAL_DEFAULT } from "@/lib/clinica-agenda-visual";

function ev(
  id: string,
  start: string,
  end: string,
  professional: number,
  extras: Partial<AgendaEventData["extendedProps"]> = {},
): AgendaEventData {
  return {
    id,
    title: `Ev ${id}`,
    start,
    end,
    backgroundColor: "#a855f7",
    borderColor: "#9333ea",
    textColor: "#fff",
    extendedProps: {
      status: "SCHEDULED",
      professional,
      patient_name: `Paciente ${id}`,
      ...extras,
    },
  };
}

describe("conflito vs simultâneo", () => {
  it("marca conflito só com o mesmo profissional", () => {
    const eventos = [
      ev("1", "2026-11-02T10:00:00", "2026-11-02T11:00:00", 1),
      ev("2", "2026-11-02T10:30:00", "2026-11-02T11:30:00", 1),
      ev("3", "2026-11-02T10:00:00", "2026-11-02T11:00:00", 2),
    ];
    const conflito = idsEventosSobrepostosMesmoProf(eventos);
    expect(conflito.has("1")).toBe(true);
    expect(conflito.has("2")).toBe(true);
    expect(conflito.has("3")).toBe(false);
  });

  it("marca simultâneo entre profissionais diferentes", () => {
    const eventos = [
      ev("1", "2026-11-02T10:00:00", "2026-11-02T11:00:00", 1),
      ev("2", "2026-11-02T10:30:00", "2026-11-02T11:30:00", 2),
      ev("3", "2026-11-02T14:00:00", "2026-11-02T15:00:00", 1),
    ];
    const sim = idsEventosSimultaneosOutrosProf(eventos);
    expect(sim.has("1")).toBe(true);
    expect(sim.has("2")).toBe(true);
    expect(sim.has("3")).toBe(false);
  });

  it("não trata bloqueio como conflito de cliente", () => {
    const eventos = [
      ev("1", "2026-11-02T10:00:00", "2026-11-02T11:00:00", 1, { isBloqueio: true }),
      ev("2", "2026-11-02T10:30:00", "2026-11-02T11:30:00", 1),
    ];
    expect(idsEventosSobrepostosMesmoProf(eventos).size).toBe(0);
  });
});

describe("janela de carga da agenda", () => {
  beforeEach(() => {
    resetAgendaFetchRange(defaultAgendaFetchRange(new Date(2026, 10, 2)));
  });

  it("não refetch se o período visível cabe na janela com margem", () => {
    // Interior da janela padrão (21 atrás ↔ 45 à frente a partir de 2026-11-02)
    expect(syncAgendaFetchRangeToVisible("2026-11-02", "2026-11-09")).toBe(false);
    expect(getAgendaFetchRange().start).toBe("2026-10-12");
  });

  it("expande a janela ao navegar para fora da margem", () => {
    expect(syncAgendaFetchRangeToVisible("2025-01-01", "2025-01-31")).toBe(true);
    const next = getAgendaFetchRange();
    expect(next.start <= "2025-01-01").toBe(true);
    expect(next.end >= "2025-01-31").toBe(true);
  });
});

describe("normalizeAgendaVisual", () => {
  it("aceita os cinco estilos e cai no padrão", () => {
    expect(normalizeAgendaVisual("pulse")).toBe("pulse");
    expect(normalizeAgendaVisual("breezy")).toBe("breezy");
    expect(normalizeAgendaVisual("monarch")).toBe("monarch");
    expect(normalizeAgendaVisual("forma")).toBe("forma");
    expect(normalizeAgendaVisual("classic")).toBe("classic");
    expect(normalizeAgendaVisual("x")).toBe(AGENDA_VISUAL_DEFAULT);
  });
});
