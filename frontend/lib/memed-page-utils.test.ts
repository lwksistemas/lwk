import { describe, expect, it } from "vitest";
import { buildMemedConfigBasePath, buildTimbradoApplyFeedback, formatTimbradoBytes, mensagemPrescritorMemedPendente, resumoProntoParaPrescrever } from "@/components/clinica-beleza/memed-page/memed-page-utils";

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
      aviso: "",
    });
  });

  it("aviso quando prescritor ainda esta em analise", () => {
    const r = buildTimbradoApplyFeedback({
      tem_timbrado: true,
      aplicados: 0,
      total: 1,
      warning:
        "Timbrado salvo no LWK. A Memed ainda não aplica o papel timbrado para NAYARA (cadastro Em análise ou termos não aceitos).",
      detalhes: [{ error: "prescritor_pendente_memed", nome: "NAYARA" }],
    });
    expect(r.msg).toBe("Timbrado salvo no LWK.");
    expect(r.erro).toBe("");
    expect(r.aviso).toContain("NAYARA");
  });

  it("erro quando aplicados é zero", () => {
    const r = buildTimbradoApplyFeedback({ tem_timbrado: true, aplicados: 0, total: 1 });
    expect(r.msg).toBe("");
    expect(r.erro).toContain("Memed não aplicou");
  });
});

describe("mensagemPrescritorMemedPendente", () => {
  it("explica cadastro em análise sem termos", () => {
    const msg = mensagemPrescritorMemedPendente({
      nome: "Nayara",
      status: "Em análise",
      terms_accepted: false,
    });
    expect(msg).toContain("Em análise");
    expect(msg).toContain("termos");
  });

  it("nao bloqueia prescritor ativo com termos", () => {
    expect(
      mensagemPrescritorMemedPendente({ nome: "Nayara", status: "Ativo", terms_accepted: true }),
    ).toBeNull();
  });
});

describe("resumoProntoParaPrescrever", () => {
  it("nao diz pronto quando prescritor esta em analise", () => {
    const r = resumoProntoParaPrescrever({
      credentials_configured: true,
      ready_for_production: true,
      prescritores: [
        {
          nome: "NAYARA",
          status: "Em análise",
          terms_accepted: false,
          pode_prescrever: false,
        },
      ],
    });
    expect(r.tom).toBe("aviso");
    expect(r.texto).toContain("e-mail da Memed");
  });

  it("diz pronto quando todos podem prescrever", () => {
    const r = resumoProntoParaPrescrever({
      credentials_configured: true,
      prescritores: [{ nome: "NAYARA", status: "Ativo", terms_accepted: true, pode_prescrever: true }],
    });
    expect(r.tom).toBe("ok");
  });
});
