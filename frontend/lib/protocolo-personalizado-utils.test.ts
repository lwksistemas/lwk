import { describe, expect, it } from "vitest";
import { aplicarDescontoProtocolo } from "@/components/clinica-beleza/prontuario/protocolo-personalizado-utils";
import { dividirValorProtocolo } from "@/components/clinica-beleza/protocolos-page/protocolos-page-utils";

describe("protocolo personalizado", () => {
  it("tira 10% de 3650 e divide 3285 em 5 sessões", () => {
    const { desconto, liquido } = aplicarDescontoProtocolo(3650, "percentual", 10);
    expect(desconto).toBe(365);
    expect(liquido).toBe(3285);
    expect(dividirValorProtocolo(liquido, 5, "POR_CONSULTA")).toEqual([657, 657, 657, 657, 657]);
  });

  it("desconto fixo não passa da soma", () => {
    expect(aplicarDescontoProtocolo(150, "fixo", 200)).toEqual({ desconto: 150, liquido: 0 });
  });

  it("pagar tudo deixa o pacote na primeira sessão", () => {
    expect(dividirValorProtocolo(3285, 5, "TOTAL")).toEqual([3285, 0, 0, 0, 0]);
  });
});
