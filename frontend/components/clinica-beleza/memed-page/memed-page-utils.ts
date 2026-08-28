import type { MemedDiagStatus, MemedPrescritorDiag, TimbradoStatus } from "./memed-page-types";

export function buildMemedConfigBasePath(slug: string): string {
  return `/loja/${slug}/clinica-beleza/configuracoes`;
}

export function formatTimbradoBytes(n?: number): string {
  if (!n) return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export function buildTimbradoApplyFeedback(data: TimbradoStatus): { msg: string; erro: string } {
  const aplicados = data.aplicados;
  const total = data.total;
  if (typeof aplicados !== "number") {
    return { msg: "Timbrado salvo no sistema.", erro: "" };
  }
  if (aplicados > 0) {
    return { msg: `Timbrado aplicado na Memed para ${aplicados} de ${total} prescritor(es).`, erro: "" };
  }
  const detalhes = data.detalhes ?? [];
  const memedErr = detalhes.find((d) => d.detail)?.detail || detalhes[0]?.error;
  return {
    msg: "",
    erro:
      (typeof data.warning === "string" && data.warning) ||
      `Timbrado salvo no LWK, mas a Memed não aplicou (${aplicados}/${total}).` +
        (memedErr ? ` Detalhe: ${String(memedErr).slice(0, 200)}` : "") +
        ' Isso costuma ocorrer enquanto o prescritor está "Em análise" na Memed — tente de novo quando estiver Ativo, ou contate o suporte Memed.',
    };
}

export function mensagemPrescritorMemedPendente(prescritor?: {
  nome?: string;
  status?: string;
  terms_accepted?: boolean;
} | null): string | null {
  if (!prescritor) return null;
  const status = String(prescritor.status || "").trim();
  const emAnalise = /an[aá]lise/i.test(status);
  const semTermos = prescritor.terms_accepted === false;
  if (!emAnalise && !semTermos) return null;
  const quem = prescritor.nome ? ` de ${prescritor.nome}` : "";
  if (emAnalise && semTermos) {
    return (
      `A Memed ainda não liberou o prescritor${quem} (cadastro Em análise e termos não aceitos). ` +
      "Peça para a médica aceitar os termos no e-mail da Memed e aguarde o status Ativo."
    );
  }
  if (semTermos) {
    return `O prescritor${quem} ainda não aceitou os termos da Memed. Peça para aceitar no e-mail/cadastro da Memed e tente de novo.`;
  }
  return `O prescritor${quem} está "${status}" na Memed. Aguarde a aprovação (status Ativo) para prescrever.`;
}

export function prescritorPodePrescrever(p?: MemedPrescritorDiag | null): boolean {
  if (!p) return false;
  if (typeof p.pode_prescrever === "boolean") return p.pode_prescrever;
  if (p.terms_accepted === false) return false;
  return String(p.status || p.label || "").trim().toLowerCase() === "ativo";
}

export function detalhePrescritorMemed(p: MemedPrescritorDiag): string {
  const partes: string[] = [];
  const status = String(p.status || p.label || "").trim();
  if (status) partes.push(status);
  if (p.terms_accepted === false) partes.push("termos não aceitos");
  else if (p.terms_accepted) partes.push("termos aceitos");
  return partes.join(" · ") || "Sem status na Memed";
}

export function resumoProntoParaPrescrever(diag: MemedDiagStatus): {
  tom: "ok" | "aviso" | "pendente";
  texto: string;
} {
  const lista = diag.prescritores ?? [];
  const liberados = lista.filter(prescritorPodePrescrever);
  if (!diag.credentials_configured) {
    return {
      tom: "pendente",
      texto: "Complete credenciais, CPF dos prescritores e timbrado antes de ir a produção.",
    };
  }
  if (lista.length === 0) {
    return {
      tom: "pendente",
      texto: "Cadastre o CPF dos médicos em Profissionais para prescrever na Memed.",
    };
  }
  if (liberados.length === 0) {
    return {
      tom: "aviso",
      texto:
        "A clínica está conectada à Memed, mas nenhum prescritor está Ativo com os termos aceitos. Isso se resolve no e-mail da Memed, não nesta tela.",
    };
  }
  if (liberados.length < lista.length) {
    return {
      tom: "aviso",
      texto: `${liberados.length} de ${lista.length} prescritor(es) podem prescrever. Os demais precisam aceitar os termos no e-mail da Memed e aguardar o status Ativo.`,
    };
  }
  return { tom: "ok", texto: "Pronto para prescrição em produção." };
}
