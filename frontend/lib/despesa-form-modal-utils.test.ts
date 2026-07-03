import { describe, expect, it } from "vitest";
import {
  buildDespesaPayload,
  emptyDespesaForm,
  validateDespesaForm,
} from "@/components/clinica-beleza/despesa-form-modal/despesa-form-modal-types";

describe("validateDespesaForm", () => {
  it("valida campos obrigatórios", () => {
    const form = emptyDespesaForm();
    expect(validateDespesaForm({ ...form, descricao: "" })).toContain("descrição");
    expect(validateDespesaForm({ ...form, descricao: "OK", valor: "0" })).toContain("valor");
    expect(validateDespesaForm({ ...form, descricao: "OK", valor: "100", data_vencimento: "" })).toContain("vencimento");
    expect(validateDespesaForm(form)).toBeNull();
  });
});

describe("buildDespesaPayload", () => {
  it("monta payload com categoria e pagamento", () => {
    const form = { ...emptyDespesaForm(), descricao: "Aluguel", valor: "1500", categoria: 3, status: "PAID" };
    const payload = buildDespesaPayload(form);
    expect(payload.descricao).toBe("Aluguel");
    expect(payload.categoria).toBe(3);
    expect(payload.data_pagamento).toBeTruthy();
  });
});
