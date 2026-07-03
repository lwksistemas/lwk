import { describe, expect, it } from "vitest";
import {
  getDesktopSidebarClassName,
  getMobileDrawerClassName,
  normalizeNavPath,
  shouldSkipNavigation,
} from "@/components/clinica-beleza/clinica-beleza-shell/clinica-beleza-shell-utils";

describe("normalizeNavPath", () => {
  it("remove barra final e query", () => {
    expect(normalizeNavPath("/loja/x/agenda/?tab=1")).toBe("/loja/x/agenda");
  });
});

describe("shouldSkipNavigation", () => {
  it("ignora navegação para mesma rota sem query", () => {
    expect(shouldSkipNavigation("/loja/x/agenda", "/loja/x/agenda")).toBe(true);
    expect(shouldSkipNavigation("/loja/x/agenda", "/loja/x/agenda?novo=1")).toBe(false);
  });
});

describe("getDesktopSidebarClassName", () => {
  it("alterna largura conforme collapsed", () => {
    expect(getDesktopSidebarClassName(true)).toContain("w-16");
    expect(getDesktopSidebarClassName(false)).toContain("w-64");
  });
});

describe("getMobileDrawerClassName", () => {
  it("mostra ou esconde drawer", () => {
    expect(getMobileDrawerClassName(true)).toContain("translate-x-0");
    expect(getMobileDrawerClassName(false)).toContain("-translate-x-full");
  });
});
