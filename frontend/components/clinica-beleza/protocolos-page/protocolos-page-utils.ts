import { procedureCategoria } from "@/lib/clinica-beleza-entities";
import { procedureMatchesModule } from "@/lib/clinica-beleza-categories";
import type {
  Protocol,
  ProtocoloFormState,
  ProtocoloIntervaloUnidade,
  ProtocoloProcedureOption,
} from "./protocolos-page-types";

const UNIDADES = new Set<ProtocoloIntervaloUnidade>(["dias", "semanas", "meses"]);

export function buildProtocolosListPath(defaultCategoria: string): string {
  return defaultCategoria
    ? `/protocolos?categoria=${encodeURIComponent(defaultCategoria)}`
    : "/protocolos";
}

export function filterProceduresByModule(
  procedures: ProtocoloProcedureOption[],
  defaultCategoria: string,
): ProtocoloProcedureOption[] {
  if (!defaultCategoria) return procedures;
  return procedures.filter((p) =>
    procedureMatchesModule(procedureCategoria(p), defaultCategoria),
  );
}

export function protocolToForm(p: Protocol): ProtocoloFormState {
  return {
    nome: p.nome || "",
    procedure: String(p.procedure),
    descricao: p.descricao || "",
    tempo_estimado: String(p.tempo_estimado || 30),
    materiais_necessarios: p.materiais_necessarios || "",
    preparacao: p.preparacao || "",
    execucao: p.execucao || "",
    pos_procedimento: p.pos_procedimento || "",
    contraindicacoes: p.contraindicacoes || "",
    cuidados_especiais: p.cuidados_especiais || "",
    sessoes: String(p.sessoes || 1),
    intervalo_quantidade: String(p.intervalo_quantidade || 1),
    intervalo_unidade: p.intervalo_unidade || "dias",
    valor: p.valor != null && p.valor !== "" ? String(p.valor) : "",
    produtos: (p.produtos || []).map((linha) => ({
      produto: String(linha.produto),
      quantidade: String(linha.quantidade),
    })),
  };
}

function numeroFormulario(valor: string): number {
  const texto = String(valor).trim();
  if (texto.includes(",")) {
    return Number(texto.replace(/\./g, "").replace(",", "."));
  }
  return Number(texto);
}

export function dividirValorProtocolo(
  valor: number,
  sessoes: number,
  forma: "POR_CONSULTA" | "TOTAL",
): number[] {
  const total = Math.round(valor * 100);
  if (sessoes < 1) return [];
  if (forma === "TOTAL") {
    return [total / 100, ...Array.from({ length: sessoes - 1 }, () => 0)];
  }
  const base = Math.floor(total / sessoes);
  const partes = Array.from({ length: sessoes }, () => base);
  partes[partes.length - 1] = total - base * (sessoes - 1);
  return partes.map((centavos) => centavos / 100);
}

export function formatarValorProtocolo(valor: string | number | null | undefined): string {
  const n = typeof valor === "number" ? valor : numeroFormulario(String(valor ?? ""));
  if (!Number.isFinite(n)) return "—";
  return n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function rotuloIntervaloProtocolo(quantidade: number, unidade: string): string {
  const rotulos: Record<string, [string, string]> = {
    dias: ["dia", "dias"],
    semanas: ["semana", "semanas"],
    meses: ["mês", "meses"],
  };
  const par = rotulos[unidade] || [unidade, unidade];
  const nome = quantidade === 1 ? par[0] : par[1];
  return `a cada ${quantidade} ${nome}`;
}

export function validateProtocoloForm(form: ProtocoloFormState): string | null {
  if (!form.nome.trim() || !form.procedure) {
    return "Nome e procedimento são obrigatórios.";
  }
  const sessoes = Number(form.sessoes);
  if (!Number.isInteger(sessoes) || sessoes < 1) {
    return "Informe a quantidade de sessões.";
  }
  const intervalo = Number(form.intervalo_quantidade);
  if (!Number.isInteger(intervalo) || intervalo < 1) {
    return "Informe o intervalo entre as sessões.";
  }
  if (!UNIDADES.has(form.intervalo_unidade)) {
    return "Escolha dias, semanas ou meses.";
  }
  const valor = numeroFormulario(form.valor);
  if (!Number.isFinite(valor) || valor < 0 || form.valor.trim() === "") {
    return "Informe o valor do protocolo.";
  }
  const produtos = new Set<string>();
  for (const linha of form.produtos) {
    if (!linha.produto) return "Selecione o produto.";
    if (produtos.has(linha.produto)) return "Produto repetido no protocolo.";
    produtos.add(linha.produto);
    const quantidade = numeroFormulario(linha.quantidade);
    if (!Number.isFinite(quantidade) || quantidade <= 0) {
      return "Informe a quantidade do produto por sessão.";
    }
  }
  return null;
}

export function buildProtocoloSaveBody(form: ProtocoloFormState): Record<string, unknown> {
  return {
    nome: form.nome.trim(),
    procedure: Number(form.procedure),
    descricao: form.descricao.trim(),
    tempo_estimado: Number(form.tempo_estimado) || 30,
    materiais_necessarios: form.materiais_necessarios.trim(),
    preparacao: form.preparacao.trim(),
    execucao: form.execucao.trim(),
    pos_procedimento: form.pos_procedimento.trim(),
    contraindicacoes: form.contraindicacoes.trim(),
    cuidados_especiais: form.cuidados_especiais.trim(),
    sessoes: Number(form.sessoes),
    intervalo_quantidade: Number(form.intervalo_quantidade),
    intervalo_unidade: form.intervalo_unidade,
    valor: numeroFormulario(form.valor).toFixed(2),
    produtos: form.produtos.map((linha) => ({
      produto: Number(linha.produto),
      quantidade: numeroFormulario(linha.quantidade).toFixed(2),
    })),
  };
}

export function extractProtocoloSaveError(e: unknown, fallback = "Erro ao salvar protocolo."): string {
  if (e instanceof Error && e.message === "SESSION_ENDED") return "SESSION_ENDED";
  if (e && typeof e === "object" && "error" in e && typeof (e as { error?: string }).error === "string") {
    return (e as { error: string }).error;
  }
  return fallback;
}
