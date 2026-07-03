import { describe, expect, it } from "vitest";
import { buildMemedConfigBasePath, buildTimbradoApplyFeedback, formatTimbradoBytes } from "@/components/clinica-beleza/memed-page/memed-page-utils";

describe("buildMemedConfigBasePath", () => {
  it("monta path de configurações", () => {
    expect(buildMemedConfigBasePath("novaimagem")).toBe(
      "/loja/novaimagem/clinica-beleza/configuracoes",
    );
  });
});

describe("formatTimbradoBytes", () => {
  it("formata bytes, KB e MB", () => {
    expect(formatTimbradoBytes()).toBe("—");
    expect(formatTimbradoBytes(512)).toBe("512 B");
    expect(formatTimbradoBytes(2048)).toBe("2.0 KB");
    expect(formatTimbradoBytes(2 * 1024 * 1024)).toBe("2.0 MB");
  });
});

describe("buildTimbradoApplyFeedback", () => {
  it("mensagem de sucesso quando aplicados > 0", () => {
    expect(buildTimbradoApplyFeedback({ tem_timbrado: true, aplicados: 2, total: 3 })).toEqual({
      msg: "Timbrado aplicado na Memed para 2 de 3 prescritor(es).",
      erro: "",
    });
  });

  it("erro quando aplicados é zero", () => {
    const r = buildTimbradoApplyFeedback({ tem_timbrado: true, aplicados: 0, total: 1 });
    expect(r.msg).toBe("");
    expect(r.erro).toContain("Memed não aplicou");
  });
});
