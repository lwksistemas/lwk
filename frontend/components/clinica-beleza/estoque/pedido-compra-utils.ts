import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api/fetch";
import { downloadBlobFile } from "@/lib/download-blob";
import { extractEstoqueApiError } from "./estoque-types";

export function numeroPedidoLabel(numero: number | string): string {
  const n = Number(numero);
  return Number.isFinite(n) ? String(n).padStart(2, "0") : String(numero);
}

export function canalResultado(
  res: { email?: { sucesso?: boolean; erro?: string }; whatsapp?: { sucesso?: boolean; erro?: string } },
  canal: "email" | "whatsapp",
): string {
  const r = res[canal];
  if (r?.sucesso) return canal === "email" ? "Enviado por e-mail." : "Enviado por WhatsApp.";
  return r?.erro || extractEstoqueApiError(res, "Não foi possível enviar.");
}

export function slugNomeArquivo(nome: string): string {
  const ascii = (nome || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_|_$/g, "")
    .slice(0, 60);
  return (ascii || "fornecedor").toUpperCase();
}

export function nomeArquivoPedidoPdf(pedido: {
  numero?: number | string;
  fornecedor?: { nome_fantasia?: string; razao_social?: string };
}): string {
  const forn = slugNomeArquivo(
    pedido.fornecedor?.nome_fantasia || pedido.fornecedor?.razao_social || "fornecedor",
  );
  return `Pedido_${numeroPedidoLabel(pedido.numero ?? "")}_${forn}.pdf`;
}

export async function abrirPdfPedido(id: number, filename: string): Promise<void> {
  const res = await clinicaBelezaFetch(`/estoque/pedidos/${id}/pdf/`);
  if (!res.ok) {
    throw new Error("Não foi possível gerar o PDF.");
  }
  const blob = await res.blob();
  if (blob.size < 100) {
    throw new Error("PDF vazio ou inválido.");
  }
  const nome = filename.endsWith(".pdf") ? filename : `${filename}.pdf`;
  downloadBlobFile(blob, nome);
  const url = window.URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => window.URL.revokeObjectURL(url), 60_000);
}
