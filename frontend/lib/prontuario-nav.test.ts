import { describe, expect, it } from "vitest";
import {
  CLINICA_BELEZA_NAV_ITEMS,
  isClinicaBelezaNavActive,
  navItemsClinicaBeleza,
  usuarioPodeVerConsulta,
} from "@/components/clinica-beleza/clinica-beleza-nav";
import {
  buildProntuarioAgendamentoPath,
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

  it("monta ficha a partir do paciente do agendamento", () => {
    expect(buildProntuarioAgendamentoPath("clinicaharmonis", 9)).toBe(
      "/loja/clinicaharmonis/clinica-beleza/pacientes/9/prontuario",
    );
    expect(buildProntuarioAgendamentoPath("clinicaharmonis", "12")).toBe(
      "/loja/clinicaharmonis/clinica-beleza/pacientes/12/prontuario",
    );
    expect(buildProntuarioAgendamentoPath("", 9)).toBe(null);
    expect(buildProntuarioAgendamentoPath("clinicaharmonis", 0)).toBe(null);
    expect(buildProntuarioAgendamentoPath("clinicaharmonis", undefined)).toBe(null);
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
    expect(CLINICA_BELEZA_NAV_ITEMS.map((i) => i.label)).toContain("Financeiro");
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

  it("esconde Consultas para recepção e mantém para profissional/admin", () => {
    expect(usuarioPodeVerConsulta({ perfil: "recepcionista" })).toBe(false);
    expect(usuarioPodeVerConsulta({ perfil: "recepcao" })).toBe(false);
    expect(usuarioPodeVerConsulta({ perfil: "profissional" })).toBe(true);
    expect(usuarioPodeVerConsulta({ is_administrador: true, perfil: "recepcionista" })).toBe(true);
    expect(usuarioPodeVerConsulta({ pode_ver_consulta: false, perfil: "profissional" })).toBe(false);
    expect(navItemsClinicaBeleza(false).map((i) => i.label)).not.toContain("Consultas");
    expect(navItemsClinicaBeleza(true).map((i) => i.label)).toContain("Consultas");
    expect(navItemsClinicaBeleza(false).map((i) => i.label)).toContain("Agenda");
  });
});
