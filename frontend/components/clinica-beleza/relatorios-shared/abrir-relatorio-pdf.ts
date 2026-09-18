import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api";
import { abrirPdfBlobFromResponse, type ConsultaPdfModo } from "@/lib/consulta-print";

export async function abrirRelatorioPdf(
  path: string,
  modo: ConsultaPdfModo,
  janela?: Window | null,
): Promise<void> {
  const res = await clinicaBelezaFetch(path);
  if (!res.ok) {
    throw new Error("Não foi possível gerar o PDF. Tente novamente.");
  }
  await abrirPdfBlobFromResponse(res, modo, janela);
}
