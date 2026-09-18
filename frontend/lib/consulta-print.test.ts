import { describe, expect, it, vi, afterEach } from "vitest";
import { abrirPdfUrl, direcionarJanelaPdf, escreverPaginaImpressaoPdf } from "@/lib/consulta-print";

function fakeWindow() {
  const doc = {
    open: vi.fn(),
    write: vi.fn(),
    close: vi.fn(),
  };
  return {
    document: doc,
    location: { href: "" },
    close: vi.fn(),
    focus: vi.fn(),
    print: vi.fn(),
  };
}

describe("escreverPaginaImpressaoPdf", () => {
  it("grava HTML com iframe do PDF e chama print, sem navegar para o blob", () => {
    const win = fakeWindow();
    escreverPaginaImpressaoPdf(win as unknown as Window, "blob:http://localhost/abc");
    expect(win.document.open).toHaveBeenCalled();
    expect(win.document.write).toHaveBeenCalled();
    const html = String(win.document.write.mock.calls[0][0]);
    expect(html).toContain('src="blob:http://localhost/abc"');
    expect(html).toContain("cw.print()");
    expect(win.document.close).toHaveBeenCalled();
    expect(win.location.href).toBe("");
  });
});

describe("direcionarJanelaPdf", () => {
  it("visualizar só aponta a aba para o PDF", () => {
    const win = fakeWindow();
    direcionarJanelaPdf(win as unknown as Window, "blob:http://localhost/pdf", "visualizar");
    expect(win.location.href).toBe("blob:http://localhost/pdf");
    expect(win.document.write).not.toHaveBeenCalled();
  });

  it("imprimir monta a página de impressão em vez de só abrir o PDF", () => {
    const win = fakeWindow();
    direcionarJanelaPdf(win as unknown as Window, "blob:http://localhost/pdf", "imprimir");
    expect(win.location.href).toBe("");
    expect(win.document.write).toHaveBeenCalled();
  });
});

describe("abrirPdfUrl", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("imprimir abre aba em branco e escreve a página de impressão", () => {
    const win = fakeWindow();
    const open = vi.fn(() => win);
    vi.stubGlobal("window", { open });
    abrirPdfUrl("https://media.example/relatorio.pdf", "imprimir");
    expect(open).toHaveBeenCalledWith("", "_blank");
    expect(win.document.write).toHaveBeenCalled();
  });

  it("visualizar abre o PDF direto", () => {
    const win = fakeWindow();
    const open = vi.fn(() => win);
    vi.stubGlobal("window", { open });
    abrirPdfUrl("https://media.example/relatorio.pdf", "visualizar");
    expect(open).toHaveBeenCalledWith("https://media.example/relatorio.pdf", "_blank");
    expect(win.document.write).not.toHaveBeenCalled();
  });
});
