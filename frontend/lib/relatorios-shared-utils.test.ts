import { describe, expect, it, vi } from "vitest";
import {
  buildRelatorioPdfFilename,
  formatRelatorioCurrency,
  getDefaultRelatorioPeriod,
} from "@/components/clinica-beleza/relatorios-shared/relatorios-shared-utils";
import { abrirRelatorioPdf } from "@/components/clinica-beleza/relatorios-shared/abrir-relatorio-pdf";

vi.mock("@/lib/clinica-beleza-api", () => ({
  clinicaBelezaFetch: vi.fn(),
}));
vi.mock("@/lib/consulta-print", () => ({
  abrirPdfBlobFromResponse: vi.fn(),
}));

describe("getDefaultRelatorioPeriod", () => {

  it("retorna início do mês e hoje em ISO", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-06-20T12:00:00"));
    const { dataInicio, dataFim } = getDefaultRelatorioPeriod();
    expect(dataInicio).toBe("2026-06-01");
    expect(dataFim).toBe("2026-06-20");
    vi.useRealTimers();
  });
});

describe("formatRelatorioCurrency", () => {
  it("formata em BRL", () => {
    expect(formatRelatorioCurrency(1234.5)).toContain("1.234,50");
  });
});

describe("buildRelatorioPdfFilename", () => {
  it("inclui nome do profissional quando informado", () => {
    expect(buildRelatorioPdfFilename("comissoes", "Ana Silva", "2026-01-01", "2026-01-31")).toBe(
      "comissoes_Ana_Silva_2026-01-01_2026-01-31.pdf",
    );
  });

  it("omite profissional quando null", () => {
    expect(buildRelatorioPdfFilename("repasse", null, "2026-01-01", "2026-01-31")).toBe(
      "repasse_2026-01-01_2026-01-31.pdf",
    );
  });
});

describe("abrirRelatorioPdf", () => {
  it("abre o blob quando a API responde ok", async () => {
    const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
    const { abrirPdfBlobFromResponse } = await import("@/lib/consulta-print");
    const res = { ok: true } as Response;
    vi.mocked(clinicaBelezaFetch).mockResolvedValue(res);
    await abrirRelatorioPdf("/relatorios/lancamentos/pdf/", "visualizar", null);
    expect(clinicaBelezaFetch).toHaveBeenCalledWith("/relatorios/lancamentos/pdf/");
    expect(abrirPdfBlobFromResponse).toHaveBeenCalledWith(res, "visualizar", null);
  });

  it("lança erro quando a API falha", async () => {
    const { clinicaBelezaFetch } = await import("@/lib/clinica-beleza-api");
    vi.mocked(clinicaBelezaFetch).mockResolvedValue({ ok: false } as Response);
    await expect(abrirRelatorioPdf("/relatorios/lancamentos/pdf/", "imprimir")).rejects.toThrow(
      "Não foi possível gerar o PDF",
    );
  });
});
