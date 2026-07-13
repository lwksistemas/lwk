/** Utilitários puros para parse do evento `prescricaoImpressa` da Memed. */

export interface ItemPrescricaoMemed {
  nome?: string;
  posologia?: string;
  tipo?: string;
  receituario?: string;
}

export interface PrescricaoMemedParseResult {
  prescricaoId: string;
  itens: ItemPrescricaoMemed[];
  resumo: string;
  pdfUrl: string;
}

/** Remove tags HTML simples (a posologia vem como HTML). */
export function stripHtmlMemed(value: unknown): string {
  if (typeof value !== "string") return "";
  return value.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

export function extrairUrlPdfMemed(obj: unknown, profundidade = 0): string {
  if (profundidade > 6 || obj == null) return "";
  if (typeof obj === "string") {
    const s = obj.trim();
    if (/^https?:\/\//i.test(s)) return s;
    return "";
  }
  if (Array.isArray(obj)) {
    for (const item of obj) {
      const u = extrairUrlPdfMemed(item, profundidade + 1);
      if (u) return u;
    }
    return "";
  }
  if (typeof obj === "object") {
    const o = obj as Record<string, unknown>;
    for (const key of ["url_pdf", "pdf_url", "link_pdf", "pdf", "url", "link", "secure_url"]) {
      const val = o[key];
      if (typeof val === "string" && /^https?:\/\//i.test(val.trim())) return val.trim();
    }
    for (const val of Object.values(o)) {
      const u = extrairUrlPdfMemed(val, profundidade + 1);
      if (u) return u;
    }
  }
  return "";
}

/** Extrai dados úteis do payload do evento prescricaoImpressa. */
export function parsePrescricaoMemed(data: unknown): PrescricaoMemedParseResult {
  const d = (data ?? {}) as Record<string, unknown>;
  const prescricao = (d.prescricao ?? d["prescrição"] ?? d) as Record<string, unknown>;
  const meds: unknown[] = Array.isArray(d.medicamentos)
    ? d.medicamentos
    : Array.isArray(prescricao?.medicamentos)
      ? prescricao.medicamentos
      : Array.isArray(prescricao?.itens)
        ? prescricao.itens
        : [];
  const prescricaoId = String(prescricao?.id ?? d.prescricao_id ?? d.id ?? "");

  const pdfUrl = extrairUrlPdfMemed(d) || extrairUrlPdfMemed(prescricao);

  const itens: ItemPrescricaoMemed[] = meds.map((raw) => {
    const m = raw as Record<string, unknown>;
    return {
      nome: String(m?.nome ?? m?.descricao ?? m?.titulo ?? ""),
      posologia: String(m?.sanitized_posology ?? stripHtmlMemed(m?.posologia)),
      tipo: String(m?.tipo ?? ""),
      receituario: String(m?.receituario ?? ""),
    };
  });

  const resumo = itens
    .map((it) => (it.posologia ? `- ${it.nome} — ${it.posologia}` : `- ${it.nome}`))
    .filter((line) => line.replace(/^- /, "").trim())
    .join("\n");

  return { prescricaoId, itens, resumo, pdfUrl };
}

/** Converte data ISO (YYYY-MM-DD) para dd/mm/aaaa (Memed). */
export function toBrDateMemed(value?: string | null): string {
  if (!value) return "";
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(value);
  if (!match) return "";
  const [, y, m, d] = match;
  return `${d}/${m}/${y}`;
}
