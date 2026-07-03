import { describe, expect, it } from "vitest";
import {
  buildCampanhaDestinoLabel,
  pacienteCampanhaElegivel,
  pacienteCampanhaTelefone,
} from "@/components/clinica-beleza/campanha-enviar-modal/campanha-enviar-modal-types";

describe("pacienteCampanhaTelefone", () => {
  it("prefere telefone sobre phone", () => {
    expect(pacienteCampanhaTelefone({ id: 1, telefone: " 11999 ", phone: "11888" })).toBe("11999");
    expect(pacienteCampanhaTelefone({ id: 1, phone: "11888" })).toBe("11888");
  });
});

describe("pacienteCampanhaElegivel", () => {
  it("exige ativo, whatsapp e telefone", () => {
    expect(pacienteCampanhaElegivel({ id: 1, is_active: false, telefone: "1" })).toBe(false);
    expect(pacienteCampanhaElegivel({ id: 1, allow_whatsapp: false, telefone: "1" })).toBe(false);
    expect(pacienteCampanhaElegivel({ id: 1, telefone: "" })).toBe(false);
    expect(pacienteCampanhaElegivel({ id: 1, telefone: "11999" })).toBe(true);
  });
});

describe("buildCampanhaDestinoLabel", () => {
  it("formata destino por modo", () => {
    expect(buildCampanhaDestinoLabel("todos", 10, 0)).toContain("10");
    expect(buildCampanhaDestinoLabel("segmentacao", 10, 3)).toContain("3");
  });
});
