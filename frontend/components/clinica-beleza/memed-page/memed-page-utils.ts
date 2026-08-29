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

export function buildTimbradoApplyFeedback(data: TimbradoStatus): { msg: string; erro: string; aviso: string } {
  const aplicados = data.aplicados;
  const total = data.total;
  if (typeof aplicados !== "number") {
    return { msg: "Timbrado salvo no sistema.", erro: "", aviso: "" };
  }
  const detalhes = data.detalhes ?? [];
  const pendentes = detalhes.filter((d) => d.error === "prescritor_pendente_memed");
  if (aplicados > 0) {
    const aviso =
      pendentes.length > 0
        ? `Não aplicado em ${pendentes.length} prescritor(es) ainda pendentes na Memed (Em análise / termos).`
        : "";
    return {
      msg: `Timbrado aplicado na Memed para ${aplicados} de ${total} prescritor(es).`,
      erro: "",
      aviso,
    };
  }
  const soPendentes = pendentes.length > 0 && pendentes.length === detalhes.length;
  if (soPendentes || (typeof data.warning === "string" && /Em análise|termos não aceitos/i.test(data.warning))) {
    return {
      msg: "Timbrado salvo no LWK.",
      erro: "",
      aviso:
        (typeof data.warning === "string" && data.warning) ||
        "A Memed ainda não aplica o papel timbrado enquanto o prescritor está Em análise. Quando estiver Ativo, use Reaplicar aos prescritores.",
    };
  }
  const memedErr = detalhes.find((d) => d.detail)?.detail || detalhes[0]?.error;
  return {
    msg: "",
    erro:
      (typeof data.warning === "string" && data.warning) ||
      `Timbrado salvo no LWK, mas a Memed não aplicou (${aplicados}/${total}).` +
        (memedErr ? ` Detalhe: ${String(memedErr).slice(0, 200)}` : "") +
        " Tente Reaplicar ou fale com o suporte Memed (permissão de layout da conta parceira).",
    aviso: "",
  };
}

export function mensagemPrescritorMemedPendente(
  _prescritor?: {
    nome?: string;
    status?: string;
    terms_accepted?: boolean;
  } | null,
): string | null {
  return null;
}

export function prescritorPodePrescrever(p?: MemedPrescritorDiag | null): boolean {
  if (!p) return false;
  if (typeof p.pode_prescrever === "boolean") return p.pode_prescrever;
  const st = String(p.status || p.label || p.state || "").trim();
  if (!st) return false;
  if (/não cadastrado|nao cadastrado|indispon[ií]vel|erro/i.test(st)) return false;
  return true;
}

export function detalhePrescritorMemed(p: MemedPrescritorDiag): string {
  const status = String(p.status || p.label || "").trim();
  if (/an[aá]lise/i.test(status)) {
    return `${status} (não impede emitir receitas)`;
  }
  const partes: string[] = [];
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
        "A clínica está conectada à Memed, mas nenhum prescritor foi encontrado no cadastro da Memed.",
    };
  }
  if (liberados.length < lista.length) {
    return {
      tom: "aviso",
      texto: `${liberados.length} de ${lista.length} prescritor(es) podem prescrever. Confira CPF e cadastro na Memed dos demais.`,
    };
  }
  return { tom: "ok", texto: "Pronto para prescrição em produção. O status Em análise na Memed não impede emitir receitas." };
}
