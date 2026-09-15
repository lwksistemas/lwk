import { describe, expect, it } from "vitest";
import {
  nomeArquivoPedidoPdf,
  numeroPedidoLabel,
  slugNomeArquivo,
} from "@/components/clinica-beleza/estoque/pedido-compra-utils";

describe("pedido-compra-utils", () => {
  it("numero com zero à esquerda", () => {
    expect(numeroPedidoLabel(1)).toBe("01");
    expect(numeroPedidoLabel(12)).toBe("12");
  });

  it("slug do fornecedor em maiúsculas sem acento", () => {
    expect(slugNomeArquivo("PHD DO BRASIL")).toBe("PHD_DO_BRASIL");
    expect(slugNomeArquivo("Farmácia São José")).toBe("FARMACIA_SAO_JOSE");
  });

  it("nome do PDF usa número e fornecedor", () => {
    expect(
      nomeArquivoPedidoPdf({
        numero: 1,
        fornecedor: { nome_fantasia: "PHD DO BRASIL", razao_social: "Outro" },
      }),
    ).toBe("Pedido_01_PHD_DO_BRASIL.pdf");
  });
});
