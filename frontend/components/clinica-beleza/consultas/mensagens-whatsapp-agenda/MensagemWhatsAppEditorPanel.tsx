import { Loader2 } from "lucide-react";
import { MENSAGEM_WHATSAPP_PADRAO } from "./mensagens-whatsapp-agenda-constants";

export function MensagemWhatsAppEditorPanel({
  loading,
  mensagem,
  error,
  onMensagemChange,
}: {
  loading: boolean;
  mensagem: string;
  error: string;
  onMensagemChange: (v: string) => void;
}) {
  return (
    <div className="space-y-3">
      {loading ? (
        <div className="flex items-center justify-center py-8 text-gray-500">
          <Loader2 size={20} className="animate-spin mr-2" />
          Carregando...
        </div>
      ) : (
        <textarea
          value={mensagem}
          onChange={(e) => onMensagemChange(e.target.value)}
          rows={14}
          placeholder={MENSAGEM_WHATSAPP_PADRAO}
          className="w-full rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 font-mono leading-relaxed resize-y min-h-[280px]"
        />
      )}

      {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
    </div>
  );
}
