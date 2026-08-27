import { describe, expect, it } from "vitest";
import {
  mostrarEditorNotasAtendimento,
  mostrarSeletorProtocolo,
} from "@/components/clinica-beleza/consultas/consulta-atendimento-tab-utils";

describe("mostrarSeletorProtocolo", () => {
  it("mostra protocolos durante atendimento em andamento", () => {
    expect(mostrarSeletorProtocolo(2, false)).toBe(true);
    expect(mostrarSeletorProtocolo(0, false)).toBe(false);
    expect(mostrarSeletorProtocolo(2, true)).toBe(false);
  });
});

describe("mostrarEditorNotasAtendimento", () => {
  it("abre o campo de notas sem exigir clique em Editar", () => {
    expect(mostrarEditorNotasAtendimento(false)).toBe(true);
    expect(mostrarEditorNotasAtendimento(true)).toBe(false);
  });
});
