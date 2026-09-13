import { describe, expect, it } from "vitest";
import {
  filtrarProcedimentosPorCategoria,
  listarCategoriasProcedimento,
} from "./procedimento-categoria-filtro";

const itens = [
  { id: 1, nome: "Vitamina C", categoria: "soroterapia" },
  { id: 2, nome: "Botox", categoria: "injetavel" },
  { id: 3, nome: "Peeling", categoria: "facial" },
  { id: 4, nome: "Outro soro", categoria: "soroterapia" },
];

describe("listarCategoriasProcedimento", () => {
  it("conta e ordena pelas categorias com mais itens", () => {
    const cards = listarCategoriasProcedimento(itens);
    expect(cards[0]).toEqual({ value: "soroterapia", label: "Soroterapia", count: 2 });
    expect(cards.map((c) => c.value)).toEqual(["soroterapia", "facial", "injetavel"]);
  });
});

describe("filtrarProcedimentosPorCategoria", () => {
  it("devolve todos sem filtro e só a categoria ativa com filtro", () => {
    expect(filtrarProcedimentosPorCategoria(itens, "")).toHaveLength(4);
    expect(filtrarProcedimentosPorCategoria(itens, "soroterapia").map((p) => p.id)).toEqual([1, 4]);
  });
});
