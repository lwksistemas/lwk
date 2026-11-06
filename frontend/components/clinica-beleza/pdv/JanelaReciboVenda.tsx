import { CalendarDays, Check, DollarSign, FileText, Mail, MessageCircle, Printer, UserRound, X } from "lucide-react";
import { formatCurrency } from "@/lib/financeiro-helpers";
import type { EntregaRecibo } from "./pdv-tipos";

export function JanelaReciboVenda({
  entrega,
  aviso,
  enviando,
  onImprimir,
  onWhatsapp,
  onEmail,
  onFechar,
}: {
  entrega: EntregaRecibo;
  aviso: string;
  enviando: "whatsapp" | "email" | null;
  onImprimir: () => void;
  onWhatsapp: () => void;
  onEmail: () => void;
  onFechar: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-4 flex justify-end">
          <button type="button" onClick={onFechar} aria-label="Fechar"><X size={18} className="text-gray-500" /></button>
        </div>
        <div className="mb-2 flex justify-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-500"><Check size={28} /></span>
        </div>
        <h2 className="mb-4 text-center text-lg font-semibold text-gray-900">Pagamento registrado com sucesso</h2>
        <div className="mb-4 space-y-2 rounded-xl bg-gray-50 px-4 py-3 text-sm">
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><UserRound size={14} /> Cliente</span><strong className="text-right">{entrega.cliente}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><FileText size={14} /> Recibo nº</span><strong>{entrega.numero}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><DollarSign size={14} /> Forma de pagamento</span><strong className="text-right">{entrega.forma}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><DollarSign size={14} /> Valor pago</span><strong>{formatCurrency(Number(entrega.total || 0))}</strong></p>
          <p className="flex justify-between gap-3"><span className="inline-flex items-center gap-2 text-gray-500"><CalendarDays size={14} /> Data e hora</span><strong>{entrega.quando}</strong></p>
        </div>
        {aviso && <p className="mb-3 text-center text-sm text-gray-600">{aviso}</p>}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <button type="button" onClick={onImprimir} className="rounded-xl bg-sky-50 px-2 py-3 text-center text-sky-700">
            <Printer size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">Imprimir / PDF</span>
            <span className="block text-[11px]">Imprimir ou salvar em PDF</span>
          </button>
          <button type="button" disabled={!entrega.telefone || enviando !== null} onClick={onWhatsapp} className="rounded-xl bg-emerald-50 px-2 py-3 text-center text-emerald-700 disabled:opacity-40">
            <MessageCircle size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">{enviando === "whatsapp" ? "Enviando..." : "WhatsApp"}</span>
            <span className="block text-[11px]">{entrega.telefone ? "Enviar o recibo pelo WhatsApp" : "Informe um telefone"}</span>
          </button>
          <button type="button" disabled={!entrega.email || enviando !== null} onClick={onEmail} className="rounded-xl bg-violet-50 px-2 py-3 text-center text-violet-700 disabled:opacity-40">
            <Mail size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">{enviando === "email" ? "Enviando..." : "E-mail"}</span>
            <span className="block text-[11px]">{entrega.email ? "Enviar o recibo por e-mail" : "Informe um e-mail"}</span>
          </button>
          <button type="button" onClick={onFechar} className="rounded-xl bg-gray-100 px-2 py-3 text-center text-gray-600">
            <X size={18} className="mx-auto" />
            <span className="mt-1 block text-sm font-semibold">Fechar</span>
            <span className="block text-[11px]">Sem enviar agora</span>
          </button>
        </div>
      </div>
    </div>
  );
}
