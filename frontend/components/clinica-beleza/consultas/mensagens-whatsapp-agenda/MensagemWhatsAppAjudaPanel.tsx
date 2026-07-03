import {
  MENSAGEM_WHATSAPP_PADRAO,
  MENSAGEM_WHATSAPP_PLACEHOLDERS,
} from "./mensagens-whatsapp-agenda-constants";

export function MensagemWhatsAppAjudaPanel() {
  return (
    <div className="space-y-4">
      <p className="text-sm text-gray-600 dark:text-gray-400">
        Texto enviado ao paciente com o link para confirmar ou cancelar o agendamento. Deixe em branco
        para usar a mensagem padrão do sistema.
      </p>

      <div>
        <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Variáveis disponíveis</p>
        <div className="flex flex-wrap gap-1.5">
          {MENSAGEM_WHATSAPP_PLACEHOLDERS.map((ph) => (
            <code
              key={ph}
              className="text-xs px-2 py-0.5 rounded bg-gray-100 dark:bg-neutral-800 text-gray-700 dark:text-gray-300"
            >
              {ph}
            </code>
          ))}
        </div>
      </div>

      <div className="rounded-lg border border-dashed border-gray-200 dark:border-neutral-700 p-3 text-xs text-gray-500 dark:text-gray-400 font-mono whitespace-pre-wrap hidden lg:block">
        {MENSAGEM_WHATSAPP_PADRAO}
      </div>
    </div>
  );
}
