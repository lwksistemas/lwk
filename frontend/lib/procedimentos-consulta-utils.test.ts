import { describe, expect, it } from "vitest";
import {
  avisoTermoProcedimentoAdicionado,
  deveExibirProcedimentosSection,
  mapProcedimentosFromConsulta,
} from "@/components/clinica-beleza/consultas/procedimentos-consulta/procedimentos-consulta-utils";
import type { ConsultaProcedimento } from "@/components/clinica-beleza/consultas/consultas-types";

describe("mapProcedimentosFromConsulta", () => {
  it("mapeia apenas itens com appointment_procedure_id", () => {
    const lista: ConsultaProcedimento[] = [
      { id: 1, nome: "Botox", valor: 100, appointment_procedure_id: 10 },
      { id: 2, nome: "Sem vínculo", valor: 50 },
    ];
    const mapped = mapProcedimentosFromConsulta(lista);
    expect(mapped).toHaveLength(1);
    expect(mapped[0].id).toBe(10);
    expect(mapped[0].procedure_name).toBe("Botox");
  });
});

describe("deveExibirProcedimentosSection", () => {
  it("oculta quando vazio e sem ações", () => {
    expect(
      deveExibirProcedimentosSection({
        loading: false,
        itensCount: 0,
        podeAdicionar: false,
        showAddForm: false,
        erro: "",
        avisoTermo: "",
      }),
    ).toBe(false);
  });

  it("exibe quando há itens", () => {
    expect(
      deveExibirProcedimentosSection({
        loading: false,
        itensCount: 1,
        podeAdicionar: false,
        showAddForm: false,
        erro: "",
        avisoTermo: "",
      }),
    ).toBe(true);
  });
});

describe("avisoTermoProcedimentoAdicionado", () => {
  it("retorna aviso quando exige termo", () => {
    const msg = avisoTermoProcedimentoAdicionado(
      { procedures_list: [{ id: 5, nome: "X", valor: 1, exige_termo: true }] },
      5,
    );
    expect(msg).toContain("termo de consentimento");
  });
});
