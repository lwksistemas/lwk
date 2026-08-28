import { describe, expect, it } from "vitest";
import { homePathForTipo, isTipoClinicaBeleza } from "@/lib/loja-tipo";

describe("Clínica da Beleza — home", () => {
  it("abre o prontuário em vez da lista de consultas", () => {
    expect(isTipoClinicaBeleza("Clínica da Beleza")).toBe(true);
    expect(homePathForTipo("clinicaharmonis", "Clínica da Beleza")).toBe(
      "/loja/clinicaharmonis/clinica-beleza/prontuario",
    );
  });
});
