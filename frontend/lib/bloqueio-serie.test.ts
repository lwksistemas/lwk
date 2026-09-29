import { describe, expect, it } from "vitest";
import { serieBloqueioDiaInteiro } from "@/lib/bloqueio-serie";

function dia(id: number, ano: number, mes: number, diaMes: number) {
  const inicio = new Date(ano, mes - 1, diaMes, 0, 0, 0);
  const fim = new Date(ano, mes - 1, diaMes, 23, 59, 59);
  return {
    id,
    professional: 6,
    motivo: "Férias do profissional",
    data_inicio: inicio.toISOString(),
    data_fim: fim.toISOString(),
  };
}

describe("serieBloqueioDiaInteiro", () => {
  it("junta os dias seguidos das férias e deixa o dia isolado de fora", () => {
    const outubro = [dia(1, 2026, 10, 1), dia(2, 2026, 10, 2), dia(3, 2026, 10, 3)];
    const novembro = dia(9, 2026, 11, 16);
    const serie = serieBloqueioDiaInteiro([...outubro, novembro], 2);
    expect(serie.map((b) => b.id)).toEqual([1, 2, 3]);
    expect(serieBloqueioDiaInteiro([...outubro, novembro], 9).map((b) => b.id)).toEqual([9]);
  });
});
