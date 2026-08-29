import { describe, expect, it } from "vitest";
import { extraConnectSrcOrigins, MEMED_HTTPS, MEMED_WSS } from "./csp-policy.js";

describe("CSP connect-src Memed", () => {
  it("não libera Unleash (gate V4 esvazia a busca de medicamentos)", () => {
    const connect = extraConnectSrcOrigins();
    expect(MEMED_HTTPS).not.toContain("https://*.memed.rocks");
    expect(MEMED_HTTPS).not.toContain("https://*.data.memed.rocks");
    expect(MEMED_WSS).not.toContain("wss://*.memed.rocks");
    expect(connect).not.toContain("https://*.memed.rocks");
    expect(connect).not.toContain("https://*.data.memed.rocks");
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
