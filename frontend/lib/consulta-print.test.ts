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
  it("abre o PDF nativo em vez de iframe+print (Chrome fica em branco)", () => {
    const win = fakeWindow();
    escreverPaginaImpressaoPdf(win as unknown as Window, "blob:http://localhost/abc");
    expect(win.location.href).toBe("blob:http://localhost/abc");
    expect(win.document.write).not.toHaveBeenCalled();
  });
});

describe("direcionarJanelaPdf", () => {
  it("visualizar só aponta a aba para o PDF", () => {
    const win = fakeWindow();
    direcionarJanelaPdf(win as unknown as Window, "blob:http://localhost/pdf", "visualizar");
    expect(win.location.href).toBe("blob:http://localhost/pdf");
    expect(win.document.write).not.toHaveBeenCalled();
  });

  it("imprimir também abre o PDF nativo (sem wrapper iframe)", () => {
    const win = fakeWindow();
    direcionarJanelaPdf(win as unknown as Window, "blob:http://localhost/pdf", "imprimir");
    expect(win.location.href).toBe("blob:http://localhost/pdf");
    expect(win.document.write).not.toHaveBeenCalled();
  });
});

describe("abrirPdfUrl", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("imprimir abre o PDF direto na aba", () => {
    const win = fakeWindow();
    const open = vi.fn(() => win);
    vi.stubGlobal("window", { open });
    abrirPdfUrl("https://media.example/relatorio.pdf", "imprimir");
    expect(open).toHaveBeenCalledWith("https://media.example/relatorio.pdf", "_blank");
  });

  it("visualizar abre o PDF direto", () => {
    const win = fakeWindow();
    const open = vi.fn(() => win);
    vi.stubGlobal("window", { open });
    abrirPdfUrl("https://media.example/relatorio.pdf", "visualizar");
    expect(open).toHaveBeenCalledWith("https://media.example/relatorio.pdf", "_blank");
  });
});
