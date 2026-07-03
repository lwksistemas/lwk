import { describe, expect, it } from "vitest";
import {
  MENSAGEM_WHATSAPP_PADRAO,
  MENSAGEM_WHATSAPP_PLACEHOLDERS,
} from "@/components/clinica-beleza/consultas/mensagens-whatsapp-agenda/mensagens-whatsapp-agenda-constants";

describe("MENSAGEM_WHATSAPP_PLACEHOLDERS", () => {
  it("inclui variáveis essenciais", () => {
    expect(MENSAGEM_WHATSAPP_PLACEHOLDERS).toContain("{nome}");
    expect(MENSAGEM_WHATSAPP_PLACEHOLDERS).toContain("{link}");
  });
});

describe("MENSAGEM_WHATSAPP_PADRAO", () => {
  it("usa todos os placeholders", () => {
    for (const ph of MENSAGEM_WHATSAPP_PLACEHOLDERS) {
      expect(MENSAGEM_WHATSAPP_PADRAO).toContain(ph);
    }
  });
});
