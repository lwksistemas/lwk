import { describe, expect, it } from "vitest";
import {
  CLINICA_BELEZA_NAV_ITEMS,
  isClinicaBelezaNavActive,
} from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  buildProntuarioHubPath,
  buildProntuarioPacientePath,
  isProntuarioPacientePath,
} from "@/components/clinica-beleza/prontuario/prontuario-paths";

describe("prontuario paths", () => {
  it("monta hub e ficha", () => {
    expect(buildProntuarioHubPath("clinicaharmonis")).toBe(
      "/loja/clinicaharmonis/clinica-beleza/prontuario",
    );
    expect(buildProntuarioPacientePath("clinicaharmonis", 9)).toBe(
      "/loja/clinicaharmonis/clinica-beleza/pacientes/9/prontuario",
    );
  });

  it("reconhece path da ficha", () => {
    expect(
      isProntuarioPacientePath("/loja/clinicaharmonis/clinica-beleza/pacientes/9/prontuario", "clinicaharmonis"),
    ).toBe(true);
    expect(
      isProntuarioPacientePath("/loja/clinicaharmonis/clinica-beleza/prontuario", "clinicaharmonis"),
    ).toBe(false);
  });
});

describe("nav consultas", () => {
  it("mostra Consultas no menu no lugar do hub Prontuário", () => {
    expect(CLINICA_BELEZA_NAV_ITEMS.map((i) => i.label)).toContain("Consultas");
    expect(CLINICA_BELEZA_NAV_ITEMS.map((i) => i.label)).not.toContain("Prontuário");
  });

  it("marca ativo na lista, na ficha e no hub legado", () => {
    const slug = "clinicaharmonis";
    const path = "clinica-beleza/consultas";
    expect(isClinicaBelezaNavActive("/loja/clinicaharmonis/clinica-beleza/consultas", slug, path)).toBe(
      true,
    );
    expect(
      isClinicaBelezaNavActive("/loja/clinicaharmonis/clinica-beleza/pacientes/3/prontuario", slug, path),
    ).toBe(true);
    expect(isClinicaBelezaNavActive("/loja/clinicaharmonis/clinica-beleza/prontuario", slug, path)).toBe(
      true,
    );
    expect(isClinicaBelezaNavActive("/loja/clinicaharmonis/clinica-beleza/pacientes", slug, path)).toBe(
      false,
    );
  });
});
