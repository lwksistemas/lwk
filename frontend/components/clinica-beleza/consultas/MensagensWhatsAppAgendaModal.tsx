"use client";

import { Loader2, MessageCircle, RotateCcw, X } from "lucide-react";
import { MensagemWhatsAppAjudaPanel } from "./mensagens-whatsapp-agenda/MensagemWhatsAppAjudaPanel";
import { MensagemWhatsAppEditorPanel } from "./mensagens-whatsapp-agenda/MensagemWhatsAppEditorPanel";
import { useMensagensWhatsAppAgenda } from "./mensagens-whatsapp-agenda/useMensagensWhatsAppAgenda";

interface MensagensWhatsAppAgendaModalProps {
  open: boolean;
  onClose: () => void;
}

export function MensagensWhatsAppAgendaModal({ open, onClose }: MensagensWhatsAppAgendaModalProps) {
  const { loading, saving, mensagem, error, setMensagem, usarPadraoSistema, salvar } =
    useMensagensWhatsAppAgenda(open, onClose);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50 p-0 sm:p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-t-xl sm:rounded-xl shadow-xl w-full max-w-md sm:max-w-4xl sm:w-[calc(100vw-2rem)] max-h-[95vh] sm:max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 sm:px-6 py-4 border-b border-gray-200 dark:border-neutral-700 shrink-0">
          <div className="flex items-center gap-2">
            <MessageCircle size={18} style={{ color: 'var(--cb-primary, #8B3D52)' }} />
            <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
              Mensagem WhatsApp — confirmação
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 text-gray-500"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="p-4 sm:p-6 overflow-y-auto flex-1">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
            <MensagemWhatsAppAjudaPanel />
            <MensagemWhatsAppEditorPanel
              loading={loading}
              mensagem={mensagem}
              error={error}
              onMensagemChange={setMensagem}
            />
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 px-4 sm:px-6 py-4 border-t border-gray-200 dark:border-neutral-700 shrink-0">
          <button
            type="button"
            onClick={usarPadraoSistema}
            disabled={saving || loading}
            className="inline-flex items-center gap-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 disabled:opacity-50"
          >
            <RotateCcw size={14} />
            Usar padrão do sistema
          </button>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={saving}
              className="px-4 py-2 text-sm rounded-lg border border-gray-300 dark:border-neutral-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-neutral-800 disabled:opacity-50"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={() => void salvar()}
              disabled={saving || loading}
              className="px-4 py-2 text-sm text-white rounded-lg disabled:opacity-50 inline-flex items-center gap-2"
              style={{ backgroundColor: 'var(--cb-primary, #8B3D52)' }}
            >
              {saving && <Loader2 size={14} className="animate-spin" />}
              Salvar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
