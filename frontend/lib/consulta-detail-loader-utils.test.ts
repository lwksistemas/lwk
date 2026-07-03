import { describe, expect, it } from "vitest";
import type { Consulta } from "@/components/clinica-beleza/consultas/consultas-types";
import {
  extractObservacoesConsulta,
  isTabWithoutRemoteLoad,
  mergeAnamnese,
  mergeConsultaFresh,
  normalizeConsultaList,
  resolveInitialConsultaTab,
  temHistoricoAnterior,
} from "@/hooks/clinica-beleza/consulta-detail-loader/consulta-detail-loader-utils";

const consulta = (overrides: Partial<Consulta> = {}): Consulta =>
  ({
    id: 1,
    patient: 10,
    procedure: 2,
    patient_name: "Paciente",
    professional_name: "Dr.",
    procedure_name: "Botox",
    status: "SCHEDULED",
    ...overrides,
  }) as Consulta;

describe("isTabWithoutRemoteLoad", () => {
  it("ignora abas com carregamento próprio", () => {
    expect(isTabWithoutRemoteLoad("produtos")).toBe(true);
    expect(isTabWithoutRemoteLoad("atendimento")).toBe(false);
  });
});

describe("mergeAnamnese", () => {
  it("preenche defaults vazios", () => {
    const merged = mergeAnamnese({ queixa_principal: "Dor" });
    expect(merged.queixa_principal).toBe("Dor");
    expect(merged.alergias).toBe("");
  });
});

describe("normalizeConsultaList", () => {
  it("retorna array vazio para entrada inválida", () => {
    expect(normalizeConsultaList(null)).toEqual([]);
  });
});

describe("extractObservacoesConsulta", () => {
  it("prioriza observacoes_gerais", () => {
    expect(
      extractObservacoesConsulta(
        consulta({ observacoes_gerais: "Obs geral", protocolo_notas: "Notas" }),
      ),
    ).toBe("Obs geral");
  });
});

describe("resolveInitialConsultaTab", () => {
  it("abre histórico para agendada com retorno", () => {
    expect(resolveInitialConsultaTab("SCHEDULED", 2)).toBe("historico");
  });

  it("abre atendimento por padrão", () => {
    expect(resolveInitialConsultaTab("SCHEDULED", 1)).toBe("atendimento");
    expect(resolveInitialConsultaTab("IN_PROGRESS", 3)).toBe("atendimento");
  });
});

describe("mergeConsultaFresh", () => {
  it("mescla dados frescos da API", () => {
    const base = consulta({ status: "SCHEDULED" });
    const merged = mergeConsultaFresh(base, { status: "IN_PROGRESS" });
    expect(merged.status).toBe("IN_PROGRESS");
    expect(merged.id).toBe(1);
  });
});

describe("temHistoricoAnterior", () => {
  it("exige mais de uma consulta no histórico", () => {
    expect(temHistoricoAnterior([consulta()])).toBe(false);
    expect(temHistoricoAnterior([consulta(), consulta({ id: 2 })])).toBe(true);
  });
});
