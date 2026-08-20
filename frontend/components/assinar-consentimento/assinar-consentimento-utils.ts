export function decodeAssinaturaToken(tokenRaw: string): string {
  try {
    return decodeURIComponent(tokenRaw);
  } catch {
    return tokenRaw;
  }
}

export function buildAssinaturaConsentimentoUrls(tokenApiSegment: string) {
  const base = `/clinica-beleza/assinar-consentimento/${tokenApiSegment}`;
  return {
    termo: `${base}/`,
    pdf: `${base}/pdf/`,
  };
}

export function podeAssinarTermo(
  pdfPronto: boolean,
  pdfInteracaoFeita: boolean,
  declarouLeituraCompleta: boolean,
): boolean {
  return pdfPronto && pdfInteracaoFeita && declarouLeituraCompleta;
}

export function ehTcleInterativoPaciente(termo: {
  tipo_termo?: string;
  tipo_assinante?: string;
} | null): boolean {
  return termo?.tipo_termo === "interativo" && termo?.tipo_assinante === "paciente";
}

export function respostasInterativoValidas(
  secoes: { id: string; tipo: string }[],
  respostas: Record<string, { sim_nao?: string; consinto?: string }>,
): boolean {
  if (!secoes.length) return false;
  for (const secao of secoes) {
    const r = respostas[secao.id] || {};
    const simNao = (r.sim_nao || "").toLowerCase();
    if (secao.tipo === "sim_nao" && simNao !== "sim") return false;
    if (secao.tipo === "fotos" && simNao !== "sim" && simNao !== "nao" && simNao !== "não") {
      return false;
    }
    if (secao.tipo === "gravidez" && simNao !== "sim" && simNao !== "nao" && simNao !== "não") {
      return false;
    }
    if (secao.tipo === "consinto" && (r.consinto || "").toLowerCase() !== "consinto") {
      return false;
    }
  }
  return true;
}
