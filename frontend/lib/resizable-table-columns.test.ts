import { describe, expect, it } from "vitest";
import { applyIntendedColumnWidths } from "@/lib/resizable-table-columns";

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
  it("preenche o container jogando o espaço extra na primeira coluna", () => {
    const { table, cols } = tableWithParent(800);
    applyIntendedColumnWidths(table, cols, [80, 100, 120]);
    expect(table.style.width).toBe("100%");
    expect(table.style.minWidth).toBe("300px");
    expect(cols[0].style.width).toBe("580px");
    expect(cols[1].style.width).toBe("100px");
    expect(cols[2].style.width).toBe("120px");
  });

  it("não estica a última coluna quando a soma já passa do container", () => {
    const { table, cols } = tableWithParent(200);
    applyIntendedColumnWidths(table, cols, [120, 100, 120]);
    expect(table.style.width).toBe("340px");
    expect(cols[0].style.width).toBe("120px");
    expect(cols[2].style.width).toBe("120px");
  });
});
