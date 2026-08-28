import { describe, expect, it } from "vitest";
import { extraConnectSrcOrigins, MEMED_HTTPS, MEMED_WSS } from "./csp-policy.js";

describe("CSP connect-src Memed", () => {
  it("libera HTTPS e WebSocket em memed.rocks (Unleash da Sinapse)", () => {
    const connect = extraConnectSrcOrigins();
    expect(MEMED_HTTPS).toContain("https://*.memed.rocks");
    expect(MEMED_WSS).toContain("wss://*.memed.rocks");
    expect(connect).toContain("https://*.memed.rocks");
    expect(connect).toContain("wss://*.memed.rocks");
  });

  it("libera o Unleash e o widget V4 da Memed (atualização 3.11 / ago 2026)", () => {
    const connect = extraConnectSrcOrigins();
    expect(MEMED_HTTPS).toContain("https://*.data.memed.rocks");
    expect(MEMED_HTTPS).toContain("https://v4-embedded.memed.com.br");
    expect(MEMED_WSS).toContain("wss://*.data.memed.rocks");
    expect(connect).toContain("https://*.data.memed.rocks");
    expect(connect).toContain("https://v4-embedded.memed.com.br");
  });

  it("mantém os hosts clássicos memed.com.br", () => {
    const connect = extraConnectSrcOrigins();
    expect(connect).toContain("https://memed.com.br");
    expect(connect).toContain("https://*.memed.com.br");
    expect(connect).toContain("wss://*.memed.com.br");
  });
});
