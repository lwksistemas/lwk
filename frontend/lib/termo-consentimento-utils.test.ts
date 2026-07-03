import { describe, expect, it } from "vitest";
import {
  labelCanalTermo,
  snapshotTermoStatus,
  type TermoProcedimento,
} from "@/components/clinica-beleza/consultas/termo-consentimento/termo-consentimento-types";

const termo = (procedure_id: number, status: string): TermoProcedimento => ({
  id: procedure_id,
  procedure_id,
  procedure_nome: `Proc ${procedure_id}`,
  status,
  status_display: status,
  tem_conteudo: true,
});

describe("snapshotTermoStatus", () => {
  it("concatena procedure_id e status", () => {
    expect(snapshotTermoStatus([termo(1, "rascunho"), termo(2, "concluido")])).toBe(
      "1:rascunho|2:concluido",
    );
  });
});

describe("labelCanalTermo", () => {
  it("formata canais", () => {
    expect(labelCanalTermo("email")).toBe("e-mail");
    expect(labelCanalTermo("whatsapp")).toBe("WhatsApp");
  });
});
