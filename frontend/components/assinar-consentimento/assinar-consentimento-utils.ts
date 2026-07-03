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
