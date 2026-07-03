import { describe, expect, it } from "vitest";
import { parsePrescricaoMemed, stripHtmlMemed, toBrDateMemed } from "./memed-prescricao-parser";

describe("parsePrescricaoMemed", () => {
  it("extrai id, itens e resumo de medicamentos", () => {
    const result = parsePrescricaoMemed({
      prescricao: {
        id: 99,
        medicamentos: [{ nome: "Dipirona", posologia: "<p>1 cp 6/6h</p>" }],
      },
    });
    expect(result.prescricaoId).toBe("99");
    expect(result.itens).toHaveLength(1);
    expect(result.itens[0].nome).toBe("Dipirona");
    expect(result.itens[0].posologia).toBe("1 cp 6/6h");
    expect(result.resumo).toContain("Dipirona");
  });

  it("encontra pdf_url aninhado", () => {
    const result = parsePrescricaoMemed({
      prescricao: { id: 1 },
      documento: { pdf_url: "https://cdn.memed.com.br/doc.pdf" },
    });
    expect(result.pdfUrl).toBe("https://cdn.memed.com.br/doc.pdf");
  });
});

describe("stripHtmlMemed", () => {
  it("remove tags html", () => {
    expect(stripHtmlMemed("<b>teste</b>")).toBe("teste");
  });
});

describe("toBrDateMemed", () => {
  it("converte ISO para BR", () => {
    expect(toBrDateMemed("1990-05-12")).toBe("12/05/1990");
  });
});
