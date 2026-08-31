import { describe, expect, it, vi } from "vitest";
import {
  garantirEditorMemedVisivel,
  isMemedMessageReady,
  isMemedV4Boot,
  MEMED_V4_BOOT_KEY,
  podeReforcarTokenMemed,
  scriptMemedPrecisaReiniciar,
  urlScriptWidgetMemed,
  withTimeout,
} from "./memed-sdk";

describe("withTimeout", () => {
  it("resolve quando a promise termina a tempo", async () => {
    await expect(withTimeout(Promise.resolve("ok"), 50, "teste")).resolves.toBe("ok");
  });

  it("rejeita se a promise da Memed não responder", async () => {
    vi.useFakeTimers();
    const pending = withTimeout(new Promise(() => {}), 40, "Memed: travou");
    const assertion = expect(pending).rejects.toThrow(/Memed: travou/);
    await vi.advanceTimersByTimeAsync(40);
    await assertion;
    vi.useRealTimers();
  });
});

describe("detecção V4", () => {
  it("reconhece o boot do widget V4", () => {
    const win = { [MEMED_V4_BOOT_KEY]: { teardown() {} } } as unknown as Window;
    expect(isMemedV4Boot(win)).toBe(true);
    expect(isMemedV4Boot({} as Window)).toBe(false);
  });

  it("reconhece MEMED_READY do iframe", () => {
    expect(isMemedMessageReady({ type: "MEMED_READY" })).toBe(true);
    expect(isMemedMessageReady({ type: "COMMAND_RESULT" })).toBe(false);
    expect(isMemedMessageReady(null)).toBe(false);
  });
});

describe("garantirEditorMemedVisivel", () => {
  function iframeMemed() {
    return {
      tagName: "IFRAME",
      style: {} as Record<string, string>,
      getAttribute: (key: string) => (key === "title" ? "Memed Prescrição" : ""),
    };
  }

  it("devolve false sem editor", () => {
    const doc = {
      getElementById: () => null,
      querySelectorAll: () => [],
    } as unknown as Document;
    expect(garantirEditorMemedVisivel(doc, "lwk-memed-host")).toBe(false);
  });

  it("nao move o iframe da overlay (appendChild recarrega e perde o token)", () => {
    const iframe = iframeMemed();
    const overlay = {
      style: { display: "none", visibility: "hidden", pointerEvents: "none" } as Record<string, string>,
      contains: (el: unknown) => el === iframe,
      childElementCount: 1,
    };
    const host = {
      querySelectorAll: () => [],
      contains: () => false,
      appendChild: vi.fn(),
    };
    const doc = {
      getElementById: (id: string) =>
        id === "lwk-memed-host" ? host : id === "memed-auto-generated" ? overlay : null,
      querySelectorAll: () => [iframe],
    } as unknown as Document;

    expect(garantirEditorMemedVisivel(doc, "lwk-memed-host")).toBe(true);
    expect(host.appendChild).not.toHaveBeenCalled();
    expect(overlay.style.display).not.toBe("none");
    expect(overlay.style.visibility).toBe("visible");
    expect(overlay.style.zIndex).toBe("2147483646");
  });
});

describe("token da Memed", () => {
  it("nunca chama setToken depois do data-token (legado recarrega o iframe)", () => {
    const win = { [MEMED_V4_BOOT_KEY]: { teardown() {} } } as unknown as Window;
    expect(podeReforcarTokenMemed({} as Window)).toBe(false);
    expect(podeReforcarTokenMemed(win)).toBe(false);
  });

  it("reinicia o script se o token do prescritor mudou", () => {
    expect(scriptMemedPrecisaReiniciar("token-a", "token-b")).toBe(true);
    expect(scriptMemedPrecisaReiniciar("token-a", "token-a")).toBe(false);
    expect(scriptMemedPrecisaReiniciar(null, "token-a")).toBe(false);
  });

  it("força o widget V4 em produção para abrir o editor", () => {
    const prod =
      "https://memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js";
    const homo =
      "https://integrations.memed.com.br/modulos/plataforma.sinapse-prescricao/build/sinapse-prescricao.min.js";
    expect(urlScriptWidgetMemed(prod)).toBe(
      "https://v4-embedded.memed.com.br/sinapse/sinapse-v4.min.js",
    );
    expect(urlScriptWidgetMemed(homo)).toBe(homo);
  });
});
