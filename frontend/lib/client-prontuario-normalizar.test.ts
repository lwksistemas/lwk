import { describe, expect, it } from "vitest";
import { normalizarDocItem } from "./clinica-beleza-api/client-prontuario";

describe("normalizarDocItem (prontuário)", () => {
  it("mapeia prescricao_memed do backend para source=memed", () => {
    // Formato REAL do backend (ProntuarioSectionSerializer._serialize_prescricao)
    const raw = {
      id: 9,
      tipo: "receituario",
      titulo: "Nebacetin",
      conteudo: "Nebacetin, Pomada dermatológica",
      profissional_nome: "NAYARA",
      consulta_id: null,
      data: "2026-09-09T13:00:00",
      tipo_fonte: "prescricao_memed",
      pdf_url: "",
    };
    const out = normalizarDocItem(raw);
    expect(out.source).toBe("memed");
    expect(out.professional_name).toBe("NAYARA");
    expect(out.created_at).toBe("2026-09-09T13:00:00");
    // id preservado (usado no endpoint /prescricoes-memed/{id}/pdf/)
    expect(out.id).toBe(9);
  });

  it("mapeia documento_clinico para source=documento_clinico", () => {
    const raw = {
      id: 3,
      tipo: "atestado",
      profissional_nome: "Dr. X",
      data: "2026-09-01T10:00:00",
      tipo_fonte: "documento_clinico",
    };
    const out = normalizarDocItem(raw);
    expect(out.source).toBe("documento_clinico");
    expect(out.professional_name).toBe("Dr. X");
    expect(out.created_at).toBe("2026-09-01T10:00:00");
  });

  it("preserva campos já no formato do app (idempotente)", () => {
    const raw = {
      id: 1,
      source: "memed",
      professional_name: "Y",
      created_at: "2026-01-01T00:00:00",
    };
    const out = normalizarDocItem(raw);
    expect(out.source).toBe("memed");
    expect(out.professional_name).toBe("Y");
    expect(out.created_at).toBe("2026-01-01T00:00:00");
  });
});
