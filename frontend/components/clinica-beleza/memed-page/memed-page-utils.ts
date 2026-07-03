import type { TimbradoDetalhe, TimbradoStatus } from "./memed-page-types";

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
