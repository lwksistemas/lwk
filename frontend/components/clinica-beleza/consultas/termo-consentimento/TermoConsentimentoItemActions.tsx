import { Download, Mail, MessageCircle, RefreshCw } from "lucide-react";
import type { TermoConsentimentoCanal, TermoProcedimento } from "./termo-consentimento-types";
import { TERMO_STATUS_BADGE } from "./termo-consentimento-types";

export function TermoConsentimentoItemActions({
  termo,
  loading,
  termoWhatsappHabilitado,
  onEnviar,
  onReenviar,
  onBaixarPdf,
  onEnviarPdfWhatsapp,
}: {
  termo: TermoProcedimento;
  loading: boolean;
  termoWhatsappHabilitado: boolean;
  onEnviar: (procedureId: number, canal: TermoConsentimentoCanal) => void;
  onReenviar: (procedureId: number, nome: string, canal: TermoConsentimentoCanal) => void;
  onBaixarPdf: (procedureId: number, nome: string) => void;
  onEnviarPdfWhatsapp: (procedureId: number, nome: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {termo.status === "rascunho" && (
        <>
          <button
            type="button"
            onClick={() => onEnviar(termo.procedure_id, "email")}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-white text-xs font-medium disabled:opacity-50"
            style={{ backgroundColor: "var(--cb-primary, #8B3D52)" }}
          >
            <Mail size={12} />
            E-mail
          </button>
          {termoWhatsappHabilitado && (
            <button
              type="button"
              onClick={() => onEnviar(termo.procedure_id, "whatsapp")}
              disabled={loading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-green-200 text-green-700 dark:border-green-800 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50"
            >
              <MessageCircle size={12} />
              WhatsApp
            </button>
          )}
        </>
      )}
      {(termo.status === "aguardando_paciente" || termo.status === "aguardando_profissional") && (
        <>
          <button
            type="button"
            onClick={() => onReenviar(termo.procedure_id, termo.procedure_nome, "email")}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} />
            Reenviar e-mail
          </button>
          {termoWhatsappHabilitado && termo.status === "aguardando_paciente" && (
            <button
              type="button"
              onClick={() => onReenviar(termo.procedure_id, termo.procedure_nome, "whatsapp")}
              disabled={loading}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-green-200 text-green-700 dark:border-green-800 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50"
            >
              <MessageCircle size={12} />
              Reenviar WhatsApp
            </button>
          )}
        </>
      )}
      <button
        type="button"
        onClick={() => onBaixarPdf(termo.procedure_id, termo.procedure_nome)}
        disabled={loading}
        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-gray-200 dark:border-neutral-600 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
      >
        <Download size={12} />
        PDF
      </button>
      {termo.status === "concluido" && termoWhatsappHabilitado && (
        <button
          type="button"
          onClick={() => onEnviarPdfWhatsapp(termo.procedure_id, termo.procedure_nome)}
          disabled={loading}
          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium border border-green-200 text-green-700 dark:border-green-800 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50"
          title="Enviar PDF assinado no WhatsApp do cliente"
        >
          <MessageCircle size={12} />
          WhatsApp PDF
        </button>
      )}
    </div>
  );
}

export function TermoConsentimentoItemRow({
  termo,
  loading,
  termoWhatsappHabilitado,
  onEnviar,
  onReenviar,
  onBaixarPdf,
  onEnviarPdfWhatsapp,
}: {
  termo: TermoProcedimento;
  loading: boolean;
  termoWhatsappHabilitado: boolean;
  onEnviar: (procedureId: number, canal: TermoConsentimentoCanal) => void;
  onReenviar: (procedureId: number, nome: string, canal: TermoConsentimentoCanal) => void;
  onBaixarPdf: (procedureId: number, nome: string) => void;
  onEnviarPdfWhatsapp: (procedureId: number, nome: string) => void;
}) {
  return (
    <li className="px-4 py-3">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-sm font-medium text-gray-900 dark:text-gray-100 leading-tight">
          {termo.procedure_nome}
        </span>
        <span
          className={`shrink-0 text-[10px] px-2 py-0.5 rounded-full font-medium ${
            TERMO_STATUS_BADGE[termo.status] || TERMO_STATUS_BADGE.rascunho
          }`}
        >
          {termo.status_display}
        </span>
      </div>
      <TermoConsentimentoItemActions
        termo={termo}
        loading={loading}
        termoWhatsappHabilitado={termoWhatsappHabilitado}
        onEnviar={onEnviar}
        onReenviar={onReenviar}
        onBaixarPdf={onBaixarPdf}
        onEnviarPdfWhatsapp={onEnviarPdfWhatsapp}
      />
    </li>
  );
}
