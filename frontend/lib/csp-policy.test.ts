import { describe, expect, it } from "vitest";
import { extraConnectSrcOrigins, MEMED_HTTPS, MEMED_WSS } from "./csp-policy.js";

describe("CSP connect-src Memed", () => {
  it("libera Unleash para o widget V4 abrir o iframe", () => {
    const connect = extraConnectSrcOrigins();
    expect(MEMED_HTTPS).toContain("https://*.memed.rocks");
    expect(MEMED_HTTPS).toContain("https://data.memed.rocks");
    expect(connect).toContain("https://*.memed.rocks");
  });

  it("libera o widget e o gateway da Memed", () => {
    const connect = extraConnectSrcOrigins();
    expect(MEMED_HTTPS).toContain("https://v4-embedded.memed.com.br");
    expect(MEMED_HTTPS).toContain("https://gateway.memed.com.br");
    expect(connect).toContain("https://v4-embedded.memed.com.br");
  });

  it("mantém os hosts clássicos memed.com.br", () => {
    const connect = extraConnectSrcOrigins();
    expect(connect).toContain("https://memed.com.br");
    expect(connect).toContain("https://*.memed.com.br");
    expect(connect).toContain("wss://*.memed.com.br");
  });
});
