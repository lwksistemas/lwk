import { Mail, MessageCircle } from "lucide-react";
import type { TermoConsentimentoCanal, TermoProcedimento } from "./termo-consentimento-types";
import { TermoConsentimentoItemRow } from "./TermoConsentimentoItemActions";

export function TermoConsentimentoPanel({
  termos,
  loading,
  pendentesEnvioCount,
  termoWhatsappHabilitado,
  onEnviar,
  onReenviar,
  onBaixarPdf,
  onEnviarTodos,
}: {
  termos: TermoProcedimento[];
  loading: boolean;
  pendentesEnvioCount: number;
  termoWhatsappHabilitado: boolean;
  onEnviar: (procedureId: number, canal: TermoConsentimentoCanal) => void;
  onReenviar: (procedureId: number, nome: string, canal: TermoConsentimentoCanal) => void;
  onBaixarPdf: (procedureId: number, nome: string) => void;
  onEnviarTodos: (canal: TermoConsentimentoCanal) => void;
}) {
  return (
    <div className="absolute left-0 top-full mt-2 z-50 w-[min(100vw-2rem,22rem)] rounded-xl border border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-900 shadow-xl overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-100 dark:border-neutral-800">
        <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">Termos de consentimento</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          Cada procedimento exige leitura e assinatura separadas.
        </p>
      </div>

      <div className="max-h-[min(50vh,16rem)] overflow-y-auto">
        {!termos.length ? (
          <p className="px-4 py-6 text-sm text-gray-500 text-center">Carregando…</p>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-neutral-800">
            {termos.map((t) => (
              <TermoConsentimentoItemRow
                key={t.procedure_id}
                termo={t}
                loading={loading}
                termoWhatsappHabilitado={termoWhatsappHabilitado}
                onEnviar={onEnviar}
                onReenviar={onReenviar}
                onBaixarPdf={onBaixarPdf}
              />
            ))}
          </ul>
        )}
      </div>

      {pendentesEnvioCount > 1 && (
        <div className="px-4 py-3 border-t border-gray-100 dark:border-neutral-800 bg-gray-50/80 dark:bg-neutral-800/50 space-y-2">
          <button
            type="button"
            onClick={() => onEnviarTodos("email")}
            disabled={loading}
            className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-white text-sm font-medium disabled:opacity-50"
            style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
          >
            <Mail size={14} />
            {loading ? "Enviando…" : `Enviar todos por e-mail (${pendentesEnvioCount})`}
          </button>
          {termoWhatsappHabilitado && (
            <button
              type="button"
              onClick={() => onEnviarTodos("whatsapp")}
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium border border-green-200 text-green-700 dark:border-green-800 dark:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 disabled:opacity-50"
            >
              <MessageCircle size={14} />
              {loading ? "Enviando…" : `Enviar todos por WhatsApp (${pendentesEnvioCount})`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
