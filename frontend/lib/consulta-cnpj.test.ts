import { afterEach, describe, expect, it, vi } from "vitest";
import { consultaCnpj, mapBrasilApiCnpj, mapCnpjaCnpj } from "@/lib/consulta-cnpj";

describe("mapCnpjaCnpj", () => {
  it("preenche T E PALARO a partir da CNPJA", () => {
    const dados = mapCnpjaCnpj({
      razao_social: "T E PALARO LTDA",
      simples: { simples: "Não" },
      estabelecimento: {
        nome_fantasia: null,
        email: "contato@npcontabilidade.com.br",
        cep: "85770000",
        logradouro: "Rua Arnaldo Busatto",
        numero: "3313",
        complemento: "Sala 03",
        bairro: "Centro",
        ddd1: "46",
        telefone1: "35431343",
        atividade_principal: { id: "8640205" },
        cidade: { nome: "Realeza", ibge_id: 4121406 },
        estado: { sigla: "PR" },
      },
    });
    expect(dados).toMatchObject({
      razao_social: "T E PALARO LTDA",
      cep: "85770-000",
      logradouro: "Rua Arnaldo Busatto",
      numero: "3313",
      municipio: "Realeza",
      uf: "PR",
      email: "contato@npcontabilidade.com.br",
      telefone: "4635431343",
      codigo_municipio_ibge: "4121406",
      cnae_fiscal: "8640205",
      optante_simples: false,
    });
  });
});

describe("mapBrasilApiCnpj", () => {
  it("exige razão social", () => {
    expect(mapBrasilApiCnpj({})).toBeNull();
  });
});

describe("consultaCnpj", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("cai na CNPJA quando a BrasilAPI não encontra", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (String(url).includes("brasilapi.com.br")) {
          return new Response(JSON.stringify({ message: "não encontrado" }), { status: 404 });
        }
        return new Response(
          JSON.stringify({
            razao_social: "T E PALARO LTDA",
            estabelecimento: {
              cep: "85770000",
              logradouro: "R ARNALDO BUSATTO",
              numero: "3313",
              complemento: "SALA 03",
              bairro: "CENTRO",
              email: "contato@npcontabilidade.com.br",
              cidade: { nome: "REALEZA", ibge_id: 4121406 },
              estado: { sigla: "PR" },
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }),
    );

    const dados = await consultaCnpj("68.487.467/0001-41");
    expect(dados?.razao_social).toBe("T E PALARO LTDA");
    expect(dados?.municipio).toBe("REALEZA");
    expect(dados?.uf).toBe("PR");
  });
});
