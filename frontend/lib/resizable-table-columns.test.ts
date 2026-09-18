import { describe, expect, it } from "vitest";
import {
  applyIntendedColumnWidths,
  splitPairWidths,
} from "@/lib/resizable-table-columns";

function tableWithParent(parentWidth: number): {
  table: HTMLTableElement;
  cols: HTMLElement[];
} {
  const cols = [0, 1, 2].map(() => ({ style: { width: "" } }));
  const table = {
    parentElement: { clientWidth: parentWidth },
    style: { tableLayout: "", minWidth: "", maxWidth: "", width: "" },
    dataset: {} as Record<string, string>,
  };
  return {
    table: table as unknown as HTMLTableElement,
    cols: cols as unknown as HTMLElement[],
  };
}

describe("applyIntendedColumnWidths", () => {
  it("preenche o container rateando o espaço em todas as colunas", () => {
    const { table, cols } = tableWithParent(800);
    applyIntendedColumnWidths(table, cols, [200, 100, 80]);
    expect(table.style.width).toBe("100%");
    const w0 = Number.parseFloat(cols[0].style.width);
    const w1 = Number.parseFloat(cols[1].style.width);
    const w2 = Number.parseFloat(cols[2].style.width);
    expect(w0 + w1 + w2).toBeCloseTo(800, 0);
    expect(w0).toBeGreaterThan(w1);
    expect(w1).toBeGreaterThan(w2);
    expect(w0).toBeLessThan(500);
  });

  it("mantém a proporção quando a soma já enche o container", () => {
    const { table, cols } = tableWithParent(300);
    applyIntendedColumnWidths(table, cols, [100, 100, 100]);
    expect(table.style.width).toBe("100%");
    expect(Number.parseFloat(cols[0].style.width)).toBeCloseTo(100, 0);
    expect(Number.parseFloat(cols[2].style.width)).toBeCloseTo(100, 0);
  });
});

describe("splitPairWidths", () => {
  it("ao arrastar a borda, a esquerda encolhe e a direita cresce", () => {
    const next = splitPairWidths([400, 120, 80], 0, -100);
    expect(next[0]).toBe(300);
    expect(next[1]).toBe(220);
    expect(next[2]).toBe(80);
  });

  it("não deixa coluna abaixo do mínimo", () => {
    const next = splitPairWidths([80, 200], 0, -50);
    expect(next[0]).toBe(72);
    expect(next[1]).toBe(208);
  });
});
