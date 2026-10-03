import { formatCpfCnpj } from "@/lib/format-br";

export type WhatsappNumero = {
  instance_name: string;
  telefone: string;
  status: string;
  rotulo?: string;
  profile_name?: string;
  conectado_desde?: string | null;
};

export type WhatsappMensagens = {
  total: number;
  enviadas: number;
  falhas: number;
  ultimas_24h: number;
  ultimos_7d: number;
  ultimo_envio: string | null;
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
  mensagens?: WhatsappMensagens;
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

/** "conectado há 3h 12min" a partir de um ISO timestamp. */
export function tempoConectado(desde: string | null | undefined): string {
  if (!desde) return "";
  const inicio = new Date(desde).getTime();
  if (Number.isNaN(inicio)) return "";
  const seg = Math.max(0, Math.floor((Date.now() - inicio) / 1000));
  const dias = Math.floor(seg / 86400);
  const horas = Math.floor((seg % 86400) / 3600);
  const min = Math.floor((seg % 3600) / 60);
  if (dias > 0) return `conectado há ${dias}d ${horas}h`;
  if (horas > 0) return `conectado há ${horas}h ${min}min`;
  return `conectado há ${min}min`;
}

/** Data/hora curta em pt-BR a partir de ISO; vazio se nulo. */
export function dataHoraCurta(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
