import { describe, expect, it } from "vitest";
import {
  intervalosEventsFromHorarios,
  isWithinWorkHours,
  weekdayFromDate,
  workHoursRejectionMessage,
  type HorarioTrabalho,
} from "./clinica-beleza-work-hours";

const expediente: HorarioTrabalho = {
  dia_semana: 0,
  hora_entrada: "08:00",
  hora_saida: "18:00",
  intervalo_inicio: "12:00",
  intervalo_fim: "13:00",
  ativo: true,
};

describe("expediente da agenda", () => {
  const segunda = new Date(2026, 9, 12, 10, 0);

  it("segunda-feira é o dia 0", () => {
    expect(weekdayFromDate(segunda)).toBe(0);
  });

  it("aceita horário dentro do expediente e recusa o intervalo", () => {
    expect(isWithinWorkHours(segunda, 30, [expediente])).toBe(true);
    expect(isWithinWorkHours(new Date(2026, 9, 12, 12, 15), 30, [expediente])).toBe(false);
    expect(isWithinWorkHours(segunda, 30, [])).toBe(true);
  });

  it("explica quando o profissional não trabalha ou está no intervalo", () => {
    expect(workHoursRejectionMessage(new Date(2026, 9, 13, 10, 0), 30, [expediente])).toContain(
      "não trabalha",
    );
    expect(workHoursRejectionMessage(new Date(2026, 9, 12, 12, 15), 30, [expediente])).toContain(
      "intervalo",
    );
  });
});

describe("intervalos na agenda", () => {
  it("marca o intervalo com o profissional para cair na coluna certa", () => {
    const eventos = intervalosEventsFromHorarios("7", [expediente], "Marina", 7);
    const segunda = eventos.find((ev) => ev.start.includes("T12:00"));
    expect(segunda?.extendedProps.professional).toBe(7);
    expect(segunda?.extendedProps.isIntervalo).toBe(true);
    expect(segunda?.extendedProps.professional_name).toBe("Marina");
  });

  it("não desenha intervalo quando o horário está zerado", () => {
    const eventos = intervalosEventsFromHorarios(
      "1",
      [{ ...expediente, intervalo_inicio: "00:00", intervalo_fim: "00:00" }],
      "Nayara",
      7,
    );
    expect(eventos).toEqual([]);
  });
});
