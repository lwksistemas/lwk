import { describe, expect, it } from "vitest";
import { duracaoSlotAgenda, intervaloAgendaMinutos } from "./intervalo-agenda";

describe("intervaloAgendaMinutos", () => {
  it("usa 15 quando o profissional não tem intervalo", () => {
    expect(intervaloAgendaMinutos(null)).toBe(15);
    expect(intervaloAgendaMinutos({})).toBe(15);
    expect(intervaloAgendaMinutos({ intervalo_agenda_minutos: null })).toBe(15);
  });

  it("usa o intervalo do profissional quando está na lista", () => {
    expect(intervaloAgendaMinutos({ intervalo_agenda_minutos: 30 })).toBe(30);
    expect(intervaloAgendaMinutos({ intervalo_agenda_minutos: 7 })).toBe(15);
  });

  it("formata 60 minutos como uma hora", () => {
    expect(duracaoSlotAgenda(15)).toBe("00:15:00");
    expect(duracaoSlotAgenda(60)).toBe("01:00:00");
  });
});
