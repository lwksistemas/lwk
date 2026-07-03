import { describe, expect, it } from "vitest";
import {
  mensagemEstoqueInsuficiente,
  totalPorProduto,
} from "@/components/clinica-beleza/consultas/produtos/produtos-utils";
import type { ConsultaProdutoItem } from "@/components/clinica-beleza/consultas/produtos/produtos-types";

const item = (id: number, produto: number, qtd: number, baixado = false): ConsultaProdutoItem => ({
  id,
  produto,
  produto_nome: `Produto ${produto}`,
  quantidade: qtd,
  lote: "",
  validade: null,
  estoque_baixado: baixado,
});

describe("totalPorProduto", () => {
  it("soma quantidades por produto ignorando baixados", () => {
    const map = totalPorProduto([item(1, 10, 2), item(2, 10, 3), item(3, 20, 1, true)]);
    expect(map.get(10)).toBe(5);
    expect(map.has(20)).toBe(false);
  });
});

describe("mensagemEstoqueInsuficiente", () => {
  it("formata mensagem com unidade", () => {
    expect(mensagemEstoqueInsuficiente("Soro", 5, 2, "ml")).toBe(
      "Soro: necessário 5 ml, disponível 2 ml.",
    );
  });
});
