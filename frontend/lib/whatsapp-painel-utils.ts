import { formatCpfCnpj } from "@/lib/format-br";

export type WhatsappNumero = {
  instance_name: string;
  telefone: string;
  status: string;
  rotulo?: string;
};

export type WhatsappChave = {
  id: number;
  nome: string;
  prefixo: string;
  revogada: boolean;
  ultimo_uso: string | null;
};

export type WhatsappCliente = {
  id: number | null;
  tipo: string;
  loja_id: number | null;
  nome: string;
  slug: string | null;
  documento: string;
  ativo: boolean;
  quota_numeros: number;
  app?: string;
  webhook_url?: string;
  chaves: WhatsappChave[];
  numeros: WhatsappNumero[];
};

export function filtrarClientesWhatsapp(clientes: WhatsappCliente[], q: string): WhatsappCliente[] {
  const term = q.trim().toLowerCase();
  if (!term) return clientes;
  return clientes.filter((c) => {
    const blob = `${c.nome} ${c.slug || ""} ${c.documento} ${c.app || ""}`.toLowerCase();
    if (blob.includes(term)) return true;
    return c.numeros.some(
      (n) => n.instance_name.toLowerCase().includes(term) || n.telefone.includes(term),
    );
  });
}

export function labelStatusWhatsapp(status: string): string {
  if (status === "connected") return "Conectado";
  if (status === "qr_pending") return "Aguardando QR";
  return "Desconectado";
}

export function classeStatusWhatsapp(status: string): string {
  if (status === "connected") return "bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200";
  if (status === "qr_pending") return "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200";
  return "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-200";
}

export function labelTipoWhatsapp(tipo: string): string {
  if (tipo === "lwk_loja") return "Loja LWK";
  if (tipo === "parceiro") return "Parceiro API";
  return "Sem cliente";
}

export function formatarDocumentoWhatsapp(documento: string): string {
  const d = (documento || "").replace(/\D/g, "");
  if (!d) return "";
  return formatCpfCnpj(d);
}
