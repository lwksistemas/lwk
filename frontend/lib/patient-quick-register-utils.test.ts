import { describe, expect, it } from "vitest";
import {
  buildPatientQuickSearchQuery,
  filterPatientsLocal,
} from "@/components/clinica-beleza/patient-quick-register/patient-quick-register-utils";

describe("buildPatientQuickSearchQuery", () => {
  it("prioriza CPF, depois telefone, depois nome", () => {
    expect(buildPatientQuickSearchQuery("Ana", "", "12345678901")).toBe("12345678901");
    expect(buildPatientQuickSearchQuery("", "(11) 98765-4321", "")).toBe("11987654321");
    expect(buildPatientQuickSearchQuery("Lu", "", "")).toBe("Lu");
    expect(buildPatientQuickSearchQuery("", "", "")).toBe("");
  });
});

describe("filterPatientsLocal", () => {
  it("limita resultados", () => {
    const patients = Array.from({ length: 50 }, (_, i) => ({
      id: i + 1,
      nome: `Paciente ${i}`,
    }));
    expect(filterPatientsLocal(patients, "Paciente", 10)).toHaveLength(10);
  });
});
