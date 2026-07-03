export interface CategoriaDespesa {
  id: number;
  nome: string;
}

export interface DespesaItem {
  id: number;
  descricao: string;
  categoria: number | null;
  categoria_nome?: string;
  valor: string | number;
  status: string;
  data_vencimento: string;
  data_pagamento: string | null;
  forma_pagamento: string;
  observacoes?: string;
}

export interface DespesaFormState {
  descricao: string;
  categoria: number | "";
  valor: string;
  status: string;
  data_vencimento: string;
  data_pagamento: string;
  forma_pagamento: string;
  observacoes: string;
}

export const DESPESA_FORM_INPUT_CLASS =
  "w-full px-3 py-2 text-sm border dark:border-neutral-600 rounded-lg bg-white dark:bg-neutral-700 text-gray-900 dark:text-gray-100";

export function emptyDespesaForm(): DespesaFormState {
  return {
    descricao: "",
    categoria: "",
    valor: "",
    status: "PENDING",
    data_vencimento: new Date().toISOString().slice(0, 10),
    data_pagamento: "",
    forma_pagamento: "PIX",
    observacoes: "",
  };
}

export function despesaItemToForm(editing: DespesaItem): DespesaFormState {
  return {
    descricao: editing.descricao,
    categoria: editing.categoria ?? "",
    valor: String(editing.valor),
    status: editing.status,
    data_vencimento: String(editing.data_vencimento).slice(0, 10),
    data_pagamento: editing.data_pagamento ? String(editing.data_pagamento).slice(0, 10) : "",
    forma_pagamento: editing.forma_pagamento || "PIX",
    observacoes: editing.observacoes || "",
  };
}

export function validateDespesaForm(form: DespesaFormState): string | null {
  if (!form.descricao.trim()) return "Informe a descrição.";
  const valor = Number(form.valor);
  if (!valor || valor <= 0) return "Informe um valor válido.";
  if (!form.data_vencimento) return "Informe o vencimento.";
  return null;
}

export function buildDespesaPayload(form: DespesaFormState): Record<string, unknown> {
  const valor = Number(form.valor);
  const payload: Record<string, unknown> = {
    descricao: form.descricao.trim(),
    valor,
    status: form.status,
    data_vencimento: form.data_vencimento,
    forma_pagamento: form.forma_pagamento,
    observacoes: form.observacoes.trim(),
  };
  if (form.categoria) payload.categoria = Number(form.categoria);
  if (form.status === "PAID") {
    payload.data_pagamento = form.data_pagamento || form.data_vencimento;
  } else {
    payload.data_pagamento = null;
  }
  return payload;
}

export function extractDespesaSaveError(e: unknown): string {
  if (e && typeof e === "object" && "error" in e) {
    return String((e as { error: string }).error);
  }
  return "Não foi possível salvar a despesa.";
}
