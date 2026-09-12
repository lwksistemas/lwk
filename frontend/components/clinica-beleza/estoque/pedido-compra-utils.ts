import { clinicaBelezaFetch } from "@/lib/clinica-beleza-api/fetch";
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

export async function abrirPdfPedido(id: number): Promise<void> {
  const res = await clinicaBelezaFetch(`/estoque/pedidos/${id}/pdf/`);
  if (!res.ok) {
    throw new Error("Não foi possível gerar o PDF.");
  }
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  window.open(url, "_blank");
  setTimeout(() => window.URL.revokeObjectURL(url), 15000);
}
