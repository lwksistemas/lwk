import { describe, expect, it } from "vitest";
import {
  buildHorariosSavePayload,
  createDefaultHorarioRows,
  mergeHorariosFromApi,
} from "@/components/clinica-beleza/horarios-trabalho-modal/horarios-trabalho-modal-utils";

describe("createDefaultHorarioRows", () => {
  it("cria 7 dias com seg-sex ativos", () => {
    const rows = createDefaultHorarioRows();
    expect(Object.keys(rows)).toHaveLength(7);
    expect(rows[0].ativo).toBe(true);
    expect(rows[5].ativo).toBe(false);
  });
});

describe("mergeHorariosFromApi", () => {
  it("mescla dados da API", () => {
    const merged = mergeHorariosFromApi([
      { id: 1, dia_semana: 0, hora_entrada: "09:00:00", hora_saida: "17:00:00", intervalo_inicio: null, intervalo_fim: null, ativo: true },
    ]);
    expect(merged[0].hora_entrada).toBe("09:00");
    expect(merged[0].ativo).toBe(true);
    expect(merged[1].ativo).toBe(false);
  });
});

describe("buildHorariosSavePayload", () => {
  it("retorna só dias ativos", () => {
    const rows = createDefaultHorarioRows();
    const payload = buildHorariosSavePayload(rows);
    expect(payload.length).toBe(5);
    expect(payload[0].dia_semana).toBe(0);
  });
});
