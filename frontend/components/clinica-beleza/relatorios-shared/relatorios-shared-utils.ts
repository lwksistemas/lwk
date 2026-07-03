export interface RelatorioProfessionalOption {
  id: number;
  nome: string;
}

export function getDefaultRelatorioPeriod(): { dataInicio: string; dataFim: string } {
  const d = new Date();
  return {
    dataInicio: new Date(d.getFullYear(), d.getMonth(), 1).toISOString().split("T")[0],
    dataFim: d.toISOString().split("T")[0],
  };
}

export function formatRelatorioCurrency(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export function downloadBlob(blob: Blob, filename: string): void {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}

export function buildRelatorioPdfFilename(
  prefix: string,
  profissionalNome: string | null,
  dataInicio: string,
  dataFim: string,
): string {
  if (profissionalNome) {
    return `${prefix}_${profissionalNome.replace(/\s+/g, "_")}_${dataInicio}_${dataFim}.pdf`;
  }
  return `${prefix}_${dataInicio}_${dataFim}.pdf`;
}
